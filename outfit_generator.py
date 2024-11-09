import pandas as pd
import random
from PIL import Image
import os
import uuid
import logging
from datetime import datetime, timedelta
import numpy as np
from color_recommendation import (
    learn_color_preferences,
    recommend_matching_colors,
    calculate_color_harmony_score
)
from data_manager import load_saved_outfits

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

def parse_color(color_str):
    """Parse color string to RGB tuple"""
    try:
        return tuple(map(int, color_str.split(',')))
    except:
        return (0, 0, 0)

def filter_by_color_harmony(items_df, selected_items, min_harmony_score=0.6):
    """Filter items based on color harmony with already selected items"""
    filtered_items = items_df.copy()
    
    if selected_items:
        selected_colors = [parse_color(item['color']) for item in selected_items.values()]
        
        def calculate_harmony(color_str):
            color = parse_color(color_str)
            scores = [calculate_color_harmony_score(color, sc) for sc in selected_colors]
            return np.mean(scores)
        
        filtered_items['harmony_score'] = filtered_items['color'].apply(calculate_harmony)
        filtered_items = filtered_items[filtered_items['harmony_score'] >= min_harmony_score]
    
    return filtered_items

def generate_outfit(clothing_items, size, style, gender):
    """Generate outfit with smart color matching"""
    selected_outfit = {}
    missing_items = []
    
    if not os.path.exists('merged_outfits'):
        os.makedirs('merged_outfits')
    
    cleanup_merged_outfits()
    
    # Load saved outfits for learning color preferences
    saved_outfits = load_saved_outfits()
    color_combinations, color_scores = learn_color_preferences(saved_outfits)
    
    # Order of selection: shirt first (as anchor), then pants, then shoes
    selection_order = ['shirt', 'pants', 'shoes']
    
    for item_type in selection_order:
        type_items = clothing_items[clothing_items['type'] == item_type]
        filtered_items = type_items[
            (type_items['size'].str.contains(size, na=False)) &
            (type_items['style'].str.contains(style, na=False)) &
            (type_items['gender'].str.contains(gender, na=False))
        ]
        
        # Apply color harmony filtering if we already have selected items
        if selected_outfit:
            filtered_items = filter_by_color_harmony(filtered_items, selected_outfit)
        
        if len(filtered_items) > 0:
            # If this is not the first item, use color recommendations
            if selected_outfit:
                best_harmony_score = 0
                best_item = None
                
                for _, item in filtered_items.iterrows():
                    current_color = parse_color(item['color'])
                    harmony_scores = []
                    
                    for selected_item in selected_outfit.values():
                        selected_color = parse_color(selected_item['color'])
                        harmony_scores.append(
                            calculate_color_harmony_score(current_color, selected_color)
                        )
                    
                    avg_harmony = np.mean(harmony_scores)
                    if avg_harmony > best_harmony_score:
                        best_harmony_score = avg_harmony
                        best_item = item
                
                if best_item is not None:
                    selected_outfit[item_type] = best_item.to_dict()
            else:
                # For the first item, select randomly
                selected_outfit[item_type] = filtered_items.iloc[
                    random.randint(0, len(filtered_items) - 1)
                ].to_dict()
        else:
            missing_items.append(item_type)
    
    if len(selected_outfit) == 3:  # We have all three items
        try:
            # Create outfit visualization
            template_width = 1000
            template_height = 1200
            background_color = (174, 162, 150)  # HEX AEA296 in RGB
            template = Image.new('RGB', (template_width, template_height), background_color)
            
            new_template_height = int(template_height * 0.8)
            template = template.resize((template_width, new_template_height))
            template_width, template_height = template.size
            
            item_height = template_height // 4
            vertical_spacing = item_height // 6
            
            merged_image = template.copy()
            
            for i, item_type in enumerate(['shirt', 'pants', 'shoes']):
                try:
                    item_img = Image.open(selected_outfit[item_type]['image_path'])
                    
                    aspect_ratio = item_img.size[0] / item_img.size[1]
                    new_height = int(item_height * 1.1)
                    new_width = int(new_height * aspect_ratio)
                    
                    if new_width > template_width * 0.9:
                        new_width = int(template_width * 0.9)
                        new_height = int(new_width / aspect_ratio)
                    
                    item_img = item_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    x_position = (template_width - new_width) // 2
                    y_position = vertical_spacing + (i * (item_height + vertical_spacing))
                    
                    if item_img.mode == 'RGBA':
                        mask = item_img.split()[3]
                    else:
                        mask = None
                    
                    merged_image.paste(item_img, (x_position, y_position), mask)
                    
                except Exception as e:
                    logging.error(f"Error processing {item_type} image: {str(e)}")
            
            merged_filename = f"outfit_{uuid.uuid4()}.png"
            merged_path = os.path.join('merged_outfits', merged_filename)
            merged_image.save(merged_path)
            
            selected_outfit['merged_image_path'] = merged_path
            
        except Exception as e:
            logging.error(f"Error creating merged outfit image: {str(e)}")
    
    return selected_outfit, missing_items
