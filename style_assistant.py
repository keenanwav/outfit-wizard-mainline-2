import anthropic
import os
from typing import Dict, List
import streamlit as st

def get_style_recommendation(
    clothing_items: List[Dict],
    occasion: str = None,
    weather: str = None,
    preferences: str = None
) -> str:
    """Get style recommendations from Claude AI"""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    # Prepare the context about available clothing items
    items_context = "Available clothing items:\n"
    for item in clothing_items:
        items_context += f"- {item['type'].capitalize()}: {item['style']} style, {item['color']} color\n"
    
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
    1. A specific outfit recommendation using the available items
    2. Style tips for this combination
    3. Accessory suggestions if applicable
    
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
    
    return message.content

def format_clothing_items(items_df) -> List[Dict]:
    """Format clothing items dataframe into a list of dictionaries"""
    formatted_items = []
    for _, item in items_df.iterrows():
        formatted_items.append({
            'type': item['type'],
            'style': item['style'],
            'color': item['color'],
            'size': item['size'],
            'tags': item['tags'] if 'tags' in item else []
        })
    return formatted_items
