import pandas as pd
import random
from PIL import Image, ImageDraw, ImageFont
import os
import uuid
import logging
from datetime import datetime, timedelta
import time
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict
import psycopg2

def is_valid_image(image_path: str) -> bool:
    """Validate if an image file exists and can be opened"""
    try:
        if not os.path.exists(image_path):
            return False
        # Try to open the image to ensure it's valid
        with Image.open(image_path) as img:
            img.verify()
        return True
    except Exception as e:
        logging.debug(f"Invalid image file {image_path}: {str(e)}")
        return False

def delete_file_batch(file_batch: List[str]) -> Tuple[int, List[str]]:
    """Delete a batch of files and return success count and errors"""
    success_count = 0
    errors = []
    
    for file_path in file_batch:
        try:
            os.remove(file_path)
            success_count += 1
            logging.debug(f"Successfully deleted file: {os.path.basename(file_path)}")
        except Exception as e:
            errors.append(f"Error deleting {file_path}: {str(e)}")
            logging.error(f"Failed to delete file {file_path}: {str(e)}")
    
    return success_count, errors

def cleanup_merged_outfits():
    """Clean up old unsaved outfit files and orphaned database entries"""
    try:
        # First, clean up orphaned database entries
        from data_manager import cleanup_orphaned_entries
        success, message = cleanup_orphaned_entries()
        if not success:
            logging.error(f"Failed to clean up orphaned entries: {message}")
        else:
            logging.info(f"Orphaned entries cleanup: {message}")

        if not os.path.exists('merged_outfits'):
            logging.info("Merged outfits directory does not exist. No cleanup needed.")
            return
            
        # Get cleanup settings from database
        from data_manager import get_cleanup_settings, update_last_cleanup_time
        
        settings = get_cleanup_settings()
        if not settings:
            logging.error("Failed to get cleanup settings from database")
            return
            
        current_time = datetime.now()
        last_cleanup = settings['last_cleanup']
        cleanup_interval = timedelta(hours=settings['cleanup_interval_hours'])
        
        # Check if cleanup is needed based on interval
        if last_cleanup and (current_time - last_cleanup) < cleanup_interval:
            logging.info(f"Cleanup not needed yet. Next cleanup in {cleanup_interval - (current_time - last_cleanup)}")
            return
            
        stats = {
            'total_files': 0,
            'cleaned_count': 0,
            'skipped_files': 0,
            'error_count': 0,
            'batches_processed': 0
        }
        all_errors = []
        
        # Get list of saved outfits from database to avoid deleting them
        from data_manager import get_db_connection
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("SELECT image_path FROM saved_outfits WHERE image_path IS NOT NULL")
                saved_paths = set(path[0] for path in cur.fetchall())
                logging.info(f"Found {len(saved_paths)} saved outfits to preserve")
            finally:
                cur.close()
        
        # Get all files to delete
        files_to_delete = []
        for filename in os.listdir('merged_outfits'):
            stats['total_files'] += 1
            file_path = os.path.join('merged_outfits', filename)
            
            # Skip if file is in saved outfits
            if file_path in saved_paths:
                stats['skipped_files'] += 1
                logging.debug(f"Skipping saved outfit file: {filename}")
                continue
                
            # Check file age
            try:
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                age = current_time - file_time
                
                if age > timedelta(hours=settings['max_age_hours']):
                    files_to_delete.append(file_path)
                    logging.debug(f"Marking file for deletion: {filename} (Age: {age})")
                else:
                    stats['skipped_files'] += 1
                    logging.debug(f"File {filename} is not old enough for cleanup (Age: {age})")
            except OSError as e:
                logging.error(f"Error checking file age for {file_path}: {str(e)}")
                stats['error_count'] += 1
                continue
        
        # Process files in batches using thread pool
        if files_to_delete:
            with ThreadPoolExecutor(max_workers=settings['max_workers']) as executor:
                # Split files into batches
                batches = [files_to_delete[i:i + settings['batch_size']] 
                          for i in range(0, len(files_to_delete), settings['batch_size'])]
                
                # Submit batch jobs
                future_to_batch = {
                    executor.submit(delete_file_batch, batch): batch 
                    for batch in batches
                }
                
                # Process completed batches
                for future in as_completed(future_to_batch):
                    batch = future_to_batch[future]
                    try:
                        success_count, errors = future.result()
                        stats['cleaned_count'] += success_count
                        stats['error_count'] += len(errors)
                        all_errors.extend(errors)
                        stats['batches_processed'] += 1
                        
                        # Log batch completion
                        logging.info(f"Batch completed: {success_count}/{len(batch)} files deleted successfully")
                        if errors:
                            logging.warning(f"Batch errors: {len(errors)} errors occurred")
                    except Exception as e:
                        logging.error(f"Batch processing error: {str(e)}")
                        stats['error_count'] += len(batch)
        
        # Update last cleanup time
        update_last_cleanup_time()
        
        # Log final cleanup statistics
        logging.info(
            f"Cleanup Summary: "
            f"Total files: {stats['total_files']}, "
            f"Cleaned: {stats['cleaned_count']}, "
            f"Skipped: {stats['skipped_files']}, "
            f"Errors: {stats['error_count']}, "
            f"Batches: {stats['batches_processed']}"
        )
        
        if all_errors:
            logging.warning(f"Cleanup Errors:\n" + "\n".join(all_errors))
        
        return stats['cleaned_count']
    except Exception as e:
        logging.error(f"Error during outfit cleanup: {str(e)}")
        return 0

