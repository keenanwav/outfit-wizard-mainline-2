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
from color_utils import get_color_palette
from outfit_generator import generate_outfit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

st.set_page_config(page_title="Outfit Wizard", page_icon="👕", layout="wide")

def parse_color_string(color_string, default_color=(0, 0, 0)):
    """Helper function to safely parse color string"""
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
    """Helper function to normalize case of strings"""
    return value.strip().title() if isinstance(value, str) else value

def get_dominant_color(image):
    try:
        img = Image.open(image)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img = img.resize((100, 100))
        img_array = np.array(img)
        colors = img_array.reshape(-1, 3)
        color_counts = Counter(map(tuple, colors))
        dominant_color = color_counts.most_common(1)[0][0]
        return '#{:02x}{:02x}{:02x}'.format(*dominant_color)
    except Exception as e:
        logging.error(f"Error processing image: {str(e)}")
        return "#000000"

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
            
            # Only show color picker after image upload
            color = None
            if image_file is not None:
                st.image(image_file, width=200)
                try:
                    dominant_color = get_dominant_color(image_file)
                    st.write(f"Dominant color detected: {dominant_color}")
                    color = st.color_picker("Adjust Color", dominant_color)
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
                            image_file
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
            logging.info(f"Loaded {len(personal_items)} clothing items")
        except Exception as e:
            st.error("Error loading clothing items")
            logging.error(f"Error loading clothing items: {str(e)}")
            return
        
        if len(personal_items) == 0:
            st.info("No clothing items found.")
            return

        # Group items by type
        item_types = ["shirt", "pants", "shoes"]
        for item_type in item_types:
            type_items = personal_items[personal_items['type'] == item_type]
            if len(type_items) > 0:
                st.subheader(f"{item_type.title()}s")
                
                # Calculate number of columns (3 items per row)
                n_items = len(type_items)
                n_rows = (n_items + 2) // 3  # Round up division
                
                for row in range(n_rows):
                    cols = st.columns(3)
                    for col in range(3):
                        idx = row * 3 + col
                        if idx < n_items:
                            item = type_items.iloc[idx]
                            with cols[col]:
                                # Create a container for the item
                                with st.container():
                                    # Display image
                                    if os.path.exists(item['image_path']):
                                        st.image(item['image_path'], use_column_width=True)
                                    else:
                                        st.error(f"Image not found")
                                    
                                    # Create two columns for edit and delete buttons
                                    button_cols = st.columns(2)
                                    
                                    # Show item details in an expander
                                    with st.expander("Edit Details"):
                                        try:
                                            color_values = parse_color_string(item['color'], (0, 0, 0))
                                            new_color = st.color_picker(
                                                "Color", 
                                                f"#{color_values[0]:02x}{color_values[1]:02x}{color_values[2]:02x}",
                                                key=f"color_{item_type}_{item['id']}"
                                            )
                                        except Exception as e:
                                            logging.error(f"Error handling color for item {item['id']}: {str(e)}")
                                            new_color = st.color_picker("Color", "#000000", key=f"color_{item_type}_{item['id']}")
                                        
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
                                                    item.get('hyperlink', '')
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

def main_page():
    st.title("Outfit Wizard 🧙‍♂️👚👖👞")
    
    try:
        clothing_items = load_clothing_items()
        logging.info("Successfully loaded clothing items for main page")
        
        st.sidebar.header("Set Your Preferences")
        size = st.sidebar.selectbox("Size", ["XS", "S", "M", "L", "XL"])
        style = st.sidebar.selectbox("Style", ["Casual", "Formal", "Sporty"])
        gender = st.sidebar.selectbox("Gender", ["Male", "Female", "Unisex"])
        
        if st.sidebar.button("Generate New Outfit 🔄"):
            outfit, missing_items = generate_outfit(clothing_items, size, style, gender)
            st.session_state.current_outfit = outfit
            st.session_state.missing_items = missing_items
            logging.info("Generated new outfit")
        
        # Display current outfit if available
        current_outfit = st.session_state.get('current_outfit')
        missing_items = st.session_state.get('missing_items', [])
        
        if current_outfit:
            st.success("Outfit generated successfully!")
            
            if 'merged_image_path' in current_outfit:
                st.image(current_outfit['merged_image_path'], use_column_width=True)
                
                cols = st.columns(3)
                for i, item_type in enumerate(['shirt', 'pants', 'shoes']):
                    with cols[i]:
                        if item_type in current_outfit:
                            if st.button(f"Like {item_type}"):
                                store_user_preference(current_outfit[item_type]['id'])
                                st.success(f"You liked this {item_type}!")
                                logging.info(f"User liked {item_type} (ID: {current_outfit[item_type]['id']})")
            
            if st.button("Save Outfit"):
                saved_path = save_outfit(current_outfit)
                if saved_path:
                    st.success("Outfit saved successfully!")
                    logging.info("Successfully saved outfit")
                else:
                    st.error("Failed to save outfit")
                    logging.error("Failed to save outfit")
                    
        if missing_items:
            st.warning(f"Couldn't find matching items for: {', '.join(missing_items)}")
            logging.warning(f"Missing items in outfit generation: {missing_items}")
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logging.error(f"Error in main page: {str(e)}")

def saved_outfits_page():
    st.title("Saved Outfits")
    
    try:
        saved_outfits = load_saved_outfits()
        logging.info(f"Loaded {len(saved_outfits)} saved outfits")
        
        if saved_outfits:
            cols = st.columns(2)
            for i, outfit in enumerate(saved_outfits):
                with cols[i % 2]:
                    st.subheader(f"Outfit {i+1}")
                    if os.path.exists(outfit['image_path']):
                        st.image(outfit['image_path'])
                    else:
                        st.error(f"Image not found: {outfit['image_path']}")
                        logging.error(f"Missing saved outfit image: {outfit['image_path']}")
        else:
            st.info("No saved outfits yet.")
    except Exception as e:
        st.error("Error loading saved outfits")
        logging.error(f"Error loading saved outfits: {str(e)}")

def main():
    # Initialize only outfit-related session state
    if 'current_outfit' not in st.session_state:
        st.session_state.current_outfit = None
    if 'missing_items' not in st.session_state:
        st.session_state.missing_items = []
    
    pages = {
        "Home": main_page,
        "My Wardrobe": personal_wardrobe_page,
        "Saved Outfits": saved_outfits_page
    }
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", list(pages.keys()))
    
    try:
        pages[page]()
    except Exception as e:
        st.error("An error occurred while loading the page")
        logging.error(f"Error loading page {page}: {str(e)}")

if __name__ == "__main__":
    main()
