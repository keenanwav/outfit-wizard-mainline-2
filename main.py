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

# Load custom CSS
def load_custom_css():
    with open("static/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state for price visibility
if 'show_prices' not in st.session_state:
    st.session_state.show_prices = True

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
                st.rerun()

def check_cleanup_needed():
    """Check if cleanup is needed based on configured interval"""
    try:
        from data_manager import get_cleanup_settings
        settings = get_cleanup_settings()
        
        if not settings or not settings['last_cleanup']:
            cleanup_merged_outfits()
        else:
            time_since_cleanup = datetime.now() - settings['last_cleanup']
            if time_since_cleanup.total_seconds() > (settings['cleanup_interval_hours'] * 3600):
                cleanup_merged_outfits()
    except Exception as e:
        logging.error(f"Error checking cleanup status: {str(e)}")

def main_page():
    """Display main page with outfit generation"""
    load_custom_css()
    st.title("Outfit Wizard")
    
    # Initialize session state for current outfit
    if 'current_outfit' not in st.session_state:
        st.session_state.current_outfit = None
        
    # Load clothing items
    items_df = load_clothing_items()
    
    # Initialize missing_items
    missing_items = []
    
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
            # Toggle button for price visibility
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
        st.markdown("### 🤖 Smart Style Assistant")
        st.markdown("Get personalized style recommendations based on your wardrobe and preferences.")
        
        # Input fields for style assistant
        occasion = st.text_input("What's the occasion?", 
                                placeholder="E.g., job interview, casual dinner, wedding")
        
        weather = st.text_input("Weather conditions?", 
                               placeholder="E.g., sunny and warm, cold and rainy")
        
        preferences = st.text_area("Additional preferences or requirements?",
                                  placeholder="E.g., prefer dark colors, need to look professional")
        
        if st.button("Get Style Advice"):
            with st.spinner("🎨 Analyzing your wardrobe and generating recommendations..."):
                # Format clothing items for the AI
                formatted_items = format_clothing_items(items_df)
                
                # Get AI recommendation
                recommendation = get_style_recommendation(
                    formatted_items,
                    occasion=occasion,
                    weather=weather,
                    preferences=preferences
                )
                
                # Display recommendation text
                st.markdown("### Your Personalized Style Recommendation")
                st.markdown(recommendation['text'])
                
                # Display recommended items in a grid
                if recommendation['recommended_items']:
                    st.markdown("### Recommended Items")
                    
                    # Create columns for the grid (3 items per row)
                    cols = st.columns(3)
                    for idx, item in enumerate(recommendation['recommended_items']):
                        col = cols[idx % 3]
                        with col:
                            if os.path.exists(item['image_path']):
                                st.image(item['image_path'], use_column_width=True)
                                st.markdown(f"**{item['type'].capitalize()}**")
                                st.markdown(f"Style: {item['style']}")
                                
                                # Display item color
                                color = parse_color_string(str(item['color']))
                                display_color_palette([color])

def personal_wardrobe_page():
    """Display and manage personal wardrobe items"""
    st.title("My Items")
    
    # Load existing items
    items_df = load_clothing_items()
    
    # Add custom CSS for image preview with enhanced styling
    st.markdown("""
        <style>
        .preview-container {
            border: 2px solid #e0e0e0;
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            background-color: #f8f9fa;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .preview-header {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
            text-align: center;
            padding-bottom: 10px;
            border-bottom: 1px solid #dee2e6;
        }
        .preview-images {
            display: flex;
            justify-content: space-between;
            gap: 30px;
            margin: 20px 0;
            align-items: center;
        }
        .preview-image-box {
            flex: 1;
            border: 2px solid #e0e0e0;
            padding: 15px;
            border-radius: 10px;
            background-color: white;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }
        .preview-image-box:hover {
            transform: translateY(-2px);
        }
        .preview-buttons {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #dee2e6;
        }
        .preview-button {
            padding: 8px 20px;
            border-radius: 20px;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: bold;
        }
        .confirm-button {
            background-color: #28a745;
            color: white;
        }
        .cancel-button {
            background-color: #dc3545;
            color: white;
        }
        .confirm-button:hover, .cancel-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Upload new item form
    with st.expander("Upload New Item", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            item_type = st.selectbox("Type", ["Shirt", "Pants", "Shoes"])
            styles = st.multiselect("Style", ["Casual", "Formal", "Sport", "Beach"])
            sizes = st.multiselect("Size", ["S", "M", "L", "XL"])
            price = st.number_input("Price ($)", min_value=0.0, step=0.01, format="%.2f")
        
        with col2:
            genders = st.multiselect("Gender", ["Male", "Female", "Unisex"])
            uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'], key="new_item_upload")
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
                        item_type.lower(), colors[0], styles, genders, sizes, 
                        temp_path, hyperlink, price if price > 0 else None
                    )
                    if success:
                        st.success(message)
                        st.rerun()
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
                    col = cols[int(idx) % 3]
                    with col:
                        if os.path.exists(item['image_path']):
                            st.image(item['image_path'], use_column_width=True)
                            
                            # Edit/Delete buttons
                            edit_col, change_img_col, del_col = st.columns([2, 2, 1])
                            
                            with edit_col:
                                if st.button(f"Edit Details {idx}"):
                                    st.session_state.editing_item = item
                            
                            with change_img_col:
                                # Add camera icon button for image change
                                if st.button("📷", key=f"camera_icon_{idx}", help="Change Image"):
                                    # Create a preview container
                                    st.markdown('<div class="preview-container">', unsafe_allow_html=True)
                                    st.markdown('<div class="preview-header">📸 Change Item Image</div>', unsafe_allow_html=True)
                                    
                                    # Upload new image
                                    new_image = st.file_uploader("Choose new image", 
                                                               type=['png', 'jpg', 'jpeg'], 
                                                               key=f"change_image_{idx}")
                                    
                                    if new_image:
                                        # Show side-by-side preview
                                        st.markdown('<div class="preview-images">', unsafe_allow_html=True)
                                        
                                        # Current image preview
                                        st.markdown("""
                                            <div class="preview-image-box">
                                                <h4>Current Image</h4>
                                            </div>
                                        """, unsafe_allow_html=True)
                                        st.image(item['image_path'], use_column_width=True)
                                        
                                        # New image preview
                                        st.markdown("""
                                            <div class="preview-image-box">
                                                <h4>New Image</h4>
                                            </div>
                                        """, unsafe_allow_html=True)
                                        st.image(new_image, use_column_width=True)
                                        
                                        st.markdown('</div>', unsafe_allow_html=True)
                                        
                                        # Add confirm and cancel buttons
                                        st.markdown('<div class="preview-buttons">', unsafe_allow_html=True)
                                        
                                        confirm_col, cancel_col = st.columns(2)
                                        with confirm_col:
                                            if st.button("✅ Confirm Change", key=f"confirm_{idx}"):
                                                # Save uploaded image
                                                temp_path = f"temp_{new_image.name}"
                                                with open(temp_path, "wb") as f:
                                                    f.write(new_image.getvalue())
                                                
                                                # Update image in database
                                                success, message = update_item_image(item['id'], temp_path)
                                                
                                                if success:
                                                    st.success("Image updated successfully!")
                                                    # Clean up temporary file
                                                    os.remove(temp_path)
                                                    # Refresh the page
                                                    st.rerun()
                                                else:
                                                    st.error(f"Error updating image: {message}")
                                                    if os.path.exists(temp_path):
                                                        os.remove(temp_path)
                                        
                                        with cancel_col:
                                            if st.button("❌ Cancel", key=f"cancel_{idx}"):
                                                st.rerun()
                                                
                                        st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    st.markdown('</div>', unsafe_allow_html=True)
                            
                            with del_col:
                                if st.button(f"🗑️ {idx}"):
                                    if delete_clothing_item(item['id']):
                                        st.success(f"Item {item['id']} deleted successfully!")
                                        st.rerun()
                            
                            # Display item details
                            st.write(f"Style: {item['style']}")
                            if item.get('price'):
                                st.write(f"Price: ${float(item['price']):.2f}")
                            
                            # Display color palette
                            if item['color']:
                                color = parse_color_string(str(item['color']))
                                display_color_palette([color])
    else:
        st.info("Your wardrobe is empty. Start by adding some items!")

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
        col = cols[int(idx) % 3]
        with col:
            image_path = str(outfit.get('image_path', ''))
            if os.path.exists(image_path):
                st.image(image_path, use_column_width=True)
                
                # Organization features
                tags = outfit.get('tags', [])
                new_tags = st.text_input(
                    f"Tags ###{idx}", 
                    value=','.join(tags) if tags else "",
                    help="Comma-separated tags"
                )
                
                current_season = str(outfit.get('season', ''))
                season_options = ["", "Spring", "Summer", "Fall", "Winter"]
                season_index = season_options.index(current_season) if current_season in season_options else 0
                
                season = st.selectbox(
                    f"Season ###{idx}",
                    season_options,
                    index=season_index
                )
                
                current_notes = str(outfit.get('notes', ''))
                notes = st.text_area(
                    f"Notes ###{idx}", 
                    value=current_notes,
                    help="Add notes about this outfit"
                )
                
                # Save and Delete buttons
                save_col, del_col = st.columns([3, 1])
                with save_col:
                    if st.button(f"Save Details ###{idx}"):
                        success, message = update_outfit_details(
                            str(outfit['outfit_id']),
                            tags=new_tags.split(',') if new_tags.strip() else None,
                            season=season if season else None,
                            notes=notes if notes.strip() else None
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                
                with del_col:
                    if st.button(f"🗑️ ###{idx}"):
                        success, message = delete_saved_outfit(str(outfit['outfit_id']))
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

def cleanup_status_dashboard():
    """Display cleanup status dashboard"""
    st.title("Cleanup Status Dashboard")
    
    from data_manager import get_cleanup_statistics
    stats = get_cleanup_statistics()
    
    if not stats:
        st.warning("No cleanup settings found. Please configure cleanup settings first.")
        return
    
    # Display current settings
    st.header("📊 Cleanup Settings")
    settings = stats['settings']
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Maximum File Age", f"{settings['max_age_hours']} hours")
        st.metric("Cleanup Interval", f"{settings['cleanup_interval_hours']} hours")
    
    with col2:
        st.metric("Batch Size", str(settings['batch_size']))
        st.metric("Max Workers", str(settings['max_workers']))
    
    # Display last cleanup time
    st.header("⏱️ Last Cleanup")
    if settings['last_cleanup']:
        last_cleanup = settings['last_cleanup']
        time_since = datetime.now() - last_cleanup
        hours_since = time_since.total_seconds() / 3600
        
        status_color = "🟢" if hours_since < settings['cleanup_interval_hours'] else "🔴"
        st.write(f"{status_color} Last cleanup: {last_cleanup.strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"Time since last cleanup: {int(hours_since)} hours")
        
        # Next scheduled cleanup
        next_cleanup = last_cleanup + timedelta(hours=settings['cleanup_interval_hours'])
        st.write(f"Next scheduled cleanup: {next_cleanup.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.warning("No cleanup has been performed yet")
    
    # Display file statistics
    st.header("📁 File Statistics")
    statistics = stats['statistics']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Files", statistics['total_files'])
    with col2:
        st.metric("Saved Outfits", statistics['saved_outfits'])
    with col3:
        st.metric("Temporary Files", statistics['temporary_files'])
    
    # Add manual cleanup button
    st.header("🧹 Manual Cleanup")
    if st.button("Run Cleanup Now"):
        with st.spinner("Running cleanup..."):
            cleaned_count = cleanup_merged_outfits()
            st.success(f"Cleanup completed. {cleaned_count} files removed.")
            st.rerun()

# Update the main sidebar menu to include the new dashboard
if __name__ == "__main__":
    create_user_items_table()
    show_first_visit_tips()
    check_cleanup_needed()
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "My Items", "Saved Outfits", "Cleanup Status"])
    
    if page == "Home":
        main_page()
    elif page == "My Items":
        personal_wardrobe_page()
    elif page == "Saved Outfits":
        saved_outfits_page()
    elif page == "Cleanup Status":
        cleanup_status_dashboard()