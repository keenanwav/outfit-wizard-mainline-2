import streamlit as st
import os
from PIL import Image
import numpy as np
import pandas as pd
from collections import Counter
import uuid
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

st.set_page_config(page_title="Outfit Wizard", page_icon="👕", layout="wide")
logging.basicConfig(level=logging.INFO)

def generate_unique_form_key(item_id, item_type):
    return f"edit_item_{item_id}_{item_type}_{uuid.uuid4().hex[:8]}"

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
        st.error(f"Error processing image: {str(e)}")
        return "#000000"

def personal_wardrobe_page():
    try:
        st.title("My Personal Wardrobe 👕")
        create_user_items_table()
        
        tabs = st.tabs(["Upload New Item", "View My Items"])
        
        with tabs[0]:
            st.header("Add Personal Clothing Item")
            
            image_file = st.file_uploader("Upload Image (PNG)", type="png")
            selected_color = None
            color_hex = None
            
            if image_file:
                upload_key = f"upload_{uuid.uuid4().hex[:8]}"
                selected_color, color_hex = create_color_picker(image_file, upload_key)
            
            with st.form("add_personal_item", clear_on_submit=True):
                form_id = uuid.uuid4().hex[:8]
                item_type = st.selectbox("Item Type", ["shirt", "pants", "shoes"], key=f"type_{form_id}")
                
                st.write("Style (select all that apply):")
                style_options = ["Casual", "Formal", "Sporty"]
                styles = []
                cols = st.columns(len(style_options))
                for i, style in enumerate(style_options):
                    if cols[i].checkbox(style, key=f"style_{form_id}_{style}"):
                        styles.append(style)
                
                st.write("Gender (select all that apply):")
                gender_options = ["Male", "Female", "Unisex"]
                genders = []
                gender_cols = st.columns(len(gender_options))
                for i, gender in enumerate(gender_options):
                    if gender_cols[i].checkbox(gender, key=f"gender_{form_id}_{gender}"):
                        genders.append(gender)
                
                st.write("Size (select all that apply):")
                size_options = ["XS", "S", "M", "L", "XL"]
                sizes = []
                size_cols = st.columns(len(size_options))
                for i, size in enumerate(size_options):
                    if size_cols[i].checkbox(size, key=f"size_{form_id}_{size}"):
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
                                rgb_color = (0, 0, 0)
                            
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
                                st.experimental_rerun()
                            else:
                                st.error(message)
                        except Exception as e:
                            st.error(f"Error adding clothing item: {str(e)}")
                            logging.error(f"Error adding clothing item: {str(e)}")
        
        with tabs[1]:
            st.header("My Uploaded Items")
            personal_items = load_clothing_items("default_user")
            
            if len(personal_items) == 0:
                st.info("You haven't uploaded any clothing items yet.")
                return
            
            for _, item in personal_items.iterrows():
                with st.expander(f"{item['type'].capitalize()} - ID: {item['id']}"):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        if os.path.exists(item['image_path']):
                            color_picker_key = f"item_{item['id']}_{item['type']}_{uuid.uuid4().hex[:8]}"
                            selected_color, color_hex = create_color_picker(
                                item['image_path'], 
                                color_picker_key
                            )
                        else:
                            st.error(f"Image not found: {item['image_path']}")
                    
                    with col2:
                        try:
                            form_key = generate_unique_form_key(item['id'], item['type'])
                            
                            with st.form(key=form_key):
                                if selected_color:
                                    new_color = selected_color
                                else:
                                    color_values = [int(c) for c in item['color'].split(',')]
                                    new_color = tuple(color_values)
                                
                                style_list = item['style'].split(',')
                                new_styles = []
                                st.write("Styles:")
                                style_cols = st.columns(len(["Casual", "Formal", "Sporty"]))
                                for i, style in enumerate(["Casual", "Formal", "Sporty"]):
                                    if style_cols[i].checkbox(style, value=style in style_list, 
                                                           key=f"{form_key}_style_{style}"):
                                        new_styles.append(style)
                                
                                gender_list = item['gender'].split(',')
                                new_genders = []
                                st.write("Genders:")
                                gender_cols = st.columns(len(["Male", "Female", "Unisex"]))
                                for i, gender in enumerate(["Male", "Female", "Unisex"]):
                                    if gender_cols[i].checkbox(gender, value=gender in gender_list, 
                                                            key=f"{form_key}_gender_{gender}"):
                                        new_genders.append(gender)
                                
                                size_list = item['size'].split(',')
                                new_sizes = []
                                st.write("Sizes:")
                                size_cols = st.columns(len(["XS", "S", "M", "L", "XL"]))
                                for i, size in enumerate(["XS", "S", "M", "L", "XL"]):
                                    if size_cols[i].checkbox(size, value=size in size_list, 
                                                          key=f"{form_key}_size_{size}"):
                                        new_sizes.append(size)
                                
                                if st.form_submit_button("Update"):
                                    try:
                                        success, message = edit_clothing_item(
                                            item['id'],
                                            new_color,
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
                                        logging.error(f"Error updating item: {str(e)}")
                            
                            delete_key = f"delete_{item['id']}_{item['type']}_{uuid.uuid4().hex[:8]}"
                            if st.button("Delete", key=delete_key):
                                try:
                                    success, message = delete_clothing_item(item['id'])
                                    if success:
                                        st.success(message)
                                        st.experimental_rerun()
                                    else:
                                        st.error(message)
                                except Exception as e:
                                    st.error(f"Error deleting item: {str(e)}")
                                    logging.error(f"Error deleting item: {str(e)}")
                        except Exception as e:
                            st.error(f"Form error: {str(e)}")
                            logging.error(f"Form error in item {item['id']}: {str(e)}")
    
    except Exception as e:
        st.error(f"Page error: {str(e)}")
        logging.error(f"Page error in personal wardrobe: {str(e)}")

def main_page():
    st.title("Outfit Wizard 🧙‍♂️👚👖👞")
    
    st.sidebar.header("Set Your Preferences")
    
    try:
        clothing_items = load_clothing_items()
        
        size = st.sidebar.selectbox("Size", ["XS", "S", "M", "L", "XL"])
        style = st.sidebar.selectbox("Style", ["Casual", "Formal", "Sporty"])
        gender = st.sidebar.selectbox("Gender", ["Male", "Female", "Unisex"])
        
        if 'outfit' not in st.session_state:
            st.session_state.outfit = None
            st.session_state.missing_items = []
        
        if st.sidebar.button("Generate New Outfit 🔄"):
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
                saved_path = save_outfit(st.session_state.outfit, "default_user")
                if saved_path:
                    st.success("Outfit saved successfully!")
                else:
                    st.error("Failed to save outfit")
                    
        if st.session_state.missing_items:
            st.warning(f"Couldn't find matching items for: {', '.join(st.session_state.missing_items)}")
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

def saved_outfits_page():
    st.title("Saved Outfits")
    
    saved_outfits = load_saved_outfits("default_user")
    
    if saved_outfits:
        cols = st.columns(2)
        for i, outfit in enumerate(saved_outfits):
            with cols[i % 2]:
                st.subheader(f"Outfit {i+1}")
                if os.path.exists(outfit['image_path']):
                    st.image(outfit['image_path'])
                    if st.button(f"Delete Outfit {i+1}", key=f"delete_outfit_{outfit['outfit_id']}_{uuid.uuid4().hex[:8]}"):
                        delete_outfit(outfit['outfit_id'])
                        st.success(f"Outfit {i+1} deleted successfully!")
                        st.experimental_rerun()
                else:
                    st.error(f"Image not found: {outfit['image_path']}")
    else:
        st.info("You haven't saved any outfits yet.")

def main():
    pages = {
        "Home": main_page,
        "My Wardrobe": personal_wardrobe_page,
        "Saved Outfits": saved_outfits_page
    }
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", list(pages.keys()))
    
    pages[page]()

if __name__ == "__main__":
    main()