import random
import numpy as np

def generate_outfit(clothing_items, size, style, gender):
    try:
        filtered_items = clothing_items[
            (clothing_items['size'].str.contains(size)) &
            (clothing_items['style'].str.contains(style)) &
            ((clothing_items['gender'].str.contains(gender)) | (clothing_items['gender'].str.contains('unisex')))
        ]
        
        outfit = {}
        missing_items = []
        
        for item_type in ['shirt', 'pants', 'shoes']:
            type_items = filtered_items[filtered_items['type'] == item_type]
            if len(type_items) > 0:
                outfit[item_type] = select_item(type_items)
            else:
                missing_items.append(item_type)
        
        return outfit, missing_items
    except Exception as e:
        print(f"Error in generate_outfit: {str(e)}")
        return {}, ['shirt', 'pants', 'shoes']

def select_item(items):
    try:
        return items.sample(1).iloc[0].to_dict()
    except Exception as e:
        print(f"Error in select_item: {str(e)}")
        return None

def color_difference(color1, color2):
    try:
        return np.sqrt(sum((np.array(color1) - np.array(color2)) ** 2))
    except Exception as e:
        print(f"Error in color_difference: {str(e)}")
        return 0
