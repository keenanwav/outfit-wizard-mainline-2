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
        st.subheader("Eyedropper Tool")
        st.markdown("""
            <style>
                .stImage:hover {cursor: crosshair !important;}
            </style>
            """, unsafe_allow_html=True)
        
        # Display the image
        st.image(image, use_column_width=True)

    # Create a form for the color picker controls
    with st.form(key=f"color_picker_form_{image_hash}"):
        # Coordinate sliders
        st.markdown("### Adjust Coordinates")
        x = st.slider("X coordinate", 0, width-1, st.session_state[f"{key_prefix}_x_{image_hash}"], 
                     key=f"{key_prefix}_x_slider_{image_hash}")
        y = st.slider("Y coordinate", 0, height-1, st.session_state[f"{key_prefix}_y_{image_hash}"], 
                     key=f"{key_prefix}_y_slider_{image_hash}")
        
        st.markdown("### Quick Color Selection")
        
        # Define color swatches
        primary_colors = {
            "Red": "#FF0000", "Blue": "#0000FF", "Yellow": "#FFFF00",
            "Green": "#00FF00", "Purple": "#800080", "Orange": "#FFA500"
        }
        secondary_colors = {
            "Pink": "#FFC0CB", "Brown": "#A52A2A", "Gray": "#808080",
            "Black": "#000000", "White": "#FFFFFF"
        }
        
        # Create CSS for color swatches
        st.markdown("""
            <style>
                .color-swatch {
                    width: 30px;
                    height: 30px;
                    border-radius: 4px;
                    border: 1px solid #ccc;
                    display: inline-block;
                    margin: 4px;
                }
                .swatch-section {
                    background: #f8f9fa;
                    padding: 12px;
                    border-radius: 8px;
                    margin-bottom: 16px;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Primary colors section
        st.markdown("#### Primary Colors")
        selected_primary = st.radio(
            "Select a primary color:",
            list(primary_colors.keys()),
            key=f"{key_prefix}_primary_radio_{image_hash}",
            horizontal=True,
            label_visibility="collapsed"
        )
        
        # Secondary colors section
        st.markdown("#### Secondary Colors")
        selected_secondary = st.radio(
            "Select a secondary color:",
            list(secondary_colors.keys()),
            key=f"{key_prefix}_secondary_radio_{image_hash}",
            horizontal=True,
            label_visibility="collapsed"
        )
        
        # Submit button for the form
        submitted = st.form_submit_button("Apply Color")
        
        if submitted:
            # Update coordinates in session state
            st.session_state[f"{key_prefix}_x_{image_hash}"] = x
            st.session_state[f"{key_prefix}_y_{image_hash}"] = y
            
            # Set color based on radio selection
            if selected_primary != st.session_state.get(f"{key_prefix}_last_primary_{image_hash}"):
                st.session_state[f"{key_prefix}_color_{image_hash}"] = hex_to_rgb(primary_colors[selected_primary])
                st.session_state[f"{key_prefix}_last_primary_{image_hash}"] = selected_primary
            elif selected_secondary != st.session_state.get(f"{key_prefix}_last_secondary_{image_hash}"):
                st.session_state[f"{key_prefix}_color_{image_hash}"] = hex_to_rgb(secondary_colors[selected_secondary])
                st.session_state[f"{key_prefix}_last_secondary_{image_hash}"] = selected_secondary
            else:
                # Use eyedropper color if no radio button changed
                st.session_state[f"{key_prefix}_color_{image_hash}"] = get_pixel_color(image, x, y)
    
    # Display the currently selected color
    if st.session_state[f"{key_prefix}_color_{image_hash}"] is not None:
        color = st.session_state[f"{key_prefix}_color_{image_hash}"]
    else:
        color = get_pixel_color(image, x, y)
    
    color_hex = "#{:02x}{:02x}{:02x}".format(*color)
    
    # Display color preview
    st.markdown("### Selected Color")
    st.markdown(f"""
        <div style="
            background: #f8f9fa;
            padding: 16px;
            border-radius: 8px;
            margin-top: 16px;
        ">
            <div style="
                width: 100%;
                height: 100px;
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
    
    # Reset button outside the form
    if st.button("Reset Color Selection", key=f"{key_prefix}_reset_{image_hash}"):
        st.session_state[f"{key_prefix}_color_{image_hash}"] = None
        st.session_state[f"{key_prefix}_last_primary_{image_hash}"] = None
        st.session_state[f"{key_prefix}_last_secondary_{image_hash}"] = None
    
    return color, color_hex
