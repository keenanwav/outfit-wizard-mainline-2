from PIL import Image
import numpy as np
import streamlit as st
import hashlib

def get_pixel_color(image, x, y):
    """Get the color of a specific pixel in an image."""
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = Image.open(image)
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    pixel_color = img.getpixel((x, y))
    return pixel_color

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_image_hash(image):
    """Generate a unique hash for an image."""
    if isinstance(image, str):
        return str(hash(image))
    return str(hash(image.name))

def create_color_picker(image, key_prefix):
    """Create an interactive color picker with an image."""
    if image is None:
        return None, None
    
    # Generate a unique identifier for this image
    image_hash = get_image_hash(image)
    
    # Open and display the image
    img = Image.open(image)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Get image dimensions
    width, height = img.size
    
    # Initialize session state for coordinates and color if not exists
    if f"{key_prefix}_x_{image_hash}" not in st.session_state:
        st.session_state[f"{key_prefix}_x_{image_hash}"] = width // 2
    if f"{key_prefix}_y_{image_hash}" not in st.session_state:
        st.session_state[f"{key_prefix}_y_{image_hash}"] = height // 2
    if f"{key_prefix}_color_{image_hash}" not in st.session_state:
        st.session_state[f"{key_prefix}_color_{image_hash}"] = None
    
    # Create main columns for layout
    col1, col2 = st.columns([2, 1])
    
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
            x = st.session_state[f"{key_prefix}_x_{image_hash}"]
            y = st.session_state[f"{key_prefix}_y_{image_hash}"]
        else:
            with st.form(key=f"coordinates_form_{image_hash}"):
                x = st.slider("X coordinate", 0, width-1, st.session_state[f"{key_prefix}_x_{image_hash}"], 
                            key=f"{key_prefix}_x_slider_{image_hash}")
                y = st.slider("Y coordinate", 0, height-1, st.session_state[f"{key_prefix}_y_{image_hash}"], 
                            key=f"{key_prefix}_y_slider_{image_hash}")
                if st.form_submit_button("Update Coordinates"):
                    st.session_state[f"{key_prefix}_x_{image_hash}"] = x
                    st.session_state[f"{key_prefix}_y_{image_hash}"] = y
    
    with col2:
        # Define color swatches
        primary_colors = {
            "Red": "#FF0000", "Blue": "#0000FF", "Yellow": "#FFFF00",
            "Green": "#00FF00", "Purple": "#800080", "Orange": "#FFA500"
        }
        secondary_colors = {
            "Pink": "#FFC0CB", "Brown": "#A52A2A", "Gray": "#808080",
            "Black": "#000000", "White": "#FFFFFF"
        }
        
        # Create CSS for form elements
        st.markdown("""
            <style>
                div[data-testid="stForm"] {
                    background: #f8f9fa;
                    padding: 16px;
                    border-radius: 8px;
                    margin-bottom: 16px;
                }
                .color-section {
                    margin-bottom: 16px;
                }
                .color-section h4 {
                    margin-bottom: 8px;
                }
                .color-preview {
                    width: 100%;
                    height: 80px;
                    border: 2px solid #ccc;
                    border-radius: 8px;
                    margin: 8px 0;
                }
            </style>
        """, unsafe_allow_html=True)
        
        with st.form(key=f"color_picker_form_{image_hash}"):
            st.write("Quick Color Selection")
            
            # Primary colors section
            st.write("Primary Colors")
            primary_cols = st.columns(len(primary_colors))
            for i, (color_name, hex_code) in enumerate(primary_colors.items()):
                with primary_cols[i]:
                    if st.form_submit_button(color_name, key=f"{key_prefix}_primary_{color_name}_{image_hash}"):
                        st.session_state[f"{key_prefix}_color_{image_hash}"] = hex_to_rgb(hex_code)
                    st.markdown(
                        f'<div style="background-color: {hex_code}; height: 30px; '
                        f'border-radius: 4px; border: 1px solid #ccc;" title="{color_name}: {hex_code}"></div>',
                        unsafe_allow_html=True
                    )
            
            # Secondary colors section
            st.write("Secondary Colors")
            secondary_cols = st.columns(len(secondary_colors))
            for i, (color_name, hex_code) in enumerate(secondary_colors.items()):
                with secondary_cols[i]:
                    if st.form_submit_button(color_name, key=f"{key_prefix}_secondary_{color_name}_{image_hash}"):
                        st.session_state[f"{key_prefix}_color_{image_hash}"] = hex_to_rgb(hex_code)
                    st.markdown(
                        f'<div style="background-color: {hex_code}; height: 30px; '
                        f'border-radius: 4px; border: 1px solid #ccc;" title="{color_name}: {hex_code}"></div>',
                        unsafe_allow_html=True
                    )
            
            # Add form submit button
            submitted = st.form_submit_button("Apply Color Selection")
        
        # Get the color from either the image or selected swatch
        if st.session_state[f"{key_prefix}_color_{image_hash}"] is not None:
            color = st.session_state[f"{key_prefix}_color_{image_hash}"]
        else:
            color = get_pixel_color(image, x, y)
        
        color_hex = "#{:02x}{:02x}{:02x}".format(*color)
        
        # Display color preview
        st.markdown(f"""
            <div style="background: #f8f9fa; padding: 16px; border-radius: 8px;">
                <div style="font-weight: bold; margin-bottom: 8px;">Selected Color</div>
                <div style="background-color: {color_hex};" class="color-preview"></div>
                <div style="background: white; padding: 8px; border-radius: 4px; font-family: monospace;">
                    RGB: {color}<br>
                    Hex: {color_hex}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Reset color selection with form
        with st.form(key=f"reset_form_{image_hash}"):
            if st.form_submit_button("Reset Color Selection"):
                st.session_state[f"{key_prefix}_color_{image_hash}"] = None
    
    return color, color_hex
