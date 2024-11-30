import streamlit as st
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import pandas as pd
from collections import Counter
from data_manager import (
    load_clothing_items, save_outfit, load_saved_outfits,
    edit_clothing_item, delete_clothing_item, create_user_items_table,
    add_user_clothing_item, update_outfit_details,
    get_outfit_details, update_item_details, delete_saved_outfit,
    get_price_history, update_item_image
)
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity
import logging
from color_utils import get_color_palette, display_color_palette, rgb_to_hex, parse_color_string
from outfit_generator import generate_outfit, cleanup_merged_outfits, is_valid_image
from datetime import datetime, timedelta
from style_assistant import get_style_recommendation, format_clothing_items
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

st.set_page_config(
    page_title="Outfit Wizard",
    page_icon="👕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for various UI states
if 'show_prices' not in st.session_state:
    st.session_state.show_prices = True
if 'editing_color' not in st.session_state:
    st.session_state.editing_color = None
if 'color_preview' not in st.session_state:
    st.session_state.color_preview = None

# Load custom CSS
def load_custom_css():
    with open("static/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state for price visibility
if 'show_prices' not in st.session_state:
    st.session_state.show_prices = True

def show_first_visit_tips():
    """Show first-visit tips in the sidebar"""
    if 'show_tips' not in st.session_state:
        st.session_state.show_tips = True

    if st.session_state.show_tips:
        with st.sidebar:
            st.info("""
            ### 👋 Welcome to Outfit Wizard!
            
            Quick tips to get started:
            1. Add your clothing items in the 'My Items' section
            2. Generate outfits based on your preferences
            3. Save your favorite combinations
            4. Use tags and seasons to organize your wardrobe
            """)
            
            if st.checkbox("Don't show again"):
                st.session_state.show_tips = False
                st.rerun()

def check_cleanup_needed():
    """Check if cleanup is needed based on configured interval"""
    try:
        from data_manager import get_cleanup_settings
        settings = get_cleanup_settings()
        
        if not settings or not settings['last_cleanup']:
            cleanup_merged_outfits()
        else:
            time_since_cleanup = datetime.now() - settings['last_cleanup']
            if time_since_cleanup.total_seconds() > (settings['cleanup_interval_hours'] * 3600):
                cleanup_merged_outfits()
    except Exception as e:
        logging.error(f"Error checking cleanup status: {str(e)}")

def main_page():
    """Display main page with outfit generation"""
    load_custom_css()
    st.title("Outfit Wizard")
    
    # Initialize session state for current outfit
    if 'current_outfit' not in st.session_state:
        st.session_state.current_outfit = None
        
    # Load clothing items
    items_df = load_clothing_items()
    
    # Initialize missing_items
    missing_items = []
    
    if items_df.empty:
        st.warning("Please add some clothing items in the 'My Items' section first!")
        return
    
    # Add tabs for different features
    tab1, tab2 = st.tabs(["📋 Generate Outfit", "🎯 Smart Style Assistant"])
    
    with tab1:
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            size = st.selectbox("Size", ["S", "M", "L", "XL"])
            style = st.selectbox("Style", ["Casual", "Formal", "Sport", "Beach"])
        
        with col2:
            gender = st.selectbox("Gender", ["Male", "Female", "Unisex"])
            
        with col3:
            st.write("")
            st.write("")
            # Toggle button for price visibility
            if st.button("Toggle Prices" if st.session_state.show_prices else "Show Prices"):
                st.session_state.show_prices = not st.session_state.show_prices
                st.rerun()
        
        # Create two columns for outfit display and price information
        outfit_col, price_col = st.columns([0.7, 0.3])
        
        if st.button("🔄 Generate Outfit"):
            with st.spinner("🔮 Generating your perfect outfit..."):
                # Generate the outfit
                outfit, missing_items = generate_outfit(items_df, size, style, gender)
                st.session_state.current_outfit = outfit
        
        # Display current outfit details if available
        if st.session_state.current_outfit:
            outfit = st.session_state.current_outfit
            
            # Display outfit image in the left column
            with outfit_col:
                if 'merged_image_path' in outfit and os.path.exists(outfit['merged_image_path']):
                    st.image(outfit['merged_image_path'], use_column_width=True)
                
                if missing_items:
                    st.warning(f"Missing items: {', '.join(missing_items)}")
            
            # Display prices and colors in the right column with animation
            with price_col:
                price_container_class = "" if st.session_state.show_prices else "hidden"
                st.markdown(f"""
                    <div class="price-container {price_container_class}">
                        <h3>Price Information</h3>
                """, unsafe_allow_html=True)
                
                # Display individual prices with animation
                for item_type, item in outfit.items():
                    if item_type not in ['merged_image_path', 'total_price'] and isinstance(item, dict):
                        st.markdown(f"""
                            <div class="price-item">
                                <strong>{item_type.capitalize()}</strong><br>
                                {'$' + f"{float(item['price']):.2f}" if item.get('price') else 'Price not available'}
                            </div>
                        """, unsafe_allow_html=True)
                
                # Display total price with animation
                if 'total_price' in outfit:
                    st.markdown("""<hr>""", unsafe_allow_html=True)
                    st.markdown(f"""
                        <div class="total-price">
                            <h3>Total Price</h3>
                            ${outfit['total_price']:.2f}
                        </div>
                    """, unsafe_allow_html=True)
                
                # Display individual item colors within price_col
                st.markdown("### Color Palette")
                for item_type, item in outfit.items():
                    if item_type not in ['merged_image_path', 'total_price'] and isinstance(item, dict):
                        st.markdown(f"**{item_type.capitalize()}**")
                        color = parse_color_string(str(item['color']))
                        display_color_palette([color])
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Add shopping information below the outfit display
            st.markdown("### Shop Items")
            shop_cols = st.columns(3)
            for idx, (item_type, item) in enumerate(outfit.items()):
                if item_type not in ['merged_image_path', 'total_price'] and isinstance(item, dict):
                    with shop_cols[idx]:
                        if item.get('hyperlink'):
                            if item_type == 'shirt':
                                st.link_button("👕", item['hyperlink'])
                            elif item_type == 'pants':
                                st.link_button("👖", item['hyperlink'])
                            elif item_type == 'shoes':
                                st.link_button("👞", item['hyperlink'])
            
            # Save and Download outfit options
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Outfit"):
                    saved_path = save_outfit(outfit)
                    if saved_path:
                        st.success("Outfit saved successfully!")
                    else:
                        st.error("Error saving outfit")
            
            with col2:
                if 'merged_image_path' in outfit and os.path.exists(outfit['merged_image_path']):
                    # Add custom filename input
                    custom_name = st.text_input("Enter a name for your outfit (optional)", 
                                             placeholder="e.g., summer_casual_outfit",
                                             key="outfit_name")
                    
                    # Generate filename using custom name if provided, otherwise use timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{custom_name or f'outfit_{timestamp}'}.png"
                    
                    # Extract colors from individual items
                    colors = {}
                    for item_type in ['shirt', 'pants', 'shoes']:
                        if item_type in outfit and isinstance(outfit[item_type], dict):
                            item_color = parse_color_string(outfit[item_type]['color'])
                            colors[item_type] = item_color

                    if colors:
                        # Open the original image
                        with Image.open(outfit['merged_image_path']) as img:
                            # Create a new image with extra space for the color palette and text
                            palette_height = 100  # Reduced space for color blocks and two lines of text
                            new_img = Image.new('RGB', (img.width, img.height + palette_height), 'white')
                            # Paste the original image
                            new_img.paste(img, (0, 0))
                            
                            # Draw color palette
                            draw = ImageDraw.Draw(new_img)
                            
                            # Calculate dimensions for blocks (3:1 width to height ratio)
                            margin = img.width * 0.1  # 10% margin on each side
                            available_width = img.width - (2 * margin)  # Width available for blocks
                            total_width = available_width * 0.8  # Total width is 80% of available width
                            block_width = total_width // 3  # Width for each block
                            block_height = block_width // 3  # Height is 1/3 of width for 3:1 ratio
                            spacing = (available_width - total_width) // 4  # Equal spacing between blocks
                            
                            # Position for color blocks
                            y1 = img.height + 20  # Reduced padding from the image
                            y2 = y1 + block_height
                            
                            # Set up typography with smaller font size
                            try:
                                # Try multiple sans-serif font options
                                font_options = [
                                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                                    "Arial.ttf",
                                    "/usr/share/fonts/truetype/liberation/LiberationSans.ttf"
                                ]
                                font = None
                                for font_path in font_options:
                                    try:
                                        font = ImageFont.truetype(font_path, 10)  # Further reduced font size to 10px
                                        break
                                    except:
                                        continue
                                if font is None:
                                    font = ImageFont.load_default()
                            except:
                                font = ImageFont.load_default()

                            # Add item types and color blocks
                            x_start = margin + spacing  # Starting position for first block
                            for idx, item_type in enumerate(['shirt', 'pants', 'shoes']):
                                if item_type in colors:
                                    # Calculate x positions for current block
                                    x1 = x_start + idx * (block_width + spacing)
                                    x2 = x1 + block_width
                                    
                                    # Draw color block with thin border
                                    color = tuple(colors[item_type])
                                    draw.rectangle([x1, y1, x2, y2], fill=color, outline='#000000', width=1)
                                    
                                    # Add combined item type and hex code on single line
                                    text_y = y2 + 5  # Minimal spacing after block
                                    hex_code = rgb_to_hex(colors[item_type]).lower()  # Convert to lowercase
                                    combined_text = f"{item_type} {hex_code}"  # Format: "shirt #d8a918"
                                    draw.text((x1, text_y), combined_text, fill='black', font=font)
                            
                            # Save the new image with palette
                            temp_path = f"temp_download_{filename}"
                            new_img.save(temp_path)
                            
                            # Provide download button for the modified image
                            with open(temp_path, 'rb') as file:
                                btn = st.download_button(
                                    label="Download Outfit with Color Palette",
                                    data=file,
                                    file_name=filename,
                                    mime="image/png"
                                )
                            
                            # Clean up temporary file
                            os.remove(temp_path)
                    else:
                        # Fallback to original image if color extraction fails
                        with open(outfit['merged_image_path'], 'rb') as file:
                            btn = st.download_button(
                                label="Download Outfit",
                                data=file,
                                file_name=filename,
                                mime="image/png"
                            )

    with tab2:
        st.markdown("### 🤖 Smart Style Assistant")
        st.markdown("Get personalized style recommendations based on your wardrobe and preferences.")
        
        # Input fields for style assistant
        occasion = st.text_input("What's the occasion?", 
                                placeholder="E.g., job interview, casual dinner, wedding")
        
        weather = st.text_input("Weather conditions?", 
                               placeholder="E.g., sunny and warm, cold and rainy")
        
        preferences = st.text_area("Additional preferences or requirements?",
                                  placeholder="E.g., prefer dark colors, need to look professional")
        
        if st.button("Get Style Advice"):
            with st.spinner("🎨 Analyzing your wardrobe and generating recommendations..."):
                # Format clothing items for the AI
                formatted_items = format_clothing_items(items_df)
                
                # Get AI recommendation
                recommendation = get_style_recommendation(
                    formatted_items,
                    occasion=occasion,
                    weather=weather,
                    preferences=preferences
                )
                
                # Display recommendation text
                st.markdown("### Your Personalized Style Recommendation")
                st.markdown(recommendation['text'])
                
                # Display recommended items in a grid
                if recommendation['recommended_items']:
                    st.markdown("### Recommended Items")
                    
                    # Create columns for the grid (3 items per row)
                    cols = st.columns(3)
                    for idx, item in enumerate(recommendation['recommended_items']):
                        col = cols[idx % 3]
                        with col:
                            if item.get('image_path') and os.path.exists(item['image_path']):
                                st.image(item['image_path'], use_column_width=True)
                                st.markdown(f"**{item['type'].capitalize()}**")
                                st.markdown(f"Style: {item['style']}")
                                
                                # Display item color
                                color = parse_color_string(str(item['color']))
                                display_color_palette([color])

def personal_wardrobe_page():
    """Display and manage personal wardrobe items"""
    st.title("My Items")
    
    # Initialize session state for editing
    if 'editing_item' not in st.session_state:
        st.session_state.editing_item = None
    if 'editing_image' not in st.session_state:
        st.session_state.editing_image = None
    if 'editing_color' not in st.session_state:
        st.session_state.editing_color = None
    if 'edit_success' not in st.session_state:
        st.session_state.edit_success = False
    if 'form_errors' not in st.session_state:
        st.session_state.form_errors = {}
    if 'edit_history' not in st.session_state:
        st.session_state.edit_history = {}
    if 'undo_stack' not in st.session_state:
        st.session_state.undo_stack = {}
    if 'redo_stack' not in st.session_state:
        st.session_state.redo_stack = {}
    
    # Load existing items
    items_df = load_clothing_items()
    
    # Add custom CSS for styling
    st.markdown("""
        <style>
        .item-container {
            border: 1px solid #e0e0e0;
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            background-color: #f8f9fa;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .item-details {
            margin-top: 15px;
            padding: 10px;
            background-color: #ffffff;
            border-radius: 5px;
        }
        .item-actions {
            margin-top: 10px;
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }
        .edit-form {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
            border: 1px solid #dee2e6;
        }
        .validation-error {
            color: #dc3545;
            font-size: 0.875em;
            margin-top: 0.25rem;
            padding: 0.375rem 0.75rem;
            border-radius: 0.25rem;
            background-color: rgba(220, 53, 69, 0.1);
        }
        .success-message {
            color: #198754;
            font-size: 0.875em;
            margin-top: 0.25rem;
            padding: 0.375rem 0.75rem;
            border-radius: 0.25rem;
            background-color: rgba(25, 135, 84, 0.1);
        }
        .separator {
            margin: 30px 0;
            border-top: 1px solid #dee2e6;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Upload new item form
    with st.expander("Upload New Item", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            item_type = st.selectbox("Type", ["Shirt", "Pants", "Shoes"])
            styles = st.multiselect("Style", ["Casual", "Formal", "Sport", "Beach"])
            sizes = st.multiselect("Size", ["S", "M", "L", "XL"])
            price = st.number_input("Price ($)", min_value=0.0, step=0.01, format="%.2f")
        
        with col2:
            genders = st.multiselect("Gender", ["Male", "Female", "Unisex"])
            uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'], key="new_item_upload")
            hyperlink = st.text_input("Shopping Link (optional)", 
                                    help="Add a link to where this item can be purchased")
        
        # Form validation
        is_valid = True
        validation_messages = []
        
        if not styles:
            is_valid = False
            validation_messages.append("Please select at least one style")
        if not sizes:
            is_valid = False
            validation_messages.append("Please select at least one size")
        if not genders:
            is_valid = False
            validation_messages.append("Please select at least one gender")
        
        for message in validation_messages:
            st.markdown(f'<p class="validation-error">{message}</p>', unsafe_allow_html=True)
        
        if uploaded_file and is_valid:
            # Validate file type
            if not uploaded_file.name.lower().endswith('.png'):
                st.error("Only PNG files are allowed. Please upload a PNG image.")
                return

            # Extract color after image upload
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Validate the image file
            if not is_valid_image(temp_path):
                os.remove(temp_path)
                st.error("The uploaded file is not a valid PNG image. Please try again with a valid image file.")
                return
            
            colors = get_color_palette(temp_path)
            if colors is not None:
                st.write("Extracted Color:")
                display_color_palette(colors)
                
                if st.button("Add Item"):
                    success, message = add_user_clothing_item(
                        item_type.lower(), colors[0], styles, genders, sizes, 
                        temp_path, hyperlink, price if price > 0 else None
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.error("Could not extract colors from the image. Please try a different image.")
            
            os.remove(temp_path)
    
    # Display existing items in grid
    if not items_df.empty:
        st.markdown("### Your Items")
        
        # Add filter dropdowns
        col1, col2 = st.columns(2)
        with col1:
            selected_type = st.selectbox(
                "Filter by Type",
                ["All"] + ["shirt", "pants", "shoes"],
                format_func=lambda x: x.capitalize() if x != "All" else x
            )
        with col2:
            selected_gender = st.selectbox(
                "Filter by Gender",
                ["All", "Male", "Female", "Unisex"]
            )
        
        # Apply filters
        filtered_df = items_df.copy()
        if selected_type != "All":
            filtered_df = filtered_df[filtered_df['type'] == selected_type]
        if selected_gender != "All":
            filtered_df = filtered_df[filtered_df['gender'].str.contains(selected_gender, na=False)]
        
        # Group items by type
        displayed_types = [selected_type] if selected_type != "All" else ["shirt", "pants", "shoes"]
        for item_type in displayed_types:
            type_items = filtered_df[filtered_df['type'] == item_type]
            if not type_items.empty:
                st.markdown(f"#### {item_type.capitalize()}s")
                
                # Create grid layout (3 items per row)
                cols = st.columns(3)
                for idx, item in type_items.iterrows():
                    col = cols[int(idx) % 3]
                    with col:
                        if item.get('image_path') and os.path.exists(item['image_path']):
                            st.image(item['image_path'], use_column_width=True)
                            
                            # Show current color
                            current_color = parse_color_string(item['color'])
                            st.markdown("**Current Color:**")
                            display_color_palette([current_color])
                            
                            # Edit/Delete/Color buttons
                            edit_col, del_col = st.columns([3, 1])
                            
                            with edit_col:
                                if st.button(f"Edit Details {idx}"):
                                    st.session_state.editing_item = item
                                    st.session_state.edit_success = False
                            
                            with del_col:
                                if st.button("🗑️", key=f"delete_{idx}"):
                                    if delete_clothing_item(item['id']):
                                        st.success(f"Item deleted successfully!")
                                        st.rerun()
                            
                            # Edit form
                            if st.session_state.editing_item is not None and st.session_state.editing_item['id'] == item['id']:
                                with st.form(key=f"edit_form_{idx}"):
                                    st.markdown("### Edit Item Details")
                                    
                                    # Split current values
                                    current_styles = item['style'].split(',') if item['style'] else []
                                    current_sizes = item['size'].split(',') if item['size'] else []
                                    current_genders = item['gender'].split(',') if item['gender'] else []
                                    
                                    # Edit fields
                                    new_styles = st.multiselect("Style", ["Casual", "Formal", "Sport", "Beach"], 
                                                              default=current_styles)
                                    new_sizes = st.multiselect("Size", ["S", "M", "L", "XL"], 
                                                             default=current_sizes)
                                    new_genders = st.multiselect("Gender", ["Male", "Female", "Unisex"], 
                                                               default=current_genders)
                                    new_hyperlink = st.text_input("Shopping Link", 
                                                                value=item['hyperlink'] if item['hyperlink'] else "")
                                    new_price = st.number_input("Price ($)", 
                                                              value=float(item['price']) if item['price'] else 0.0,
                                                              min_value=0.0, 
                                                              step=0.01, 
                                                              format="%.2f")
                                    
                                    # Form validation
                                    is_valid = True
                                    if not new_styles:
                                        is_valid = False
                                        st.markdown('<p class="validation-error">Please select at least one style</p>', 
                                                  unsafe_allow_html=True)
                                    if not new_sizes:
                                        is_valid = False
                                        st.markdown('<p class="validation-error">Please select at least one size</p>', 
                                                  unsafe_allow_html=True)
                                    if not new_genders:
                                        is_valid = False
                                        st.markdown('<p class="validation-error">Please select at least one gender</p>', 
                                                  unsafe_allow_html=True)
                                    
                                    submitted = st.form_submit_button("Save Changes")
                                    if submitted and is_valid:
                                        # Get current color
                                        color = parse_color_string(item['color'])
                                        success, message = edit_clothing_item(
                                            item['id'],
                                            color,
                                            new_styles,
                                            new_genders,
                                            new_sizes,
                                            new_hyperlink,
                                            new_price if new_price > 0 else None
                                        )
                                        if success:
                                            st.session_state.edit_success = True
                                            st.success(message)
                                            # Add edit to history
                                            add_to_edit_history(item['id'], {
                                                'color': color,
                                                'style': new_styles,
                                                'gender': new_genders,
                                                'size': new_sizes,
                                                'hyperlink': new_hyperlink,
                                                'price': new_price
                                            })
                                            st.rerun()
                                        else:
                                            st.error(message)
                            
                            # Image editing interface
                            if st.session_state.editing_image is not None and st.session_state.editing_image['id'] == item['id']:
                                st.markdown("### Update Image")
                                new_image = st.file_uploader("Choose new image", 
                                                           type=['png', 'jpg', 'jpeg'],
                                                           key=f"edit_image_{idx}")
                                
                                if new_image:
                                    preview_col, button_col = st.columns([3, 1])
                                    with preview_col:
                                        st.image(new_image, width=200)
                                    with button_col:
                                        if st.button("Save New Image"):
                                            # Save new image
                                            temp_path = f"temp_edit_{new_image.name}"
                                            with open(temp_path, "wb") as f:
                                                f.write(new_image.getvalue())
                                            
                                            success = update_item_image(item['id'], temp_path)
                                            if success:
                                                st.success("Image updated successfully!")
                                                st.rerun()
                                            else:
                                                st.error("Failed to update image")
                                            
                                            os.remove(temp_path)
                            
                            # Color editing interface
                            if st.session_state.editing_color is not None and st.session_state.editing_color['id'] == item['id']:
                                st.markdown("### Edit Color")
                                temp_path = item['image_path']
                                colors = get_color_palette(temp_path)
                                
                                if colors is not None:
                                    st.write("Available Colors:")
                                    display_color_palette(colors)
                                    
                                    if st.button("Update Color"):
                                        success, message = edit_clothing_item(
                                            item['id'],
                                            colors[0],
                                            item['style'].split(','),
                                            item['gender'].split(','),
                                            item['size'].split(','),
                                            item['hyperlink'],
                                            float(item['price']) if item['price'] else None
                                        )
                                        if success:
                                            st.success("Color updated successfully!")
                                            st.rerun()
                                        else:
                                            st.error(message)
                                    
                                    # Add undo/redo buttons
                                    undo_col, redo_col = st.columns(2)
                                    with undo_col:
                                        if st.button(f"↩ Undo {idx}"):
                                            success, message = undo_edit(item.id)
                                            if success:
                                                st.success(message)
                                                st.rerun()
                                            else:
                                                st.warning(message)
                                    
                                    with redo_col:
                                        if st.button(f"↪ Redo {idx}"):
                                            success, message = redo_edit(item.id)
                                            if success:
                                                st.success(message)
                                                st.rerun()
                                            else:
                                                st.warning(message)

    else:
        st.info("Your wardrobe is empty. Start by adding some items!")

def saved_outfits_page():
    """Display saved outfits page"""
    st.title("Saved Outfits")
    
    outfits = load_saved_outfits()
    
    if not outfits:
        st.info("No saved outfits yet. Generate and save some outfits first!")
        return
    
    # Display outfits in grid layout
    cols = st.columns(3)
    for idx, outfit in enumerate(outfits):
        col = cols[int(idx) % 3]
        with col:
            image_path = str(outfit.get('image_path', ''))
            if os.path.exists(image_path):
                st.image(image_path, use_column_width=True)
                
                # Organization features
                tags = outfit.get('tags', [])
                new_tags = st.text_input(
                    f"Tags ###{idx}", 
                    value=','.join(tags) if tags else "",
                    help="Comma-separated tags"
                )
                
                current_season = str(outfit.get('season', ''))
                season_options = ["", "Spring", "Summer", "Fall", "Winter"]
                season_index = season_options.index(current_season) if current_season in season_options else 0
                
                season = st.selectbox(
                    f"Season ###{idx}",
                    season_options,
                    index=season_index
                )
                
                current_notes = str(outfit.get('notes', ''))
                notes = st.text_area(
                    f"Notes ###{idx}", 
                    value=current_notes,
                    help="Add notes about this outfit"
                )
                
                # Save and Delete buttons
                save_col, del_col = st.columns([3, 1])
                with save_col:
                    if st.button(f"Save Details ###{idx}"):
                        success, message = update_outfit_details(
                            str(outfit['outfit_id']),
                            tags=new_tags.split(',') if new_tags.strip() else None,
                            season=season if season else None,
                            notes=notes if notes.strip() else None
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                
                with del_col:
                    if st.button(f"🗑️ ###{idx}"):
                        success, message = delete_saved_outfit(str(outfit['outfit_id']))
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

def cleanup_status_dashboard():
    """Display cleanup status dashboard"""
    st.title("Cleanup Status Dashboard")
    
    from data_manager import get_cleanup_statistics
    stats = get_cleanup_statistics()
    
    if not stats:
        st.warning("No cleanup settings found. Please configure cleanup settings first.")
        return
    
    # Display current settings
    st.header("📊 Cleanup Settings")
    settings = stats['settings']
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Maximum File Age", f"{settings['max_age_hours']} hours")
        st.metric("Cleanup Interval", f"{settings['cleanup_interval_hours']} hours")
    
    with col2:
        st.metric("Batch Size", str(settings['batch_size']))
        st.metric("Max Workers", str(settings['max_workers']))
    
    # Display last cleanup time
    st.header("⏱️ Last Cleanup")
    if settings['last_cleanup']:
        last_cleanup = settings['last_cleanup']
        time_since = datetime.now() - last_cleanup
        hours_since = time_since.total_seconds() / 3600
        
        status_color = "🟢" if hours_since < settings['cleanup_interval_hours'] else "🔴"
        st.write(f"{status_color} Last cleanup: {last_cleanup.strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"Time since last cleanup: {int(hours_since)} hours")
        
        # Next scheduled cleanup
        next_cleanup = last_cleanup + timedelta(hours=settings['cleanup_interval_hours'])
        st.write(f"Next scheduled cleanup: {next_cleanup.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.warning("No cleanup has been performed yet")
    
    # Display file statistics
    st.header("📁 File Statistics")
    statistics = stats['statistics']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Files", statistics['total_files'])
    with col2:
        st.metric("Saved Outfits", statistics['saved_outfits'])
    with col3:
        st.metric("Temporary Files", statistics['temporary_files'])
    
    # Add manual cleanup button
    st.header("🧹 Manual Cleanup")
    if st.button("Run Cleanup Now"):
        with st.spinner("Running cleanup..."):
            cleaned_count = cleanup_merged_outfits()
            st.success(f"Cleanup completed. {cleaned_count} files removed.")
            st.rerun()

def add_to_edit_history(item_id, new_values):
    """Adds a new edit to the edit history for the given item"""
    if item_id not in st.session_state.edit_history:
        st.session_state.edit_history[item_id] = []
    
    st.session_state.edit_history[item_id].append(new_values)

def undo_edit(item_id):
    """Undoes the last edit for the given item"""
    if item_id in st.session_state.edit_history and st.session_state.edit_history[item_id]:
        # Pop the last edit from the history
        last_edit = st.session_state.edit_history[item_id].pop()
        
        # Push the last edit to the redo stack
        if item_id not in st.session_state.redo_stack:
            st.session_state.redo_stack[item_id] = []
        st.session_state.redo_stack[item_id].append(last_edit)
        
        # Update the item details
        success, message = edit_clothing_item(
            item_id,
            last_edit['color'],
            last_edit['style'],
            last_edit['gender'],
            last_edit['size'],
            last_edit['hyperlink'],
            last_edit['price']
        )
        
        return success, message
    else:
        return False, "No edits to undo"

def redo_edit(item_id):
    """Redoes the last undone edit for the given item"""
    if item_id in st.session_state.redo_stack and st.session_state.redo_stack[item_id]:
        # Pop the last undone edit from the redo stack
        last_undone_edit = st.session_state.redo_stack[item_id].pop()
        
        # Push the undone edit to the edit history
        if item_id not in st.session_state.edit_history:
            st.session_state.edit_history[item_id] = []
        st.session_state.edit_history[item_id].append(last_undone_edit)
        
        # Update the item details
        success, message = edit_clothing_item(
            item_id,
            last_undone_edit['color'],
            last_undone_edit['style'],
            last_undone_edit['gender'],
            last_undone_edit['size'],
            last_undone_edit['hyperlink'],
            last_undone_edit['price']
        )
        
        return success, message
    else:
        return False, "No edits to redo"

# Update the main sidebar menu to include the new dashboard
if __name__ == "__main__":
    create_user_items_table()
    show_first_visit_tips()
    check_cleanup_needed()
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "My Items", "Saved Outfits", "Cleanup Status"])
    
    if page == "Home":
        main_page()
    elif page == "My Items":
        personal_wardrobe_page()
    elif page == "Saved Outfits":
        saved_outfits_page()
    elif page == "Cleanup Status":
        cleanup_status_dashboard()