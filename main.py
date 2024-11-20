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

# Initialize session state for various UI states
if 'show_prices' not in st.session_state:
    st.session_state.show_prices = True
if 'editing_color' not in st.session_state:
    st.session_state.editing_color = None
if 'color_preview' not in st.session_state:
    st.session_state.color_preview = None
if 'edit_form_data' not in st.session_state:
    st.session_state.edit_form_data = {}
if 'validation_errors' not in st.session_state:
    st.session_state.validation_errors = {}

def reset_edit_form():
    st.session_state.edit_form_data = {}
    st.session_state.validation_errors = {}
    st.session_state.editing_item = None
    st.session_state.editing_color = None
    st.session_state.color_preview = None

def validate_edit_form(form_data):
    errors = {}
    if not form_data.get('styles'):
        errors['styles'] = "Please select at least one style"
    if not form_data.get('sizes'):
        errors['sizes'] = "Please select at least one size"
    if not form_data.get('genders'):
        errors['genders'] = "Please select at least one gender"
    if form_data.get('price') is not None and form_data['price'] < 0:
        errors['price'] = "Price cannot be negative"
    if form_data.get('hyperlink') and not form_data['hyperlink'].startswith(('http://', 'https://')):
        errors['hyperlink'] = "Please enter a valid URL starting with http:// or https://"
    return errors

