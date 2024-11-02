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
    
    # Create columns for layout
    col1, col2 = st.columns([2, 1])
    
    # Initialize session state for coordinates if not exists
    if f"{key_prefix}_x" not in st.session_state:
        st.session_state[f"{key_prefix}_x"] = width // 2
    if f"{key_prefix}_y" not in st.session_state:
        st.session_state[f"{key_prefix}_y"] = height // 2
    
    with col1:
        # Display the image with a click handler
        st.markdown("""
            <style>
                .stImage:hover {cursor: crosshair !important;}
            </style>
            """, unsafe_allow_html=True)
        
        clicked = st.image(image, use_column_width=True)
        
        # Handle click events using streamlit callback
        if clicked:
            # Get click coordinates from mouse event
            x = st.session_state[f"{key_prefix}_x"]
            y = st.session_state[f"{key_prefix}_y"]
        else:
            # Use sliders for fine-tuning
            x = st.slider("X coordinate", 0, width-1, st.session_state[f"{key_prefix}_x"], 
                         key=f"{key_prefix}_x_slider")
            y = st.slider("Y coordinate", 0, height-1, st.session_state[f"{key_prefix}_y"], 
                         key=f"{key_prefix}_y_slider")
            st.session_state[f"{key_prefix}_x"] = x
            st.session_state[f"{key_prefix}_y"] = y
    
    # Get the color at the selected coordinates
    color = get_pixel_color(image, x, y)
    color_hex = "#{:02x}{:02x}{:02x}".format(*color)
    
    with col2:
        # Display the selected color more prominently
        st.markdown("""
            <style>
                .color-preview {
                    width: 150px;
                    height: 150px;
                    border: 2px solid #ccc;
                    border-radius: 10px;
                    margin: 10px 0;
                }
                .color-info {
                    padding: 10px;
                    background-color: #f0f0f0;
                    border-radius: 5px;
                    margin: 5px 0;
                }
            </style>
            <div class="color-preview" style="background-color: {color_hex};"></div>
            <div class="color-info">
                <strong>Selected Color:</strong><br>
                RGB: {color}<br>
                Hex: {color_hex}
            </div>
            """.format(color_hex=color_hex, color=color),
            unsafe_allow_html=True
        )
    
    return color, color_hex
