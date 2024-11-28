from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
from webcolors import rgb_to_name, CSS3_HEX_TO_NAMES, hex_to_rgb
from scipy.spatial import KDTree
import numpy as np
import os
import streamlit as st

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

def display_color_palette(colors):
    """Create a streamlit color palette display"""
    if colors is None or len(colors) == 0:
        return
    
    # Create columns for each color
    cols = st.columns(len(colors))
    
    # Display each color with its hex value
    for idx, color in enumerate(colors):
        hex_color = rgb_to_hex(color)
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
                """,

def get_color_name(rgb_color):
    """Get the closest color name for an RGB value"""
    try:
        # Try getting the exact color name
        hex_color = rgb_to_hex(rgb_color)
        color_name = rgb_to_name(rgb_color)
        return color_name
    except ValueError:
        # If exact match not found, find the closest color
        names = []
        rgb_values = []
        for hex_code, name in CSS3_HEX_TO_NAMES.items():
            names.append(name)
            rgb_values.append(hex_to_rgb(hex_code))
        
        kdtree = KDTree(rgb_values)
        _, index = kdtree.query(rgb_color)
        return names[index]
                unsafe_allow_html=True
            )
