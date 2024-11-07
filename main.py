import streamlit as st
import os
from PIL import Image
import numpy as np
import pandas as pd
from collections import Counter
from data_manager import (
    load_clothing_items, save_outfit, load_saved_outfits,
    edit_clothing_item, delete_clothing_item, create_user_items_table,
    add_user_clothing_item, store_user_preference
)
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity
import logging
from color_utils import get_color_palette, display_color_palette
from outfit_generator import generate_outfit, cleanup_merged_outfits
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

st.set_page_config(page_title="Outfit Wizard", page_icon="👕", layout="wide")

if 'last_cleanup_time' not in st.session_state:
    st.session_state.last_cleanup_time = datetime.now()
    cleanup_merged_outfits()

def check_cleanup_needed():
    current_time = datetime.now()
    hours_since_cleanup = (current_time - st.session_state.last_cleanup_time).total_seconds() / 3600
    
    if hours_since_cleanup >= 1:
        cleanup_count = cleanup_merged_outfits()
        st.session_state.last_cleanup_time = current_time
        if cleanup_count > 0:
            logging.info(f"Periodic cleanup removed {cleanup_count} old outfit files")

def parse_color_string(color_string, default_color=(0, 0, 0)):
    try:
        if not color_string or ',' not in color_string:
            logging.warning(f"Invalid color string format: {color_string}")
            return default_color
        
        color_values = [int(c.strip()) for c in color_string.split(',')]
        if len(color_values) != 3:
            logging.warning(f"Invalid number of color values: {color_values}")
            return default_color
            
        return tuple(color_values)
    except (ValueError, IndexError) as e:
        logging.error(f"Error parsing color string: {str(e)}")
        return default_color

def normalize_case(value):
    return value.strip().title() if isinstance(value, str) else value

