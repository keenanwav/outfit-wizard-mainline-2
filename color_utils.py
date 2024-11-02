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
        
        # Generate a unique identifier for this image
        image_hash = get_image_hash(image)
        
        # Generate unique keys for all widgets
        form_key = f"{key_prefix}_form_{image_hash}"
        x_key = f"{key_prefix}_x_{image_hash}"
        y_key = f"{key_prefix}_y_{image_hash}"
        primary_key = f"{key_prefix}_primary_{image_hash}"
        secondary_key = f"{key_prefix}_secondary_{image_hash}"
        submit_key = f"{key_prefix}_submit_{image_hash}"
        reset_key = f"{key_prefix}_reset_{image_hash}"
        
        # Open and display the image
        img = Image.open(image)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get image dimensions
        width, height = img.size
        
        # Initialize session state for coordinates and color if not exists
        if x_key not in st.session_state:
            st.session_state[x_key] = width // 2
        if y_key not in st.session_state:
            st.session_state[y_key] = height // 2
        
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
        with st.form(key=form_key):
            st.markdown("### Adjust Coordinates")
            x = st.slider("X coordinate", 0, width-1, 
                         st.session_state[x_key], 
                         key=x_key)
            y = st.slider("Y coordinate", 0, height-1, 
                         st.session_state[y_key], 
                         key=y_key)
            
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
            
            # Create color selection sections
            st.markdown("#### Primary Colors")
            selected_primary = st.radio(
                "Select a primary color:",
                list(primary_colors.keys()),
                key=primary_key,
                horizontal=True,
                label_visibility="collapsed"
            )
            
            st.markdown("#### Secondary Colors")
            selected_secondary = st.radio(
                "Select a secondary color:",
                list(secondary_colors.keys()),
                key=secondary_key,
                horizontal=True,
                label_visibility="collapsed"
            )
            
            submitted = st.form_submit_button("Apply Color", key=submit_key)
            
            if submitted:
                st.session_state[x_key] = x
                st.session_state[y_key] = y
                
                # Set color based on radio selection
                if selected_primary != st.session_state.get(f"{key_prefix}_last_primary_{image_hash}"):
                    color = hex_to_rgb(primary_colors[selected_primary])
                    st.session_state[f"{key_prefix}_last_primary_{image_hash}"] = selected_primary
                elif selected_secondary != st.session_state.get(f"{key_prefix}_last_secondary_{image_hash}"):
                    color = hex_to_rgb(secondary_colors[selected_secondary])
                    st.session_state[f"{key_prefix}_last_secondary_{image_hash}"] = selected_secondary
                else:
                    color = get_pixel_color(image, x, y)
                
                color_hex = "#{:02x}{:02x}{:02x}".format(*color)
                return color, color_hex
        
        # Get current color for display
        current_color = get_pixel_color(image, 
                                      st.session_state[x_key], 
                                      st.session_state[y_key])
        color_hex = "#{:02x}{:02x}{:02x}".format(*current_color)
        
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
                    RGB: {current_color}<br>
                    Hex: {color_hex}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Reset button outside the form
        if st.button("Reset Color Selection", key=reset_key):
            st.session_state[f"{key_prefix}_last_primary_{image_hash}"] = None
            st.session_state[f"{key_prefix}_last_secondary_{image_hash}"] = None
            return None, None
        
        return current_color, color_hex
        
    except Exception as e:
        st.error(f"Error in color picker: {str(e)}")
        logging.error(f"Color picker error: {str(e)}")
        return None, None
