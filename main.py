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
    
    tabs = st.tabs(["Upload New Item", "View My Items"])
    
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

def main_page():
    st.title("Outfit Wizard 🧙‍♂️👚👖👞")
    
    st.sidebar.header("Set Your Preferences")
    
    try:
        clothing_items = load_clothing_items()
        
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
                    if st.button(f"Delete Outfit {i+1}"):
                        delete_outfit(outfit['outfit_id'])
                        st.success(f"Outfit {i+1} deleted successfully!")
                        st.experimental_rerun()
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
