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
from datetime import datetime

# [Previous code remains exactly the same up to line 445]

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
