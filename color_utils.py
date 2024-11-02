from PIL import Image
import numpy as np
import streamlit as st

def get_pixel_color(image, x, y):
    """Get the color of a specific pixel in an image."""
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = Image.open(image)
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Get the pixel color at the specified coordinates
    pixel_color = img.getpixel((x, y))
    return pixel_color

def create_color_picker(image, key_prefix):
    """Create an interactive color picker with an image."""
    if image is None:
        return None, None
    
    # Open and display the image
    img = Image.open(image)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Get image dimensions
    width, height = img.size
    
    # Create a container for the image
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display the image
        st.image(image, use_column_width=True)
        
        # Create sliders for X and Y coordinates
        x = st.slider("X coordinate", 0, width-1, width//2, key=f"{key_prefix}_x")
        y = st.slider("Y coordinate", 0, height-1, height//2, key=f"{key_prefix}_y")
    
    # Get the color at the selected coordinates
    color = get_pixel_color(image, x, y)
    
    with col2:
        # Display the selected color
        st.write("Selected Color:")
        color_hex = "#{:02x}{:02x}{:02x}".format(*color)
        st.markdown(
            f'<div style="background-color: {color_hex}; width: 100px; height: 100px; border: 1px solid black;"></div>',
            unsafe_allow_html=True
        )
        st.write(f"RGB: {color}")
        st.write(f"Hex: {color_hex}")
    
    return color, color_hex
