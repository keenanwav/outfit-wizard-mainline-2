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
    
    # Select items by type ensuring complete outfit from user's wardrobe
    selected_items = {'shirt': None, 'pants': None, 'shoes': None}
    for item_type in selected_items:
        # Filter items by type from the user's wardrobe (suitable_items already contains user's items)
        type_items = [item for item in suitable_items if item['type'] == item_type]
        if type_items:
            selected_items[item_type] = type_items[0]  # Select first suitable item from user's wardrobe
            recommended_items.append(type_items[0])
    
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
