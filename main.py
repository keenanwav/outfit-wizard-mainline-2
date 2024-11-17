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
    get_outfit_details, update_item_details, delete_saved_outfit,
    get_price_history, update_item_image
)
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity
import logging
from color_utils import get_color_palette, display_color_palette, rgb_to_hex, parse_color_string
from outfit_generator import generate_outfit, cleanup_merged_outfits
from datetime import datetime, timedelta
from style_assistant import get_style_recommendation, format_clothing_items
import time
from error_pages import render_404_page, render_500_page, render_websocket_error, render_maintenance_page, init_error_handling

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

def show_tutorial():
    """Show the tutorial in the navigation bar"""
    # Initialize session state variables
    if 'tutorial_shown' not in st.session_state:
        st.session_state.tutorial_shown = False
    if 'tutorial_step' not in st.session_state:
        st.session_state.tutorial_step = 0
    if 'tutorial_dismissed' not in st.session_state:
        st.session_state.tutorial_dismissed = False

    # Only show tutorial for first-time visitors
    if not st.session_state.tutorial_shown and not st.session_state.tutorial_dismissed:
        tutorial_content = [
            {
                "title": "Welcome to Outfit Wizard! 👋",
                "content": """
                Let me guide you through the key features:
                - Create your digital wardrobe
                - Generate outfit combinations
                - Get style recommendations
                """
            },
            {
                "title": "Adding Items 📸",
                "content": """
                Start by adding your clothing items:
                - Upload item photos
                - Set size and style preferences
                - Add price and shopping links
                """
            },
            {
                "title": "Generate Outfits ✨",
                "content": """
                Let AI help you create perfect combinations:
                - Choose your style preference
                - Get personalized recommendations
                - Save your favorite outfits
                """
            }
        ]

        if st.session_state.tutorial_step < len(tutorial_content):
            current_step = tutorial_content[st.session_state.tutorial_step]
            
            with st.container():
                # Tutorial bubble with custom styling
                st.markdown("""
                    <div class="tutorial-bubble visible">
                        <div class="tutorial-content">
                            <h3>{}</h3>
                            <div class="tutorial-text">{}</div>
                        </div>
                    </div>
                """.format(
                    current_step["title"],
                    current_step["content"]
                ), unsafe_allow_html=True)
                
                # Navigation buttons
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("Next ➡️", key="tutorial_next"):
                        st.session_state.tutorial_step += 1
                        st.rerun()
                with col2:
                    if st.button("Skip Tutorial ✖️", key="tutorial_skip"):
                        st.session_state.tutorial_shown = True
                        st.session_state.tutorial_dismissed = True
                        st.rerun()

        # Tutorial completion
        if st.session_state.tutorial_step >= len(tutorial_content):
            st.session_state.tutorial_shown = True
            st.session_state.tutorial_dismissed = True
            st.rerun()

def load_custom_css():
    """Load custom CSS for the application"""
    try:
        with open("static/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error loading custom CSS: {str(e)}")

