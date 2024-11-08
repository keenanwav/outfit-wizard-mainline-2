import streamlit as st
import os
from PIL import Image
import numpy as np
import pandas as pd
from collections import Counter
from data_manager import (
    load_clothing_items, save_outfit, load_saved_outfits,
    edit_clothing_item, delete_clothing_item, create_user_items_table,
    add_user_clothing_item, update_outfit_details,
    get_outfit_details, update_item_details, delete_saved_outfit
)
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity
import logging
from color_utils import get_color_palette, display_color_palette, rgb_to_hex
from outfit_generator import generate_outfit, cleanup_merged_outfits
from datetime import datetime, timedelta

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

# Add custom CSS for dark theme styling
st.markdown("""
<style>
    /* General theme */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Button styling */
    .stButton>button {
        background-color: #FF4B4B;
        color: #FAFAFA;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.3rem;
        transition: background-color 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #FF6B6B;
    }
    
    /* Input fields styling */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>input,
    .stTextArea>div>div>textarea {
        background-color: #262730;
        color: #FAFAFA;
        border: 1px solid #4B4B4B;
    }
    
    /* File uploader styling */
    .stFileUploader {
        background-color: #262730;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px dashed #4B4B4B;
    }
    
    .stFileUploader>div>button {
        background-color: #262730;
        color: #FAFAFA;
        border: 1px solid #4B4B4B;
    }
    
    /* Expander and container styling */
    div[data-testid="stExpander"],
    div.stContainer {
        background-color: #262730;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #4B4B4B;
    }
    
    /* Image container styling */
    div[data-testid="stImage"] {
        background-color: #262730;
        border-radius: 0.5rem;
        padding: 0.5rem;
        border: 1px solid #4B4B4B;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #262730;
        border-right: 1px solid #4B4B4B;
    }
    
    section[data-testid="stSidebar"] .stMarkdown {
        color: #FAFAFA;
    }
    
    /* Headers styling */
    h1, h2, h3, h4, h5, h6 {
        color: #FAFAFA !important;
    }
    
    /* Text styling */
    p, span, div, label {
        color: #FAFAFA;
    }
    
    /* Link styling */
    a {
        color: #FF4B4B !important;
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #262730;
        padding: 0.5rem;
        border-radius: 0.5rem;
        border: 1px solid #4B4B4B;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #FAFAFA;
    }
    
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #FF4B4B;
    }
    
    /* Success/Error message styling */
    div[data-testid="stAlert"] {
        background-color: #262730;
        border: 1px solid #4B4B4B;
        color: #FAFAFA;
    }
    
    /* Checkbox styling */
    .stCheckbox>label>div[data-testid="stMarkdownContainer"]>p {
        color: #FAFAFA;
    }
    
    /* Radio button styling */
    .stRadio>label>div[data-testid="stMarkdownContainer"]>p {
        color: #FAFAFA;
    }
    
    /* Selectbox styling */
    .stSelectbox>div>div>div {
        background-color: #262730;
        color: #FAFAFA;
    }
    
    /* Color picker styling */
    .stColorPicker>label {
        color: #FAFAFA;
    }
    
    /* Caption styling */
    .stCaption {
        color: #B0B0B0;
    }
</style>
""", unsafe_allow_html=True)

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
                st.experimental_rerun()

def check_cleanup_needed():
    """Check if cleanup is needed and perform it"""
    if 'last_cleanup' not in st.session_state:
        st.session_state.last_cleanup = datetime.now()
        cleanup_merged_outfits()
    else:
        time_since_cleanup = datetime.now() - st.session_state.last_cleanup
        if time_since_cleanup.total_seconds() > 3600:  # Check every hour
            cleanup_merged_outfits()
            st.session_state.last_cleanup = datetime.now()

def parse_color_string(color_str):
    """Parse color string to RGB tuple"""
    try:
        return tuple(map(int, color_str.split(',')))
    except:
        return (0, 0, 0)

