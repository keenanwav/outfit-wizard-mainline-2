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
    
    # Initialize session state for coordinates and color if not exists
    if f"{key_prefix}_x_{image_hash}" not in st.session_state:
        st.session_state[f"{key_prefix}_x_{image_hash}"] = None
    if f"{key_prefix}_y_{image_hash}" not in st.session_state:
        st.session_state[f"{key_prefix}_y_{image_hash}"] = None
    if f"{key_prefix}_color_{image_hash}" not in st.session_state:
        st.session_state[f"{key_prefix}_color_{image_hash}"] = None
    
    # Apply global styling
    st.markdown('''
        <style>
            /* Base text color */
            .stMarkdown, .stText, .stTitle, .stHeader {
                color: #31333F !important;
            }
            
            /* Form elements */
            div[data-testid="stForm"] {
                background: #f8f9fa;
                padding: 16px;
                border-radius: 8px;
                margin-bottom: 16px;
                color: #31333F;
            }
            
            /* Headers and labels */
            h1, h2, h3, h4, label {
                color: #31333F !important;
            }
            
            /* Color section styling */
            .color-section {
                background: white;
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 16px;
            }
            
            /* Color preview area */
            .color-preview {
                width: 100%;
                height: 80px;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin: 8px 0;
            }
            
            /* Color information text */
            .color-info {
                background: white;
                padding: 8px;
                border-radius: 4px;
                color: #31333F;
                font-family: monospace;
            }
            
            /* Color swatch styling */
            .color-swatch {
                width: 100%;
                height: 30px;
                border-radius: 4px;
                border: 1px solid #ddd;
                margin-bottom: 4px;
                cursor: pointer;
                transition: transform 0.2s;
            }
            .color-swatch:hover {
                transform: scale(1.05);
            }
        </style>
    ''', unsafe_allow_html=True)
    
    # Create main columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Open and display the image
        img = Image.open(image)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        width, height = img.size
        
        # Display the image with a click handler
        st.markdown("""
            <style>
                .stImage:hover {cursor: crosshair !important;}
            </style>
            """, unsafe_allow_html=True)
        
        # Handle coordinates with a single form
        with st.form(key=f"coordinates_form_{image_hash}"):
            clicked = st.image(image, use_column_width=True)
            x = st.slider("X coordinate", 0, width-1, 
                         st.session_state[f"{key_prefix}_x_{image_hash}"] or width//2, 
                         key=f"{key_prefix}_x_slider_{image_hash}")
            y = st.slider("Y coordinate", 0, height-1, 
                         st.session_state[f"{key_prefix}_y_{image_hash}"] or height//2, 
                         key=f"{key_prefix}_y_slider_{image_hash}")
            if st.form_submit_button("Pick Color"):
                st.session_state[f"{key_prefix}_x_{image_hash}"] = x
                st.session_state[f"{key_prefix}_y_{image_hash}"] = y
                st.session_state[f"{key_prefix}_color_{image_hash}"] = get_pixel_color(image, x, y)
    
    with col2:
        st.markdown("<div class='color-section'>", unsafe_allow_html=True)
        st.write("Quick Color Selection")
        
        # Define color swatches
        primary_colors = {
            "Red": "#FF0000", "Blue": "#0000FF", "Yellow": "#FFFF00",
            "Green": "#00FF00", "Purple": "#800080", "Orange": "#FFA500"
        }
        secondary_colors = {
            "Pink": "#FFC0CB", "Brown": "#A52A2A", "Gray": "#808080",
            "Black": "#000000", "White": "#FFFFFF"
        }
        
        # Primary colors section
        st.write("Primary Colors")
        primary_cols = st.columns(len(primary_colors))
        for i, (color_name, hex_code) in enumerate(primary_colors.items()):
            with primary_cols[i]:
                if st.button(color_name, key=f"{key_prefix}_primary_{color_name}_{image_hash}"):
                    st.session_state[f"{key_prefix}_color_{image_hash}"] = hex_to_rgb(hex_code)
                st.markdown(
                    f'<div class="color-swatch" style="background-color: {hex_code};" '
                    f'title="{color_name}: {hex_code}"></div>',
                    unsafe_allow_html=True
                )
        
        # Secondary colors section
        st.write("Secondary Colors")
        secondary_cols = st.columns(len(secondary_colors))
        for i, (color_name, hex_code) in enumerate(secondary_colors.items()):
            with secondary_cols[i]:
                if st.button(color_name, key=f"{key_prefix}_secondary_{color_name}_{image_hash}"):
                    st.session_state[f"{key_prefix}_color_{image_hash}"] = hex_to_rgb(hex_code)
                st.markdown(
                    f'<div class="color-swatch" style="background-color: {hex_code};" '
                    f'title="{color_name}: {hex_code}"></div>',
                    unsafe_allow_html=True
                )
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Get the current color
        if st.session_state[f"{key_prefix}_color_{image_hash}"] is not None:
            color = st.session_state[f"{key_prefix}_color_{image_hash}"]
        elif st.session_state[f"{key_prefix}_x_{image_hash}"] is not None:
            color = get_pixel_color(image, 
                                  st.session_state[f"{key_prefix}_x_{image_hash}"], 
                                  st.session_state[f"{key_prefix}_y_{image_hash}"])
        else:
            color = get_pixel_color(image, width//2, height//2)
        
        color_hex = "#{:02x}{:02x}{:02x}".format(*color)
        
        # Display color preview with new styling
        st.markdown(f'''
            <div class="color-section">
                <div style="font-weight: bold;">Selected Color</div>
                <div style="background-color: {color_hex};" class="color-preview"></div>
                <div class="color-info">
                    RGB: {color}<br>
                    Hex: {color_hex}
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
        # Reset color button
        if st.button("Reset Color Selection", key=f"{key_prefix}_reset_{image_hash}"):
            st.session_state[f"{key_prefix}_color_{image_hash}"] = None
            st.session_state[f"{key_prefix}_x_{image_hash}"] = None
            st.session_state[f"{key_prefix}_y_{image_hash}"] = None
    
    return color, color_hex