def main():
    """Main application entry point"""
    try:
        # Initialize error handling
        init_error_handling()
        
        # Load custom CSS
        load_custom_css()
        
        # Configure Streamlit page
        st.set_page_config(
            page_title="Outfit Wizard",
            page_icon="👕",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Create sidebar navigation
        with st.sidebar:
            st.title("Navigation")
            # Show tutorial in navigation bar
            show_tutorial()
            
            # Navigation menu
            st.markdown("---")  # Separator
            page = st.radio("Go to:", ["Home", "My Items", "Saved Outfits"])
        
        # Initialize session states
        if 'show_prices' not in st.session_state:
            st.session_state.show_prices = True
        
        # Main content
        st.title("Outfit Wizard")
        
        # Load clothing items
        items_df = load_clothing_items()
        
        if items_df.empty:
            st.warning("Please add some clothing items in the 'My Items' section first!")
            return
        
        # Add tabs for different features
        tab1, tab2 = st.tabs(["📋 Generate Outfit", "🎯 Smart Style Assistant"])
        
        with tab1:
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                size = st.selectbox("Size", ["S", "M", "L", "XL"])
                style = st.selectbox("Style", ["Casual", "Formal", "Sport", "Beach"])
            
            with col2:
                gender = st.selectbox("Gender", ["Male", "Female", "Unisex"])
                
            with col3:
                st.write("")
                st.write("")
                if st.button("Toggle Prices" if st.session_state.show_prices else "Show Prices"):
                    st.session_state.show_prices = not st.session_state.show_prices
                    st.rerun()
            
            # Create two columns for outfit display and price information
            outfit_col, price_col = st.columns([0.7, 0.3])
            
            if st.button("Generate Outfit"):
                with st.spinner("🔮 Generating your perfect outfit..."):
                    # Generate the outfit
                    outfit, missing_items = generate_outfit(items_df, size, style, gender)
                    st.session_state.current_outfit = outfit
            
            # Display current outfit details if available
            if st.session_state.current_outfit:
                outfit = st.session_state.current_outfit
                
                # Display outfit image in the left column
                with outfit_col:
                    if 'merged_image_path' in outfit and os.path.exists(outfit['merged_image_path']):
                        st.image(outfit['merged_image_path'], use_column_width=True)
                    
                    if missing_items:
                        st.warning(f"Missing items: {', '.join(missing_items)}")
                
                # Display prices and colors in the right column with animation
                with price_col:
                    price_container_class = "" if st.session_state.show_prices else "hidden"
                    st.markdown(f"""
                        <div class="price-container {price_container_class}">
                            <h3>Price Information</h3>
                    """, unsafe_allow_html=True)
                    
                    # Display individual prices with animation
                    for item_type, item in outfit.items():
                        if item_type not in ['merged_image_path', 'total_price'] and isinstance(item, dict):
                            st.markdown(f"""
                                <div class="price-item">
                                    <strong>{item_type.capitalize()}</strong><br>
                                    {'$' + f"{float(item['price']):.2f}" if item.get('price') else 'Price not available'}
                                </div>
                            """, unsafe_allow_html=True)
                    
                    # Display total price with animation
                    if 'total_price' in outfit:
                        st.markdown("""<hr>""", unsafe_allow_html=True)
                        st.markdown(f"""
                            <div class="total-price">
                                <h3>Total Price</h3>
                                ${outfit['total_price']:.2f}
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # Display individual item colors within price_col
                    st.markdown("### Color Palette")
                    for item_type, item in outfit.items():
                        if item_type not in ['merged_image_path', 'total_price'] and isinstance(item, dict):
                            st.markdown(f"**{item_type.capitalize()}**")
                            color = parse_color_string(str(item['color']))
                            display_color_palette([color])
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Add shopping information below the outfit display
                st.markdown("### Shop Items")
                shop_cols = st.columns(3)
                for idx, (item_type, item) in enumerate(outfit.items()):
                    if item_type not in ['merged_image_path', 'total_price'] and isinstance(item, dict):
                        with shop_cols[idx]:
                            if item.get('hyperlink'):
                                st.link_button(f"Shop {item_type.capitalize()}", item['hyperlink'])
                
                # Save outfit option
                if st.button("Save Outfit"):
                    saved_path = save_outfit(outfit)
                    if saved_path:
                        st.success("Outfit saved successfully!")
                    else:
                        st.error("Error saving outfit")

        with tab2:
            # Add style assistant code here, using st.columns for layout, and st.selectbox, st.multiselect for user input.
            st.header("Smart Style Assistant")
            st.write("This section allows you to get personalized style recommendations based on your wardrobe.")
            
            # Add a button to initiate style recommendation
            if st.button("Get Style Recommendations"):
                with st.spinner("🧠 Analyzing your wardrobe..."):
                    # Fetch recommendations
                    recommendations = get_style_recommendation(items_df)
                    
                    if recommendations:
                        st.success("Recommendations generated successfully!")
                        
                        # Display recommendations
                        recommendations_col, example_outfit_col = st.columns([2, 1])
                        
                        with recommendations_col:
                            st.markdown("### Recommendations")
                            for recommendation in recommendations:
                                st.write(f"**{recommendation['recommendation_type']}:** {recommendation['description']}")
                        
                        with example_outfit_col:
                            st.markdown("### Example Outfit")
                            st.markdown(f"**Size:** {recommendations[0]['size']}")
                            st.markdown(f"**Style:** {recommendations[0]['style']}")
                            st.markdown(f"**Gender:** {recommendations[0]['gender']}")
                            
                            # Generate an example outfit based on the recommendation
                            example_outfit, missing_items = generate_outfit(items_df, recommendations[0]['size'], recommendations[0]['style'], recommendations[0]['gender'])
                            
                            if 'merged_image_path' in example_outfit and os.path.exists(example_outfit['merged_image_path']):
                                st.image(example_outfit['merged_image_path'], use_column_width=True)
                            
                            if missing_items:
                                st.warning(f"Missing items: {', '.join(missing_items)}")
                    
                    else:
                        st.warning("No recommendations found for your wardrobe. Please add more items.")
                        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        render_500_page()

if __name__ == "__main__":
    main()