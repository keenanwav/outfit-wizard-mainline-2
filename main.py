import streamlit as st
import os
from PIL import Image, ImageDraw, ImageFont
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
from color_utils import get_color_palette, display_color_palette, rgb_to_hex, parse_color_string, get_color_name
from outfit_generator import generate_outfit, bulk_delete_items, is_valid_image
from datetime import datetime, timedelta
from style_assistant import get_style_recommendation, format_clothing_items
import time

def create_mannequin_outfit_image(recommended_items, weather=None, template_size=(800, 1000)):
    """Create a visualization of the outfit using the mannequin template and clothing templates"""
    from clothing_templates import get_template_for_item, apply_color_to_template, get_item_position, parse_color_string
    
    # Load the mannequin template
    template = Image.open('manikin temp.png')
    
    # Resize the template while maintaining aspect ratio
    template.thumbnail(template_size, Image.Resampling.LANCZOS)
    
    # Create a new image with white background
    final_image = Image.new('RGBA', template_size, 'white')
    
    # Calculate position to center the template
    x_offset = (template_size[0] - template.width) // 2
    y_offset = (template_size[1] - template.height) // 2
    
    # Paste the mannequin template
    final_image.paste(template, (x_offset, y_offset), template)
    
    # Define layering order
    layer_order = ['pants', 'shirt', 'shoes']
    
    # Layer clothing items in the correct order
    for layer_type in layer_order:
        for item in recommended_items:
            if item['type'] == layer_type:
                # Get appropriate template based on item type and weather
                template_path = get_template_for_item(item['type'], weather)
                if template_path and os.path.exists(template_path):
                    # Parse color and apply to template
                    color = parse_color_string(item['color'])
                    colored_item = apply_color_to_template(template_path, color)
                    
                    # Get position for this item type
                    pos = get_item_position(item['type'], template_size)
                    
                    # Resize colored item to match template proportions
                    colored_item.thumbnail((template_size[0] // 2, template_size[1] // 2), Image.Resampling.LANCZOS)
                    
                    # Paste the colored item onto the final image
                    final_image.paste(colored_item, pos, colored_item)
    
    # Save the visualization
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f"style_recipes/mannequin_outfit_{timestamp}.png"
    os.makedirs("style_recipes", exist_ok=True)
    
    final_image.save(output_path, 'PNG')
    return output_path

def create_style_recipe_image(recommendation, template_size=(1000, 1200)):
    """Create a visually appealing image for the style recommendation"""
    # Create a new image with white background
    image = Image.new('RGB', template_size, 'white')
    draw = ImageDraw.Draw(image)
    
    # Try to load a nice font, fallback to default if not available
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        heading_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        title_font = ImageFont.load_default()
        heading_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
    
    # Add decorative header
    header_gradient = Image.new('RGB', (template_size[0], 100), '#ff6b6b')
    image.paste(header_gradient, (0, 0))
    
    # Add title
    draw.text((template_size[0]//2, 60), "✨ Your Magical Style Recipe ✨", 
              font=title_font, fill='white', anchor="mm")
    
    # Parse recommendation text into sections
    sections = {
        'Outfit': '',
        'Style Tips': '',
        'Accessories': ''
    }
    
    current_section = None
    # Handle both string and list types for recommendation['text']
    text_lines = []
    if isinstance(recommendation['text'], str):
        text_lines = recommendation['text'].split('\n')
    elif isinstance(recommendation['text'], list):
        text_lines = recommendation['text']
    
    for line in text_lines:
        line = str(line).strip()
        if line.startswith(('- Outfit:', '- Style Tips:', '- Accessories:')):
            current_section = line[2:].split(':')[0]
            sections[current_section] = line.split(':', 1)[1].strip()
        elif current_section and line:
            sections[current_section] += '\n' + line
    
    # Layout sections
    y_offset = 150
    for section_title, content in sections.items():
        # Section header with gradient background
        draw.rectangle([(50, y_offset), (template_size[0]-50, y_offset+50)], 
                      fill='#4ecdc4')
        draw.text((75, y_offset+25), f"{section_title}", 
                 font=heading_font, fill='white', anchor="lm")
        
        # Section content with wrapped text
        y_offset += 70
        words = content.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            text_width = draw.textlength(" ".join(current_line), font=body_font)
            if text_width > template_size[0] - 100:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
        
        for line in lines:
            draw.text((75, y_offset), line, font=body_font, fill='black')
            y_offset += 35
        
        y_offset += 50
    
    # Add recommended items if available
    if recommendation['recommended_items']:
        draw.text((template_size[0]//2, y_offset), "Recommended Pieces", 
                 font=heading_font, fill='#4ecdc4', anchor="mm")
        y_offset += 50
        
        # Calculate thumbnail size and positions
        thumb_size = 200
        spacing = (template_size[0] - (3 * thumb_size)) // 4
        
        for idx, item in enumerate(recommendation['recommended_items'][:3]):
            if item.get('image_path') and os.path.exists(item['image_path']):
                # Load and resize item image
                item_img = Image.open(item['image_path'])
                item_img.thumbnail((thumb_size, thumb_size))
                
                # Calculate position
                x_pos = spacing + idx * (thumb_size + spacing)
                image.paste(item_img, (x_pos, y_offset))
                
                # Add item details below thumbnail
                details_y = y_offset + thumb_size + 10
                draw.text((x_pos + thumb_size//2, details_y), 
                         f"{item['type'].capitalize()}", 
                         font=body_font, fill='#4ecdc4', anchor="mm")
    
    # Add decorative footer
    footer_gradient = Image.new('RGB', (template_size[0], 50), '#4ecdc4')
    image.paste(footer_gradient, (0, template_size[1]-50))
    
    # Generate unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f"style_recipes/recipe_{timestamp}.png"
    os.makedirs("style_recipes", exist_ok=True)
    
    # Save the image
    image.save(output_path)
    return output_path

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

def bulk_delete_clothing_items(item_ids):
    """Delete multiple clothing items in bulk"""
    try:
        success, message, stats = bulk_delete_items(item_ids)
        if success:
            st.success(message)
        else:
            st.warning(f"{message}\nSome items failed to delete.")
            if stats.get("errors"):
                st.error("\n".join(stats["errors"]))
        return success
    except Exception as e:
        st.error(f"Error during bulk delete: {str(e)}")
        return False

def main_page():
    """Display main page with outfit generation"""
    load_custom_css()

    # Initialize session state for login popup
    if 'show_login' not in st.session_state:
        st.session_state.show_login = False

    # Add login button in top left
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("🔐 Login/Signup", use_container_width=True):
            st.session_state.show_login = True

    # Login popup
    if st.session_state.show_login:
        with st.form(key='login_form'):
            st.subheader("Login/Signup")
            # Toggle between login and signup
            is_signup = st.checkbox("Create new account?")

            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if is_signup:
                email = st.text_input("Email")

            submit = st.form_submit_button("Submit")

            if submit:
                if is_signup:
                    # Assuming create_user function exists in auth_utils.py
                    from auth_utils import create_user
                    success, user_id = create_user(username, email, password)
                    if success:
                        st.success("Account created successfully! Please check your email for verification.")
                        st.session_state.show_login = False
                else:
                    # Assuming authenticate_user function exists in auth_utils.py
                    from auth_utils import authenticate_user
                    success, user_data = authenticate_user(username, password)
                    if success:
                        st.session_state.user = user_data
                        st.success("Login successful!")
                        st.session_state.show_login = False
                        st.rerun()

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
            size = st.selectbox(
                "Size",
                ["S", "M", "L", "XL"],
                key="size_select",
                help="Select your preferred size"
            )
            style = st.selectbox(
                "Style",
                ["Casual", "Formal", "Sport", "Beach"],
                key="style_select",
                help="Choose your preferred style"
            )
        
        with col2:
            gender = st.selectbox(
                "Gender",
                ["Male", "Female", "Unisex"],
                key="gender_select",
                help="Select your gender preference"
            )
            
        with col3:
            st.write("")
            st.write("")
            # Toggle button for price visibility
            if st.button("Toggle Prices" if st.session_state.show_prices else "Show Prices"):
                st.session_state.show_prices = not st.session_state.show_prices
                st.rerun()
        
        # Create two columns for outfit display and price information
        outfit_col, price_col = st.columns([0.7, 0.3])
        
        if st.button("🔄 Generate Outfit"):
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
                            if item_type == 'shirt':
                                st.link_button("👕", item['hyperlink'])
                            elif item_type == 'pants':
                                st.link_button("👖", item['hyperlink'])
                            elif item_type == 'shoes':
                                st.link_button("👞", item['hyperlink'])
            
            # Save and Download outfit options
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Outfit"):
                    saved_path = save_outfit(outfit)
                    if saved_path:
                        st.success("Outfit saved successfully!")
                    else:
                        st.error("Error saving outfit")
            
            with col2:
                if 'merged_image_path' in outfit and os.path.exists(outfit['merged_image_path']):
                    # Add custom filename input
                    custom_name = st.text_input("Enter a name for your outfit (optional)", 
                                                 placeholder="e.g., summer_casual_outfit",
                                                 key="outfit_name")
                    
                    # Generate filename using custom name if provided, otherwise use timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{custom_name or f'outfit_{timestamp}'}.png"
                    
                    # Extract colors from individual items
                    colors = {}
                    for item_type in ['shirt', 'pants', 'shoes']:
                        if item_type in outfit and isinstance(outfit[item_type], dict):
                            item_color = parse_color_string(outfit[item_type]['color'])
                            colors[item_type] = item_color
                    
                    if colors:
                        # Open the original image
                        with Image.open(outfit['merged_image_path']) as img:
                            # Create a new image with extra space for the color palette and text
                            palette_height = 100  # Reduced space for color blocks and two lines of text
                            new_img = Image.new('RGB', (img.width, img.height + palette_height), 'white')
                            # Paste the original image
                            new_img.paste(img, (0, 0))
                            
                            # Draw color palette
                            draw = ImageDraw.Draw(new_img)
                            
                            # Calculate dimensions for blocks (3:1 width to height ratio)
                            margin = img.width * 0.1  # 10% margin on each side
                            available_width = img.width - (2 * margin)  # Width available for blocks
                            total_width = available_width * 0.8  # Total width is 80% of available width
                            block_width = total_width // 3  # Width for each block
                            block_height = block_width // 3  # Height is 1/3 of width for 3:1 ratio
                            spacing = (available_width - total_width) // 4  # Equal spacing between blocks
                            
                            # Position for color blocks
                            y1 = img.height + 20  # Reduced padding from the image
                            y2 = y1 + block_height
                            
                            # Set up typography with smaller font size
                            try:
                                # Try multiple sans-serif font options
                                font_options = [
                                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                                    "Arial.ttf",
                                    "/usr/share/fonts/truetype/liberation/LiberationSans.ttf"
                                ]
                                font = None
                                for font_path in font_options:
                                    try:
                                        font = ImageFont.truetype(font_path, 10)  # Further reduced font size to 10px
                                        break
                                    except:
                                        continue
                                if font is None:
                                    font = ImageFont.load_default()
                            except:
                                font = ImageFont.load_default()
                            
                            # Add item types and color blocks
                            x_start = margin + spacing  # Starting position for first block
                            for idx, item_type in enumerate(['shirt', 'pants', 'shoes']):
                                if item_type in colors:
                                    # Calculate x positions for current block
                                    x1 = x_start + idx * (block_width + spacing)
                                    x2 = x1 + block_width
                                    
                                    # Draw color block with thin border
                                    color = tuple(colors[item_type])
                                    draw.rectangle([x1, y1, x2, y2], fill=color, outline='#000000', width=1)
                                    
                                    # Add item type, hex code, and color name
                                    text_y = y2 + 5  # Minimal spacing after block
                                    hex_code = rgb_to_hex(colors[item_type]).lower()  # Convert to lowercase
                                    color_name = get_color_name(colors[item_type])
                                    # Format: "shirt - Olive #d8a18"
                                    combined_text = f"{item_type} - {color_name} {hex_code}"
                                    draw.text((x1, text_y), combined_text, fill='black', font=font)
                            
                            # Save the new image with palette
                            temp_path = f"temp_download_{filename}"
                            new_img.save(temp_path)
                            
                            # Provide download button for the modified image
                            with open(temp_path, 'rb') as file:
                                btn = st.download_button(
                                    label="Download Outfit with Color Palette",
                                    data=file,
                                    file_name=filename,
                                    mime="image/png"
                                )
                            
                            # Clean up temporary file
                            os.remove(temp_path)
                    else:
                        # Fallback to original image if color extraction fails
                        with open(outfit['merged_image_path'], 'rb') as file:
                            btn = st.download_button(
                                label="Download Outfit",
                                data=file,
                                file_name=filename,
                                mime="image/png"
                            )
    with tab2:
        # Add custom CSS for magic wand animation
        st.markdown("""
        <style>
        .magic-wand {
            display: inline-block;
            font-size: 2em;
            animation: sparkle 1.5s infinite;
        }
        @keyframes sparkle {
            0% { transform: rotate(0deg); opacity: 1; }
            50% { transform: rotate(15deg); opacity: 0.8; }
            100% { transform: rotate(0deg); opacity: 1; }
        }
        .style-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            transition: transform 0.3s ease;
        }
        .style-card:hover {
            transform: translateY(-5px);
        }
        .input-container {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
        }
        .recommendation-header {
            background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
            color: white;
            padding: 10px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .item-grid {
            display: grid;
            gap: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header with animated magic wand
        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h2>
                <span class="magic-wand">🪄</span>
                Smart Style Assistant
                <span class="magic-wand">✨</span>
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Input section with enhanced UI
        st.markdown('<div class="input-container">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            occasion = st.text_input("✨ What's the occasion?", 
                                   placeholder="E.g., job interview, casual dinner, wedding")
            weather = st.text_input("🌤️ Weather conditions?", 
                                  placeholder="E.g., sunny and warm, cold and rainy")
        
        with col2:
            preferences = st.text_area("🎯 Style preferences?",
                                   placeholder="E.g., prefer dark colors, need to look professional",
                                   height=122)
        
        generate_col, _ = st.columns([2, 3])
        with generate_col:
            generate_button = st.button("🪄 Generate Magic Style", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if generate_button:
            with st.spinner("🎨 Creating your style recipe..."):
                # Format clothing items for recommendation
                formatted_items = format_clothing_items(items_df)
                
                # Get rule-based recommendation
                recommendation = get_style_recommendation(
                    formatted_items,
                    occasion=occasion,
                    weather=weather,
                    preferences=preferences
                )
                
                # Create two columns for manual selection toggle
                toggle_col1, toggle_col2 = st.columns([1, 3])
                with toggle_col1:
                    manual_selection = st.checkbox(
                        "Enable Manual Selection",
                        help="Manually select clothing items for visualization"
                    )
                
                # Manual selection interface
                if manual_selection:
                    st.markdown("### 👕 Manual Item Selection")
                    items_df = load_clothing_items()
                    
                    if not items_df.empty:
                        select_col1, select_col2, select_col3 = st.columns(3)
                        
                        with select_col1:
                            selected_shirt = st.selectbox(
                                "Select Shirt",
                                options=items_df[items_df['type'] == 'shirt']['id'].tolist(),
                                format_func=lambda x: f"Shirt #{x}"
                            )
                        
                        with select_col2:
                            selected_pants = st.selectbox(
                                "Select Pants",
                                options=items_df[items_df['type'] == 'pants']['id'].tolist(),
                                format_func=lambda x: f"Pants #{x}"
                            )
                        
                        with select_col3:
                            selected_shoes = st.selectbox(
                                "Select Shoes",
                                options=items_df[items_df['type'] == 'shoes']['id'].tolist(),
                                format_func=lambda x: f"Shoes #{x}"
                            )
                        
                        # Create custom recommendation from selected items
                        selected_items = []
                        for item_id in [selected_shirt, selected_pants, selected_shoes]:
                            item = items_df[items_df['id'] == item_id].iloc[0]
                            selected_items.append({
                                'id': int(item['id']),
                                'type': item['type'],
                                'image_path': item['image_path'],
                                'color': item['color'],
                                'style': item['style']
                            })
                        recommendation = {'recommended_items': selected_items}
                
                # Display visualization
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 👔 Outfit Visualization")
                    # Generate mannequin-based visualization using initial weather input
                    mannequin_image_path = create_mannequin_outfit_image(
                        recommendation['recommended_items'],
                        weather=weather.lower() if weather and not manual_selection else None
                    )
                    if os.path.exists(mannequin_image_path):
                        st.image(mannequin_image_path, use_column_width=True)
                        
                        # Add download button for the mannequin visualization
                        with open(mannequin_image_path, 'rb') as file:
                            st.download_button(
                                label="📥 Download Outfit Visualization",
                                data=file,
                                file_name=os.path.basename(mannequin_image_path),
                                mime="image/png"
                            )
                    else:
                        st.error("Failed to generate outfit visualization")
                
                with col2:
                    st.markdown("### 📝 Style Recipe")
                    # Generate traditional style recipe image
                    recipe_image_path = create_style_recipe_image(recommendation)
                    
                    if os.path.exists(recipe_image_path):
                        st.image(recipe_image_path, use_column_width=True)
                        
                        # Add download button for the recipe image
                        with open(recipe_image_path, 'rb') as file:
                            st.download_button(
                                label="📥 Download Style Recipe",
                                data=file,
                                file_name=os.path.basename(recipe_image_path),
                                mime="image/png"
                            )
                    else:
                        st.error("Failed to generate style recipe image")
                    
                # Keep the text version in an expander for accessibility
                with st.expander("View Text Version"):
                    st.markdown(recommendation['text'])
                
                # Display recommended items in an enhanced grid
                if recommendation['recommended_items']:
                    st.markdown("### 🎭 Recommended Pieces")
                    st.markdown('<div class="item-grid">', unsafe_allow_html=True)
                    
                    # Create columns for the grid (3 items per row)
                    cols = st.columns(3)
                    for idx, item in enumerate(recommendation['recommended_items']):
                        col = cols[idx % 3]
                        with col:
                            with st.container():
                                if item.get('image_path') and os.path.exists(item['image_path']):
                                    st.image(item['image_path'], use_column_width=True)
                                    st.markdown(f"**{item['type'].capitalize()}** ✨")
                                    st.markdown(f"Style: {item['style']} 🎯")
                                    
                                    # Display item color with enhanced visualization
                                    color = parse_color_string(str(item['color']))
                                    st.markdown("**Color Palette**")
                                    display_color_palette([color])
                                    
                                    # Add a subtle separator
                                    st.markdown("---")
                    
                    st.markdown('</div>', unsafe_allow_html=True)

def personal_wardrobe_page():
    # Initialize session state for editing
    if 'editing_item' not in st.session_state:
        st.session_state.editing_item = None
    if 'editing_image' not in st.session_state:
        st.session_state.editing_image = None
    if 'editing_color' not in st.session_state:
        st.session_state.editing_color = None
    if 'edit_success' not in st.session_state:
        st.session_state.edit_success = False
    if 'form_errors' not in st.session_state:
        st.session_state.form_errors = {}
    if 'edit_history' not in st.session_state:
        st.session_state.edit_history = {}
    if 'undo_stack' not in st.session_state:
        st.session_state.undo_stack = {}
    if 'redo_stack' not in st.session_state:
        st.session_state.redo_stack = {}
    """Display and manage personal wardrobe items"""
    st.title("My Items")
    
    # Load existing items
    items_df = load_clothing_items()
    
    # Create tabs for List View and Statistics
    list_view, statistics = st.tabs(["List View", "📊 Statistics"])
    
    with statistics:
        if not items_df.empty:
            st.markdown("### Items by Type")
            # Count items by type
            type_counts = items_df['type'].value_counts()
            st.bar_chart(type_counts)
            
            st.markdown("### Items by Style")
            # Count items by style (handle multiple styles per item)
            style_counts = pd.Series([style.strip() 
                                    for styles in items_df['style'].str.split(',')
                                    for style in styles]).value_counts()
            st.bar_chart(style_counts)
            
            st.markdown("### Items by Gender")
            # Count items by gender (handle multiple genders per item)
            gender_counts = pd.Series([gender.strip() 
                                     for genders in items_df['gender'].str.split(',')
                                     for gender in genders]).value_counts()
            st.bar_chart(gender_counts)
        else:
            st.info("Add some items to see statistics!")
    
    with list_view:
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
        
        # Form validation
        is_valid = True
        validation_messages = []
        
        if not styles:
            is_valid = False
            validation_messages.append("Please select at least one style")
        if not sizes:
            is_valid = False
            validation_messages.append("Please select at least one size")
        if not genders:
            is_valid = False
            validation_messages.append("Please select at least one gender")
        
        for message in validation_messages:
            st.markdown(f'<p class="validation-error">{message}</p>', unsafe_allow_html=True)
        
        if uploaded_file and is_valid:
            # Validate file type
            if not uploaded_file.name.lower().endswith('.png'):
                st.error("Only PNG files are allowed. Please upload a PNG image.")
                return
            
            # Extract color after image upload
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Validate the image file
            if not is_valid_image(temp_path):
                os.remove(temp_path)
                st.error("The uploaded file is not a valid PNG image. Please try again with a valid image file.")
                return
            
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
            else:
                st.error("Could not extract colors from the image. Please try a different image.")
            
            os.remove(temp_path)
    
    # Load existing items
    items_df = load_clothing_items()
    
    if not items_df.empty:
        # Add type filter
        selected_type = st.selectbox(
            "Filter by Type",
            ["All", "Shirt", "Pants", "Shoes"],
            format_func=lambda x: x if x == "All" else f"{x}s"
        )
        
        # Filter items based on selection
        if selected_type != "All":
            filtered_df = items_df[items_df['type'] == selected_type.lower()]
            display_types = [selected_type.lower()]
        else:
            filtered_df = items_df
            display_types = ["shirt", "pants", "shoes"]
            
        # Display items by type
        for item_type in display_types:
            type_items = filtered_df[filtered_df['type'] == item_type]
            if not type_items.empty:
                st.markdown(f"### {item_type.capitalize()}s")
                
                # Create grid layout (3 items per row)
                cols = st.columns(3)
                for idx, item in type_items.iterrows():
                    col = cols[int(idx) % 3]
                    with col:
                        if item.get('image_path') and os.path.exists(item['image_path']):
                            st.image(item['image_path'], use_column_width=True)
                            
                            # Show current color
                            current_color = parse_color_string(item['color'])
                            st.markdown("**Color:**")
                            st.markdown(f'''
                                <div style="
                                    background-color: rgb({current_color[0]}, {current_color[1]}, {current_color[2]});
                                    width: 50px;
                                    height: 50px;
                                    border-radius: 8px;
                                    margin: 8px auto;
                                "></div>
                            ''', unsafe_allow_html=True)
                            
                            # Display item details
                            st.markdown(f"**Style:** {item['style']}")
                            st.markdown(f"**Size:** {item['size']}")
                            if item['price']:
                                st.markdown(f"**Price:** ${float(item['price']):.2f}")
                            
                            # Edit/Delete/Color buttons
                            edit_col, color_col, del_col = st.columns([2, 2, 1])
                            
                            with edit_col:
                                if st.button(f"Edit Details {idx}"):
                                    st.session_state.editing_item = item
                                    st.session_state.edit_success = False
                            
                            with color_col:
                                if st.button("🎨", key=f"color_{idx}"):
                                    st.session_state.editing_color = item
                            
                            with del_col:
                                unique_key = f"delete_{item['type']}_{item['id']}_{idx}"
                                if st.button("🗑️", key=unique_key):
                                    if delete_clothing_item(item['id']):
                                        st.success(f"Item deleted successfully!")
                                        st.rerun()
                                        
                            # Quick color edit interface
                            if st.session_state.editing_color is not None and st.session_state.editing_color['id'] == item['id']:
                                st.markdown("### Quick Color Edit")
                                current_color = parse_color_string(item['color'])
                                hex_color = rgb_to_hex(current_color)
                                
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    new_color = st.color_picker("Pick a new color", hex_color, key=f"color_picker_{idx}")
                                    # Convert hex to RGB for preview
                                    r = int(new_color[1:3], 16)
                                    g = int(new_color[3:5], 16)
                                    b = int(new_color[5:7], 16)
                                    preview_rgb = (r, g, b)
                                    
                                    # Show color preview
                                    st.markdown("### Preview")
                                    st.markdown(f'''
                                        <div style="
                                            background-color: rgb({preview_rgb[0]}, {preview_rgb[1]}, {preview_rgb[2]});
                                            width: 50px;
                                            height: 50px;
                                            border-radius: 8px;
                                            margin: 8px auto;
                                        "></div>
                                    ''', unsafe_allow_html=True)
                                    st.markdown(f"Color Name: **{get_color_name(preview_rgb)}**")
                                
                                with col2:
                                    st.markdown("### Current")
                                    st.markdown(f'''
                                        <div style="
                                            background-color: rgb({current_color[0]}, {current_color[1]}, {current_color[2]});
                                            width: 50px;
                                            height: 50px;
                                            border-radius: 8px;
                                            margin: 8px auto;
                                        "></div>
                                    ''', unsafe_allow_html=True)
                                    st.markdown(f"Color Name: **{get_color_name(current_color)}**")
                                
                                save_col, cancel_col = st.columns(2)
                                with save_col:
                                    if st.button("💾 Save Color", key=f"save_color_{idx}", type="primary"):
                                        success, message = edit_clothing_item(
                                            item['id'],
                                            preview_rgb,
                                            item['style'].split(','),
                                            item['gender'].split(','),
                                            item['size'].split(','),
                                            item['hyperlink'],
                                            float(item['price']) if item['price'] else None
                                        )
                                        
                                        if success:
                                            st.session_state.editing_color = None
                                            st.success("Color updated successfully!")
                                            st.rerun()
                                        else:
                                            st.error(message)
                                
                                with cancel_col:
                                    if st.button("❌ Cancel", key=f"cancel_color_{idx}"):
                                        st.session_state.editing_color = None
                                        st.rerun()
                            
                            # Edit form
                            if st.session_state.editing_item is not None and st.session_state.editing_item['id'] == item['id']:
                                with st.form(key=f"edit_form_{idx}"):
                                    st.markdown("### Edit Item Details")
                                    
                                    # Split current values
                                    current_styles = item['style'].split(',') if item['style'] else []
                                    current_sizes = item['size'].split(',') if item['size'] else []
                                    current_genders = item['gender'].split(',') if item['gender'] else []
                                    
                                    # Edit fields
                                    new_styles = st.multiselect("Style", ["Casual", "Formal", "Sport", "Beach"], 
                                                                default=current_styles)
                                    new_sizes = st.multiselect("Size", ["S", "M", "L", "XL"], 
                                                                default=current_sizes)
                                    new_genders = st.multiselect("Gender", ["Male", "Female", "Unisex"], 
                                                                default=current_genders)
                                    new_hyperlink = st.text_input("Shopping Link", 
                                                                 value=item['hyperlink'] if item['hyperlink'] else "")
                                    new_price = st.number_input("Price ($)", 
                                                                value=float(item['price']) if item['price'] else 0.0,
                                                                min_value=0.0, 
                                                                step=0.01, 
                                                                format="%.2f")
                                    
                                    # Form validation
                                    is_valid = True
                                    if not new_styles:
                                        is_valid = False
                                        st.markdown('<p class="validation-error">Please select at least one style</p>', 
                                                  unsafe_allow_html=True)
                                    if not new_sizes:
                                        is_valid = False
                                        st.markdown('<p class="validation-error">Please select at least one size</p>', 
                                                  unsafe_allow_html=True)
                                    if not new_genders:
                                        is_valid = False
                                        st.markdown('<p class="validation-error">Please select at least one gender</p>', 
                                                  unsafe_allow_html=True)
                                    
                                    submitted = st.form_submit_button("Save Changes")
                                    if submitted and is_valid:
                                        # Get current color
                                        color = parse_color_string(item['color'])
                                        success, message = edit_clothing_item(
                                            item['id'],
                                            color,
                                            new_styles,
                                            new_genders,
                                            new_sizes,
                                            new_hyperlink,
                                            new_price if new_price > 0 else None
                                        )
                                        if success:
                                            st.session_state.edit_success = True
                                            st.success(message)
                                            # Add edit to history
                                            add_to_edit_history(item['id'], {
                                                'color': color,
                                                'style': new_styles,
                                                'gender': new_genders,
                                                'size': new_sizes,
                                                'hyperlink': new_hyperlink,
                                                'price': new_price
                                            })
                                            st.rerun()
                                        else:
                                            st.error(message)
                                            
                            # Add a separator between items
                            st.markdown("---")
    else:
        st.info("Your wardrobe is empty. Start by adding some items!")
    
def bulk_delete_page():
    """Display bulk delete and edit interface for clothing items"""
    st.title("Bulk Item Management")
    
    # Load all clothing items
    items_df = load_clothing_items()
    
    if items_df.empty:
        st.warning("No items available in your wardrobe.")
        return
        
    with st.form("bulk_management_form"):
        # Create formatted options for multiselect
        item_options = [
            f"{row['id']} - {row['type'].capitalize()} ({row['color']}, {row['style']})"
            for _, row in items_df.iterrows()
        ]
        
        selected_items = st.multiselect(
            "Select Items to Manage",
            options=item_options,
            help="Choose multiple items to delete or edit"
        )
        
        # Extract IDs from selected items
        selected_ids = [int(item.split(' - ')[0]) for item in selected_items]
        
        # Only show bulk edit options if items are selected
        if selected_ids:
            st.subheader("Bulk Edit Options")
            col1, col2 = st.columns(2)
            
            with col1:
                new_style = st.selectbox(
                    "Update Style",
                    options=["", "Casual", "Formal", "Sport", "Beach"],
                    help="Leave empty to keep current styles"
                )
                
                new_season = st.selectbox(
                    "Update Season",
                    options=["", "Spring", "Summer", "Fall", "Winter"],
                    help="Leave empty to keep current seasons"
                )
            
            with col2:
                new_gender = st.selectbox(
                    "Update Gender",
                    options=["", "Male", "Female", "Unisex"],
                    help="Leave empty to keep current gender settings"
                )
                
                new_size = st.selectbox(
                    "Update Size",
                    options=["", "S", "M", "L", "XL"],
                    help="Leave empty to keep current sizes"
                )
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            delete_button = st.form_submit_button("🗑️ Delete Selected Items")
        with col2:
            update_button = st.form_submit_button("✨ Update Selected Items")
            
    # Handle delete action
    if delete_button and selected_ids:
        if st.session_state.get('confirm_delete', False):
            success, message, stats = bulk_delete_items(selected_ids)
            if success:
                st.success(f"Successfully deleted {stats['deleted']} items!")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"Error during deletion: {message}")
                if stats.get('errors'):
                    with st.expander("View Error Details"):
                        for error in stats['errors']:
                            st.write(error)
            st.session_state.confirm_delete = False
        else:
            st.warning(f"⚠️ Are you sure you want to delete {len(selected_ids)} items?")
            if st.button("Yes, Delete Items"):
                st.session_state.confirm_delete = True
                st.rerun()
                
    # Handle update action
    if update_button and selected_ids:
        try:
            updates = {}
            if new_style: updates['style'] = new_style
            if new_season: updates['season'] = new_season
            if new_gender: updates['gender'] = new_gender
            if new_size: updates['size'] = new_size
            
            if updates:
                with st.spinner("Updating items..."):
                    for item_id in selected_ids:
                        update_item_details(item_id, updates)
                st.success(f"Successfully updated {len(selected_ids)} items!")
                time.sleep(1)
                st.rerun()
            else:
                st.info("No updates selected. Choose at least one attribute to update.")
        except Exception as e:
            st.error(f"Error updating items: {str(e)}")
    # Initialize session state for editing
    if 'editing_item' not in st.session_state:
        st.session_state.editing_item = None
    if 'editing_image' not in st.session_state:
        st.session_state.editing_image = None
    if 'editing_color' not in st.session_state:
        st.session_state.editing_color = None
    if 'edit_success' not in st.session_state:
        st.session_state.edit_success = False
    if 'form_errors' not in st.session_state:
        st.session_state.form_errors = {}
    if 'edit_history' not in st.session_state:
        st.session_state.edit_history = {}
    if 'undo_stack' not in st.session_state:
        st.session_state.undo_stack = {}
    if 'redo_stack' not in st.session_state:
        st.session_state.redo_stack = {}
    
    # Load existing items
    items_df = load_clothing_items()
    
    # Add custom CSS for styling
    st.markdown("""
        <style>
        .item-container {
            border: 1px solid #e0e0e0;
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            background-color: #f8f9fa;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .item-details {
            margin-top: 15px;
            padding: 10px;
            background-color: #ffffff;
            border-radius: 5px;
        }
        .item-actions {
            margin-top: 10px;
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }
        .edit-form {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
            border: 1px solid #dee2e6;
        }
        .validation-error {
            color: #dc3545;
            font-size: 0.875em;
            margin-top: 0.25rem;
            padding: 0.375rem 0.75rem;
            border-radius: 0.25rem;
            background-color: rgba(220, 53, 69, 0.1);
        }
        .success-message {
            color: #198754;
            font-size: 0.875em;
            margin-top: 0.25rem;
            padding: 0.375rem 0.75rem;
            border-radius: 0.25rem;
            background-color: rgba(25, 135, 84, 0.1);
        }
        .separator {
            margin: 30px 0;
            border-top: 1px solid #dee2e6;
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
        
        # Form validation
        is_valid = True
        validation_messages = []
        
        if not styles:
            is_valid = False
            validation_messages.append("Please select at least one style")
        if not sizes:
            is_valid = False
            validation_messages.append("Please select at least one size")
        if not genders:
            is_valid = False
            validation_messages.append("Please select at least one gender")
        
        for message in validation_messages:
            st.markdown(f'<p class="validation-error">{message}</p>', unsafe_allow_html=True)
        
        if uploaded_file and is_valid:
            # Validate file type
            if not uploaded_file.name.lower().endswith('.png'):
                st.error("Only PNG files are allowed. Please upload a PNG image.")
                return
            
            # Extract color after image upload
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Validate the image file
            if not is_valid_image(temp_path):
                os.remove(temp_path)
                st.error("The uploaded file is not a valid PNG image. Please try again with a valid image file.")
                return
            
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
            else:
                st.error("Could not extract colors from the image. Please try a different image.")
            
            os.remove(temp_path)
    
    # Display existing items in grid
    if not items_df.empty:
        st.markdown("### Your Items")
        
        # Add filter dropdowns
        col1, col2 = st.columns(2)
        with col1:
            selected_type = st.selectbox(
                "Filter by Type",
                ["All"] + ["shirt", "pants", "shoes"],
                format_func=lambda x: x.capitalize() if x != "All" else x
            )
        with col2:
            selected_gender = st.selectbox(
                "Filter by Gender",
                ["All", "Male", "Female", "Unisex"]
            )
        
        # Apply filters
        filtered_df = items_df.copy()
        if selected_type != "All":
            filtered_df = filtered_df[filtered_df['type'] == selected_type]
        if selected_gender != "All":
            filtered_df = filtered_df[filtered_df['gender'].str.contains(selected_gender, na=False)]
        
        # Group items by type
        displayed_types = [selected_type] if selected_type != "All" else ["shirt", "pants", "shoes"]
        for item_type in displayed_types:
            type_items = filtered_df[filtered_df['type'] == item_type]
            if not type_items.empty:
                st.markdown(f"#### {item_type.capitalize()}s")
                
                # Create grid layout (3 items per row)
                cols = st.columns(3)
                for idx, item in type_items.iterrows():
                    col = cols[int(idx) % 3]
                    with col:
                        if item.get('image_path') and os.path.exists(item['image_path']):
                            st.image(item['image_path'], use_column_width=True)
                            
                            # Show current color
                            current_color = parse_color_string(item['color'])
                            st.markdown("**Current Color:**")
                            st.markdown(f'''
                                <div style="
                                    background-color: rgb({current_color[0]}, {current_color[1]}, {current_color[2]});
                                    width: 50px;
                                    height: 50px;
                                    border-radius: 8px;
                                    margin: 8px auto;
                                "></div>
                            ''', unsafe_allow_html=True)
                            
                            # Edit/Delete/Color buttons
                            edit_col, color_col, del_col = st.columns([2, 2, 1])
                            
                            with edit_col:
                                if st.button(f"Edit Details {idx}"):
                                    st.session_state.editing_item = item
                                    st.session_state.edit_success = False
                            
                            with color_col:
                                if st.button("🎨", key=f"color_{idx}"):
                                    st.session_state.editing_color = item
                            
                            with del_col:
                                unique_key = f"delete_{item['type']}_{item['id']}_{idx}"
                                if st.button("🗑️", key=unique_key):
                                    if delete_clothing_item(item['id']):
                                        st.success(f"Item deleted successfully!")
                                        st.rerun()
                                        
                            # Quick color edit interface
                            if st.session_state.editing_color is not None and st.session_state.editing_color['id'] == item['id']:
                                st.markdown("### Quick Color Edit")
                                current_color = parse_color_string(item['color'])
                                hex_color = rgb_to_hex(current_color)
                                
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    new_color = st.color_picker("Pick a new color", hex_color, key=f"color_picker_{idx}")
                                    # Convert hex to RGB for preview
                                    r = int(new_color[1:3], 16)
                                    g = int(new_color[3:5], 16)
                                    b = int(new_color[5:7], 16)
                                    preview_rgb = (r, g, b)
                                    
                                    # Show color preview
                                    st.markdown("### Preview")
                                    st.markdown(f'''
                                        <div style="
                                            background-color: rgb({preview_rgb[0]}, {preview_rgb[1]}, {preview_rgb[2]});
                                            width: 50px;
                                            height: 50px;
                                            border-radius: 8px;
                                            margin: 8px auto;
                                        "></div>
                                    ''', unsafe_allow_html=True)
                                    st.markdown(f"Color Name: **{get_color_name(preview_rgb)}**")
                                
                                with col2:
                                    st.markdown("### Current")
                                    st.markdown(f'''
                                        <div style="
                                            background-color: rgb({current_color[0]}, {current_color[1]}, {current_color[2]});
                                            width: 50px;
                                            height: 50px;
                                            border-radius: 8px;
                                            margin: 8px auto;
                                        "></div>
                                    ''', unsafe_allow_html=True)
                                    st.markdown(f"Color Name: **{get_color_name(current_color)}**")
                                
                                save_col, cancel_col = st.columns(2)
                                with save_col:
                                    if st.button("💾 Save Color", key=f"save_color_{idx}", type="primary"):
                                        success, message = edit_clothing_item(
                                            item['id'],
                                            preview_rgb,
                                            item['style'].split(','),
                                            item['gender'].split(','),
                                            item['size'].split(','),
                                            item['hyperlink'],
                                            float(item['price']) if item['price'] else None
                                        )
                                        
                                        if success:
                                            st.session_state.editing_color = None
                                            st.success("Color updated successfully!")
                                            st.rerun()
                                        else:
                                            st.error(message)
                                
                                with cancel_col:
                                    if st.button("❌ Cancel", key=f"cancel_color_{idx}"):
                                        st.session_state.editing_color = None
                                        st.rerun()
                            
                            # Edit form
                            if st.session_state.editing_item is not None and st.session_state.editing_item['id'] == item['id']:
                                with st.form(key=f"edit_form_{idx}"):
                                    st.markdown("### Edit Item Details")
                                    
                                    # Split current values
                                    current_styles = item['style'].split(',') if item['style'] else []
                                    current_sizes = item['size'].split(',') if item['size'] else []
                                    current_genders = item['gender'].split(',') if item['gender'] else []
                                    
                                    # Edit fields
                                    new_styles = st.multiselect("Style", ["Casual", "Formal", "Sport", "Beach"], 
                                                                default=current_styles)
                                    new_sizes = st.multiselect("Size", ["S", "M", "L", "XL"], 
                                                                default=current_sizes)
                                    new_genders = st.multiselect("Gender", ["Male", "Female", "Unisex"], 
                                                                default=current_genders)
                                    new_hyperlink = st.text_input("Shopping Link", 
                                                                 value=item['hyperlink'] if item['hyperlink'] else "")
                                    new_price = st.number_input("Price ($)", 
                                                                value=float(item['price']) if item['price'] else 0.0,
                                                                min_value=0.0, 
                                                                step=0.01, 
                                                                format="%.2f")
                                    
                                    # Form validation
                                    is_valid = True
                                    if not new_styles:
                                        is_valid = False
                                        st.markdown('<p class="validation-error">Please select at least one style</p>', 
                                                  unsafe_allow_html=True)
                                    if not new_sizes:
                                        is_valid = False
                                        st.markdown('<p class="validation-error">Please select at least one size</p>', 
                                                  unsafe_allow_html=True)
                                    if not new_genders:
                                        is_valid = False
                                        st.markdown('<p class="validation-error">Please select at least one gender</p>', 
                                                  unsafe_allow_html=True)
                                    
                                    submitted = st.form_submit_button("Save Changes")
                                    if submitted and is_valid:
                                        # Get current color
                                        color = parse_color_string(item['color'])
                                        success, message = edit_clothing_item(
                                            item['id'],
                                            color,
                                            new_styles,
                                            new_genders,
                                            new_sizes,
                                            new_hyperlink,
                                            new_price if new_price > 0 else None
                                        )
                                        if success:
                                            st.session_state.edit_success = True
                                            st.success(message)
                                            # Add edit to history
                                            add_to_edit_history(item['id'], {
                                                'color': color,
                                                'style': new_styles,
                                                'gender': new_genders,
                                                'size': new_sizes,
                                                'hyperlink': new_hyperlink,
                                                'price': new_price
                                            })
                                            st.rerun()
                                        else:
                                            st.error(message)
                                            
                            # Add a separator between items
                            st.markdown("---")
    else:
        st.info("Your wardrobe is empty. Start by adding some items!")
    
def bulk_delete_page():
    """Display bulk delete and edit interface for clothing items"""
    st.title("Bulk Item Management")
    
    # Load all clothing items
    items_df = load_clothing_items()
    
    if items_df.empty:
        st.warning("No items available in your wardrobe.")
        return
        
    with st.form("bulk_management_form"):
        # Create formatted options for multiselect
        item_options = [
            f"{row['id']} - {row['type'].capitalize()} ({row['color']}, {row['style']})"
            for _, row in items_df.iterrows()
        ]
        
        selected_items = st.multiselect(
            "Select Items to Manage",
            options=item_options,
            help="Choose multiple items to delete or edit"
        )
        
        # Extract IDs from selected items
        selected_ids = [int(item.split(' - ')[0]) for item in selected_items]
        
        # Only show bulk edit options if items are selected
        if selected_ids:
            st.subheader("Bulk Edit Options")
            col1, col2 = st.columns(2)
            
            with col1:
                new_style = st.selectbox(
                    "Update Style",
                    options=["", "Casual", "Formal", "Sport", "Beach"],
                    help="Leave empty to keep current styles"
                )
                
                new_season = st.selectbox(
                    "Update Season",
                    options=["", "Spring", "Summer", "Fall", "Winter"],
                    help="Leave empty to keep current seasons"
                )
            
            with col2:
                new_gender = st.selectbox(
                    "Update Gender",
                    options=["", "Male", "Female", "Unisex"],
                    help="Leave empty to keep current gender settings"
                )
                
                new_size = st.selectbox(
                    "Update Size",
                    options=["", "S", "M", "L", "XL"],
                    help="Leave empty to keep current sizes"
                )
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            delete_button = st.form_submit_button("🗑️ Delete Selected Items")
        with col2:
            update_button = st.form_submit_button("✨ Update Selected Items")
            
    # Handle delete action
    if delete_button and selected_ids:
        if st.session_state.get('confirm_delete', False):
            success, message, stats = bulk_delete_items(selected_ids)
            if success:
                st.success(f"Successfully deleted {stats['deleted']} items!")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"Error during deletion: {message}")
                if stats.get('errors'):
                    with st.expander("View Error Details"):
                        for error in stats['errors']:
                            st.write(error)
            st.session_state.confirm_delete = False
        else:
            st.warning(f"⚠️ Are you sure you want to delete {len(selected_ids)} items?")
            if st.button("Yes, Delete Items"):
                st.session_state.confirm_delete = True
                st.rerun()
                
    # Handle update action
    if update_button and selected_ids:
        try:
            updates = {}
            if new_style: updates['style'] = new_style
            if new_season: updates['season'] = new_season
            if new_gender: updates['gender'] = new_gender
            if new_size: updates['size'] = new_size
            
            if updates:
                with st.spinner("Updating items..."):
                    for item_id in selected_ids:
                        update_item_details(item_id, updates)
                st.success(f"Successfully updated {len(selected_ids)} items!")
                time.sleep(1)
                st.rerun()
            else:
                st.info("No updates selected. Choose at least one attribute to update.")
        except Exception as e:
            st.error(f"Error updating items: {str(e)}")
    # Initialize session state for editing
    if 'editing_item' not in st.session_state:
        st.session_state.editing_item = None
    if 'editing_image' not in st.session_state:
        st.session_state.editing_image = None
    if 'editing_color' not in st.session_state:
        st.session_state.editing_color = None
    if 'edit_success' not in st.session_state:
        st.session_state.edit_success = False
    if 'form_errors' not in st.session_state:
        st.session_state.form_errors = {}
    if 'edit_history' not in st.session_state:
        st.session_state.edit_history = {}
    if 'undo_stack' not in st.session_state:
        st.session_state.undo_stack = {}
    if 'redo_stack' not in st.session_state:
        st.session_state.redo_stack = {}
    
    # Load existing items
    items_df = load_clothing_items()
    
    # Add custom CSS for styling
    st.markdown("""
        <style>
        .item-container {
            border: 1px solid #e0e0e0;
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            background-color: #f8f9fa;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .item-details {
            margin-top: 15px;
            padding: 10px;
            background-color: #ffffff;
            border-radius: 5px;
        }
        .item-actions {
            margin-top: 10px;
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }
        .edit-form {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
            border: 1px solid #dee2e6;
        }
        .validation-error {
            color: #dc3545;
            font-size: 0.875em;
            margin-top: 0.25rem;
            padding: 0.375rem 0.75rem;
            border-radius: 0.25rem;
            background-color: rgba(220, 53, 69, 0.1);
        }
        .success-message {
            color: #198754;
            font-size: 0.875em;
            margin-top: 0.25rem;
            padding: 0.375rem 0.75rem;
            border-radius: 0.25rem;
            background-color: rgba(25, 135, 84, 0.1);
        }
        .separator {
            margin: 30px 0;
            border-top: 1px solid #dee2e6;
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
        
        # Form validation
        is_valid = True
        validation_messages = []
        
        if not styles:
            is_valid = False
            validation_messages.append("Please select at least one style")
        if not sizes:
            is_valid = False
            validation_messages.append("Please select at least one size")
        if not genders:
            is_valid = False
            validation_messages.append("Please select at least one gender")
        
        for message in validation_messages:
            st.markdown(f'<p class="validation-error">{message}</p>', unsafe_allow_html=True)
        
        if uploaded_file and is_valid:
            # Validate file type
            if not uploaded_file.name.lower().endswith('.png'):
                st.error("Only PNG files are allowed. Please upload a PNG image.")
                return
            
            # Extract color after image upload
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Validate the image file
            if not is_valid_image(temp_path):
                os.remove(temp_path)
                st.error("The uploaded file is not a valid PNG image. Please try again with a valid image file.")
                return
            
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
            else:
                st.error("Could not extract colors from the image. Please try a different image.")
            
            os.remove(temp_path)
    
    # Display existing items in grid
    if not items_df.empty:
        st.markdown("### Your Items")
        
        # Add filter dropdowns
        col1, col2 = st.columns(2)
        with col1:
            selected_type = st.selectbox(
                "Filter by Type",
                ["All"] + ["shirt", "pants", "shoes"],
                format_func=lambda x: x.capitalize() if x != "All" else x
            )
        with col2:
            selected_gender = st.selectbox(
                "Filter by Gender",
                ["All", "Male", "Female", "Unisex"]
            )
        
        # Apply filters
        filtered_df = items_df.copy()
        if selected_type != "All":
            filtered_df = filtered_df[filtered_df['type'] == selected_type]
        if selected_gender != "All":
            filtered_df = filtered_df[filtered_df['gender'].str.contains(selected_gender, na=False)]
        
        # Group items by type
        displayed_types = [selected_type] if selected_type != "All" else ["shirt", "pants", "shoes"]
        for item_type in displayed_types:
            type_items = filtered_df[filtered_df['type'] == item_type]
            if not type_items.empty:
                st.markdown(f"#### {item_type.capitalize()}s")
                
                # Create grid layout (3 items per row)
                cols = st.columns(3)
                for idx, item in type_items.iterrows():
                    col = cols[int(idx) % 3]
                    with col:
                        if item.get('image_path') and os.path.exists(item['image_path']):
                            st.image(item['image_path'], use_column_width=True)
                            
                            # Show current color
                            current_color = parse_color_string(item['color'])
                            st.markdown("**Current Color:**")
                            st.markdown(f'''
                                <div style="
                                    background-color: rgb({current_color[0]}, {current_color[1]}, {current_color[2]});
                                    width: 50px;
                                    height: 50px;
                                    border-radius: 8px;
                                    margin: 8px auto;
                                "></div>
                            ''', unsafe_allow_html=True)
                            
                            # Edit/Delete/Color buttons
                            edit_col, color_col, del_col = st.columns([2, 2, 1])
                            
                            with edit_col:
                                if st.button(f"Edit Details {idx}"):
                                    st.session_state.editing_item = item
                                    st.session_state.edit_success = False
                            
                            with color_col:
                                if st.button("🎨", key=f"color_{idx}"):
                                    st.session_state.editing_color = item
                            
                            with del_col:
                                unique_key = f"delete_{item['type']}_{item['id']}_{idx}"
                                if st.button("🗑️", key=unique_key):
                                    if delete_clothing_item(item['id']):
                                        st.success(f"Item deleted successfully!")
                                        st.rerun()
                                        
                            # Quick color edit interface
                            if st.session_state.editing_color is not None and st.session_state.editing_color['id'] == item['id']:
                                st.markdown("### Quick Color Edit")
                                current_color = parse_color_string(item['color'])
                                hex_color = rgb_to_hex(current_color)
                                
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    new_color = st.color_picker("Pick a new color", hex_color, key=f"color_picker_{idx}")
                                    # Convert hex to RGB for preview
                                    r = int(new_color[1:3], 16)
                                    g = int(new_color[3:5], 16)
                                    b = int(new_color[5:7], 16)
                                    preview_rgb = (r, g, b)
                                    
                                    # Show color preview
                                    st.markdown("### Preview")
                                    st.markdown(f'''
                                        <div style="
                                            background-color: rgb({preview_rgb[0]}, {preview_rgb[1]}, {preview_rgb[2]});
                                            width: 50px;
                                            height: 50px;
                                            border-radius: 8px;
                                            margin: 8px auto;
                                        "></div>
                                    ''', unsafe_allow_html=True)
                                    st.markdown(f"Color Name: **{get_color_name(preview_rgb)}**")
                                
                                with col2:
                                    st.markdown("### Current")
                                    st.markdown(f'''
                                        <div style="
                                            background-color: rgb({current_color[0]}, {current_color[1]}, {current_color[2]});
                                            width: 50px;
                                            height: 50px;
                                            border-radius: 8px;
                                            margin: 8px auto;
                                        "></div>
                                    ''', unsafe_allow_html=True)
                                    st.markdown(f"Color Name: **{get_color_name(current_color)}**")
                                
                                save_col, cancel_col = st.columns(2)
                                with save_col:
                                    if st.button("💾 Save Color", key=f"save_color_{idx}", type="primary"):
                                        success, message = edit_clothing_item(
                                            item['id'],
                                            preview_rgb,
                                            item['style'].split(','),
                                            item['gender'].split(','),
                                            item['size'].split(','),
                                            item['hyperlink'],
                                            float(item['price']) if item['price'] else None
                                        )
                                        
                                        if success:
                                            st.session_state.editing_color = None
                                            st.success("Color updated successfully!")
                                            st.rerun()
                                        else:
                                            st.error(message)
                                
                                with cancel_col:
                                    if st.button("❌ Cancel", key=f"cancel_color_{idx}"):
                                        st.session_state.editing_color = None
                                        st.rerun()
                            
                            # Edit form
                            if st.session_state.editing_item is not None and st.session_state.editing_item['id'] == item['id']:
                                with st.form(key=f"edit_form_{idx}"):
                                    st.markdown("### Edit Item Details")
                                    
                                    # Split current values
                                    current_styles = item['style'].split(',') if item['style'] else []
                                    current_sizes = item['size'].split(',') if item['size'] else []
                                    current_genders = item['gender'].split(',') if item['gender'] else []
                                    
                                    # Edit fields
                                    new_styles = st.multiselect("Style", ["Casual", "Formal", "Sport", "Beach"], 
                                                                default=current_styles)
                                    new_sizes = st.multiselect("Size", ["S", "M", "L", "XL"], 
                                                                default=current_sizes)
                                    new_genders = st.multiselect("Gender", ["Male", "Female", "Unisex"], 
                                                                default=current_genders)
                                    new_hyperlink = st.text_input("Shopping Link", 
                                                                 value=item['hyperlink'] if item['hyperlink'] else "")
                                    new_price = st.number_input("Price ($)", 
                                                                value=float(item['price']) if item['price'] else 0.0,
                                                                min_value=0.0, 
                                                                step=0.01, 
                                                                format="%.2f")
                                    
                                    # Form validation
                                    is_valid = True
                                    if not new_styles:
                                        is_valid = False
                                        st.markdown('<p class="validation-error">Please select at least one style</p>', 
                                                  unsafe_allow_html=True)
                                    if not new_sizes:
                                        is_valid = False
                                        st.markdown('<p class="validation-error">Please select at least one size</p>', 
                                                  unsafe_allow_html=True)
                                    if not new_genders:
                                        is_valid = False
                                        st.markdown('<p class="validation-error">Please select at least one gender</p>', 
                                                  unsafe_allow_html=True)
                                    
                                    submitted = st.form_submit_button("Save Changes")
                                    if submitted and is_valid:
                                        # Get current color
                                        color = parse_color_string(item['color'])
                                        success, message = edit_clothing_item(
                                            item['id'],
                                            color,
                                            new_styles,
                                            new_genders,
                                            new_sizes,
                                            new_hyperlink,
                                            new_price if new_price > 0 else None
                                        )
                                        if success:
                                            st.session_state.edit_success = True
                                            st.success(message)
                                            # Add edit to history
                                            add_to_edit_history(item['id'], {
                                                'color': color,
                                                'style': new_styles,
                                                'gender': new_genders,
                                                'size': new_sizes,
                                                'hyperlink': new_hyperlink,
                                                'price': new_price
                                            })
                                            st.rerun()
                                        else:
                                            st.error(message)
                                            
                            # Add a separator between items
                            st.markdown("---")
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
        
def add_to_edit_history(item_id, new_values):
    """Adds a new edit to the edit history for the given item"""
    if item_id not in st.session_state.edit_history:
        st.session_state.edit_history[item_id] = []
    
    st.session_state.edit_history[item_id].append(new_values)
    
def undo_edit(item_id):
    """Undoes the last edit for the given item"""
    if item_id in st.session_state.edit_history and st.session_state.edit_history[item_id]:
        # Pop the last edit from the history
        last_edit = st.session_state.edit_history[item_id].pop()
        
        # Push the last edit to the redo stack
        if item_id not in st.session_state.redo_stack:
            st.session_state.redo_stack[item_id] = []
        st.session_state.redo_stack[item_id].append(last_edit)
        
        # Update the item details
        success, message = edit_clothing_item(
            item_id,
            last_edit['color'],
            last_edit['style'],
            last_edit['gender'],
            last_edit['size'],
            last_edit['hyperlink'],
            last_edit['price']
        )
        
        return success, message
    else:
        return False, "No edits to undo"
    
def redo_edit(item_id):
    """Redoes the last undone edit for the given item"""
    if item_id in st.session_state.redo_stack and st.session_state.redo_stack[item_id]:
        # Pop the last undone edit from the redo stack
        last_undone_edit = st.session_state.redo_stack[item_id].pop()
        
        # Push the undone edit to the edit history
        if item_id not in st.session_state.edit_history:
            st.session_state.edit_history[item_id] = []
        st.session_state.edit_history[item_id].append(last_undone_edit)
        
        # Update the item details
        success, message = edit_clothing_item(
            item_id,
            last_undone_edit['color'],
            last_undone_edit['style'],
            last_undone_edit['gender'],
            last_undone_edit['size'],
            last_undone_edit['hyperlink'],
            last_undone_edit['price']
        )
        
        return success, message
    else:
        return False, "No edits to redo"
    
# Update the main sidebar menu to include the bulk delete page
def bulk_delete_page():
    """Display the bulk delete interface for managing uploaded items"""
    st.title("Bulk Delete Items")
    
    # Fetch all user items
    from data_manager import get_db_connection
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, type, color, style, gender, size, hyperlink, price, image_path 
            FROM user_clothing_items 
            ORDER BY type, id
        """)
        items = cur.fetchall()
        
    if not items:
        st.info("No items found in your wardrobe.")
        return
        
    # Create a DataFrame for better display
    df = pd.DataFrame(items, columns=[
        'id', 'type', 'color', 'style', 'gender', 
        'size', 'hyperlink', 'price', 'image_path'
    ])
    
    # Group items by type for better organization
    st.write("Select items to delete:")
    selected_items = []
    
    for item_type in df['type'].unique():
        with st.expander(f"{item_type.title()} Items"):
            type_items = df[df['type'] == item_type]
            for _, item in type_items.iterrows():
                col1, col2 = st.columns([1, 4])
                with col1:
                    checkbox_key = f"delete_{item_type}_{item['id']}_{hash(str(item['image_path']))}"
                    if st.checkbox(label=f"Select {item_type} item", key=checkbox_key):
                        selected_items.append(item['id'])
                with col2:
                    st.write(f"Color: {item['color']}, Style: {item['style']}, Size: {item['size']}")
    
    if selected_items:
        if st.button("Delete Selected Items", type="primary"):
            if bulk_delete_clothing_items(selected_items):
                st.success("Selected items have been deleted.")
                time.sleep(1)
                st.rerun()
            
if __name__ == "__main__":
    create_user_items_table()
    show_first_visit_tips()
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "My Items", "Saved Outfits", "Bulk Delete"])
    
    if page == "Home":
        main_page()
    elif page == "My Items":
        personal_wardrobe_page()
    elif page == "Saved Outfits":
        saved_outfits_page()
    elif page == "Bulk Delete":
        bulk_delete_page()