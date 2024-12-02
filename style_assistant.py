from typing import Dict, List, Optional, TypedDict
import random

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
    
    # Filter items based on occasion
    occasion = occasion.lower() if occasion else "casual"
    suitable_items = [
        item for item in clothing_items
        if occasion in item['style'].lower()
    ]
    
    # Apply weather-based rules
    if weather:
        weather = weather.lower()
        is_cold = any(word in weather for word in ['cold', 'cool', 'chilly', 'freezing'])
        is_warm = any(word in weather for word in ['warm', 'hot', 'sunny'])
        
        if is_cold:
            recommendation_text.append("- Outfit: Selected warmer clothing for cold weather")
            # Prefer long sleeves and pants
            suitable_items = [
                item for item in suitable_items
                if not (item['type'] == 'shirt' and 'short' in item.get('tags', []))
            ]
        elif is_warm:
            recommendation_text.append("- Outfit: Selected lighter clothing for warm weather")
            # Prefer short sleeves and lighter materials
            suitable_items = [
                item for item in suitable_items
                if not (item['type'] == 'shirt' and 'long' in item.get('tags', []))
            ]
    
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
    
    # Select items by type
    selected_items = {'shirt': None, 'pants': None, 'shoes': None}
    for item_type in selected_items:
        type_items = [item for item in suitable_items if item['type'] == item_type]
        if type_items:
            selected_items[item_type] = random.choice(type_items)
            recommended_items.append(selected_items[item_type])
    
    # Generate style tips based on occasion
    if occasion == 'formal':
        recommendation_text.append("- Style Tips: Keep accessories minimal and elegant. Make sure your clothes are well-pressed.")
    elif occasion == 'casual':
        recommendation_text.append("- Style Tips: Focus on comfort while maintaining a put-together look.")
    elif occasion == 'sport':
        recommendation_text.append("- Style Tips: Choose breathable fabrics and ensure freedom of movement.")
    elif occasion == 'beach':
        recommendation_text.append("- Style Tips: Light, airy fabrics are key. Don't forget sun protection!")
    
    # Add accessory suggestions based on occasion
    recommendation_text.append("- Accessories:")
    if occasion == 'formal':
        recommendation_text.append("  Consider a classic watch and minimal jewelry")
    elif occasion == 'casual':
        recommendation_text.append("  A simple necklace or bracelet can add personal style")
    elif occasion == 'sport':
        recommendation_text.append("  Don't forget a water bottle and sweatband if needed")
    elif occasion == 'beach':
        recommendation_text.append("  Bring a hat and sunglasses for sun protection")
    
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
            'tags': item['tags'] if 'tags' in item else [],
            'image_path': item['image_path']
        })
    return formatted_items
