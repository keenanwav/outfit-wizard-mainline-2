import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
import colorsys

def rgb_to_hsv(rgb):
    """Convert RGB color to HSV"""
    r, g, b = [x/255.0 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h, s, v

def hsv_to_rgb(hsv):
    """Convert HSV color to RGB"""
    h, s, v = hsv
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return tuple(int(x * 255) for x in (r, g, b))

def get_complementary_color(rgb):
    """Get the complementary color"""
    h, s, v = rgb_to_hsv(rgb)
    h = (h + 0.5) % 1.0
    return hsv_to_rgb((h, s, v))

def get_analogous_colors(rgb, angle=30):
    """Get analogous colors"""
    h, s, v = rgb_to_hsv(rgb)
    angle = angle / 360.0
    colors = []
    for a in [-angle, angle]:
        new_h = (h + a) % 1.0
        colors.append(hsv_to_rgb((new_h, s, v)))
    return colors

def get_triadic_colors(rgb):
    """Get triadic color harmony"""
    h, s, v = rgb_to_hsv(rgb)
    colors = []
    for a in [0.333, 0.666]:
        new_h = (h + a) % 1.0
        colors.append(hsv_to_rgb((new_h, s, v)))
    return colors

def calculate_color_harmony_score(color1, color2):
    """Calculate harmony score between two colors"""
    h1, s1, v1 = rgb_to_hsv(color1)
    h2, s2, v2 = rgb_to_hsv(color2)
    
    # Calculate hue difference (0-1 scale)
    hue_diff = min(abs(h1 - h2), 1 - abs(h1 - h2))
    
    # Complementary colors (around 0.5 hue difference)
    complementary_score = 1 - abs(hue_diff - 0.5)
    
    # Analogous colors (small hue difference)
    analogous_score = 1 - min(hue_diff, 0.25) * 4
    
    # Similar saturation and value
    saturation_score = 1 - abs(s1 - s2)
    value_score = 1 - abs(v1 - v2)
    
    # Combine scores with weights
    total_score = (complementary_score * 0.3 + 
                  analogous_score * 0.3 + 
                  saturation_score * 0.2 + 
                  value_score * 0.2)
    
    return total_score

def learn_color_preferences(saved_outfits):
    """Learn color preferences from saved outfits"""
    color_combinations = []
    color_scores = {}
    
    for outfit in saved_outfits:
        # Extract colors from each item in the outfit
        outfit_colors = []
        for item_type in ['shirt', 'pants', 'shoes']:
            if item_type in outfit:
                color_str = outfit[item_type]['color']
                if isinstance(color_str, str):
                    try:
                        color = tuple(map(int, color_str.split(',')))
                        outfit_colors.append(color)
                    except:
                        continue
        
        # Calculate harmony scores between all color pairs
        if len(outfit_colors) >= 2:
            for i in range(len(outfit_colors)):
                for j in range(i + 1, len(outfit_colors)):
                    color_pair = (outfit_colors[i], outfit_colors[j])
                    harmony_score = calculate_color_harmony_score(color_pair[0], color_pair[1])
                    
                    # Store the color combination and its score
                    color_combinations.append(color_pair)
                    color_scores[color_pair] = harmony_score
    
    return color_combinations, color_scores

def recommend_matching_colors(base_color, learned_combinations, learned_scores, n_recommendations=3):
    """Recommend matching colors based on learned preferences"""
    if not learned_combinations:
        # Fallback to basic color theory if no learned combinations
        recommendations = []
        recommendations.extend(get_analogous_colors(base_color))
        recommendations.append(get_complementary_color(base_color))
        return recommendations[:n_recommendations]
    
    # Find color combinations involving the base color
    matching_scores = {}
    for combo, score in learned_scores.items():
        if any(np.allclose(base_color, c) for c in combo):
            other_color = combo[1] if np.allclose(base_color, combo[0]) else combo[0]
            matching_scores[other_color] = score
    
    # Sort by score and get top recommendations
    sorted_matches = sorted(matching_scores.items(), key=lambda x: x[1], reverse=True)
    return [color for color, _ in sorted_matches[:n_recommendations]]
