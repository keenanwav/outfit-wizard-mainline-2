import streamlit as st
import os
from PIL import Image
import numpy as np
import pandas as pd
from collections import Counter
from color_utils import get_color_palette
from outfit_generator import generate_outfit
from data_manager import load_clothing_items, save_outfit, add_clothing_item, update_csv_structure, store_user_preference, get_advanced_recommendations, load_saved_outfits, delete_outfit, edit_clothing_item, delete_clothing_item
from auth import auth_form, require_login
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity
import logging

st.set_page_config(page_title="Outfit Wizard", page_icon="👕", layout="wide")

logging.basicConfig(level=logging.INFO)

def normalize_case(value):
    """Helper function to normalize case of strings"""
    return value.strip().title() if isinstance(value, str) else value

def get_dominant_color(image):
    try:
        img = Image.open(image)
        st.write(f"Image mode: {img.mode}")
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img = img.resize((100, 100))
        img_array = np.array(img)
        st.write(f"Image array shape: {img_array.shape}")
        
        colors = img_array.reshape(-1, 3)
        color_counts = Counter(map(tuple, colors))
        dominant_color = color_counts.most_common(1)[0][0]
        return '#{:02x}{:02x}{:02x}'.format(*dominant_color)
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return "#000000"

def display_outfit(outfit, missing_items):
    if outfit:
        st.success("Outfit generated successfully!")
        
        if missing_items:
            st.warning(f"Unable to find the following items: {', '.join(missing_items)}. Showing partial outfit.")
        
        cols = st.columns(3)
        for i, item_type in enumerate(['shirt', 'pants', 'shoes']):
            with cols[i]:
                st.subheader(item_type.capitalize())
                if item_type in outfit:
                    image_path = outfit[item_type]['image_path']
                    if os.path.exists(image_path):
                        try:
                            img = Image.open(image_path)
                            st.image(img, use_column_width=True)
                            if st.button(f"Like {item_type}", key=f"like_{item_type}"):
                                store_user_preference(st.session_state.username, outfit[item_type]['id'])
                                st.success(f"You liked this {item_type}!")
                        except Exception as e:
                            st.error(f"Error opening image for {item_type}: {str(e)}")
                    else:
                        st.error(f"Image file not found for {item_type}: {image_path}")
                else:
                    st.error(f"No {item_type} available for the given preferences.")
        
        if st.button("Save Outfit"):
            if 'username' not in st.session_state or not st.session_state.username:
                st.error("Please log in to save outfits.")
            else:
                try:
                    saved_path = save_outfit(outfit, st.session_state.username)
                    if saved_path:
                        st.success(f"Outfit saved successfully! Path: {saved_path}")
                    else:
                        st.error("Failed to save outfit. Please try again.")
                except Exception as e:
                    st.error(f"Error saving outfit: {str(e)}")
    else:
        st.error("Unable to generate an outfit with the given preferences. Please try different options.")

def main_page():
    st.title("Outfit Wizard 🧙‍♂️👚👖👞")

    st.sidebar.header("Set Your Preferences")
    auth_form()

    try:
        clothing_items = load_clothing_items()
        st.write(f"Loaded {len(clothing_items)} clothing items")

        size = st.sidebar.selectbox("Size", ["XS", "S", "M", "L", "XL"])
        style = st.sidebar.selectbox("Style", ["Casual", "Formal", "Sporty"])
        gender = st.sidebar.selectbox("Gender", ["Male", "Female", "Unisex"])

        if 'outfit' not in st.session_state or st.sidebar.button("Generate New Outfit 🔄"):
            st.session_state.outfit, st.session_state.missing_items = generate_outfit(clothing_items, size, style, gender)

        display_outfit(st.session_state.outfit, st.session_state.missing_items)

        st.header("Advanced Personalized Recommendations")
        if 'username' in st.session_state and st.session_state.username:
            collab_weight = st.slider("Collaborative Filtering Weight", 0.0, 1.0, 0.7, 0.1)
            try:
                recommendations = get_advanced_recommendations(st.session_state.username, n_recommendations=5, collab_weight=collab_weight)
                
                if not recommendations.empty:
                    st.write("Based on your preferences and our advanced recommendation algorithm, we suggest these items:")
                    cols = st.columns(5)
                    for i, (_, item) in enumerate(recommendations.iterrows()):
                        with cols[i % 5]:
                            st.subheader(f"{item['type'].capitalize()}")
                            if os.path.exists(item['image_path']):
                                st.image(item['image_path'], use_column_width=True)
                                st.write(f"Style: {item['style']}")
                                st.write(f"Gender: {item['gender']}")
                                st.write(f"Size: {item['size']}")
                                if st.button(f"Like", key=f"like_rec_{item['id']}_{i}"):
                                    store_user_preference(st.session_state.username, item['id'])
                                    st.success(f"You liked this {item['type']}!")
                                if item['hyperlink']:
                                    st.markdown(f"[View Product]({item['hyperlink']})")
                            else:
                                st.error(f"Image not found: {item['image_path']}")
                else:
                    st.info("No recommendations available. Try liking some items!")
            except Exception as e:
                logging.error(f"Error generating recommendations: {str(e)}")
                st.error("An error occurred while generating recommendations. Please try again later.")
        else:
            st.info("Please log in to see personalized recommendations.")

    except Exception as e:
        logging.error(f"Error in main page: {str(e)}")
        st.error(f"An error occurred: {str(e)}")

    st.sidebar.markdown("---")
    st.sidebar.info("Outfit Wizard helps you create harmonious outfits based on your preferences and provides personalized recommendations using advanced machine learning algorithms.")

