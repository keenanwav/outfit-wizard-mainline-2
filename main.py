import streamlit as st
import os
from PIL import Image
import numpy as np
import pandas as pd
from collections import Counter
from data_manager import (
    load_clothing_items, save_outfit, add_clothing_item, update_csv_structure,
    store_user_preference, get_advanced_recommendations, load_saved_outfits,
    delete_outfit, edit_clothing_item, delete_clothing_item, create_user_items_table,
    add_user_clothing_item
)
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity
import logging
from color_utils import create_color_picker
from outfit_generator import generate_outfit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize directories
def initialize_directories():
    directories = ['data', 'wardrobe', 'merged_outfits', 'user_images/default_user']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    return True

# Initialize database and required tables
def initialize_database():
    try:
        create_user_items_table()
        update_csv_structure()
        return True
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        return False

# Page configuration
st.set_page_config(
    page_title="Outfit Wizard",
    page_icon="👕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize application state
def initialize_app_state():
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        st.session_state.outfit = None
        st.session_state.missing_items = []
        st.session_state.loading = False
        st.session_state.error = None

def normalize_case(value):
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
        logger.error(f"Error processing image: {str(e)}")
        return "#000000"

def personal_wardrobe_page():
    st.title("My Personal Wardrobe 👕")
    
    if not st.session_state.initialized:
        st.warning("Initializing application... Please wait.")
        return
        
    tabs = st.tabs(["Upload New Item", "View My Items"])
    
    with tabs[0]:
        st.header("Add Personal Clothing Item")
        with st.form("add_personal_item", clear_on_submit=True):
            item_type = st.selectbox("Item Type", ["shirt", "pants", "shoes"])
            image_file = st.file_uploader("Upload Image (PNG)", type="png")
            
            if image_file is not None:
                st.image(image_file, width=200)
                st.subheader("Color Selection")
                st.write("Use the sliders below to pick a color from your image:")
                selected_color, color_hex = create_color_picker(image_file, "upload")
                if selected_color:
                    color = color_hex
                else:
                    dominant_color = get_dominant_color(image_file)
                    color = st.color_picker("Or select color manually:", dominant_color)
            else:
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
                else:
                    try:
                        if selected_color:
                            rgb_color = selected_color
                        else:
                            rgb_color = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                        
                        success, message = add_user_clothing_item(
                            "default_user",
                            item_type,
                            rgb_color,
                            styles,
                            genders,
                            sizes,
                            image_file
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        logger.error(f"Error adding clothing item: {str(e)}")
                        st.error(f"Error adding clothing item: {str(e)}")
    
    with tabs[1]:
        st.header("My Uploaded Items")
        try:
            personal_items = load_clothing_items("default_user")
            
            if len(personal_items) == 0:
                st.info("You haven't uploaded any clothing items yet.")
                return
            
            for _, item in personal_items.iterrows():
                with st.expander(f"{item['type'].capitalize()} - ID: {item['id']}"):
                    col1, col2, col3 = st.columns([1, 2, 1])
                    
                    with col1:
                        if os.path.exists(item['image_path']):
                            st.image(item['image_path'], use_column_width=True)
                            st.write("Pick a new color from the image:")
                            selected_color, color_hex = create_color_picker(item['image_path'], f"item_{item['id']}")
                        else:
                            st.error(f"Image not found: {item['image_path']}")
                    
                    with col2:
                        if selected_color:
                            new_color = color_hex
                        else:
                            color_values = [int(c) for c in item['color'].split(',')]
                            new_color = st.color_picker(
                                "Or select color manually:", 
                                f"#{color_values[0]:02x}{color_values[1]:02x}{color_values[2]:02x}",
                                key=f"color_{item['id']}"
                            )
                        
                        style_list = item['style'].split(',')
                        new_styles = []
                        st.write("Styles:")
                        style_cols = st.columns(len(["Casual", "Formal", "Sporty"]))
                        for i, style in enumerate(["Casual", "Formal", "Sporty"]):
                            if style_cols[i].checkbox(style, value=style in style_list, key=f"edit_style_{item['id']}_{style}"):
                                new_styles.append(style)
                        
                        gender_list = item['gender'].split(',')
                        new_genders = []
                        st.write("Genders:")
                        gender_cols = st.columns(len(["Male", "Female", "Unisex"]))
                        for i, gender in enumerate(["Male", "Female", "Unisex"]):
                            if gender_cols[i].checkbox(gender, value=gender in gender_list, key=f"edit_gender_{item['id']}_{gender}"):
                                new_genders.append(gender)
                        
                        size_list = item['size'].split(',')
                        new_sizes = []
                        st.write("Sizes:")
                        size_cols = st.columns(len(["XS", "S", "M", "L", "XL"]))
                        for i, size in enumerate(["XS", "S", "M", "L", "XL"]):
                            if size_cols[i].checkbox(size, value=size in size_list, key=f"edit_size_{item['id']}_{size}"):
                                new_sizes.append(size)
                    
                    with col3:
                        if st.button("Update", key=f"update_{item['id']}"):
                            try:
                                if selected_color:
                                    rgb_color = selected_color
                                else:
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
                                else:
                                    st.error(message)
                            except Exception as e:
                                logger.error(f"Error updating item: {str(e)}")
                                st.error(f"Error updating item: {str(e)}")
                        
                        if st.button("Delete", key=f"delete_{item['id']}"):
                            try:
                                success, message = delete_clothing_item(item['id'])
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                            except Exception as e:
                                logger.error(f"Error deleting item: {str(e)}")
                                st.error(f"Error deleting item: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading personal items: {str(e)}")
            st.error("Error loading your wardrobe items. Please try again later.")

def main_page():
    st.title("Outfit Wizard 🧙‍♂️👚👖👞")
    
    if not st.session_state.initialized:
        st.warning("Initializing application... Please wait.")
        return
        
    st.sidebar.header("Set Your Preferences")
    
    try:
        clothing_items = load_clothing_items()
        
        size = st.sidebar.selectbox("Size", ["XS", "S", "M", "L", "XL"])
        style = st.sidebar.selectbox("Style", ["Casual", "Formal", "Sporty"])
        gender = st.sidebar.selectbox("Gender", ["Male", "Female", "Unisex"])
        
        if st.sidebar.button("Generate New Outfit 🔄"):
            with st.spinner("Generating your outfit..."):
                st.session_state.outfit, st.session_state.missing_items = generate_outfit(clothing_items, size, style, gender)
        
        if st.session_state.outfit:
            st.success("Outfit generated successfully!")
            
            if 'merged_image_path' in st.session_state.outfit:
                st.image(st.session_state.outfit['merged_image_path'], use_column_width=True)
                
                cols = st.columns(3)
                for i, item_type in enumerate(['shirt', 'pants', 'shoes']):
                    with cols[i]:
                        if item_type in st.session_state.outfit:
                            if st.button(f"Like {item_type}"):
                                store_user_preference("default_user", st.session_state.outfit[item_type]['id'])
                                st.success(f"You liked this {item_type}!")
            
            if st.button("Save Outfit"):
                with st.spinner("Saving your outfit..."):
                    saved_path = save_outfit(st.session_state.outfit, "default_user")
                    if saved_path:
                        st.success("Outfit saved successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to save outfit")
                    
        if st.session_state.missing_items:
            st.warning(f"Couldn't find matching items for: {', '.join(st.session_state.missing_items)}")
            
    except Exception as e:
        logger.error(f"Error in main page: {str(e)}")
        st.error("An error occurred while loading the application. Please try again later.")

def saved_outfits_page():
    st.title("Saved Outfits")
    
    if not st.session_state.initialized:
        st.warning("Initializing application... Please wait.")
        return
    
    try:
        saved_outfits = load_saved_outfits("default_user")
        
        if saved_outfits:
            cols = st.columns(2)
            for i, outfit in enumerate(saved_outfits):
                with cols[i % 2]:
                    st.subheader(f"Outfit {i+1}")
                    if os.path.exists(outfit['image_path']):
                        st.image(outfit['image_path'])
                        if st.button(f"Delete Outfit {i+1}"):
                            with st.spinner("Deleting outfit..."):
                                success, message = delete_outfit(outfit['outfit_id'])
                                if success:
                                    st.success(f"Outfit {i+1} deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to delete outfit: {message}")
                    else:
                        st.error(f"Image not found: {outfit['image_path']}")
        else:
            st.info("You haven't saved any outfits yet.")
    except Exception as e:
        logger.error(f"Error in saved outfits page: {str(e)}")
        st.error("Error loading saved outfits. Please try again later.")

def main():
    initialize_app_state()
    
    if not st.session_state.initialized:
        with st.spinner("Initializing application..."):
            dirs_created = initialize_directories()
            db_initialized = initialize_database()
            
            if dirs_created and db_initialized:
                st.session_state.initialized = True
                st.rerun()
            else:
                st.error("Error initializing application. Please refresh the page.")
                return
    
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
        logger.error(f"Error loading page {page}: {str(e)}")
        st.error("An error occurred while loading the page. Please try again.")

if __name__ == "__main__":
    main()
