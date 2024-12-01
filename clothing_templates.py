from PIL import Image
import os
from typing import Dict, Optional, Tuple

# Template mapping
TEMPLATE_MAPPING = {
    'long_sleeve': 'long sleeve temp.png',
    'short_sleeve': 'short shirt template.png',
    'long_pants': 'long pants temp.png',
    'short_pants': 'short pants teemp.png',
    'shoes': 'shoe temp 1.png'
}

def get_template_for_item(item_type: str, weather: Optional[str] = None) -> str:
    """Get the appropriate template based on item type and weather"""
    if 'shirt' in item_type.lower():
        if weather and ('cold' in weather.lower() or 'cool' in weather.lower()):
            return TEMPLATE_MAPPING['long_sleeve']
        return TEMPLATE_MAPPING['short_sleeve']
    elif 'pants' in item_type.lower() or 'trousers' in item_type.lower():
        if weather and ('cold' in weather.lower() or 'cool' in weather.lower()):
            return TEMPLATE_MAPPING['long_pants']
        return TEMPLATE_MAPPING['short_pants']
    elif 'shoes' in item_type.lower():
        return TEMPLATE_MAPPING['shoes']
    return None

def apply_color_to_template(template_path: str, color: Tuple[int, int, int]) -> Image.Image:
    """Apply color to the template while maintaining transparency"""
    template = Image.open(template_path).convert('RGBA')
    colored = Image.new('RGBA', template.size, color + (255,))
    
    # Use the template as a mask
    result = Image.new('RGBA', template.size, (0, 0, 0, 0))
    result.paste(colored, mask=template.split()[3])
    
    return result

def get_item_position(item_type: str, template_size: Tuple[int, int]) -> Tuple[int, int]:
    """Get the position coordinates for each clothing item type"""
    width, height = template_size
    positions = {
        'shirt': (width // 4, height // 4),  # Top position
        'pants': (width // 4, height // 2),  # Middle position
        'shoes': (width // 4, height * 3 // 4 + 50)  # Bottom position, adjusted for better alignment
    }
    
    for key in positions:
        if key in item_type.lower():
            return positions[key]
    return (0, 0)

def parse_color_string(color_str: str) -> Tuple[int, int, int]:
    """Parse color string in format 'r,g,b' to RGB tuple"""
    try:
        r, g, b = map(int, color_str.split(','))
        return (r, g, b)
    except:
        return (0, 0, 0)  # Default to black if parsing fails