def admin_page():
    st.title("Admin Panel")
    
    # Check if user is logged in or needs admin access
    is_logged_in = 'username' in st.session_state and st.session_state.username
    
    if not is_logged_in:
        st.warning("You are not logged in. Use the button below to access admin features.")
        if st.button("Access as Admin"):
            st.session_state.username = 'admin'
            st.experimental_rerun()
        return
    
    update_csv_structure()
    
    tab1, tab2, tab3 = st.tabs(["Add Item", "View/Edit Items", "Delete Items"])
    
    with tab1:
        add_clothing_item_form()
    
    with tab2:
        view_edit_items()
    
    with tab3:
        delete_items()

def add_clothing_item_form():
    st.header("Add New Clothing Item")
    with st.form("add_clothing_item"):
        item_type = st.selectbox("Item Type", ["shirt", "pants", "shoes"])
        image_file = st.file_uploader("Upload Image (PNG)", type="png")
        hyperlink = st.text_input("Add Hyperlink (optional)")
        
        if image_file is not None:
            dominant_color = get_dominant_color(image_file)
            st.write(f"Dominant color extracted: {dominant_color}")
            color = st.color_picker("Color", dominant_color)
        else:
            color = st.color_picker("Color", "#000000")
        
        st.write("Style (select all that apply):")
        style_options = ["Casual", "Formal", "Sporty"]
        styles = []
        cols = st.columns(len(style_options))
        for i, style in enumerate(style_options):
            if cols[i].checkbox(style):
                styles.append(style)
        
        st.write("Gender (select all that apply):")
        gender_options = ["Male", "Female", "Unisex"]
        genders = []
        gender_cols = st.columns(len(gender_options))
        for i, gender in enumerate(gender_options):
            if gender_cols[i].checkbox(gender):
                genders.append(gender)

        st.write("Size (select all that apply):")
        size_options = ["XS", "S", "M", "L", "XL"]
        sizes = []
        size_cols = st.columns(len(size_options))
        for i, size in enumerate(size_options):
            if size_cols[i].checkbox(size):
                sizes.append(size)

        submitted = st.form_submit_button("Submit")
        if submitted:
            if image_file is not None:
                try:
                    rgb_color = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                    success, message = add_clothing_item(item_type, rgb_color, styles, genders, sizes, image_file, hyperlink)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                except Exception as e:
                    st.error(f"Error adding clothing item: {str(e)}")
            else:
                st.error("Please upload an image file.")