def calculate_outfit_total_price(outfit: Dict) -> float:
    """Calculate the total price of an outfit"""
    total_price = 0.0
    for item_type, item in outfit.items():
        if item_type != 'merged_image_path' and isinstance(item, dict):
            if 'price' in item and item['price'] is not None:
                total_price += float(item['price'])
    return total_price

def generate_outfit(clothing_items, size, style, gender):
    """Generate an outfit based on given criteria"""
    selected_outfit = {}
    missing_items = []
    
    if not os.path.exists('merged_outfits'):
        os.makedirs('merged_outfits')
    
    cleanup_merged_outfits()
    
    # Add a small delay for better user experience
    time.sleep(0.5)
    
    # Filter items based on criteria
    filtered_items = clothing_items[
        (clothing_items['size'].str.contains(size, na=False)) &
        (clothing_items['style'].str.contains(style, na=False)) &
        (clothing_items['gender'].str.contains(gender, na=False))
    ]
    
    # Select one item of each type, ensuring images are valid
    for item_type in ['shirt', 'pants', 'shoes']:
        type_items = filtered_items[filtered_items['type'] == item_type]
        
        # Filter out items with invalid images
        valid_items = type_items[type_items['image_path'].apply(lambda x: is_valid_image(x))]
        
        if not valid_items.empty:
            selected_item = valid_items.sample(n=1).iloc[0]
            selected_outfit[item_type] = {
                'image_path': selected_item['image_path'],
                'color': selected_item['color'],
                'price': float(selected_item['price']) if selected_item['price'] else 0,
                'hyperlink': selected_item['hyperlink'] if selected_item['hyperlink'] else None
            }
        else:
            missing_items.append(item_type)
    
    if len(selected_outfit) == 3:  # We have all three items
        try:
            # Add a small delay before image processing
            time.sleep(0.5)
            
            # Increase template dimensions for larger display
            template_width = 750  # Reduced by 25% from 1000
            template_height = 900  # Reduced by 25% from 1200
            background_color = (174, 162, 150)  # HEX AEA296 in RGB
            template = Image.new('RGB', (template_width, template_height), background_color)
            
            # Adjust template height while maintaining proportions
            new_template_height = int(template_height * 0.8)  # Maintaining proportion while using new height
            template = template.resize((template_width, new_template_height))
            template_width, template_height = template.size
            
            # Optimize vertical spacing with adjusted dimensions
            item_height = template_height // 4  # Adjusted for new template height
            vertical_spacing = item_height // 6  # Maintained proportion
            
            # Load the mannequin template
            try:
                mannequin_template = Image.open('background template.png')
                # Resize mannequin template to match our dimensions while maintaining aspect ratio
                template_ratio = mannequin_template.size[1] / mannequin_template.size[0]
                new_template_height = int(template_width * template_ratio)
                mannequin_template = mannequin_template.resize((template_width, new_template_height), Image.Resampling.LANCZOS)
                merged_image = mannequin_template.copy()
            except Exception as e:
                logging.error(f"Error loading mannequin template: {str(e)}")
                # Fallback to plain template if mannequin template fails to load
                merged_image = template.copy()
            
            # Add color palette section on the right side
            palette_width = int(template_width * 0.15)  # 15% of template width
            palette_x = int(template_width * 0.82)  # 82% from left (right side)
            palette_y = int(template_height * 0.2)  # Start at 20% from top
            
            # Draw color swatches for each item
            swatch_size = int(palette_width * 0.8)  # 80% of palette width
            swatch_margin = int(swatch_size * 0.2)  # 20% of swatch size
            
            draw = ImageDraw.Draw(merged_image)
            
            for i, (item_type, item) in enumerate(selected_outfit.items()):
                if item_type not in ['merged_image_path', 'total_price']:
                    # Parse color and create swatch
                    color_str = str(item['color'])
                    if isinstance(color_str, str) and color_str.startswith('rgb'):
                        try:
                            color = tuple(map(int, color_str.strip('rgb()').split(',')))
                        except:
                            continue
                        
                        # Draw color swatch
                        swatch_y = palette_y + (i * (swatch_size + swatch_margin))
                        draw.rectangle(
                            [
                                palette_x,
                                swatch_y,
                                palette_x + swatch_size,
                                swatch_y + swatch_size
                            ],
                            fill=color,
                            outline=(255, 255, 255),
                            width=2
                        )
                        
                        # Add item label
                        draw.text(
                            (palette_x, swatch_y - 20),
                            item_type.capitalize(),
                            fill=(255, 255, 255),
                            font=ImageFont.load_default()
                        )
            
            # Add each clothing item to the merged image with mannequin-specific positioning
            # Define relative positions for each item type on the mannequin
            position_map = {
                'shirt': {
                    'width_ratio': 0.45,  # 45% of template width
                    'height_ratio': 0.35,  # 35% of item height
                    'x_offset_ratio': 0.27,  # 27% from left
                    'y_offset_ratio': 0.15,  # 15% from top
                },
                'pants': {
                    'width_ratio': 0.35,  # 35% of template width
                    'height_ratio': 0.45,  # 45% of item height
                    'x_offset_ratio': 0.32,  # 32% from left
                    'y_offset_ratio': 0.45,  # 45% from top
                },
                'shoes': {
                    'width_ratio': 0.25,  # 25% of template width
                    'height_ratio': 0.15,  # 15% of item height
                    'x_offset_ratio': 0.37,  # 37% from left
                    'y_offset_ratio': 0.85,  # 85% from top
                }
            }

            for item_type in ['shirt', 'pants', 'shoes']:
                item_img = Image.open(selected_outfit[item_type]['image_path'])
                position = position_map[item_type]
                
                # Calculate dimensions based on template size
                new_width = int(template_width * position['width_ratio'])
                aspect_ratio = item_img.size[0] / item_img.size[1]
                new_height = int(new_width / aspect_ratio)
                
                # Resize the item image
                item_img = item_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Calculate position based on template dimensions
                x_position = int(template_width * position['x_offset_ratio'])
                y_position = int(template_height * position['y_offset_ratio'])
                
                # Create a mask for transparency
                if item_img.mode == 'RGBA':
                    mask = item_img.split()[3]
                else:
                    mask = None
                
                # Paste the item image
                merged_image.paste(item_img, (x_position, y_position), mask)
            
            # Save the merged image
            merged_filename = f"outfit_{uuid.uuid4()}.png"
            merged_path = os.path.join('merged_outfits', merged_filename)
            merged_image.save(merged_path)
            
            # Add the merged image path to the outfit dictionary
            selected_outfit['merged_image_path'] = merged_path
            
            # Calculate and add total price to the outfit dictionary
            selected_outfit['total_price'] = calculate_outfit_total_price(selected_outfit)
            
        except Exception as e:
            logging.error(f"Error creating merged outfit image: {str(e)}")
            return {}, ['Error creating outfit image']
    
    return selected_outfit, missing_items
