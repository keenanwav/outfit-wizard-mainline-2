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
    
    # Get the pixel color at the specified coordinates
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
    
    # Create main columns for layout
    col1, col2 = st.columns([2, 1])
    
    # Initialize session state for coordinates and color if not exists
    if f"{key_prefix}_x_{image_hash}" not in st.session_state:
        st.session_state[f"{key_prefix}_x_{image_hash}"] = width // 2
    if f"{key_prefix}_y_{image_hash}" not in st.session_state:
        st.session_state[f"{key_prefix}_y_{image_hash}"] = height // 2
    if f"{key_prefix}_color_{image_hash}" not in st.session_state:
        st.session_state[f"{key_prefix}_color_{image_hash}"] = None
    
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
            x = st.slider("X coordinate", 0, width-1, st.session_state[f"{key_prefix}_x_{image_hash}"], 
                         key=f"{key_prefix}_x_slider_{image_hash}")
            y = st.slider("Y coordinate", 0, height-1, st.session_state[f"{key_prefix}_y_{image_hash}"], 
                         key=f"{key_prefix}_y_slider_{image_hash}")
            st.session_state[f"{key_prefix}_x_{image_hash}"] = x
            st.session_state[f"{key_prefix}_y_{image_hash}"] = y
    
    with col2:
        st.write("Quick Color Selection:")
        
        # Define color swatches
        primary_colors = {
            "Red": "#FF0000", "Blue": "#0000FF", "Yellow": "#FFFF00",
            "Green": "#00FF00", "Purple": "#800080", "Orange": "#FFA500"
        }
        secondary_colors = {
            "Pink": "#FFC0CB", "Brown": "#A52A2A", "Gray": "#808080",
            "Black": "#000000", "White": "#FFFFFF"
        }
        
        # Create CSS grid layout for color swatches
        st.markdown("""
            <style>
                .color-grid {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 8px;
                    margin-bottom: 16px;
                }
                .color-swatch {
                    aspect-ratio: 1;
                    border-radius: 4px;
                    border: 1px solid #ccc;
                    cursor: pointer;
                    transition: transform 0.2s;
                }
                .color-swatch:hover {
                    transform: scale(1.05);
                }
                .swatch-section {
                    background: #f8f9fa;
                    padding: 10px;
                    border-radius: 8px;
                    margin-bottom: 16px;
                }
                .section-title {
                    font-weight: bold;
                    margin-bottom: 8px;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Primary colors section
        st.markdown('<div class="swatch-section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Primary Colors</div>', unsafe_allow_html=True)
        st.markdown('<div class="color-grid">', unsafe_allow_html=True)
        for color_name, hex_code in primary_colors.items():
            if st.button("", key=f"{key_prefix}_primary_{color_name}_{image_hash}", 
                        help=f"{color_name}: {hex_code}"):
                st.session_state[f"{key_prefix}_color_{image_hash}"] = hex_to_rgb(hex_code)
            st.markdown(
                f'<div class="color-swatch" style="background-color: {hex_code};" '
                f'title="{color_name}: {hex_code}"></div>',
                unsafe_allow_html=True
            )
        st.markdown('</div></div>', unsafe_allow_html=True)
        
        # Secondary colors section
        st.markdown('<div class="swatch-section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Secondary Colors</div>', unsafe_allow_html=True)
        st.markdown('<div class="color-grid">', unsafe_allow_html=True)
        for color_name, hex_code in secondary_colors.items():
            if st.button("", key=f"{key_prefix}_secondary_{color_name}_{image_hash}", 
                        help=f"{color_name}: {hex_code}"):
                st.session_state[f"{key_prefix}_color_{image_hash}"] = hex_to_rgb(hex_code)
            st.markdown(
                f'<div class="color-swatch" style="background-color: {hex_code};" '
                f'title="{color_name}: {hex_code}"></div>',
                unsafe_allow_html=True
            )
        st.markdown('</div></div>', unsafe_allow_html=True)
        
        # Get the color from either the image or selected swatch
        if st.session_state[f"{key_prefix}_color_{image_hash}"] is not None:
            color = st.session_state[f"{key_prefix}_color_{image_hash}"]
        else:
            color = get_pixel_color(image, x, y)
        
        color_hex = "#{:02x}{:02x}{:02x}".format(*color)
        
        # Display color preview with improved styling
        st.markdown(f"""
            <div style="
                background: #f8f9fa;
                padding: 16px;
                border-radius: 8px;
                margin-top: 16px;
            ">
                <div style="
                    font-weight: bold;
                    margin-bottom: 8px;
                ">Selected Color</div>
                <div style="
                    width: 100%;
                    height: 80px;
                    background-color: {color_hex};
                    border: 2px solid #ccc;
                    border-radius: 8px;
                    margin-bottom: 12px;
                "></div>
                <div style="
                    background: white;
                    padding: 8px;
                    border-radius: 4px;
                    font-family: monospace;
                ">
                    RGB: {color}<br>
                    Hex: {color_hex}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Reset color selection button with unique key
        if st.button("Reset Color Selection", key=f"{key_prefix}_reset_{image_hash}"):
            st.session_state[f"{key_prefix}_color_{image_hash}"] = None
    
    return color, color_hex
