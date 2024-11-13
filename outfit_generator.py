import pandas as pd
import random
from PIL import Image
import os
import uuid
import logging
from datetime import datetime, timedelta
import time
from contextlib import contextmanager

def cleanup_merged_outfits(max_age_hours=24):
    """Clean up old unsaved outfit files from merged_outfits folder with improved connection handling"""
    try:
        if not os.path.exists('merged_outfits'):
            return
            
        current_time = datetime.now()
        cleaned_count = 0
        
        # Get list of saved outfits from database to avoid deleting them
        from data_manager import get_db_connection
        
        with get_db_connection() as conn:  # Properly use context manager
            cur = conn.cursor()
            try:
                # Use prepared statement for better performance
                cur.execute("SELECT image_path FROM saved_outfits WHERE image_path IS NOT NULL")
                saved_paths = set(path[0] for path in cur.fetchall())
            finally:
                cur.close()
        
        # Get all files to delete
        files_to_delete = []
        for filename in os.listdir('merged_outfits'):
            file_path = os.path.join('merged_outfits', filename)
            
            # Skip if file is in saved outfits
            if file_path in saved_paths:
                continue
                
            # Check file age
            try:
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                age = current_time - file_time
                
                if age > timedelta(hours=max_age_hours):
                    files_to_delete.append(file_path)
            except OSError as e:
                logging.error(f"Error checking file age for {file_path}: {str(e)}")
                continue
        
        # Batch delete files
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                cleaned_count += 1
            except Exception as e:
                logging.error(f"Error removing old outfit file {file_path}: {str(e)}")
                continue
                    
        logging.info(f"Cleaned up {cleaned_count} old outfit files")
        return cleaned_count
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