def view_edit_items():
    st.header("View/Edit Clothing Items")
    clothing_items = load_clothing_items()
    
    search_query = st.text_input("Search items by type, style, or gender:")
    if search_query:
        clothing_items = clothing_items[
            clothing_items['type'].str.contains(search_query, case=False) |
            clothing_items['style'].str.contains(search_query, case=False) |
            clothing_items['gender'].str.contains(search_query, case=False)
        ]
    
    items_per_page = 10
    num_pages = (len(clothing_items) - 1) // items_per_page + 1
    page = st.number_input("Page", min_value=1, max_value=num_pages, value=1)
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    
    # Define style options with consistent case
    style_options = ["Casual", "Formal", "Sporty"]
    
    for index, item in clothing_items.iloc[start_idx:end_idx].iterrows():
        with st.expander(f"{item['type'].capitalize()} (ID: {item['id']})"):
            col1, col2 = st.columns([1, 2])
            with col1:
                if os.path.exists(item['image_path']):
                    st.image(item['image_path'], use_column_width=True)
                else:
                    st.error(f"Image not found: {item['image_path']}")
            
            with col2:
                with st.form(f"edit_item_{item['id']}"):
                    color_value = item['color'].replace(',', '')
                    if color_value and len(color_value) == 6:
                        new_color = st.color_picker("Color", f"#{color_value}")
                    else:
                        new_color = st.color_picker("Color", "#000000")
                    
                    # Normalize the case of default values
                    current_styles = [normalize_case(style) for style in item['style'].split(',')]
                    new_styles = st.multiselect('Style', style_options, default=current_styles)
                    
                    new_genders = st.multiselect('Gender', ['Male', 'Female', 'Unisex'], 
                                               default=[gender.strip() for gender in item['gender'].split(',')])
                    new_sizes = st.multiselect("Size", ["XS", "S", "M", "L", "XL"], 
                                             default=[size.strip() for size in item['size'].split(',')])
                    new_hyperlink = st.text_input("Hyperlink", value=item['hyperlink'])
                    
                    if st.form_submit_button("Update"):
                        try:
                            rgb_color = tuple(int(new_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                            success, message = edit_clothing_item(item['id'], rgb_color, new_styles, new_genders, new_sizes, new_hyperlink)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                        except Exception as e:
                            st.error(f"Error updating clothing item: {str(e)}")

def delete_items():
    st.header("Delete Clothing Items")
    clothing_items = load_clothing_items()
    
    search_query = st.text_input("Search items to delete by type, style, or gender:")
    if search_query:
        clothing_items = clothing_items[
            clothing_items['type'].str.contains(search_query, case=False) |
            clothing_items['style'].str.contains(search_query, case=False) |
            clothing_items['gender'].str.contains(search_query, case=False)
        ]
    
    for index, item in clothing_items.iterrows():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if os.path.exists(item['image_path']):
                st.image(item['image_path'], use_column_width=True)
            else:
                st.error(f"Image not found: {item['image_path']}")
        
        with col2:
            st.write(f"Type: {item['type'].capitalize()}")
            st.write(f"Color: {item['color']}")
            st.write(f"Style: {item['style']}")
            st.write(f"Gender: {item['gender']}")
            st.write(f"Size: {item['size']}")
        
        with col3:
            if st.button(f"Delete Item {item['id']}", key=f"delete_button_{item['id']}"):
                if st.button("Confirm Delete", key=f"confirm_delete_{item['id']}"):
                    try:
                        success, message = delete_clothing_item(item['id'])
                        if success:
                            st.success(message)
                            st.experimental_rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"Error deleting clothing item: {str(e)}")
        
        st.markdown("---")

def saved_outfits_page():
    st.title("Saved Outfits")
    require_login(lambda: None)
    
    saved_outfits = load_saved_outfits(st.session_state.username)
    
    print(f'Number of saved outfits: {len(saved_outfits)}')
    
    if saved_outfits:
        cols = st.columns(2)
        for i, outfit in enumerate(saved_outfits):
            with cols[i % 2]:
                with st.container():
                    st.subheader(f"Outfit {i+1}")
                    st.caption(f"Saved on {outfit['date']}")

                    try:
                        outfit_img = Image.open(outfit['image_path'])
                        
                        width, height = outfit_img.size
                        shirt = outfit_img.crop((0, 0, width//3, height))
                        pants = outfit_img.crop((width//3, 0, 2*width//3, height))
                        shoes = outfit_img.crop((2*width//3, 0, width, height))
                        
                        vertical_img = Image.new('RGB', (width//3, height), (255, 255, 255))
                        vertical_img.paste(shirt, (0, 0))
                        vertical_img.paste(pants, (0, height//3))
                        vertical_img.paste(shoes, (0, 2*height//3))
                        
                        st.image(vertical_img, use_column_width=True)
                        
                        print(f"Displaying outfit: {outfit['image_path']}")
                        
                        if st.button(f"Delete Outfit {i+1}", key=f"delete_outfit_{i}"):
                            delete_outfit(outfit['outfit_id'])
                            st.success(f"Outfit {i+1} deleted successfully!")
                            st.experimental_rerun()
                    except FileNotFoundError:
                        st.error(f"Image file not found: {outfit['image_path']}")
                        continue
                
                st.markdown("---")
            
            if i == 7:
                break
        
        if len(saved_outfits) > 8:
            if st.button("See More Outfits"):
                st.warning("Feature coming soon!")

def main():
    page = st.sidebar.selectbox("Navigation", ["Home", "Admin", "Saved Outfits"])
    
    if page == "Home":
        main_page()
    elif page == "Admin":
        admin_page()
    else:
        saved_outfits_page()

if __name__ == "__main__":
    main()
