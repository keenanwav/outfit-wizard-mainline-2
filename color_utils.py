from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import os
import streamlit as st

def parse_color_string(color_str):
    try:
        # Handle color strings in format "r,g,b" or multiple colors "[r,g,b],[r,g,b]"
        if '[' in color_str:
            colors = []
            for color_part in color_str.split(']['):
                color_part = color_part.strip('[]')
                colors.append([int(c) for c in color_part.split(',')])
            return colors
        return [int(c) for c in color_str.split(',')]
    except:
        # Return a default color if parsing fails
        return [0, 0, 0]

def get_region_color(img, region_bounds):
    """Extract the average color from a specific region of the image"""
    try:
        region = img.crop(region_bounds)
        pixels = np.array(region)
        return pixels.mean(axis=(0, 1)).astype(int)
    except Exception as e:
        st.error(f"Error extracting region color: {str(e)}")
        return None

def is_white_color(color, threshold=15):
    """Check if a color is close to white with stricter threshold"""
    return all(c >= (255 - threshold) for c in color)

def is_pure_white(color):
    """Check if a color is pure white (#ffffff)"""
    return all(c >= 254 for c in color)

def get_pants_colors(image_path):
    """Extract colors from multiple regions of pants image with improved white handling"""
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        width, height = img.size
        
        # Define multiple sampling regions including center points
        regions = [
            # Upper region (waist area)
            (width//4, height//8, 3*width//4, height//4),
            # Upper-middle region
            (width//4, height//4, 3*width//4, height//2),
            # Center region (main body)
            (width//3, height//3, 2*width//3, 2*height//3),
            # Lower-middle region
            (width//4, height//2, 3*width//4, 3*height//4),
            # Bottom region (ankle area)
            (width//4, 3*height//4, 3*width//4, height),
            # Center vertical strip
            (width//2 - width//8, height//4, width//2 + width//8, 3*height//4)
        ]
        
        colors = []
        non_white_colors = []
        
        # Sample colors from all regions
        for region in regions:
            color = get_region_color(img, region)
            if color is not None:
                # Skip pure white colors (likely background)
                if not is_pure_white(color):
                    colors.append(color)
                    if not is_white_color(color):
                        non_white_colors.append(color)
        
        if not colors:
            return None
            
        # Use K-means to find dominant colors
        colors_array = np.array(colors)
        kmeans = KMeans(n_clusters=min(3, len(colors)), random_state=42)
        kmeans.fit(colors_array)
        dominant_colors = kmeans.cluster_centers_.astype(int)
        
        # Sort colors by occurrence (most frequent first)
        color_counts = np.bincount(kmeans.labels_, minlength=len(dominant_colors))
        sorted_indices = np.argsort(-color_counts)
        dominant_colors = dominant_colors[sorted_indices]
        
        # If the most dominant color is white-like, use the next color
        if is_white_color(dominant_colors[0]) and len(dominant_colors) > 1:
            # Return both white and the next most prominent color
            return np.array([dominant_colors[0], dominant_colors[1]])
        
        # Return the most dominant non-white color
        return np.array([dominant_colors[0]])
        
    except Exception as e:
        st.error(f"Error extracting pants colors: {str(e)}")
        return None

def get_color_palette(image_path, n_colors=1, item_type=None):
    """Extract colors from an image with item type specific handling"""
    try:
        if item_type == 'pants':
            # Use specialized pants color detection
            colors = get_pants_colors(image_path)
            return colors if colors is not None else None
            
        elif n_colors == 1:
            # Use center color detection for other items
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get the center pixel coordinates
            width, height = img.size
            center_x = width // 2
            center_y = height // 2
            
            # Get color from a small central region (5x5 pixels)
            region_size = 5
            x1 = max(0, center_x - region_size // 2)
            y1 = max(0, center_y - region_size // 2)
            x2 = min(width, x1 + region_size)
            y2 = min(height, y1 + region_size)
            
            # Get the average color of the central region
            center_region = img.crop((x1, y1, x2, y2))
            pixels = np.array(center_region)
            center_color = pixels.mean(axis=(0, 1)).astype(int)
            
            return np.array([center_color])
            
        else:
            # Original k-means clustering for multiple colors
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img.thumbnail((150, 150))
            pixels = np.array(img)
            pixels = pixels.reshape(-1, 3)
            
            kmeans = KMeans(n_clusters=n_colors, random_state=42)
            kmeans.fit(pixels)
            colors = kmeans.cluster_centers_
            
            return colors.astype(int)
            
    except Exception as e:
        st.error(f"Error extracting color palette: {str(e)}")
        return None

def rgb_to_hex(rgb):
    """Convert RGB color to hex format"""
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def display_color_palette(colors):
    """Create a streamlit color palette display"""
    if colors is None or len(colors) == 0:
        return
    
    # Create columns for each color
    cols = st.columns(len(colors))
    
    # Display each color with its hex value
    for idx, color in enumerate(colors):
        hex_color = rgb_to_hex(color)
        with cols[idx]:
            st.markdown(
                f"""
                <div style="
                    background-color: {hex_color};
                    width: 2rem;
                    aspect-ratio: 1;
                    border-radius: 8px;
                    margin: 0 auto 8px auto;
                "></div>
                <p style="text-align: center; font-size: 12px; margin: 0 auto;">{hex_color}</p>
                """,
                unsafe_allow_html=True
            )
