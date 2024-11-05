from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import os
import streamlit as st

def get_color_palette(image_path, n_colors=5):
    """Extract the main colors from an image using K-means clustering"""
    try:
        # Open and convert image to RGB
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize image to speed up processing
        img.thumbnail((150, 150))
        
        # Get colors from image
        pixels = np.array(img)
        pixels = pixels.reshape(-1, 3)
        
        # Use k-means clustering to find dominant colors
        kmeans = KMeans(n_clusters=n_colors, random_state=42)
        kmeans.fit(pixels)
        colors = kmeans.cluster_centers_
        
        # Convert to integer RGB values
        colors = colors.astype(int)
        
        return colors
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
