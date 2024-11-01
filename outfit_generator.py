import pandas as pd
import random
from PIL import Image
import os
import uuid

def generate_outfit(clothing_items, size, style, gender):
    selected_outfit = {}
    missing_items = []
    
    # Create directory for merged outfits if it doesn't exist
    if not os.path.exists('merged_outfits'):
        os.makedirs('merged_outfits')
    
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
        # Create a new image with white background
        width = 100  # Changed from 200 to 100
        total_height = 300  # Changed from 600 to 300
        merged_image = Image.new('RGB', (width, total_height), (255, 255, 255))
        
        # Add each clothing item to the merged image
        for i, item_type in enumerate(['shirt', 'pants', 'shoes']):
            try:
                item_img = Image.open(selected_outfit[item_type]['image_path'])
                # Resize while maintaining aspect ratio
                item_img.thumbnail((width, 100))  # Changed from 200 to 100
                # Calculate position to center horizontally
                x_position = (width - item_img.size[0]) // 2
                # Paste the image vertically with updated spacing
                merged_image.paste(item_img, (x_position, i * 100))  # Changed from i * 200 to i * 100
            except Exception as e:
                print(f"Error processing {item_type} image: {str(e)}")
        
        # Save the merged image
        merged_filename = f"outfit_{uuid.uuid4()}.png"
        merged_path = os.path.join('merged_outfits', merged_filename)
        merged_image.save(merged_path)
        
        # Add the merged image path to the outfit dictionary
        selected_outfit['merged_image_path'] = merged_path
    
    return selected_outfit, missing_items
