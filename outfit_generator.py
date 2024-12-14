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

def bulk_delete_items(item_ids: List[int]) -> Tuple[bool, str, Dict]:
    """Delete multiple clothing items in bulk with their associated files
    
    Args:
        item_ids: List of item IDs to delete
        
    Returns:
        Tuple containing:
        - Success status (bool)
        - Status message (str)
        - Statistics dictionary with counts of successes and failures
    """
    if not item_ids:
        return True, "No items to delete", {"deleted": 0, "failed": 0}
        
    stats = {
        "deleted": 0,
        "failed": 0,
        "errors": []
    }
    
    # Process deletions in batches using thread pool
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Split into reasonable batch sizes
        batch_size = 10
        batches = [item_ids[i:i + batch_size] for i in range(0, len(item_ids), batch_size)]
        
        # Process each batch
        for batch in batches:
            try:
                from data_manager import get_db_connection
                
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    try:
                        # Get image paths for the batch
                        placeholders = ','.join(['%s'] * len(batch))
                        cur.execute(f"""
                            SELECT id, image_path 
                            FROM user_clothing_items 
                            WHERE id IN ({placeholders})
                        """, tuple(batch))
                        items = cur.fetchall()
                        
                        for item_id, image_path in items:
                            try:
                                # Delete the image file if it exists
                                if image_path and os.path.exists(image_path):
                                    os.remove(image_path)
                                
                                # Delete from database
                                cur.execute("""
                                    DELETE FROM user_clothing_items 
                                    WHERE id = %s
                                """, (item_id,))
                                
                                stats["deleted"] += 1
                                logging.info(f"Successfully deleted item {item_id}")
                                
                            except Exception as e:
                                stats["failed"] += 1
                                error_msg = f"Failed to delete item {item_id}: {str(e)}"
                                stats["errors"].append(error_msg)
                                logging.error(error_msg)
                        
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        raise
                    finally:
                        cur.close()
                        
            except Exception as e:
                batch_error = f"Batch processing error: {str(e)}"
                stats["errors"].append(batch_error)
                logging.error(batch_error)
                stats["failed"] += len(batch)
    
    # Prepare result message
    message = f"Deleted {stats['deleted']} items"
    if stats["failed"] > 0:
        message += f", {stats['failed']} failed"
    
    success = stats["failed"] == 0
    
    if stats["errors"]:
        logging.warning("Bulk delete errors:\n" + "\n".join(stats["errors"]))
    
    return success, message, stats

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
        os.makedirs('merged_outfits', exist_ok=True)
    
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
            
            # Create a new image using the template
            merged_image = template.copy()
            
            # Add color palette section on the center-left
            palette_width = int(template_width * 0.2)  # 20% of template width
            palette_x = int(template_width * 0.05)  # 5% margin from left
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
                            (
                                palette_x,
                                swatch_y,
                                palette_x + swatch_size,
                                swatch_y + swatch_size
                            ),
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
            
            # Add each clothing item to the merged image with improved sizing
            # Adjust x_position to account for palette width
            for i, item_type in enumerate(['shirt', 'pants', 'shoes']):
                item_img = Image.open(selected_outfit[item_type]['image_path'])
                
                # Calculate dimensions with adjusted scaling
                aspect_ratio = item_img.size[0] / item_img.size[1]
                new_height = int(item_height * 1.1)  # Maintained proportion
                new_width = int(new_height * aspect_ratio)
                
                # Ensure width doesn't exceed template width while maintaining proportion
                if new_width > template_width * 0.9:
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