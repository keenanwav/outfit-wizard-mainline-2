import pandas as pd
import random
from PIL import Image
import os
import uuid
import logging
from datetime import datetime, timedelta
import time
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict
import psycopg2

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
    """Clean up old unsaved outfit files from merged_outfits folder with configurable settings"""
    try:
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

def generate_outfit(clothing_items, size, style, gender):
    selected_outfit = {}
    missing_items = []
    
    if not os.path.exists('merged_outfits'):
        os.makedirs('merged_outfits')
    
    cleanup_merged_outfits()
    
    # Add a small delay for better user experience
    time.sleep(0.5)
    
    for item_type in ['shirt', 'pants', 'shoes']:
        type_items = clothing_items[clothing_items['type'] == item_type]
        filtered_items = type_items[
            (type_items['size'].str.contains(size, na=False)) &
            (type_items['style'].str.contains(style, na=False)) &
            (type_items['gender'].str.contains(gender, na=False))
        ]
        
        if len(filtered_items) > 0:
            selected_outfit[item_type] = filtered_items.iloc[random.randint(0, len(filtered_items) - 1)].to_dict()
        else:
            missing_items.append(item_type)
    
    if len(selected_outfit) == 3:  # We have all three items
        try:
            # Add a small delay before image processing
            time.sleep(0.5)
            
            # Increase template dimensions for larger display
            template_width = 1000  # Increased from 800
            template_height = 1200  # Increased from 1000
            background_color = (174, 162, 150)  # HEX AEA296 in RGB
            template = Image.new('RGB', (template_width, template_height), background_color)
            
            # Adjust template height while maintaining proportions
            new_template_height = int(template_height * 0.8)  # Increased from 0.7 for better vertical space usage
            template = template.resize((template_width, new_template_height))
            template_width, template_height = template.size
            
            # Optimize vertical spacing
            item_height = template_height // 4  # Increased from 5 for larger items
            vertical_spacing = item_height // 6  # Adjusted for better distribution
            
            # Create a new image using the template
            merged_image = template.copy()
            
            # Add each clothing item to the merged image with improved sizing
            for i, item_type in enumerate(['shirt', 'pants', 'shoes']):
                try:
                    item_img = Image.open(selected_outfit[item_type]['image_path'])
                    
                    # Calculate dimensions with improved scaling
                    aspect_ratio = item_img.size[0] / item_img.size[1]
                    new_height = int(item_height * 1.1)  # Increased from 0.9 for larger items
                    new_width = int(new_height * aspect_ratio)
                    
                    # Ensure width doesn't exceed template width while maintaining good size
                    if new_width > template_width * 0.9:  # Increased from 0.8 for larger items
                        new_width = int(template_width * 0.9)
                        new_height = int(new_width / aspect_ratio)
                    
                    # Resize the item image
                    item_img = item_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Calculate position to center horizontally and adjust vertical position
                    x_position = (template_width - new_width) // 2
                    y_position = vertical_spacing + (i * (item_height + vertical_spacing))
                    
                    # Create a mask for transparency
                    if item_img.mode == 'RGBA':
                        mask = item_img.split()[3]
                    else:
                        mask = None
                    
                    # Paste the item image
                    merged_image.paste(item_img, (x_position, y_position), mask)
                    
                except Exception as e:
                    logging.error(f"Error processing {item_type} image: {str(e)}")
            
            # Save the merged image
            merged_filename = f"outfit_{uuid.uuid4()}.png"
            merged_path = os.path.join('merged_outfits', merged_filename)
            merged_image.save(merged_path)
            
            # Add the merged image path to the outfit dictionary
            selected_outfit['merged_image_path'] = merged_path
            
        except Exception as e:
            logging.error(f"Error creating merged outfit image: {str(e)}")
    
    return selected_outfit, missing_items