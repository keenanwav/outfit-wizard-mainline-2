# Previous imports remain the same...

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
    
    # Add tabs for different features
    tab1, tab2 = st.tabs(["📋 Generate Outfit", "🎯 Smart Style Assistant"])
    
    with tab1:
        # Previous tab1 content remains the same...
        pass
    
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
                
                # Display recommended items by type
                if any(recommendation['recommended_items'].values()):
                    st.markdown("### Recommended Outfit")
                    
                    # Display items in order: shirt, pants, shoes
                    for item_type in ['shirt', 'pants', 'shoes']:
                        items = recommendation['recommended_items'][item_type]
                        if items:
                            st.markdown(f"#### {item_type.capitalize()}")
                            item = items[0]  # Take the first recommendation for each type
                            
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                if os.path.exists(item['image_path']):
                                    st.image(item['image_path'], use_column_width=True)
                            
                            with col2:
                                st.markdown(f"**Style:** {item['style']}")
                                color = parse_color_string(str(item['color']))
                                display_color_palette([color])

# Rest of the file remains the same...
