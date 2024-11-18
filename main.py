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

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

def load_custom_css():
    """Load custom CSS for the application"""
    try:
        with open("static/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error loading custom CSS: {str(e)}")

def initialize_app():
    """Initialize the application with improved WebSocket error handling"""
    try:
        if 'initialized' not in st.session_state:
            st.session_state.initialized = True
            init_error_handling()
            create_user_items_table()
            load_custom_css()
            
            # Initialize error state
            if 'error_type' not in st.session_state:
                st.session_state.error_type = None
            
            # Add improved WebSocket error handling with exponential backoff
            st.markdown("""
                <script>
                    const MAX_RETRIES = 5;
                    const BASE_DELAY = 1000;
                    const MAX_DELAY = 16000;
                    let retryCount = 0;
                    let wsConnection = null;

                    function initializeWebSocket() {
                        if (!window._stcore) {
                            setTimeout(initializeWebSocket, 100);
                            return;
                        }

                        wsConnection = window._stcore.WebsocketConnection;
                        if (wsConnection) {
                            wsConnection.addEventListener('open', handleOpen);
                            wsConnection.addEventListener('error', handleError);
                            wsConnection.addEventListener('close', handleClose);
                            wsConnection.addEventListener('message', handleMessage);
                        }
                    }

                    function handleOpen() {
                        console.log('WebSocket connected');
                        retryCount = 0;
                    }

                    function handleError(event) {
                        console.error('WebSocket error:', event);
                        attemptReconnection();
                    }

                    function handleClose() {
                        console.log('WebSocket closed');
                        attemptReconnection();
                    }

                    function handleMessage() {
                        // Reset retry count on successful message
                        retryCount = 0;
                    }

                    function attemptReconnection() {
                        if (retryCount >= MAX_RETRIES) {
                            console.error('Max retries reached');
                            window.location.href = '/?error=websocket';
                            return;
                        }

                        const delay = Math.min(BASE_DELAY * Math.pow(2, retryCount), MAX_DELAY);
                        console.log(`Attempting reconnection in ${delay}ms (attempt ${retryCount + 1}/${MAX_RETRIES})`);

                        setTimeout(() => {
                            retryCount++;
                            if (wsConnection) {
                                // Force reconnection by reloading the page
                                window.location.reload();
                            }
                        }, delay);
                    }

                    // Initialize WebSocket handling
                    window.addEventListener('load', initializeWebSocket);
                </script>
            """, unsafe_allow_html=True)
            
            # Check for error parameters in URL
            params = st.query_params
            if 'error' in params:
                handle_error(params['error'])
                return False
        return True
    except Exception as e:
        logger.error(f"Error initializing application: {str(e)}")
        handle_error('500')
        return False

def handle_error(error_type):
    """Handle different types of errors"""
    try:
        st.session_state.error_type = error_type
        if error_type == '404':
            render_404_page()
        elif error_type == '500':
            render_500_page()
        elif error_type == 'websocket':
            render_websocket_error()
        elif error_type == 'maintenance':
            render_maintenance_page()
    except Exception as e:
        logger.error(f"Error handling error page: {str(e)}")
        st.error("An unexpected error occurred while displaying the error page.")

