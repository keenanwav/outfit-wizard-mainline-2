import os
import logging
from datetime import datetime, timedelta
import time
from contextlib import contextmanager
import uuid

# Initialize logging first
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Try imports with error handling
try:
    import streamlit as st
    import pandas as pd
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError as e:
    logger.error(f"Failed to import required packages: {str(e)}")
    raise

# Import local modules
from auth_utils import init_auth_tables, init_session_state, create_user, authenticate_user, logout_user
from data_manager import (
    load_clothing_items, save_outfit, load_saved_outfits,
    edit_clothing_item, delete_clothing_item, create_user_items_table,
    add_user_clothing_item, update_outfit_details,
    get_outfit_details, update_item_details, delete_saved_outfit,
    get_price_history, update_item_image, get_db_connection,
    share_outfit, get_shared_outfits, remove_shared_outfit, get_sharable_users,
    bulk_delete_items
)
from color_utils import get_color_palette, display_color_palette, rgb_to_hex, parse_color_string, get_color_name
from outfit_generator import generate_outfit, is_valid_image
from style_assistant import get_style_recommendation, format_clothing_items
from recommendation_engine import PersonalizedRecommender


# Configure Streamlit page settings
st.set_page_config(
    page_title="Outfit Wizard",
    page_icon="👕",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    draw.text((template_size[0] // 2, 60), "✨ Your Magical Style Recipe ✨",
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
        draw.rectangle([(50, y_offset), (template_size[0] - 50, y_offset + 50)],
                       fill='#4ecdc4')
        draw.text((75, y_offset + 25), f"{section_title}",
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
        draw.text((template_size[0] // 2, y_offset), "Recommended Pieces",
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
                draw.text((x_pos + thumb_size // 2, details_y),
                          f"{item['type'].capitalize()}",
                          font=body_font, fill='#4ecdc4', anchor="mm")

    # Add decorative footer
    footer_gradient = Image.new('RGB', (template_size[0], 50), '#4ecdc4')
    image.paste(footer_gradient, (0, template_size[1] - 50))

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

# Initialize authentication
init_auth_tables()
init_session_state()

# Initialize recommendation engine
if 'recommender' not in st.session_state:
    st.session_state.recommender = PersonalizedRecommender()

# Add login/signup button to sidebar
with st.sidebar:
    if st.session_state.user:
        st.write(f"👤 Welcome, {st.session_state.user['username']}!")
        if st.button("📤 Logout"):
            logout_user()
            st.rerun()
    else:
        if st.button("👤 Login/Signup"):
            st.session_state.show_auth = True
            st.rerun()

# Show authentication dialog when requested
if not st.session_state.user and st.session_state.get('show_auth', False):
    auth_container = st.container()
    with auth_container:
        st.markdown("## 🔐 Authentication")
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

        with tab1:
            with st.form("login_form"):
                login_email = st.text_input("Email", key="login_email")
                login_password = st.text_input("Password", type="password", key="login_password")
                login_submitted = st.form_submit_button("Login")

                if login_submitted:
                    success, user_data = authenticate_user(login_email, login_password)
                    if success:
                        st.session_state.user = user_data
                        st.session_state.show_auth = False
                        st.rerun()
                    else:
                        st.error("Invalid email or password")

        with tab2:
            with st.form("signup_form"):
                new_username = st.text_input("Username", key="signup_username")
                new_email = st.text_input("Email", key="signup_email")
                new_password = st.text_input("Password", type="password", key="signup_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
                role = st.selectbox("Role", options=['user', 'admin'], key="signup_role")
                signup_submitted = st.form_submit_button("Sign Up")

                if signup_submitted:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 8:
                        st.error("Password must be at least 8 characters long")
                    else:
                        if create_user(new_username, new_email, new_password, role):
                            success, user_data = authenticate_user(new_email, new_password)
                            if success:
                                st.session_state.user = user_data
                                st.session_state.show_auth = False
                                st.rerun()
                        else:
                            st.error("Username or email already exists")

        if st.button("✖️ Close"):
            st.session_state.show_auth = False
            st.rerun()

# Initialize session state for various UI states
if 'show_prices' not in st.session_state:
    st.session_state.show_prices = True
if 'editing_color' not in st.session_state:
    st.session_state.editing_color = None
if 'color_preview' not in st.session_state:
    st.session_state.color_preview = None

# Initialize session state for outfit sharing
if 'shared_outfits' not in st.session_state:
    st.session_state.shared_outfits = []
if 'sharing_enabled' not in st.session_state:
    st.session_state.sharing_enabled = False
if 'sharing_target_user' not in st.session_state:
    st.session_state.sharing_target_user = None

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
    st.title("Outfit Wizard")

    # Initialize session state for current outfit and missing items
    if 'current_outfit' not in st.session_state:
        st.session_state.current_outfit = None
    if 'missing_items' not in st.session_state:
        st.session_state.missing_items = []

    # Initialize local variables
    missing_items = []
    outfit = None

    # Load clothing items
    items_df = load_clothing_items()

    if items_df.empty:
        st.warning("Please add some clothing items in the 'My Items' section first!")
        return

    # Add tabs for different features
    tab1, tab2, tab3 = st.tabs(["📋 Generate Outfit", "🎯 Smart Style Assistant", "✨ Personalized Suggestions"])

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
                outfit_result, missing_items_result = generate_outfit(items_df, size, style, gender)
                st.session_state.current_outfit = outfit_result
                st.session_state.missing_items = missing_items_result
                outfit = outfit_result
                missing_items = missing_items_result

        # Display current outfit details if available
        if st.session_state.current_outfit:
            outfit = st.session_state.current_outfit
            missing_items = st.session_state.missing_items

            # Display outfit image in the left column
            with outfit_col:
                if 'merged_image_path' in outfit and outfit['merged_image_path'] and os.path.exists(outfit['merged_image_path']):
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
                        color = parse_color_string(str(item.get('color', 'rgb(0,0,0)')))
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
                    if st.session_state.user:
                        saved_path, message = save_outfit_with_validation(outfit, user_id=st.session_state.user['id'])
                        if saved_path:
                            st.success(message)

                            # Enable sharing option after saving
                            st.session_state.sharing_enabled = True

                            # Show sharing options
                            sharable_users = get_sharable_users(st.session_state.user['id'])
                            if sharable_users:
                                selected_user = st.selectbox(
                                    "Share with:",
                                    options=[(u['id'], u['name']) for u in sharable_users],
                                    format_func=lambda x: x[1]
                                )

                                if st.button("Share Outfit"):
                                    success, message = share_outfit(
                                        outfit_id=saved_path,
                                        shared_by_user_id=st.session_state.user['id'],
                                        shared_with_user_id=selected_user[0]
                                    )
                                    if success:
                                        st.success(message)
                                    else:
                                        st.error(message)
                        else:
                            st.error(message)
                    else:
                        st.warning("Please login to save outfits")

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
                                    # Format: "shirt - Olive #d8a918"
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
                                'style': item['style']                            })
                        recommendation = {'recommended_items': selected_items}

                # Display visualization
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### 👔 OutfitVisualization")                    # Generate mannequin-based visualization using initial weather input
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
                                file_name=f"style_recipe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
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
                    with col1:
                        if st.button("💾 Save Outfit"):
                            saved_path, message = save_outfit_with_validation(outfit, st.session_state.user['id'])
                            if saved_path:
                                st.success(message)
                            else:
                                st.error(message)

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
                                        # Format: "shirt - Olive #d8a918"
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

    with tab3:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h2>
                <span class="magic-wand">✨</span>
                Personalized Outfit Suggestions
                <span class="magic-wand">✨</span>
            </h2>
        </div>
        """, unsafe_allow_html=True)

        # Only show personalized suggestions for logged-in users
        if not st.session_state.user:
            st.warning("Please log in to get personalized outfit suggestions!")
            return

        # Add occasion input for context-aware suggestions
        occasion = st.text_input("What's the occasion? (Optional)",
                               placeholder="E.g., work meeting, casual dinner, wedding")

        if st.button("Get Personalized Suggestions", type="primary"):
            with st.spinner("✨ Creating personalized outfit suggestions..."):
                # Get personalized outfit suggestion
                outfit, missing_items = st.session_state.recommender.generate_personalized_outfit(
                    st.session_state.user['id'],
                    occasion=occasion
                )

                if outfit:
                    # Display the suggested outfit
                    col1, col2 = st.columns([0.7, 0.3])

                    with col1:
                        if 'merged_image_path' in outfit:
                            st.image(outfit['merged_image_path'], use_column_width=True)

                        if missing_items:
                            st.warning(f"Missing recommended items: {', '.join(missing_items)}")

                    with col2:
                        st.markdown("### Why this outfit?")
                        # Get user preferences to explain the recommendation
                        preferences = st.session_state.recommender.get_user_preferences(st.session_state.user['id'])

                        if preferences:
                            if preferences.get('color_preferences'):
                                st.markdown("#### Your Color Preferences")
                                top_colors = dict(sorted(preferences['color_preferences'].items(),
                                                      key=lambda x: x[1], reverse=True)[:3])
                                for color, count in top_colors.items():
                                    st.write(f"- {color}")

                            if preferences.get('style_preferences'):
                                st.markdown("#### Your Style Preferences")
                                top_styles = dict(sorted(preferences['style_preferences'].items(),
                                                      key=lambda x: x[1], reverse=True)[:3])
                                for style, count in top_styles.items():
                                    st.write(f"- {style}")

                        # Add save button for the personalized outfit
                        if st.button("💾 Save This Outfit"):
                            saved_path, message = save_outfit_with_validation(outfit, st.session_state.user['id'])
                            if saved_path:
                                st.success(message)
                            else:
                                st.error(message)
                else:
                    st.error("Could not generate a personalized outfit. Please try again.")

        # Show similar items section
        st.markdown("### Similar Items You Might Like")
        items_df = load_clothing_items()
        if not items_df.empty:
            # Get a random item to show similar items for
            sample_item = items_df.sample(n=1).iloc[0]
            similar_items = st.session_state.recommender.get_similar_items(sample_item.name)

            if similar_items:
                cols = st.columns(len(similar_items))
                for col, item in zip(cols, similar_items):
                    with col:
                        if item.get('image_path') and os.path.exists(item['image_path']):
                            st.image(item['image_path'], caption=f"{item['type'].capitalize()}\n{item['style']}")
                            st.progress(float(item['similarity']))

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

        # Display validation messages
        for message in validation_messages:
            st.error(message)

        if not is_valid:
            return

        # Continue with file processing if validation passes
        if uploaded_file:
            # Create temp file
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Get image color
            try:
                img = Image.open(temp_path)
                colors = get_color_palette(img)
            except Exception as e:
                st.error(f"Error processing image: {str(e)}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return

            # Show color palette
            st.markdown("### Detected Colors")
            display_color_palette(colors)

            if st.button("Add Item"):
                success, message = add_user_clothing_item(
                    item_type.lower(), colors[0], styles, genders, sizes,
                    temp_path, hyperlink, price if price > 0 else None
                )
                if success:
                    st.success(message)
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)

            if os.path.exists(temp_path):
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
            itemtype = st.selectbox("Type", ["Shirt", "Pants", "Shoes"])
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

        # Display validation messages
        for message in validation_messages:
            st.error(message)

        if not is_valid:
            return

        # Continue with file processing if validation passes
        if uploaded_file:
            # Create temp file
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Get image color
            try:
                img = Image.open(temp_path)
                colors = get_color_palette(img)
            except Exception as e:
                st.error(f"Error processing image: {str(e)}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return

            # Show color palette
            st.markdown("### Detected Colors")
            display_color_palette(colors)

            if st.button("Add Item"):
                success, message = add_user_clothing_item(
                    itemtype.lower(), colors[0], styles, genders, sizes,
                    temp_path, hyperlink, price if price > 0 else None
                )
                if success:
                    st.success(message)
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)

            if os.path.exists(temp_path):
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

def save_outfit_with_validation(outfit, user_id):
    """Save outfit with proper validation and error handling"""
    try:
        if not outfit:
            logger.warning("Attempted to save empty outfit")
            return None, "No outfit to save"

        if not user_id:
            logger.warning("Attempted to save outfit without user ID")
            return None, "User not logged in"

        # Verify all required paths exist
        for item_type, item in outfit.items():
            if isinstance(item, dict) and 'image_path' in item:
                if not os.path.exists(item['image_path']):
                    logger.error(f"Missing image file: {item['image_path']}")
                    return None, f"Missing image file for {item_type}"

        # Save the outfit
        saved_path, message = save_outfit(outfit, user_id=user_id)
        if saved_path:
            logger.info(f"Successfully saved outfit for user {user_id}")
        else:
            logger.warning(f"Failed to save outfit: {message}")

        return saved_path, message

    except Exception as e:
        logger.error(f"Error saving outfit: {str(e)}")
        return None, f"Error saving outfit: {str(e)}"

def generate_and_save_outfit(items_df, size, style, gender):
    """Generate and optionally save an outfit with proper error handling"""
    try:
        logger.info("Generating new outfit")
        outfit, missing_items = generate_outfit(items_df, size, style, gender)

        # Update session state
        st.session_state.current_outfit = outfit
        st.session_state.missing_items = missing_items

        if outfit:
            logger.info("Successfully generated outfit")

            # Verify image paths exist
            for item_type, item in outfit.items():
                if isinstance(item, dict) and 'image_path' in item:
                    if not os.path.exists(item['image_path']):
                        logger.warning(f"Image path not found for {item_type}: {item['image_path']}")

            return outfit, missing_items
        else:
            logger.warning("No outfit generated")
            return None, missing_items

    except Exception as e:
        logger.error(f"Error generating outfit: {str(e)}")
        return None, ["Error generating outfit"]

def save_outfit(outfit, user_id):
    """Save outfit with user_id for personalization"""
    try:
        if not user_id:
            return None, "User not logged in"

        with get_db_connection() as conn:
            cur = conn.cursor()
            # Save the outfit with user_id
            if 'merged_image_path' in outfit and os.path.exists(outfit['merged_image_path']):
                cur.execute("""
                    INSERT INTO saved_outfits (image_path, created_at, user_id)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (outfit['merged_image_path'], datetime.now(), user_id))
                outfit_id = cur.fetchone()[0]
                conn.commit()
                return outfit['merged_image_path'], "Outfit saved successfully"
    except Exception as e:
        logger.error(f"Error saving outfit: {str(e)}")
        return None, str(e)

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