def normalize_case(text):
    """Normalize text case for consistent display"""
    return text.strip().lower().capitalize()

def personal_wardrobe_page():
    """Display and manage personal wardrobe items"""
    st.title("My Items")
    
    # Load existing items
    items_df = load_clothing_items()
    
    # Upload new item form
    with st.expander("Upload New Item", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            item_type = st.selectbox("Type", ["Shirt", "Pants", "Shoes"])
            styles = st.multiselect("Style", ["Casual", "Formal", "Sport", "Beach"])
            sizes = st.multiselect("Size", ["S", "M", "L", "XL"])
        
        with col2:
            genders = st.multiselect("Gender", ["Male", "Female", "Unisex"])
            uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
            hyperlink = st.text_input("Shopping Link (optional)", 
                                    help="Add a link to where this item can be purchased")
        
        if uploaded_file and styles and sizes and genders:
            # Extract color after image upload
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            colors = get_color_palette(temp_path)
            if colors is not None:
                st.write("Extracted Color:")
                display_color_palette(colors)
                
                if st.button("Add Item"):
                    success, message = add_user_clothing_item(
                        item_type.lower(), colors[0], styles, genders, sizes, temp_path, hyperlink
                    )
                    if success:
                        st.success(message)
                        st.experimental_rerun()
                    else:
                        st.error(message)
            
            os.remove(temp_path)
    
    # Display existing items in grid
    if not items_df.empty:
        st.markdown("### Your Items")
        
        # Group items by type
        for item_type in ["shirt", "pants", "shoes"]:
            type_items = items_df[items_df['type'] == item_type]
            if not type_items.empty:
                st.markdown(f"#### {item_type.capitalize()}s")
                
                # Create grid layout (3 items per row)
                cols = st.columns(3)
                for idx, item in type_items.iterrows():
                    col = cols[idx % 3]
                    with col:
                        if os.path.exists(item['image_path']):
                            st.image(item['image_path'], use_column_width=True)
                            
                            # Edit/Delete buttons
                            edit_col, del_col = st.columns([3, 1])
                            with edit_col:
                                if st.button(f"Edit Details {idx}"):
                                    st.session_state.editing_item = item
                                    
                            with del_col:
                                if st.button(f"🗑️ {idx}"):
                                    success, message = delete_clothing_item(int(item['id']))
                                    if success:
                                        st.success(message)
                                        st.experimental_rerun()
                                    else:
                                        st.error(message)
                            
                            # Display item details
                            color = parse_color_string(item['color'])
                            st.markdown(f"**Style:** {item['style']}")
                            st.markdown(f"**Size:** {item['size']}")
                            if item['hyperlink']:
                                st.markdown(f"[Shop Link]({item['hyperlink']})")
                            
                            # Organization features
                            tags = item['tags'] if item['tags'] else []
                            new_tags = st.text_input(f"Tags {idx}", 
                                                   value=','.join(tags) if tags else "",
                                                   help="Comma-separated tags")
                            
                            season = st.selectbox(f"Season {idx}",
                                                ["", "Spring", "Summer", "Fall", "Winter"],
                                                index=0 if not item['season'] else 
                                                ["", "Spring", "Summer", "Fall", "Winter"].index(item['season']))
                            
                            notes = st.text_area(f"Notes {idx}", 
                                               value=item['notes'] if item['notes'] else "",
                                               help="Add notes about this item")
                            
                            if st.button(f"Save Details {idx}"):
                                success, message = update_item_details(
                                    int(item['id']),
                                    tags=new_tags.split(',') if new_tags else None,
                                    season=season if season else None,
                                    notes=notes if notes else None
                                )
                                if success:
                                    st.success(message)
                                    st.experimental_rerun()
                                else:
                                    st.error(message)

def main_page():
    """Display main page with outfit generation"""
    st.title("Outfit Generator")
    
    # Load clothing items
    items_df = load_clothing_items()
    
    if items_df.empty:
        st.warning("Please add some clothing items in the 'My Items' section first!")
        return
    
    # Outfit generation form
    col1, col2 = st.columns(2)
    
    with col1:
        size = st.selectbox("Size", ["S", "M", "L", "XL"])
        style = st.selectbox("Style", ["Casual", "Formal", "Sport", "Beach"])
    
    with col2:
        gender = st.selectbox("Gender", ["Male", "Female", "Unisex"])
    
    if st.button("Generate Outfit"):
        outfit, missing_items = generate_outfit(items_df, size, style, gender)
        
        if missing_items:
            st.warning(f"Missing items: {', '.join(missing_items)}")
        
        if 'merged_image_path' in outfit and os.path.exists(outfit['merged_image_path']):
            st.image(outfit['merged_image_path'], use_column_width=True)
            
            # Add shopping buttons
            st.markdown("### Shop Items")
            shop_cols = st.columns(3)
            for idx, (item_type, item) in enumerate(outfit.items()):
                if item_type != 'merged_image_path' and item.get('hyperlink'):
                    with shop_cols[idx]:
                        st.link_button(f"Shop {item_type.capitalize()}", item['hyperlink'])
            
            # Display individual item colors
            st.markdown("### Item Colors")
            cols = st.columns(3)
            for idx, (item_type, item) in enumerate(outfit.items()):
                if item_type != 'merged_image_path':
                    with cols[idx]:
                        color = parse_color_string(item['color'])
                        st.markdown(f"**{item_type.capitalize()}**")
                        display_color_palette([color])
            
            # Save outfit option
            if st.button("Save Outfit"):
                saved_path = save_outfit(outfit)
                if saved_path:
                    st.success("Outfit saved successfully!")
                else:
                    st.error("Error saving outfit")

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
        col = cols[idx % 3]
        with col:
            if os.path.exists(outfit['image_path']):
                st.image(outfit['image_path'], use_column_width=True)
                
                # Organization features
                tags = outfit['tags'] if outfit['tags'] else []
                new_tags = st.text_input(f"Tags {outfit['outfit_id']}", 
                                       value=','.join(tags) if tags else "",
                                       help="Comma-separated tags")
                
                season = st.selectbox(f"Season {outfit['outfit_id']}",
                                    ["", "Spring", "Summer", "Fall", "Winter"],
                                    index=0 if not outfit['season'] else 
                                    ["", "Spring", "Summer", "Fall", "Winter"].index(outfit['season']))
                
                notes = st.text_area(f"Notes {outfit['outfit_id']}", 
                                   value=outfit['notes'] if outfit['notes'] else "",
                                   help="Add notes about this outfit")
                
                # Save and Delete buttons
                save_col, del_col = st.columns([3, 1])
                with save_col:
                    if st.button(f"Save Details {outfit['outfit_id']}"):
                        success, message = update_outfit_details(
                            outfit['outfit_id'],
                            tags=new_tags.split(',') if new_tags else None,
                            season=season if season else None,
                            notes=notes if notes else None
                        )
                        if success:
                            st.success(message)
                            st.experimental_rerun()
                        else:
                            st.error(message)
                
                with del_col:
                    if st.button(f"🗑️ {outfit['outfit_id']}"):
                        success, message = delete_saved_outfit(outfit['outfit_id'])
                        if success:
                            st.success(message)
                            st.experimental_rerun()
                        else:
                            st.error(message)

def main():
    """Main application entry point"""
    # Initialize database tables
    create_user_items_table()
    
    # Show first-visit tips
    show_first_visit_tips()
    
    # Check for cleanup needed
    check_cleanup_needed()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Generate Outfit", "My Items", "Saved Outfits"])
    
    # Display selected page
    if page == "Generate Outfit":
        main_page()
    elif page == "My Items":
        personal_wardrobe_page()
    else:
        saved_outfits_page()

if __name__ == "__main__":
    main()