def personal_wardrobe_page():
    st.title("My Personal Wardrobe 👕")
    try:
        create_user_items_table()
        logging.info("Successfully created/verified user items table")
    except Exception as e:
        logging.error(f"Error creating user items table: {str(e)}")
        st.error("Error initializing wardrobe. Please try again later.")
        return
    
    tabs = st.tabs(["Upload New Item", "My Items"])
    
    with tabs[0]:
        st.header("Add Personal Clothing Item")
        with st.form("add_personal_item", clear_on_submit=True):
            item_type = st.selectbox("Item Type", ["shirt", "pants", "shoes"])
            image_file = st.file_uploader("Upload Image (PNG)", type="png")
            hyperlink = st.text_input("Item Link (Optional)", help="Enter the URL where this item can be purchased")
            
            color = None
            if image_file is not None:
                st.image(image_file, width=200)
                try:
                    dominant_color = get_color_palette(image_file, n_colors=1)[0]
                    st.write(f"Dominant color detected: {rgb_to_hex(dominant_color)}")
                    color = st.color_picker("Adjust Color", rgb_to_hex(dominant_color))
                except Exception as e:
                    logging.error(f"Error detecting dominant color: {str(e)}")
                    color = st.color_picker("Select Color", "#000000")
            
            st.write("Style (select all that apply):")
            style_options = ["Casual", "Formal", "Sporty"]
            styles = []
            cols = st.columns(len(style_options))
            for i, style in enumerate(style_options):
                if cols[i].checkbox(style, key=f"style_{style}"):
                    styles.append(style)
            
            st.write("Gender (select all that apply):")
            gender_options = ["Male", "Female", "Unisex"]
            genders = []
            gender_cols = st.columns(len(gender_options))
            for i, gender in enumerate(gender_options):
                if gender_cols[i].checkbox(gender, key=f"gender_{gender}"):
                    genders.append(gender)
            
            st.write("Size (select all that apply):")
            size_options = ["XS", "S", "M", "L", "XL"]
            sizes = []
            size_cols = st.columns(len(size_options))
            for i, size in enumerate(size_options):
                if size_cols[i].checkbox(size, key=f"size_{size}"):
                    sizes.append(size)
            
            submitted = st.form_submit_button("Upload Item")
            if submitted:
                if not image_file:
                    st.error("Please upload an image file.")
                elif not styles:
                    st.error("Please select at least one style.")
                elif not genders:
                    st.error("Please select at least one gender.")
                elif not sizes:
                    st.error("Please select at least one size.")
                elif color is None:
                    st.error("Please upload an image to select a color.")
                else:
                    try:
                        rgb_color = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                        success, message = add_user_clothing_item(
                            item_type,
                            rgb_color,
                            styles,
                            genders,
                            sizes,
                            image_file,
                            hyperlink
                        )
                        if success:
                            st.success(message)
                            logging.info(f"Successfully added new {item_type}")
                        else:
                            st.error(message)
                            logging.error(f"Failed to add {item_type}: {message}")
                    except Exception as e:
                        st.error(f"Error adding clothing item: {str(e)}")
                        logging.error(f"Error adding clothing item: {str(e)}")

    with tabs[1]:
        st.header("My Items")
        try:
            personal_items = load_clothing_items()
            if len(personal_items) == 0:
                st.info("No clothing items found.")
                return

            item_types = ["shirt", "pants", "shoes"]
            for item_type in item_types:
                type_items = personal_items[personal_items['type'] == item_type]
                if len(type_items) > 0:
                    st.subheader(f"{item_type.title()}s")
                    n_items = len(type_items)
                    n_rows = (n_items + 2) // 3
                    
                    for row in range(n_rows):
                        cols = st.columns(3)
                        for col in range(3):
                            idx = row * 3 + col
                            if idx < n_items:
                                item = type_items.iloc[idx]
                                with cols[col]:
                                    with st.container():
                                        if os.path.exists(item['image_path']):
                                            st.image(item['image_path'], use_column_width=True)
                                        else:
                                            st.error(f"Image not found")
                                        
                                        if item.get('hyperlink'):
                                            st.markdown(f"[Shop Item]({item['hyperlink']})")
                                        
                                        with st.expander("Edit Details"):
                                            try:
                                                color_values = parse_color_string(item['color'], (0, 0, 0))
                                                hex_color = '#{:02x}{:02x}{:02x}'.format(*color_values)
                                                new_color = st.color_picker(
                                                    "Color", 
                                                    hex_color,
                                                    key=f"color_{item_type}_{item['id']}"
                                                )
                                                
                                                new_hyperlink = st.text_input(
                                                    "Item Link",
                                                    value=item.get('hyperlink', ''),
                                                    key=f"hyperlink_{item_type}_{item['id']}"
                                                )
                                            except Exception as e:
                                                logging.error(f"Error handling color for item {item['id']}: {str(e)}")
                                                new_color = st.color_picker("Color", "#000000", key=f"color_{item_type}_{item['id']}")
                                                new_hyperlink = st.text_input("Item Link", "", key=f"hyperlink_{item_type}_{item['id']}")
                                            
                                            style_list = item['style'].split(',') if item['style'] else []
                                            new_styles = []
                                            st.write("Styles:")
                                            style_cols = st.columns(len(["Casual", "Formal", "Sporty"]))
                                            for i, style in enumerate(["Casual", "Formal", "Sporty"]):
                                                if style_cols[i].checkbox(style, value=style in style_list, key=f"edit_style_{item_type}_{item['id']}_{style}"):
                                                    new_styles.append(style)
                                            
                                            gender_list = item['gender'].split(',') if item['gender'] else []
                                            new_genders = []
                                            st.write("Genders:")
                                            gender_cols = st.columns(len(["Male", "Female", "Unisex"]))
                                            for i, gender in enumerate(["Male", "Female", "Unisex"]):
                                                if gender_cols[i].checkbox(gender, value=gender in gender_list, key=f"edit_gender_{item_type}_{item['id']}_{gender}"):
                                                    new_genders.append(gender)
                                            
                                            size_list = item['size'].split(',') if item['size'] else []
                                            new_sizes = []
                                            st.write("Sizes:")
                                            size_cols = st.columns(len(["XS", "S", "M", "L", "XL"]))
                                            for i, size in enumerate(["XS", "S", "M", "L", "XL"]):
                                                if size_cols[i].checkbox(size, value=size in size_list, key=f"edit_size_{item_type}_{item['id']}_{size}"):
                                                    new_sizes.append(size)
                                            
                                            if st.button("Update", key=f"update_{item_type}_{item['id']}"):
                                                try:
                                                    rgb_color = tuple(int(new_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                                                    success, message = edit_clothing_item(
                                                        item['id'],
                                                        rgb_color,
                                                        new_styles,
                                                        new_genders,
                                                        new_sizes,
                                                        new_hyperlink
                                                    )
                                                    if success:
                                                        st.success(message)
                                                        st.experimental_rerun()
                                                    else:
                                                        st.error(message)
                                                except Exception as e:
                                                    st.error(f"Error updating item: {str(e)}")
                                        
                                        if st.button("Delete", key=f"delete_{item_type}_{item['id']}"):
                                            try:
                                                success, message = delete_clothing_item(item['id'])
                                                if success:
                                                    st.success(message)
                                                    st.experimental_rerun()
                                                else:
                                                    st.error(message)
                                            except Exception as e:
                                                st.error(f"Error deleting item: {str(e)}")
        except Exception as e:
            st.error("Error loading clothing items")
            logging.error(f"Error loading clothing items: {str(e)}")
            return

def main_page():
    st.title("Outfit Wizard 🧙‍♂️👚👖👞")
    
    try:
        check_cleanup_needed()
        
        clothing_items = load_clothing_items()
        logging.info("Successfully loaded clothing items for main page")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.sidebar.header("Set Your Preferences")
            size = st.sidebar.selectbox("Size", ["XS", "S", "M", "L", "XL"])
            style = st.sidebar.selectbox("Style", ["Casual", "Formal", "Sporty"])
            gender = st.sidebar.selectbox("Gender", ["Male", "Female", "Unisex"])
            
            if st.sidebar.button("Generate New Outfit 🔄"):
                outfit, missing_items = generate_outfit(clothing_items, size, style, gender)
                st.session_state.current_outfit = outfit
                st.session_state.missing_items = missing_items
                logging.info("Generated new outfit")
        
        with col2:
            current_outfit = st.session_state.get('current_outfit')
            missing_items = st.session_state.get('missing_items', [])
            
            if current_outfit:
                if 'merged_image_path' in current_outfit:
                    with st.container():
                        # Create two columns for the outfit display
                        outfit_col1, outfit_col2 = st.columns([1, 3])
                        
                        with outfit_col1:
                            # Add the "Shop Shirt" button in the vertical rectangle area
                            if 'shirt' in current_outfit and 'hyperlink' in current_outfit['shirt'] and current_outfit['shirt']['hyperlink']:
                                st.markdown(
                                    f"""
                                    <div style='
                                        background-color: rgba(255, 255, 255, 0.5);
                                        padding: 10px;
                                        border-radius: 5px;
                                        margin-top: 60px;
                                        text-align: center;
                                    '>
                                        <a href='{current_outfit['shirt']['hyperlink']}' target='_blank'>
                                            <button style='
                                                width: 100%;
                                                padding: 8px;
                                                background-color: #f0f2f6;
                                                border: none;
                                                border-radius: 5px;
                                                cursor: pointer;
                                            '>
                                                Shop Shirt
                                            </button>
                                        </a>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                        with outfit_col2:
                            st.image(current_outfit['merged_image_path'], width=600)
                            
                            # Only show pants and shoes buttons below the image
                            button_cols = st.columns(2)
                            remaining_items = ['pants', 'shoes']
                            for i, item_type in enumerate(remaining_items):
                                with button_cols[i]:
                                    if item_type in current_outfit:
                                        if 'hyperlink' in current_outfit[item_type] and current_outfit[item_type]['hyperlink']:
                                            st.markdown(f"<a href='{current_outfit[item_type]['hyperlink']}' target='_blank'><button style='width:100%; padding: 4px;'>Shop {item_type.title()}</button></a>", unsafe_allow_html=True)
                                        
                                        item_color = get_color_palette(current_outfit[item_type]['image_path'], n_colors=1)
                                        if item_color is not None:
                                            hex_color = rgb_to_hex(item_color[0])
                                            st.markdown(f"""
                                                <div style="display: flex; align-items: center; gap: 4px; margin-top: 4px;">
                                                    <div style="width: 20px; height: 20px; background-color: {hex_color}; border-radius: 4px;"></div>
                                                    <span style="font-size: 12px;">{hex_color}</span>
                                                </div>
                                            """, unsafe_allow_html=True)
                            
                            if missing_items:
                                st.warning(f"Missing items: {', '.join(missing_items)}")
    except Exception as e:
        st.error(f"Error: {str(e)}")
        logging.error(f"Error in main page: {str(e)}")

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

# Create tabs for navigation
tab1, tab2 = st.tabs(["Generate Outfit", "My Wardrobe"])

with tab1:
    main_page()

with tab2:
    personal_wardrobe_page()
