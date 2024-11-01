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
import base64

st.set_page_config(
    page_title="Outfit Wizard",
    page_icon="👕",
    layout="wide",
    initial_sidebar_state="collapsed"  # Mobile-friendly default
)

# Load custom CSS
with open('.streamlit/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Add mobile detection
def is_mobile():
    try:
        user_agent = st.experimental_get_query_params().get('user_agent', [''])[0]
        return any(device in user_agent.lower() for device in ['mobile', 'android', 'iphone', 'ipad', 'ipod'])
    except:
        return False

def show_mobile_menu():
    menu = st.sidebar.radio("Menu", ["Home", "My Wardrobe", "Saved Outfits"])
    if menu == "Home":
        main_page()
    elif menu == "My Wardrobe":
        personal_wardrobe_page()
    else:
        saved_outfits_page()

def main_page():
    st.title("Outfit Wizard 🧙‍♂️")
    
    # Mobile-optimized authentication
    with st.container():
        auth_form()
    
    try:
        clothing_items = load_clothing_items()
        
        # Mobile-friendly preference selection
        with st.expander("Set Your Preferences", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                size = st.selectbox("Size", ["XS", "S", "M", "L", "XL"], key="mobile_size")
                style = st.selectbox("Style", ["Casual", "Formal", "Sporty"], key="mobile_style")
            with col2:
                gender = st.selectbox("Gender", ["Male", "Female", "Unisex"], key="mobile_gender")
        
        # Generate outfit button
        if st.button("Generate New Outfit 🔄", use_container_width=True):
            st.session_state.outfit, st.session_state.missing_items = generate_outfit(
                clothing_items, size, style, gender
            )
        
        # Display outfit
        if 'outfit' in st.session_state and st.session_state.outfit:
            st.success("Outfit generated successfully!")
            
            if 'merged_image_path' in st.session_state.outfit:
                # Mobile-optimized image display
                st.image(
                    st.session_state.outfit['merged_image_path'],
                    use_column_width=True,
                    caption="Your Generated Outfit"
                )
                
                # Mobile-friendly interaction buttons
                for item_type in ['shirt', 'pants', 'shoes']:
                    if item_type in st.session_state.outfit:
                        if st.button(f"Like {item_type} 👍", key=f"like_{item_type}", use_container_width=True):
                            store_user_preference(st.session_state.username, st.session_state.outfit[item_type]['id'])
                            st.success(f"You liked this {item_type}!")
            
            # Save outfit button
            if st.button("Save Outfit 💾", use_container_width=True):
                if st.session_state.username:
                    saved_path = save_outfit(st.session_state.outfit, st.session_state.username)
                    if saved_path:
                        st.success("Outfit saved successfully!")
                    else:
                        st.error("Failed to save outfit")
                else:
                    st.warning("Please log in to save outfits")
                    
        if st.session_state.get('missing_items'):
            st.warning(f"Couldn't find matching items for: {', '.join(st.session_state.missing_items)}")
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

def personal_wardrobe_page():
    st.title("My Wardrobe 👕")
    create_user_items_table()
    
    if not st.session_state.get('username'):
        st.warning("Please log in to access your wardrobe")
        return
    
    # Mobile-friendly tabs
    tab1, tab2 = st.tabs(["Upload", "View Items"])
    
    with tab1:
        with st.form("add_item_mobile", clear_on_submit=True):
            st.subheader("Add New Item")
            
            item_type = st.selectbox("Type", ["shirt", "pants", "shoes"], key="mobile_item_type")
            image_file = st.file_uploader("Take Photo or Choose Image", type="png")
            
            if image_file:
                st.image(image_file, width=200)
                color = st.color_picker("Adjust Color", "#000000")
                
                # Mobile-friendly multi-select using columns
                col1, col2 = st.columns(2)
                with col1:
                    st.write("Style:")
                    styles = [style for style in ["Casual", "Formal", "Sporty"]
                             if st.checkbox(style, key=f"style_mobile_{style}")]
                    
                    st.write("Gender:")
                    genders = [gender for gender in ["Male", "Female", "Unisex"]
                              if st.checkbox(gender, key=f"gender_mobile_{gender}")]
                
                with col2:
                    st.write("Size:")
                    sizes = [size for size in ["XS", "S", "M", "L", "XL"]
                            if st.checkbox(size, key=f"size_mobile_{size}")]
                
                if st.form_submit_button("Upload", use_container_width=True):
                    if not (styles and genders and sizes):
                        st.error("Please select all required options")
                    else:
                        rgb_color = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                        success, message = add_user_clothing_item(
                            st.session_state.username,
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
    
    with tab2:
        st.subheader("My Items")
        items = load_clothing_items(st.session_state.username)
        
        if len(items) == 0:
            st.info("No items in your wardrobe yet")
            return
        
        # Mobile-friendly item display
        for _, item in items.iterrows():
            with st.expander(f"{item['type'].title()}"):
                if os.path.exists(item['image_path']):
                    st.image(item['image_path'], use_column_width=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Edit", key=f"edit_{item['id']}", use_container_width=True):
                            st.session_state.editing_item = item['id']
                    with col2:
                        if st.button("Delete", key=f"delete_{item['id']}", use_container_width=True):
                            success, message = delete_clothing_item(item['id'])
                            if success:
                                st.success(message)
                                st.experimental_rerun()
                            else:
                                st.error(message)

def saved_outfits_page():
    st.title("My Outfits 📱")
    
    if not st.session_state.get('username'):
        st.warning("Please log in to view saved outfits")
        return
    
    outfits = load_saved_outfits(st.session_state.username)
    
    if outfits:
        for outfit in outfits:
            with st.container():
                if os.path.exists(outfit['image_path']):
                    st.image(outfit['image_path'], use_column_width=True)
                    if st.button("Delete", key=f"delete_outfit_{outfit['outfit_id']}", use_container_width=True):
                        if delete_outfit(outfit['outfit_id']):
                            st.success("Outfit deleted!")
                            st.experimental_rerun()
                else:
                    st.error("Image not found")
    else:
        st.info("No saved outfits yet")

def main():
    if is_mobile():
        show_mobile_menu()
    else:
        pages = {
            "Home": main_page,
            "My Wardrobe": personal_wardrobe_page,
            "Saved Outfits": saved_outfits_page
        }
        page = st.sidebar.radio("Navigation", list(pages.keys()))
        pages[page]()

if __name__ == "__main__":
    main()
