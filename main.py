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
from auth import auth_form, require_login
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

# ... [rest of the helper functions remain the same] ...

def main_page():
    st.title("Outfit Wizard 🧙‍♂️👚👖👞")
    
    st.sidebar.header("Set Your Preferences")
    auth_form()
    
    try:
        clothing_items = load_clothing_items()
        
        size = st.sidebar.selectbox("Size", ["XS", "S", "M", "L", "XL"])
        style = st.sidebar.selectbox("Style", ["Casual", "Formal", "Sporty"])
        gender = st.sidebar.selectbox("Gender", ["Male", "Female", "Unisex"])
        
        if 'outfit' not in st.session_state or st.sidebar.button("Generate New Outfit 🔄"):
            st.session_state.outfit, st.session_state.missing_items = generate_outfit(clothing_items, size, style, gender)
        
        if st.session_state.outfit:
            st.success("Outfit generated successfully!")
            
            # Display merged outfit image
            if 'merged_image_path' in st.session_state.outfit:
                st.image(st.session_state.outfit['merged_image_path'], use_column_width=True)
                
                # Add like buttons for individual items
                cols = st.columns(3)
                for i, item_type in enumerate(['shirt', 'pants', 'shoes']):
                    with cols[i]:
                        if item_type in st.session_state.outfit:
                            if st.button(f"Like {item_type}"):
                                store_user_preference(st.session_state.username, st.session_state.outfit[item_type]['id'])
                                st.success(f"You liked this {item_type}!")
            
            # Save outfit button
            if st.button("Save Outfit"):
                if st.session_state.username:
                    saved_path = save_outfit(st.session_state.outfit, st.session_state.username)
                    if saved_path:
                        st.success("Outfit saved successfully!")
                    else:
                        st.error("Failed to save outfit")
                else:
                    st.warning("Please log in to save outfits")
                    
        if st.session_state.missing_items:
            st.warning(f"Couldn't find matching items for: {', '.join(st.session_state.missing_items)}")
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# ... [rest of the code remains the same] ...

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
