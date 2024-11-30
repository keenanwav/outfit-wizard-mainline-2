from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import os
import streamlit as st
import colorsys

# Expanded dictionary mapping common color names to their RGB values
COLOR_NAMES = {
    # Reds
    'bright red': (255, 0, 0),
    'dark red': (139, 0, 0),
    'light red': (255, 102, 102),
    'burgundy': (128, 0, 32),
    'crimson': (220, 20, 60),
    
    # Blues
    'bright blue': (0, 0, 255),
    'navy blue': (0, 0, 128),
    'light blue': (173, 216, 230),
    'sky blue': (135, 206, 235),
    'royal blue': (65, 105, 225),
    'steel blue': (70, 130, 180),
    
    # Greens
    'bright green': (0, 255, 0),
    'dark green': (0, 100, 0),
    'forest green': (34, 139, 34),
    'olive green': (128, 128, 0),
    'sage green': (138, 154, 91),
    'mint green': (152, 255, 152),
    
    # Yellows
    'bright yellow': (255, 255, 0),
    'light yellow': (255, 255, 224),
    'golden yellow': (255, 223, 0),
    'mustard': (255, 219, 88),
    
    # Browns
    'dark brown': (101, 67, 33),
    'medium brown': (165, 42, 42),
    'light brown': (196, 164, 132),
    'tan': (210, 180, 140),
    'coffee brown': (111, 78, 55),
    
    # Grays
    'dark gray': (64, 64, 64),
    'medium gray': (128, 128, 128),
    'light gray': (192, 192, 192),
    'silver': (192, 192, 192),
    'charcoal': (54, 69, 79),
    
    # Purples
    'bright purple': (128, 0, 128),
    'dark purple': (48, 25, 52),
    'light purple': (230, 190, 255),
    'lavender': (230, 230, 250),
    'plum': (221, 160, 221),
    
    # Oranges
    'bright orange': (255, 165, 0),
    'dark orange': (255, 140, 0),
    'light orange': (255, 200, 140),
    'peach': (255, 218, 185),
    'coral': (255, 127, 80),
    
    # Pinks
    'hot pink': (255, 105, 180),
    'light pink': (255, 182, 193),
    'salmon pink': (255, 145, 164),
    'rose': (255, 0, 127),
    
    # Neutrals
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'cream': (255, 253, 208),
    'beige': (245, 245, 220),
    'ivory': (255, 255, 240),
    
    # Additional fashion colors
    'khaki': (240, 230, 140),
    'teal': (0, 128, 128),
    'maroon': (128, 0, 0),
    'mauve': (224, 176, 255),
    'turquoise': (64, 224, 208),
}

