import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity
import logging
from datetime import datetime
import streamlit as st
from data_manager import get_db_connection, load_clothing_items, load_saved_outfits

class PersonalizedRecommender:
    def __init__(self):
        self.label_encoders = {
            'color': LabelEncoder(),
            'style': LabelEncoder(),
            'type': LabelEncoder()
        }
        self.similarity_threshold = 0.3

    def _encode_features(self, items_df: pd.DataFrame) -> np.ndarray:
        """Encode categorical features to numerical values"""
        encoded_features = []
        
        # Encode colors (convert RGB string to normalized values)
        colors = items_df['color'].apply(lambda x: [int(c) for c in str(x).strip('rgb()').split(',')])
        normalized_colors = np.array(colors.tolist()) / 255.0
        encoded_features.append(normalized_colors)
        
        # Encode styles
        styles = items_df['style'].fillna('')
        self.label_encoders['style'].fit(styles)
        encoded_styles = self.label_encoders['style'].transform(styles)
        encoded_features.append(encoded_styles.reshape(-1, 1))
        
        # Encode item types
        types = items_df['type'].fillna('')
        self.label_encoders['type'].fit(types)
        encoded_types = self.label_encoders['type'].transform(types)
        encoded_features.append(encoded_types.reshape(-1, 1))
        
        # Combine all features
        return np.hstack(encoded_features)

    def get_user_preferences(self, user_id: int) -> Dict:
        """Get user's preferences based on saved outfits"""
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # Get user's saved outfits
                cur.execute("""
                    SELECT image_path, created_at 
                    FROM saved_outfits 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC
                """, (user_id,))
                saved_outfits = cur.fetchall()
                
                if not saved_outfits:
                    return {}
                
                # Analyze color preferences
                color_preferences = {}
                style_preferences = {}
                
                # Load all clothing items
                items_df = load_clothing_items()
                
                for outfit_path, _ in saved_outfits:
                    # Extract item details from saved outfits
                    outfit_items = items_df[items_df['image_path'].isin([outfit_path])]
                    
                    for _, item in outfit_items.iterrows():
                        # Track color preferences
                        color = str(item['color'])
                        if color in color_preferences:
                            color_preferences[color] += 1
                        else:
                            color_preferences[color] = 1
                            
                        # Track style preferences
                        styles = str(item['style']).split(',')
                        for style in styles:
                            if style in style_preferences:
                                style_preferences[style] += 1
                            else:
                                style_preferences[style] = 1
                
                return {
                    'color_preferences': color_preferences,
                    'style_preferences': style_preferences
                }
                
        except Exception as e:
            logging.error(f"Error getting user preferences: {str(e)}")
            return {}

    def generate_personalized_outfit(self, user_id: int, occasion: str = None) -> Tuple[Dict, List[str]]:
        """Generate a personalized outfit based on user preferences"""
        try:
            # Get user preferences
            preferences = self.get_user_preferences(user_id)
            
            # Load available items
            items_df = load_clothing_items()
            if items_df.empty:
                return {}, ['No items available']
            
            # Convert items to feature matrix
            feature_matrix = self._encode_features(items_df)
            
            # Initialize outfit selection
            selected_outfit = {}
            missing_items = []
            
            # Select items based on preferences and occasion
            for item_type in ['shirt', 'pants', 'shoes']:
                type_items = items_df[items_df['type'] == item_type]
                if type_items.empty:
                    missing_items.append(item_type)
                    continue
                
                # Calculate preference scores
                scores = np.zeros(len(type_items))
                
                # Color preference score
                if preferences.get('color_preferences'):
                    for idx, item in type_items.iterrows():
                        color = str(item['color'])
                        scores[idx] += preferences['color_preferences'].get(color, 0)
                
                # Style preference score
                if preferences.get('style_preferences'):
                    for idx, item in type_items.iterrows():
                        styles = str(item['style']).split(',')
                        style_score = sum(preferences['style_preferences'].get(style, 0) for style in styles)
                        scores[idx] += style_score
                
                # Occasion matching (if specified)
                if occasion:
                    for idx, item in type_items.iterrows():
                        if occasion.lower() in str(item['style']).lower():
                            scores[idx] *= 1.5  # Boost score for occasion-matching items
                
                # Select item with highest score
                if any(scores > 0):
                    best_idx = scores.argmax()
                    selected_item = type_items.iloc[best_idx]
                    selected_outfit[item_type] = {
                        'image_path': selected_item['image_path'],
                        'color': selected_item['color'],
                        'price': float(selected_item['price']) if selected_item['price'] else 0,
                        'hyperlink': selected_item['hyperlink'] if 'hyperlink' in selected_item else None
                    }
                else:
                    # If no preference data, select randomly
                    selected_item = type_items.sample(n=1).iloc[0]
                    selected_outfit[item_type] = {
                        'image_path': selected_item['image_path'],
                        'color': selected_item['color'],
                        'price': float(selected_item['price']) if selected_item['price'] else 0,
                        'hyperlink': selected_item['hyperlink'] if 'hyperlink' in selected_item else None
                    }
            
            return selected_outfit, missing_items
            
        except Exception as e:
            logging.error(f"Error generating personalized outfit: {str(e)}")
            return {}, ['Error generating outfit']

    def get_similar_items(self, item_id: int, n: int = 3) -> List[Dict]:
        """Get similar items based on features"""
        try:
            items_df = load_clothing_items()
            if items_df.empty or item_id not in items_df.index:
                return []
            
            # Get item features
            feature_matrix = self._encode_features(items_df)
            item_features = feature_matrix[items_df.index == item_id]
            
            # Calculate similarity
            similarities = cosine_similarity(item_features, feature_matrix)
            similar_indices = similarities[0].argsort()[::-1][1:n+1]
            
            # Get similar items
            similar_items = []
            for idx in similar_indices:
                if similarities[0][idx] >= self.similarity_threshold:
                    item = items_df.iloc[idx]
                    similar_items.append({
                        'id': item.name,
                        'type': item['type'],
                        'color': item['color'],
                        'style': item['style'],
                        'image_path': item['image_path'],
                        'similarity': similarities[0][idx]
                    })
            
            return similar_items
            
        except Exception as e:
            logging.error(f"Error finding similar items: {str(e)}")
            return []
