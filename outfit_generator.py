import pandas as pd
import random
from PIL import Image
import os
import uuid
import logging
from datetime import datetime, timedelta

def cleanup_merged_outfits(max_age_hours=24):
    """Clean up old unsaved outfit files from merged_outfits folder"""
    try:
        if not os.path.exists('merged_outfits'):
            return
            
        current_time = datetime.now()
        cleaned_count = 0
        
        # Get list of saved outfits from database to avoid deleting them
        from data_manager import get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT image_path FROM saved_outfits")
        saved_paths = set(path[0] for path in cur.fetchall())
        cur.close()
        conn.close()
        
        for filename in os.listdir('merged_outfits'):
            file_path = os.path.join('merged_outfits', filename)
            
            # Skip if file is in saved outfits
            if file_path in saved_paths:
                continue
                
            # Check file age
            file_time = datetime.fromtimestamp(os.path.getctime(file_path))
            age = current_time - file_time
            
            if age > timedelta(hours=max_age_hours):
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                except Exception as e:
                    logging.error(f"Error removing old outfit file {file_path}: {str(e)}")
                    
        logging.info(f"Cleaned up {cleaned_count} old outfit files")
        return cleaned_count
    except Exception as e:
        logging.error(f"Error during outfit cleanup: {str(e)}")
        return 0

def generate_outfit(clothing_items, size, style, gender):
    selected_outfit = {}
    missing_items = []
    
    # Create directory for merged outfits if it doesn't exist
    if not os.path.exists('merged_outfits'):
        os.makedirs('merged_outfits')
    
    # Clean up old files before generating new ones
    cleanup_merged_outfits()
    
    # Filter items by preferences
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
    
    # If we have a complete outfit, create a merged image
    if len(selected_outfit) == 3:  # We have all three items
        try:
            # Load the template image
            template = Image.open('yoyo.png')
            template_width, template_height = template.size
            
            # Calculate vertical spacing
            item_height = template_height // 4  # Divide height into 4 sections (3 items + spacing)
            vertical_spacing = item_height // 4
            
            # Create a new image using the template
            merged_image = template.copy()
            
            # Add each clothing item to the merged image
            for i, item_type in enumerate(['shirt', 'pants', 'shoes']):
                try:
                    item_img = Image.open(selected_outfit[item_type]['image_path'])
                    
                    # Calculate dimensions while maintaining aspect ratio
                    aspect_ratio = item_img.size[0] / item_img.size[1]
                    new_height = int(item_height * 0.8)  # 80% of section height
                    new_width = int(new_height * aspect_ratio)
                    
                    # Ensure width doesn't exceed template width
                    if new_width > template_width * 0.8:
                        new_width = int(template_width * 0.8)
                        new_height = int(new_width / aspect_ratio)
                    
                    # Resize the item image
                    item_img = item_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Calculate position to center horizontally
                    x_position = (template_width - new_width) // 2
                    y_position = (item_height * i) + vertical_spacing
                    
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
