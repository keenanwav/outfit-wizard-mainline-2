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

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

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
    
    # Initialize session state for coordinates and color if not exists
    if f"{key_prefix}_x" not in st.session_state:
        st.session_state[f"{key_prefix}_x"] = width // 2
    if f"{key_prefix}_y" not in st.session_state:
        st.session_state[f"{key_prefix}_y"] = height // 2
    if f"{key_prefix}_color" not in st.session_state:
        st.session_state[f"{key_prefix}_color"] = None
    
    # Predefined color swatches
    with col2:
        st.write("Quick Color Selection:")
        
        # Primary colors
        primary_colors = {
            "Red": "#FF0000",
            "Blue": "#0000FF",
            "Yellow": "#FFFF00",
            "Green": "#00FF00",
            "Purple": "#800080",
            "Orange": "#FFA500"
        }
        
        # Secondary colors
        secondary_colors = {
            "Pink": "#FFC0CB",
            "Brown": "#A52A2A",
            "Gray": "#808080",
            "Black": "#000000",
            "White": "#FFFFFF"
        }
        
        # Create color swatch buttons for primary colors
        st.write("Primary Colors:")
        primary_cols = st.columns(3)
        for i, (color_name, hex_code) in enumerate(primary_colors.items()):
            with primary_cols[i % 3]:
                if st.button(
                    "",
                    key=f"{key_prefix}_primary_{color_name}",
                    help=f"{color_name}: {hex_code}",
                    type="secondary",
                    use_container_width=True
                ):
                    st.session_state[f"{key_prefix}_color"] = hex_to_rgb(hex_code)
                st.markdown(
                    f"""
                    <div style="
                        background-color: {hex_code};
                        width: 100%;
                        height: 30px;
                        border-radius: 5px;
                        border: 1px solid #ccc;
                        margin-bottom: 5px;
                    "></div>
                    """,
                    unsafe_allow_html=True
                )
        
        # Create color swatch buttons for secondary colors
        st.write("Secondary Colors:")
        secondary_cols = st.columns(3)
        for i, (color_name, hex_code) in enumerate(secondary_colors.items()):
            with secondary_cols[i % 3]:
                if st.button(
                    "",
                    key=f"{key_prefix}_secondary_{color_name}",
                    help=f"{color_name}: {hex_code}",
                    type="secondary",
                    use_container_width=True
                ):
                    st.session_state[f"{key_prefix}_color"] = hex_to_rgb(hex_code)
                st.markdown(
                    f"""
                    <div style="
                        background-color: {hex_code};
                        width: 100%;
                        height: 30px;
                        border-radius: 5px;
                        border: 1px solid #ccc;
                        margin-bottom: 5px;
                    "></div>
                    """,
                    unsafe_allow_html=True
                )
    
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
            x = st.session_state[f"{key_prefix}_x"]
            y = st.session_state[f"{key_prefix}_y"]
        else:
            x = st.slider("X coordinate", 0, width-1, st.session_state[f"{key_prefix}_x"], 
                         key=f"{key_prefix}_x_slider")
            y = st.slider("Y coordinate", 0, height-1, st.session_state[f"{key_prefix}_y"], 
                         key=f"{key_prefix}_y_slider")
            st.session_state[f"{key_prefix}_x"] = x
            st.session_state[f"{key_prefix}_y"] = y
    
    # Get the color from either the image or selected swatch
    if st.session_state[f"{key_prefix}_color"] is not None:
        color = st.session_state[f"{key_prefix}_color"]
    else:
        color = get_pixel_color(image, x, y)
    
    color_hex = "#{:02x}{:02x}{:02x}".format(*color)
    
    with col2:
        # Display the selected color preview
        st.markdown(
            f"""
            <style>
                .color-preview {{
                    width: 100%;
                    height: 100px;
                    border: 2px solid #ccc;
                    border-radius: 10px;
                    margin: 10px 0;
                }}
                .color-info {{
                    padding: 10px;
                    background-color: #f0f0f0;
                    border-radius: 5px;
                    margin: 5px 0;
                }}
            </style>
            <div class="color-preview" style="background-color: {color_hex};"></div>
            <div class="color-info">
                <strong>Selected Color</strong><br>
                RGB: {color}<br>
                Hex: {color_hex}
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Reset color selection button
        if st.button("Reset Color Selection", key=f"{key_prefix}_reset"):
            st.session_state[f"{key_prefix}_color"] = None
    
    return color, color_hex
