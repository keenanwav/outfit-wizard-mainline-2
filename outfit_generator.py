import pandas as pd
import random
from PIL import Image, ImageDraw, ImageFont
import os
import uuid
import logging
from datetime import datetime, timedelta
from color_utils import get_color_palette, rgb_to_hex

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

def add_text_to_image(draw, text, position, font_size=30):
    """Add text to image with fixed styling"""
    try:
        # Try to use Arial font, fall back to default if not available
        try:
            font = ImageFont.truetype("Arial", font_size)
        except:
            font = ImageFont.load_default()
        
        draw.text(position, text, fill="black", font=font)
    except Exception as e:
        logging.error(f"Error adding text to image: {str(e)}")

def generate_outfit(clothing_items, size, style, gender):
    selected_outfit = {}
    missing_items = []
    
    if not os.path.exists('merged_outfits'):
        os.makedirs('merged_outfits')
    
    cleanup_merged_outfits()
    
    # Select items
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
            # Create template with new dimensions
            template_width = 800
            template_height = 1000
            background_color = (174, 162, 150)  # HEX AEA296 in RGB
            template = Image.new('RGB', (template_width, template_height), background_color)
            draw = ImageDraw.Draw(template)
            
            # Add title
            add_text_to_image(draw, "FULL OUTFIT", (template_width//2 - 80, 20), font_size=40)
            
            # Calculate dimensions for item placement
            item_width = template_width // 3
            item_height = template_height // 3
            padding = 20
            
            # Create sections for each item with rounded corners
            section_color = (230, 230, 230)  # Light gray for item sections
            
            # Function to create rounded rectangle section
            def create_section(width, height):
                section = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                section_draw = ImageDraw.Draw(section)
                section_draw.rounded_rectangle([(0, 0), (width-1, height-1)], radius=20, fill=section_color)
                return section
            
            # Add sections and items
            # Left section (shirt)
            left_section = create_section(item_width - padding*2, item_height - padding)
            template.paste(left_section, (padding, 80), left_section)
            add_text_to_image(draw, "shirt", (padding + 20, item_height - padding))
            
            # Right section (pants)
            right_section = create_section(item_width - padding*2, item_height*1.5 - padding)
            template.paste(right_section, (template_width - item_width, 80), right_section)
            add_text_to_image(draw, "pants", (template_width - item_width + 20, item_height - padding))
            add_text_to_image(draw, "shoes", (template_width - item_width + 20, item_height*1.2))
            
            # Place items in their sections
            for item_type in ['shirt', 'pants', 'shoes']:
                try:
                    item_img = Image.open(selected_outfit[item_type]['image_path'])
                    if item_img.mode == 'RGBA':
                        mask = item_img.split()[3]
                    else:
                        mask = None
                    
                    # Calculate item dimensions
                    if item_type == 'shirt':
                        max_width = item_width - padding*3
                        max_height = item_height - padding*2
                        x_pos = padding*2
                        y_pos = 100
                    elif item_type == 'pants':
                        max_width = item_width - padding*3
                        max_height = item_height - padding*2
                        x_pos = template_width - item_width + padding
                        y_pos = 100
                    else:  # shoes
                        max_width = item_width - padding*3
                        max_height = item_height - padding*2
                        x_pos = template_width - item_width + padding
                        y_pos = item_height + 100
                    
                    # Resize item while maintaining aspect ratio
                    aspect_ratio = item_img.size[0] / item_img.size[1]
                    if aspect_ratio > 1:
                        new_width = min(max_width, int(max_height * aspect_ratio))
                        new_height = int(new_width / aspect_ratio)
                    else:
                        new_height = min(max_height, int(max_width / aspect_ratio))
                        new_width = int(new_height * aspect_ratio)
                    
                    item_img = item_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Center item in its section
                    x_center = x_pos + (max_width - new_width) // 2
                    y_center = y_pos + (max_height - new_height) // 2
                    template.paste(item_img, (x_center, y_center), mask)
                    
                except Exception as e:
                    logging.error(f"Error processing {item_type} image: {str(e)}")
            
            # Add color palette at the bottom
            palette_y = template_height - 150
            add_text_to_image(draw, "COLOR PALLET", (template_width//2 - 60, palette_y - 30))
            
            # Display individual colors for each item
            color_size = 50
            spacing = 20
            start_x = (template_width - (3 * color_size + 2 * spacing)) // 2
            
            for i, item_type in enumerate(['shirt', 'pants', 'shoes']):
                color = get_color_palette(selected_outfit[item_type]['image_path'], n_colors=1)[0]
                if color is not None:
                    color_x = start_x + i * (color_size + spacing)
                    draw.ellipse(
                        [(color_x, palette_y), (color_x + color_size, palette_y + color_size)],
                        fill=tuple(color)
                    )
            
            # Save the merged image
            merged_filename = f"outfit_{uuid.uuid4()}.png"
            merged_path = os.path.join('merged_outfits', merged_filename)
            template.save(merged_path)
            
            # Add the merged image path to the outfit dictionary
            selected_outfit['merged_image_path'] = merged_path
            
        except Exception as e:
            logging.error(f"Error creating merged outfit image: {str(e)}")
    
    return selected_outfit, missing_items
