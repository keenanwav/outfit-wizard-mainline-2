from typing import Dict, List, Optional, TypedDict

class RecommendationItem(TypedDict):
    id: int
    type: str
    image_path: str
    color: str
    style: str

class StyleRecommendation(TypedDict):
    text: str
    recommended_items: List[RecommendationItem]

def get_style_recommendation(
    clothing_items: List[Dict],
    occasion: Optional[str] = None,
    weather: Optional[str] = None,
    preferences: Optional[str] = None
) -> StyleRecommendation:
    """Get style recommendations using a rule-based system"""
    # Initialize recommendation text
    recommendation_text = []
    recommended_items = []
    
    # Normalize inputs
    occasion = occasion.lower() if occasion else "casual"
    weather = weather.lower() if weather else ""
    
    # Weather condition check with comprehensive keywords
    weather_conditions = {
        'cold': ['cold', 'freezing', 'chilly', 'cool', 'windy'],  # Added 'cool' and 'windy'
        'warm': ['warm', 'hot', 'sunny'],
        'rainy': ['rainy', 'rain', 'wet'],
    }
    
    is_cold = any(word in weather for word in weather_conditions['cold'])
    is_warm = any(word in weather for word in weather_conditions['warm'])
    is_rainy = any(word in weather for word in weather_conditions['rainy'])
    
    # Strict occasion matching
    valid_occasions = ['formal', 'casual', 'sport', 'beach']
    if occasion not in valid_occasions:
        occasion = 'casual'  # Default to casual if invalid occasion
    
    # Filter items based on occasion and weather
    suitable_items = []
    for item in clothing_items:
        item_type = item['type']
        item_style = item['style'].lower()
        item_tags = item.get('tags', []) if isinstance(item.get('tags'), list) else []
        
        # Skip items that don't match the occasion
        if occasion not in item_style:
            continue
            
        # Occasion-specific rules
        if occasion == 'formal':
            if item_type == 'shirt' and item_tags and 'short' in item_tags:
                continue  # Skip short sleeves for formal occasions
            if item_type == 'pants' and item_tags and 'shorts' in item_tags:
                continue  # Skip shorts for formal occasions
                
        elif occasion == 'beach':
            if item_type == 'shirt' and item_tags and 'long' in item_tags:
                continue  # Skip long sleeves for beach
            if item_type == 'pants' and item_tags and 'long' in item_tags:
                continue  # Skip long pants for beach
                
        elif occasion == 'sport':
            if item_tags and 'athletic' not in item_tags and 'sport' not in item_tags:
                continue  # Only athletic wear for sports
        
        # Weather-based filtering with improved conditions
        if is_cold or 'cool' in weather or 'windy' in weather:
            if item_type == 'shirt' and item_tags and 'short' in item_tags:
                continue  # Skip short sleeves in cold/cool/windy weather
            if item_type == 'pants' and item_tags and 'shorts' in item_tags:
                continue  # Skip shorts in cold/cool/windy weather
                
        elif is_warm:
            if item_type == 'shirt' and item_tags and 'long' in item_tags:
                continue  # Skip long sleeves in warm weather
            if item_type == 'pants' and item_tags and 'long' in item_tags and occasion != 'formal':
                continue  # Skip long pants in warm weather (except formal)
        
        suitable_items.append(item)
    
    # Add weather-based recommendation text
    if is_cold or 'cool' in weather or 'windy' in weather:
        recommendation_text.append("- Outfit: Selected warmer clothing for cool/cold weather")
    elif is_warm:
        recommendation_text.append("- Outfit: Selected lighter clothing for warm weather")
    if is_rainy:
        recommendation_text.append("- Note: Added weather-appropriate items for rain")
    
    # Apply color preference rules
    if preferences:
        preferences = preferences.lower()
        # Extract color preferences
        preferred_colors = []
        if 'dark' in preferences:
            preferred_colors.extend(['black', 'navy', 'dark'])
        if 'light' in preferences:
            preferred_colors.extend(['white', 'beige', 'light'])
        if 'bright' in preferences:
            preferred_colors.extend(['red', 'yellow', 'blue', 'green'])
            
        if preferred_colors:
            suitable_items = [
                item for item in suitable_items
                if any(color in item['color'].lower() for color in preferred_colors)
            ]
    
    # Enhanced item selection with style matching and color coordination
    def calculate_item_score(item, occasion, preferences):
        score = 0
        # Style match with occasion
        if occasion.lower() in item['style'].lower():
            score += 3
        # Color preference match
        if preferences:
            preferences = preferences.lower()
            if ('dark' in preferences and any(dark in item['color'].lower() for dark in ['black', 'navy', 'dark'])):
                score += 2
            elif ('light' in preferences and any(light in item['color'].lower() for light in ['white', 'beige', 'light'])):
                score += 2
            elif ('bright' in preferences and any(bright in item['color'].lower() for bright in ['red', 'yellow', 'blue', 'green'])):
                score += 2
        return score

    def color_compatibility_score(color1, color2):
        # Basic color compatibility check
        if color1.lower() == color2.lower():
            return 1  # Matching colors
        neutral_colors = ['black', 'white', 'gray', 'beige', 'navy']
        if any(neutral in color1.lower() for neutral in neutral_colors) or \
           any(neutral in color2.lower() for neutral in neutral_colors):
            return 2  # Neutral colors work well with anything
        return 0  # Default compatibility

    # Select items by type ensuring complete outfit from user's wardrobe
    selected_items = {'shirt': None, 'pants': None, 'shoes': None}
    
    # First, get all items by type and sort by initial score
    categorized_items = {
        item_type: sorted(
            [item for item in suitable_items if item['type'] == item_type],
            key=lambda x: calculate_item_score(x, occasion, preferences),
            reverse=True
        )
        for item_type in selected_items
    }
    
    # Select shirt first (as base piece)
    if categorized_items['shirt']:
        selected_items['shirt'] = categorized_items['shirt'][0]
        recommended_items.append(selected_items['shirt'])
    
    # Select pants considering shirt color compatibility
    if categorized_items['pants'] and selected_items['shirt']:
        pants_items = categorized_items['pants']
        pants_items.sort(
            key=lambda x: (
                calculate_item_score(x, occasion, preferences) +
                color_compatibility_score(x['color'], selected_items['shirt']['color'])
            ),
            reverse=True
        )
        selected_items['pants'] = pants_items[0]
        recommended_items.append(selected_items['pants'])
    
    # Select shoes considering both shirt and pants colors
    if categorized_items['shoes'] and selected_items['shirt'] and selected_items['pants']:
        shoes_items = categorized_items['shoes']
        shoes_items.sort(
            key=lambda x: (
                calculate_item_score(x, occasion, preferences) +
                color_compatibility_score(x['color'], selected_items['shirt']['color']) +
                color_compatibility_score(x['color'], selected_items['pants']['color'])
            ),
            reverse=True
        )
        selected_items['shoes'] = shoes_items[0]
        recommended_items.append(selected_items['shoes'])
    
    # Generate style tips based on occasion
    if occasion == 'formal':
        recommendation_text.append("- Style Tips: Choose dark colors and pressed clothes. Opt for long sleeves and full-length pants.")
    elif occasion == 'casual':
        recommendation_text.append("- Style Tips: Focus on comfort while maintaining a put-together look.")
    elif occasion == 'sport':
        recommendation_text.append("- Style Tips: Choose breathable, athletic fabrics. Ensure freedom of movement.")
    elif occasion == 'beach':
        recommendation_text.append("- Style Tips: Light, airy fabrics. Opt for shorts and short sleeves.")
    
    # Add accessory suggestions based on occasion and weather
    recommendation_text.append("- Accessories:")
    if occasion == 'formal':
        recommendation_text.append("  Consider a classic watch and minimal jewelry")
    elif occasion == 'casual':
        recommendation_text.append("  A simple necklace or bracelet can add personal style")
    elif occasion == 'sport':
        recommendation_text.append("  Don't forget a water bottle and sweatband if needed")
    elif occasion == 'beach':
        recommendation_text.append("  Bring a hat and sunglasses for sun protection")
    
    if is_rainy:
        recommendation_text.append("  Don't forget an umbrella!")
    
    return {
        'text': '\n'.join(recommendation_text),
        'recommended_items': recommended_items
    }

def format_clothing_items(items_df) -> List[Dict]:
    """Format clothing items dataframe into a list of dictionaries"""
    formatted_items = []
    for _, item in items_df.iterrows():
        formatted_items.append({
            'id': int(item['id']),
            'type': item['type'],
            'style': item['style'],
            'color': item['color'],
            'size': item['size'],
            'tags': item.get('tags', []) if isinstance(item.get('tags'), list) else [],
            'image_path': item['image_path']
        })
    return formatted_items
