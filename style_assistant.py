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

class GroupedRecommendedItems(TypedDict):
    shirt: List[RecommendationItem]
    pants: List[RecommendationItem]
    shoes: List[RecommendationItem]

class StyleRecommendation(TypedDict):
    text: str
    recommended_items: GroupedRecommendedItems

def get_style_recommendation(
    clothing_items: List[Dict],
    occasion: Optional[str] = None,
    weather: Optional[str] = None,
    preferences: Optional[str] = None
) -> StyleRecommendation:
    """Get style recommendations from Claude AI with specific item references"""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    # Group items by type for context
    items_by_type = {
        'shirt': [],
        'pants': [],
        'shoes': []
    }
    
    for item in clothing_items:
        if item['type'] in items_by_type:
            items_by_type[item['type']].append(item)
    
    # Prepare the context about available clothing items
    items_context = "Available clothing items:\n"
    for item_type, items in items_by_type.items():
        items_context += f"\n{item_type.capitalize()}s:\n"
        for item in items:
            items_context += (
                f"- Item #{item['id']}: {item['style']} style, {item['color']} color\n"
            )
    
    # Prepare the prompt
    prompt = f"""You are a fashion expert helping someone choose an outfit. 
    {items_context}
    
    Please create a complete outfit recommendation that includes exactly:
    - One shirt
    - One pair of pants
    - One pair of shoes
    
    Make sure to reference specific items by their ID numbers."""
    
    if occasion:
        prompt += f"\nThe occasion is: {occasion}"
    if weather:
        prompt += f"\nWeather conditions: {weather}"
    if preferences:
        prompt += f"\nAdditional preferences: {preferences}"
    
    prompt += """\n
    Format your response exactly like this:
    
    Selected Outfit:
    - Shirt: #[ID]
    - Pants: #[ID]
    - Shoes: #[ID]
    
    Style Tips: [Brief styling advice]
    Accessories: [Optional suggestions]
    
    Keep the response concise and friendly."""

    # Get recommendation from Claude
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    
    # Parse the response to extract recommended item IDs
    response_text = response.content
    recommended_items: GroupedRecommendedItems = {
        'shirt': [],
        'pants': [],
        'shoes': []
    }
    
    # Extract item IDs from the response and group by type
    for item in clothing_items:
        item_id_str = f"#{item['id']}"
        if item_id_str in response_text:
            recommended_item = {
                'id': item['id'],
                'type': item['type'],
                'image_path': item['image_path'],
                'color': item['color'],
                'style': item['style']
            }
            if item['type'] in recommended_items:
                recommended_items[item['type']].append(recommended_item)
    
    return {
        'text': str(response_text),
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
