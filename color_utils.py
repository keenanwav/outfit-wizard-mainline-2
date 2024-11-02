from PIL import Image
import numpy as np
import streamlit as st
import hashlib
import logging

def get_pixel_color(image, x, y):
    """Get the color of a specific pixel in an image."""
    try:
        if isinstance(image, str):
            img = Image.open(image)
        else:
            img = Image.open(image)
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        pixel_color = img.getpixel((x, y))
        return pixel_color
    except Exception as e:
        logging.error(f"Error getting pixel color: {str(e)}")
        return (0, 0, 0)

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_image_hash(image):
    """Generate a unique hash for an image."""
    try:
        if isinstance(image, str):
            with open(image, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()[:8]
        return hashlib.md5(image.read()).hexdigest()[:8]
    except Exception as e:
        logging.error(f"Error generating image hash: {str(e)}")
        return str(hash(str(image)))

def create_color_picker(image, key_prefix):
    """Create an interactive color picker with an image."""
    try:
        if image is None:
            return None, None
        
        image_hash = get_image_hash(image)
        
        # Display the image
        st.image(image, use_column_width=True)
        
        # Create color swatch columns
        st.write("Quick Color Selection:")
        primary_colors = {
            "Red": "#FF0000", "Blue": "#0000FF", "Yellow": "#FFFF00",
            "Green": "#00FF00", "Purple": "#800080", "Orange": "#FFA500"
        }
        
        cols = st.columns(6)
        for i, (color_name, hex_color) in enumerate(primary_colors.items()):
            with cols[i]:
                if st.button(color_name, key=f"{key_prefix}_primary_{color_name}_{image_hash}"):
                    return hex_to_rgb(hex_color), hex_color
        
        # Add eyedropper functionality
        st.write("Use eyedropper to pick color from image:")
        img = Image.open(image)
        width, height = img.size
        
        col1, col2 = st.columns(2)
        with col1:
            x = st.slider("X coordinate", 0, width-1, width//2, key=f"{key_prefix}_x_{image_hash}")
        with col2:
            y = st.slider("Y coordinate", 0, height-1, height//2, key=f"{key_prefix}_y_{image_hash}")
        
        color = get_pixel_color(image, x, y)
        color_hex = "#{:02x}{:02x}{:02x}".format(*color)
        
        # Display color preview
        st.write("Selected Color:")
        st.markdown(
            f'''
            <div style="background-color: {color_hex}; 
                        width: 100px; 
                        height: 100px; 
                        border: 2px solid black;">
            </div>
            <p>RGB: {color}</p>
            <p>Hex: {color_hex}</p>
            ''',
            unsafe_allow_html=True
        )
        
        return color, color_hex
        
    except Exception as e:
        st.error(f"Error in color picker: {str(e)}")
        logging.error(f"Color picker error: {str(e)}")
        return None, None