def rgb_to_hsv(rgb):
    """Convert RGB color to HSV color space"""
    r, g, b = [x/255.0 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h, s, v

def get_color_name(rgb_color):
    """Find the closest named color for an RGB value using HSV color space"""
    min_distance = float('inf')
    closest_color = 'unknown'
    input_hsv = rgb_to_hsv(rgb_color)
    
    # Convert input color to HSV
    h_input, s_input, v_input = input_hsv
    
    for name, rgb in COLOR_NAMES.items():
        # Convert each color to HSV
        h, s, v = rgb_to_hsv(rgb)
        
        # Calculate weighted distance in HSV space
        # Hue is circular, so we need to handle it specially
        h_diff = min(abs(h - h_input), 1 - abs(h - h_input))
        s_diff = abs(s - s_input)
        v_diff = abs(v - v_input)
        
        # Weight the components (hue is most important, then saturation, then value)
        distance = (h_diff * 5.0) + (s_diff * 3.0) + (v_diff * 2.0)
        
        if distance < min_distance:
            min_distance = distance
            closest_color = name
    
    # Add brightness descriptor for very light or dark colors
    _, _, v = input_hsv
    if v < 0.2 and closest_color not in ['black', 'dark gray']:
        return f"Very dark {closest_color}"
    elif v > 0.8 and closest_color not in ['white', 'light gray', 'cream', 'ivory']:
        return f"Very light {closest_color}"
    
    return closest_color.title()


def parse_color_string(color_str):
    try:
        # Handle color strings in format "r,g,b"
        return [int(c) for c in color_str.split(',')]
    except:
        # Return a default color if parsing fails
        return [0, 0, 0]

def get_region_color(img, region_bounds):
    """Extract the average color from a specific region of the image"""
    try:
        region = img.crop(region_bounds)
        pixels = np.array(region)
        return pixels.mean(axis=(0, 1)).astype(int)
    except Exception as e:
        st.error(f"Error extracting region color: {str(e)}")
        return None

def get_pants_colors(image_path):
    """Extract colors from multiple regions of pants image"""
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        width, height = img.size
        
        # Define multiple sampling regions for pants
        regions = [
            # Upper region (waist area)
            (width//4, 0, 3*width//4, height//4),
            # Middle region (thigh area)
            (width//4, height//4, 3*width//4, height//2),
            # Lower region (leg area)
            (width//4, height//2, 3*width//4, 3*height//4),
            # Bottom region (ankle area)
            (width//4, 3*height//4, 3*width//4, height)
        ]
        
        colors = []
        for region in regions:
            color = get_region_color(img, region)
            if color is not None:
                colors.append(color)
        
        if not colors:
            return None
            
        # Use K-means to find the dominant color from all regions
        colors_array = np.array(colors)
        kmeans = KMeans(n_clusters=1, random_state=42)
        kmeans.fit(colors_array)
        dominant_color = kmeans.cluster_centers_[0].astype(int)
        
        return dominant_color
        
    except Exception as e:
        st.error(f"Error extracting pants colors: {str(e)}")
        return None

def get_color_palette(image_path, n_colors=1, item_type=None):
    """Extract colors from an image with item type specific handling"""
    try:
        if item_type == 'pants':
            # Use specialized pants color detection
            color = get_pants_colors(image_path)
            return np.array([color]) if color is not None else None
            
        elif n_colors == 1:
            # Use center color detection for other items
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get the center pixel coordinates
            width, height = img.size
            center_x = width // 2
            center_y = height // 2
            
            # Get color from a small central region (5x5 pixels)
            region_size = 5
            x1 = max(0, center_x - region_size // 2)
            y1 = max(0, center_y - region_size // 2)
            x2 = min(width, x1 + region_size)
            y2 = min(height, y1 + region_size)
            
            # Get the average color of the central region
            center_region = img.crop((x1, y1, x2, y2))
            pixels = np.array(center_region)
            center_color = pixels.mean(axis=(0, 1)).astype(int)
            
            return np.array([center_color])
            
        else:
            # Original k-means clustering for multiple colors
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img.thumbnail((150, 150))
            pixels = np.array(img)
            pixels = pixels.reshape(-1, 3)
            
            kmeans = KMeans(n_clusters=n_colors, random_state=42)
            kmeans.fit(pixels)
            colors = kmeans.cluster_centers_
            
            return colors.astype(int)
            
    except Exception as e:
        st.error(f"Error extracting color palette: {str(e)}")
        return None

def rgb_to_hex(rgb):
    """Convert RGB color to hex format"""
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def display_color_palette(colors, use_columns=True):
    """Create a streamlit color palette display with color names
    
    Args:
        colors: List of RGB color tuples
        use_columns: Boolean, if True uses st.columns layout, if False uses flex layout
    """
    if colors is None or len(colors) == 0:
        return
    
    if use_columns:
        # Create columns for each color
        cols = st.columns(len(colors))
        
        # Display each color with its hex value and name
        for idx, color in enumerate(colors):
            hex_color = rgb_to_hex(color)
            color_name = get_color_name(color)
            with cols[idx]:
                st.markdown(
                    f"""
                    <div style="
                        background-color: {hex_color};
                        width: 2rem;
                        aspect-ratio: 1;
                        border-radius: 8px;
                        margin: 0 auto 8px auto;
                    "></div>
                    <p style="text-align: center; font-size: 12px; margin: 0 auto;">{hex_color}</p>
                    <p style="text-align: center; font-size: 12px; margin: 0 auto; color: #666;">{color_name}</p>
                    """,
                    unsafe_allow_html=True
                )
    else:
        # Create a flex container for all colors
        color_blocks = []
        for color in colors:
            hex_color = rgb_to_hex(color)
            color_name = get_color_name(color)
            color_blocks.append(f"""
                <div style="
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    margin: 0 8px;
                ">
                    <div style="
                        background-color: {hex_color};
                        width: 2rem;
                        aspect-ratio: 1;
                        border-radius: 8px;
                        margin-bottom: 8px;
                    "></div>
                    <p style="text-align: center; font-size: 12px; margin: 0;">{hex_color}</p>
                    <p style="text-align: center; font-size: 12px; margin: 0; color: #666;">{color_name}</p>
                </div>
            """)
        
        # Combine all color blocks in a flex container
        st.markdown(
            f"""
            <div style="
                display: flex;
                flex-direction: row;
                justify-content: center;
                align-items: flex-start;
                flex-wrap: wrap;
                gap: 16px;
                padding: 8px 0;
            ">
                {"".join(color_blocks)}
            </div>
            """,
            unsafe_allow_html=True
        )
