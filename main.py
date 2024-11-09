# ... (previous imports remain the same) ...
from color_recommendation import (
    get_complementary_color,
    get_analogous_colors,
    get_triadic_colors,
    calculate_color_harmony_score,
    learn_color_preferences,
    recommend_matching_colors
)

# ... (previous code remains the same until main_page function) ...

def main_page():
    """Display main page with outfit generation"""
    st.title("Outfit Generator")
    
    # Initialize session state for current outfit
    if 'current_outfit' not in st.session_state:
        st.session_state.current_outfit = None
    
    # Load clothing items
    items_df = load_clothing_items()
    
    if items_df.empty:
        st.warning("Please add some clothing items in the 'My Items' section first!")
        return
    
    # Load saved outfits for learning
    saved_outfits = load_saved_outfits()
    color_combinations, color_scores = learn_color_preferences(saved_outfits)
    
    # Outfit generation form
    col1, col2 = st.columns(2)
    
    with col1:
        size = st.selectbox("Size", ["S", "M", "L", "XL"])
        style = st.selectbox("Style", ["Casual", "Formal", "Sport", "Beach"])
    
    with col2:
        gender = st.selectbox("Gender", ["Male", "Female", "Unisex"])
        
        # Add color harmony preference
        st.markdown("### Color Harmony Preference")
        harmony_strength = st.slider(
            "Color Matching Strength",
            min_value=0.0,
            max_value=1.0,
            value=0.6,
            help="Higher values create outfits with more closely matching colors"
        )
    
    if st.button("Generate Outfit"):
        outfit, missing_items = generate_outfit(items_df, size, style, gender)
        st.session_state.current_outfit = outfit
        
        if missing_items:
            st.warning(f"Missing items: {', '.join(missing_items)}")
    
    # Display current outfit if available
    if st.session_state.current_outfit:
        outfit = st.session_state.current_outfit
        if 'merged_image_path' in outfit and os.path.exists(outfit['merged_image_path']):
            st.image(outfit['merged_image_path'], use_column_width=True)
            
            # Display color harmony analysis
            st.markdown("### Color Harmony Analysis")
            outfit_colors = []
            color_cols = st.columns(3)
            
            for idx, (item_type, item) in enumerate(outfit.items()):
                if item_type != 'merged_image_path':
                    color = parse_color_string(str(item['color']))
                    outfit_colors.append(color)
                    
                    with color_cols[idx]:
                        st.markdown(f"**{item_type.capitalize()}**")
                        display_color_palette([color])
            
            # Calculate and display harmony scores
            if len(outfit_colors) >= 2:
                st.markdown("#### Color Harmony Scores")
                harmony_cols = st.columns(3)
                
                combinations = [
                    ("Shirt-Pants", (outfit_colors[0], outfit_colors[1])),
                    ("Pants-Shoes", (outfit_colors[1], outfit_colors[2])),
                    ("Shirt-Shoes", (outfit_colors[0], outfit_colors[2]))
                ]
                
                for idx, (label, (color1, color2)) in enumerate(combinations):
                    with harmony_cols[idx]:
                        harmony_score = calculate_color_harmony_score(color1, color2)
                        st.markdown(f"**{label}**")
                        st.progress(harmony_score)
                        st.markdown(f"Score: {harmony_score:.2f}")
            
            # Add shopping buttons
            st.markdown("### Shop Items")
            shop_cols = st.columns(3)
            for idx, (item_type, item) in enumerate(outfit.items()):
                if item_type != 'merged_image_path' and item.get('hyperlink'):
                    with shop_cols[idx]:
                        st.link_button(f"Shop {item_type.capitalize()}", item['hyperlink'])
            
            # Save outfit option
            if st.button("Save Outfit"):
                saved_path = save_outfit(outfit)
                if saved_path:
                    st.success("Outfit saved successfully!")
                else:
                    st.error("Error saving outfit")

# ... (rest of the code remains the same) ...
