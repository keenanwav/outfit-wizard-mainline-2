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
        total_width = 600
        height = 200
        merged_image = Image.new('RGB', (total_width, height), (255, 255, 255))
        
        # Add each clothing item to the merged image
        for i, item_type in enumerate(['shirt', 'pants', 'shoes']):
            try:
                item_img = Image.open(selected_outfit[item_type]['image_path'])
                # Resize while maintaining aspect ratio
                item_img.thumbnail((200, 200))
                # Calculate position to center vertically
                y_position = (height - item_img.size[1]) // 2
                # Paste the image
                merged_image.paste(item_img, (i * 200, y_position))
            except Exception as e:
                print(f"Error processing {item_type} image: {str(e)}")
        
        # Save the merged image
        merged_filename = f"outfit_{uuid.uuid4()}.png"
        merged_path = os.path.join('merged_outfits', merged_filename)
        merged_image.save(merged_path)
        
        # Add the merged image path to the outfit dictionary
        selected_outfit['merged_image_path'] = merged_path
    
    return selected_outfit, missing_items