# Configure Streamlit page
st.set_page_config(
    page_title="Outfit Wizard",
    page_icon="👕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize the application
if initialize_app():
    try:
        # Initialize session states
        if 'show_prices' not in st.session_state:
            st.session_state.show_prices = True
        if 'editing_color' not in st.session_state:
            st.session_state.editing_color = None
        if 'color_preview' not in st.session_state:
            st.session_state.color_preview = None
        if 'editing_item' not in st.session_state:
            st.session_state.editing_item = None
            
        def main_page():
            """Display main page with outfit generation"""
            st.title("Outfit Wizard")
            
            # Initialize session state for current outfit
            if 'current_outfit' not in st.session_state:
                st.session_state.current_outfit = None
                
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
                
                # Generate outfit button
                if st.button("Generate Outfit"):
                    with st.spinner("🔮 Generating your perfect outfit..."):
                        outfit, missing_items = generate_outfit(items_df, size, style, gender)
                        st.session_state.current_outfit = outfit
                
                # Display current outfit if available
                if st.session_state.current_outfit:
                    outfit = st.session_state.current_outfit
                    if 'merged_image_path' in outfit and os.path.exists(outfit['merged_image_path']):
                        st.image(outfit['merged_image_path'], use_column_width=True)
                    
                    # Display prices if enabled
                    if st.session_state.show_prices:
                        st.markdown("### Price Information")
                        total_price = 0
                        for item_type, item in outfit.items():
                            if item_type not in ['merged_image_path']:
                                if 'price' in item and item['price']:
                                    price = float(item['price'])
                                    st.write(f"{item_type.capitalize()}: ${price:.2f}")
                                    total_price += price
                        st.markdown(f"**Total: ${total_price:.2f}**")
                    
                    # Save outfit option
                    if st.button("Save Outfit"):
                        saved_path = save_outfit(outfit)
                        if saved_path:
                            st.success("Outfit saved successfully!")
                        else:
                            st.error("Error saving outfit")

        def personal_wardrobe_page():
            """Display and manage personal wardrobe items"""
            st.title("My Items")
            
            try:
                # Load existing items
                items_df = load_clothing_items()
                
                # Add new item form
                with st.expander("Add New Item", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        item_type = st.selectbox("Type", ["shirt", "pants", "shoes"])
                        styles = st.multiselect("Style", ["Casual", "Formal", "Sport", "Beach"])
                        sizes = st.multiselect("Size", ["S", "M", "L", "XL"])
                        price = st.number_input("Price ($)", min_value=0.0, step=0.01, format="%.2f")
                    
                    with col2:
                        genders = st.multiselect("Gender", ["Male", "Female", "Unisex"])
                        uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
                        hyperlink = st.text_input("Shopping Link (optional)", 
                                                help="Add a link to where this item can be purchased")
                    
                    if uploaded_file and styles and sizes and genders:
                        success, message = add_user_clothing_item(
                            item_type, None, styles, genders, sizes, uploaded_file, hyperlink, price
                        )
                        if success:
                            st.success(message)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                
                # Display existing items in a grid layout
                if not items_df.empty:
                    st.markdown("### Your Items")
                    for index, row in items_df.iterrows():
                        with st.container():
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                # Display item image and details
                                image_path = str(row['image_path'])
                                if os.path.exists(image_path):
                                    st.image(image_path, width=200)
                                
                                # Display item details
                                st.write(f"**Type:** {str(row['type']).title()}")
                                
                                # Handle style display
                                styles = str(row['style']).split(',') if isinstance(row['style'], str) else []
                                st.write(f"**Style:** {', '.join(styles)}")
                                
                                # Handle size display
                                sizes = str(row['size']).split(',') if isinstance(row['size'], str) else []
                                st.write(f"**Size:** {', '.join(sizes)}")
                                
                                # Display price if available
                                price = row.get('price')
                                if price is not None and pd.notna(price):
                                    st.write(f"**Price:** ${float(price):.2f}")
                            
                            with col2:
                                # Edit and Delete buttons
                                if st.button("Edit", key=f"edit_{index}"):
                                    st.session_state.editing_item = row.to_dict()
                                    st.session_state.editing_item['id'] = row['id']
                                
                                if st.button("Delete", key=f"delete_{index}"):
                                    success, message = delete_clothing_item(row['id'])
                                    if success:
                                        st.success(message)
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(message)
                            
                            # Show edit form if this item is being edited
                            if (st.session_state.editing_item is not None and 
                                st.session_state.editing_item.get('id') == row['id']):
                                with st.form(key=f"edit_form_{index}"):
                                    st.write("### Edit Item")
                                    
                                    # Convert stored strings to lists for multiselect
                                    current_styles = str(row['style']).split(',') if isinstance(row['style'], str) else []
                                    current_sizes = str(row['size']).split(',') if isinstance(row['size'], str) else []
                                    current_genders = str(row['gender']).split(',') if isinstance(row['gender'], str) else []
                                    
                                    # Edit fields
                                    new_styles = st.multiselect(
                                        "Style", 
                                        ["Casual", "Formal", "Sport", "Beach"],
                                        default=current_styles
                                    )
                                    new_sizes = st.multiselect(
                                        "Size",
                                        ["S", "M", "L", "XL"],
                                        default=current_sizes
                                    )
                                    new_genders = st.multiselect(
                                        "Gender",
                                        ["Male", "Female", "Unisex"],
                                        default=current_genders
                                    )
                                    new_hyperlink = st.text_input(
                                        "Shopping Link",
                                        value=str(row['hyperlink']) if isinstance(row['hyperlink'], str) else ""
                                    )
                                    new_price = st.number_input(
                                        "Price ($)",
                                        value=float(row['price']) if pd.notna(row['price']) else 0.0,
                                        min_value=0.0,
                                        step=0.01,
                                        format="%.2f"
                                    )
                                    
                                    # Add image upload option for updating the image
                                    new_image = st.file_uploader(
                                        "Update Image (optional)",
                                        type=['png', 'jpg', 'jpeg'],
                                        key=f"edit_image_{index}"
                                    )
                                    
                                    # Submit button
                                    if st.form_submit_button("Save Changes"):
                                        try:
                                            # Get the current color from the image
                                            current_color = parse_color_string(row['color']) if row['color'] else (0, 0, 0)
                                            
                                            # Update the item details
                                            success, message = edit_clothing_item(
                                                row['id'],
                                                current_color,
                                                new_styles,
                                                new_genders,
                                                new_sizes,
                                                new_hyperlink,
                                                new_price
                                            )
                                            
                                            # If image was uploaded, update it
                                            if new_image:
                                                success = update_item_image(row['id'], new_image)
                                                if not success:
                                                    st.error("Failed to update item image")
                                                    return
                                            
                                            if success:
                                                st.success("Item updated successfully!")
                                                st.session_state.editing_item = None
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error(f"Failed to update item: {message}")
                                        except Exception as e:
                                            st.error(f"Error updating item: {str(e)}")
                                    
                                    # Cancel button
                                    if st.form_submit_button("Cancel"):
                                        st.session_state.editing_item = None
                                        st.rerun()
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                logger.error(f"Error in personal_wardrobe_page: {str(e)}")

        # Create sidebar navigation
        st.sidebar.title("Navigation")
        page = st.sidebar.radio("Go to", ["Main", "My Items"])

        if page == "Main":
            main_page()
        elif page == "My Items":
            personal_wardrobe_page()

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An unexpected error occurred. Please try again later.")