def personal_wardrobe_page():
    """Display and manage personal wardrobe items"""
    st.title("My Items")
    
    # Load existing items
    items_df = load_clothing_items()
    
    # Add custom CSS for better UI
    st.markdown("""
        <style>
        .edit-form {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
            border: 1px solid #dee2e6;
        }
        .validation-error {
            color: #dc3545;
            font-size: 0.9em;
            padding: 5px;
            margin-top: 2px;
            border-radius: 4px;
        }
        .success-message {
            color: #28a745;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .color-preview {
            width: 50px;
            height: 50px;
            border-radius: 8px;
            margin: 10px auto;
            border: 2px solid #e0e0e0;
        }
        </style>
    """, unsafe_allow_html=True)

    # Display existing items in grid
    if not items_df.empty:
        st.markdown("### Your Items")
        
        # Group items by type
        for item_type in ["shirt", "pants", "shoes"]:
            type_items = items_df[items_df['type'] == item_type]
            if not type_items.empty:
                st.markdown(f"#### {item_type.capitalize()}s")
                
                cols = st.columns(3)
                for idx, item in type_items.iterrows():
                    col = cols[int(idx) % 3]
                    with col:
                        if os.path.exists(item['image_path']):
                            st.image(item['image_path'], use_column_width=True)
                            
                            # Show current color
                            current_color = parse_color_string(item['color'])
                            st.markdown("**Current Color:**")
                            display_color_palette([current_color])
                            
                            # Item details
                            st.markdown(f"**Style:** {item['style']}")
                            st.markdown(f"**Size:** {item['size']}")
                            if item['price']:
                                st.markdown(f"**Price:** ${float(item['price']):.2f}")
                            
                            # Action buttons
                            edit_col, color_col, del_col = st.columns([2, 2, 1])
                            
                            with edit_col:
                                if st.button("Edit", key=f"edit_{idx}"):
                                    st.session_state.editing_item = idx
                                    st.session_state.edit_form_data = {
                                        'styles': item['style'].split(','),
                                        'sizes': item['size'].split(','),
                                        'genders': item['gender'].split(','),
                                        'hyperlink': item['hyperlink'],
                                        'price': float(item['price']) if item['price'] else 0.0,
                                        'color': current_color
                                    }
                            
                            with color_col:
                                if st.button("Change Color", key=f"color_{idx}"):
                                    st.session_state.editing_color = idx
                            
                            with del_col:
                                if st.button("🗑️", key=f"del_{idx}"):
                                    success, message = delete_clothing_item(idx)
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
        
        # Edit form
        if st.session_state.editing_item is not None:
            st.markdown("### Edit Item")
            with st.form(key="edit_form", clear_on_submit=True):
                item_idx = st.session_state.editing_item
                item = items_df.iloc[item_idx]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    styles = st.multiselect(
                        "Style",
                        ["Casual", "Formal", "Sport", "Beach"],
                        default=st.session_state.edit_form_data.get('styles', [])
                    )
                    if 'styles' in st.session_state.validation_errors:
                        st.markdown(f'<p class="validation-error">{st.session_state.validation_errors["styles"]}</p>', unsafe_allow_html=True)
                    
                    sizes = st.multiselect(
                        "Size",
                        ["S", "M", "L", "XL"],
                        default=st.session_state.edit_form_data.get('sizes', [])
                    )
                    if 'sizes' in st.session_state.validation_errors:
                        st.markdown(f'<p class="validation-error">{st.session_state.validation_errors["sizes"]}</p>', unsafe_allow_html=True)
                
                with col2:
                    genders = st.multiselect(
                        "Gender",
                        ["Male", "Female", "Unisex"],
                        default=st.session_state.edit_form_data.get('genders', [])
                    )
                    if 'genders' in st.session_state.validation_errors:
                        st.markdown(f'<p class="validation-error">{st.session_state.validation_errors["genders"]}</p>', unsafe_allow_html=True)
                    
                    price = st.number_input(
                        "Price ($)",
                        min_value=0.0,
                        value=st.session_state.edit_form_data.get('price', 0.0),
                        step=0.01,
                        format="%.2f"
                    )
                    if 'price' in st.session_state.validation_errors:
                        st.markdown(f'<p class="validation-error">{st.session_state.validation_errors["price"]}</p>', unsafe_allow_html=True)
                
                hyperlink = st.text_input(
                    "Shopping Link",
                    value=st.session_state.edit_form_data.get('hyperlink', ''),
                    help="Add a link to where this item can be purchased"
                )
                if 'hyperlink' in st.session_state.validation_errors:
                    st.markdown(f'<p class="validation-error">{st.session_state.validation_errors["hyperlink"]}</p>', unsafe_allow_html=True)
                
                submit_col, cancel_col = st.columns([1, 1])
                with submit_col:
                    if st.form_submit_button("Save Changes"):
                        form_data = {
                            'styles': styles,
                            'sizes': sizes,
                            'genders': genders,
                            'hyperlink': hyperlink,
                            'price': price,
                            'color': st.session_state.edit_form_data.get('color')
                        }
                        
                        errors = validate_edit_form(form_data)
                        if errors:
                            st.session_state.validation_errors = errors
                            st.rerun()
                        else:
                            success, message = edit_clothing_item(
                                item_idx,
                                form_data['color'],
                                form_data['styles'],
                                form_data['genders'],
                                form_data['sizes'],
                                form_data['hyperlink'],
                                form_data['price']
                            )
                            if success:
                                st.success(message)
                                reset_edit_form()
                                st.rerun()
                            else:
                                st.error(message)
                
                with cancel_col:
                    if st.form_submit_button("Cancel"):
                        reset_edit_form()
                        st.rerun()
        
        # Color editing interface
        if st.session_state.editing_color is not None:
            item_idx = st.session_state.editing_color
            item = items_df.iloc[item_idx]
            temp_path = item['image_path']
            colors = get_color_palette(temp_path)
            
            if colors is not None:
                st.markdown("### Edit Color")
                st.write("Available Colors:")
                display_color_palette(colors)
                
                if st.button("Update Color"):
                    success, message = edit_clothing_item(
                        item_idx,
                        colors[0],
                        item['style'].split(','),
                        item['gender'].split(','),
                        item['size'].split(','),
                        item['hyperlink'],
                        float(item['price']) if item['price'] else None
                    )
                    if success:
                        st.success("Color updated successfully!")
                        st.rerun()
                    else:
                        st.error(message)
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