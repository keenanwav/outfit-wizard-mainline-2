from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
from webcolors import rgb_to_name, CSS3_NAMES_TO_HEX, hex_to_rgb
from scipy.spatial import KDTree
import os
import streamlit as st

def get_color_palette(image_path, n_colors=1):
    """Extract dominant colors from an image"""
    try:
        img = Image.open(image_path)
        img = img.convert('RGB')
        
        # Resize image to speed up processing
        img.thumbnail((150, 150))
        
        # Get colors from image
        pixels = np.float32(img).reshape(-1, 3)
        
        # Use k-means clustering to find dominant colors
        kmeans = KMeans(n_clusters=n_colors, random_state=0).fit(pixels)
        colors = kmeans.cluster_centers_
        
        # Convert colors to integer RGB values
        colors = colors.astype(int)
        
        return [tuple(color) for color in colors]
    except Exception as e:
        st.error(f"Error extracting colors: {str(e)}")
        return None

def rgb_to_hex(rgb_color):
    """Convert RGB tuple to hex string"""
    return '#{:02x}{:02x}{:02x}'.format(int(rgb_color[0]), int(rgb_color[1]), int(rgb_color[2]))

def parse_color_string(color_str):
    """Parse color string to RGB tuple"""
    try:
        # Remove any whitespace and parentheses
        color_str = color_str.strip('() \n')
        # Split the string into components and convert to integers
        rgb = tuple(map(int, color_str.split(',')))
        return rgb
    except:
        return None

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
        for name, hex_code in CSS3_NAMES_TO_HEX.items():
            names.append(name)
            rgb_values.append(hex_to_rgb(hex_code))
        
        kdtree = KDTree(rgb_values)
        _, index = kdtree.query(rgb_color)
        return names[index]

def display_color_palette(colors):
    """Display color palette with hex codes"""
    for color in colors:
        hex_color = rgb_to_hex(color)
        st.markdown(
            f"""
            <div style="
                background-color: {hex_color};
                width: 100px;
                height: 50px;
                display: inline-block;
                margin: 5px;
                border: 1px solid black;
            "></div>
            <p style="text-align: center; font-size: 12px; margin: 0 auto;">{hex_color}</p>
            """,
            unsafe_allow_html=True
        )