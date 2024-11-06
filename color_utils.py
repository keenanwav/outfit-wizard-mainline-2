from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import os
import streamlit as st

def get_center_color(image_path):
    """Extract the color from the center of the image"""
    try:
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
        
        return center_color
    except Exception as e:
        st.error(f"Error extracting center color: {str(e)}")
        return None

def get_color_palette(image_path, n_colors=1):
    """Extract colors from an image"""
    try:
        if n_colors == 1:
            color = get_center_color(image_path)
            return np.array([color]) if color is not None else None
            
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
                    width: 100%;
                    height: 50px;
                    border-radius: 5px;
                    margin-bottom: 5px;
                "></div>
                <p style="text-align: center; font-size: 12px;">{hex_color}</p>
                """,
                unsafe_allow_html=True
            )
