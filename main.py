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

st.set_page_config(page_title="Outfit Wizard", page_icon="👕", layout="wide")
logging.basicConfig(level=logging.INFO)

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
        st.error(f"Error processing image: {str(e)}")
        return "#000000"

def personal_wardrobe_page():
    st.title("My Personal Wardrobe 👕")
    create_user_items_table()
    
    tabs = st.tabs(["Upload New Item", "My Items"])
    
    with tabs[0]:
        st.header("Add Personal Clothing Item")
        with st.form("add_personal_item", clear_on_submit=True):
            item_type = st.selectbox("Item Type", ["shirt", "pants", "shoes"])
            image_file = st.file_uploader("Upload Image (PNG)", type="png")
            
            if image_file is not None:
                st.image(image_file, width=200)
                dominant_color = get_dominant_color(image_file)
                st.write(f"Dominant color detected: {dominant_color}")
                color = st.color_picker("Adjust Color", dominant_color)
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
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"Error adding clothing item: {str(e)}")

    with tabs[1]:
        st.header("My Items")
        personal_items = load_clothing_items()
        
        if len(personal_items) == 0:
            st.info("No clothing items found.")
            return
        
        for _, item in personal_items.iterrows():
            with st.expander(f"{item['type'].capitalize()} - ID: {item['id']}"):
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col1:
                    if os.path.exists(item['image_path']):
                        st.image(item['image_path'], use_column_width=True)
                    else:
                        st.error(f"Image not found: {item['image_path']}")
                
                with col2:
                    color_values = [int(c) for c in item['color'].split(',')]
                    new_color = st.color_picker(
                        "Color", 
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
                            st.error(f"Error updating item: {str(e)}")
                    
                    if st.button("Delete", key=f"delete_{item['id']}"):
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
        
        st.sidebar.header("Set Your Preferences")
        size = st.sidebar.selectbox("Size", ["XS", "S", "M", "L", "XL"])
        style = st.sidebar.selectbox("Style", ["Casual", "Formal", "Sporty"])
        gender = st.sidebar.selectbox("Gender", ["Male", "Female", "Unisex"])
        
        if st.sidebar.button("Generate New Outfit 🔄"):
            outfit, missing_items = generate_outfit(clothing_items, size, style, gender)
            st.session_state.current_outfit = outfit
            st.session_state.missing_items = missing_items
        
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
            
            if st.button("Save Outfit"):
                saved_path = save_outfit(current_outfit)
                if saved_path:
                    st.success("Outfit saved successfully!")
                else:
                    st.error("Failed to save outfit")
                    
        if missing_items:
            st.warning(f"Couldn't find matching items for: {', '.join(missing_items)}")
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

def saved_outfits_page():
    st.title("Saved Outfits")
    
    saved_outfits = load_saved_outfits()
    
    if saved_outfits:
        cols = st.columns(2)
        for i, outfit in enumerate(saved_outfits):
            with cols[i % 2]:
                st.subheader(f"Outfit {i+1}")
                if os.path.exists(outfit['image_path']):
                    st.image(outfit['image_path'])
                else:
                    st.error(f"Image not found: {outfit['image_path']}")
    else:
        st.info("No saved outfits yet.")

def main():
    pages = {
        "Home": main_page,
        "My Wardrobe": personal_wardrobe_page,
        "Saved Outfits": saved_outfits_page
    }
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", list(pages.keys()))
    
    # Initialize session state for outfit management only
    if 'current_outfit' not in st.session_state:
        st.session_state.current_outfit = None
    if 'missing_items' not in st.session_state:
        st.session_state.missing_items = []
    
    pages[page]()

if __name__ == "__main__":
    main()
