import anthropic
import os
from typing import Dict, List, Optional, TypedDict
import streamlit as st

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
    """Get style recommendations from Claude AI with specific item references"""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    # Prepare the context about available clothing items
    items_context = "Available clothing items:\n"
    for item in clothing_items:
        items_context += (
            f"- Item #{item['id']}: {item['type'].capitalize()}, "
            f"{item['style']} style, {item['color']} color\n"
        )
    
    # Prepare the prompt
    prompt = f"""You are a fashion expert helping someone choose an outfit. 
    {items_context}
    
    Please provide style recommendations"""
    
    if occasion:
        prompt += f" for a {occasion}"
    if weather:
        prompt += f" considering {weather} weather"
    if preferences:
        prompt += f"\nAdditional preferences: {preferences}"
    
    prompt += """\nPlease provide:
    1. A specific outfit recommendation using the available items (reference items by their ID numbers)
    2. Style tips for this combination
    3. Accessory suggestions if applicable
    
    Format your response in this structure:
    - Outfit: List the specific items by ID (e.g., "Shirt #12, Pants #5, Shoes #8")
    - Style Tips: Brief styling advice
    - Accessories: Optional suggestions
    
    Keep the response concise and friendly."""

    # Get recommendation from Claude
    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    
    # Parse the response to extract recommended item IDs
    response_text = message.content
    recommended_items = []
    
    # Extract item IDs from the response
    for item in clothing_items:
        item_id_str = f"#{item['id']}"
        if item_id_str in response_text:
            recommended_items.append({
                'id': item['id'],
                'type': item['type'],
                'image_path': item['image_path'],
                'color': item['color'],
                'style': item['style']
            })
    
    return {
        'text': response_text,
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
