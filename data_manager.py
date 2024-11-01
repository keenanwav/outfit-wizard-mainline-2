import pandas as pd
import os
from PIL import Image
import uuid
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler
from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
import logging
from datetime import datetime
from sklearn.model_selection import KFold
import joblib

def ensure_user_preferences_file():
    if not os.path.exists('data/user_preferences.csv'):
        df = pd.DataFrame(columns=['username', 'item_id', 'timestamp'])
        df.to_csv('data/user_preferences.csv', index=False)

def load_clothing_items():
    items_df = pd.read_csv('data/clothing_items.csv')
    return items_df

def save_outfit(outfit, username):
    try:
        if not os.path.exists('wardrobe'):
            os.makedirs('wardrobe')
        
        outfit_id = str(uuid.uuid4())
        outfit_filename = f"outfit_{outfit_id}.png"
        outfit_path = os.path.join('wardrobe', outfit_filename)
        
        shirt_img = Image.open(outfit['shirt']['image_path']).resize((200, 200))
        pants_img = Image.open(outfit['pants']['image_path']).resize((200, 200))
        shoes_img = Image.open(outfit['shoes']['image_path']).resize((200, 200))
        
        outfit_img = Image.new('RGB', (600, 200), (255, 255, 255))
        
        outfit_img.paste(shirt_img, (0, 0))
        outfit_img.paste(pants_img, (200, 0))
        outfit_img.paste(shoes_img, (400, 0))
        
        outfit_img.save(outfit_path)
        
        outfit_info = {
            'username': username,
            'outfit_id': outfit_id,
            'image_path': outfit_path,
            'date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        saved_outfits_df = pd.read_csv('data/saved_outfits.csv') if os.path.exists('data/saved_outfits.csv') else pd.DataFrame()
        saved_outfits_df = pd.concat([saved_outfits_df, pd.DataFrame([outfit_info])], ignore_index=True)
        saved_outfits_df.to_csv('data/saved_outfits.csv', index=False)
        
        print(f"Outfit saved successfully: {outfit_path}")
        return outfit_path
    except Exception as e:
        print(f"Error saving outfit: {str(e)}")
        return None

def add_clothing_item(item_type, color, styles, genders, sizes, image_file, hyperlink):
    items_df = load_clothing_items()
    
    new_id = items_df['id'].max() + 1 if len(items_df) > 0 else 1
    
    item_dir = f"images/{item_type}s"
    if not os.path.exists(item_dir):
        os.makedirs(item_dir)
    
    image_filename = f"{item_type}_{new_id}.png"
    image_path = os.path.join(item_dir, image_filename)
    with Image.open(image_file) as img:
        img.save(image_path)
    
    new_item = pd.DataFrame({
        'id': [new_id],
        'type': [item_type],
        'color': [f"{color[0]},{color[1]},{color[2]}"],
        'style': [','.join(styles)],
        'gender': [','.join(genders)],
        'size': [','.join(sizes)],
        'image_path': [image_path],
        'hyperlink': [hyperlink]
    })
    
    items_df = pd.concat([items_df, new_item], ignore_index=True)
    items_df.to_csv('data/clothing_items.csv', index=False)
    
    return True, f"New {item_type} added successfully with ID: {new_id}"

def update_csv_structure():
    items_df = load_clothing_items()
    if 'hyperlink' not in items_df.columns:
        items_df['hyperlink'] = ''
        items_df.to_csv('data/clothing_items.csv', index=False)

def store_user_preference(username, item_id):
    ensure_user_preferences_file()
    preferences_df = pd.read_csv('data/user_preferences.csv')
    
    new_preference = pd.DataFrame({
        'username': [username], 
        'item_id': [item_id],
        'timestamp': [datetime.now()]
    })
    preferences_df = pd.concat([preferences_df, new_preference], ignore_index=True)
    preferences_df.to_csv('data/user_preferences.csv', index=False)

def get_item_features(items_df):
    mlb = MultiLabelBinarizer()
    
    style_words = set()
    for styles in items_df['style'].str.split(','):
        for style in styles:
            style_words.update(style.lower().split())
    
    style_features = np.zeros((len(items_df), len(style_words)))
    word_to_idx = {word: idx for idx, word in enumerate(style_words)}
    
    for i, styles in enumerate(items_df['style'].str.split(',')):
        for style in styles:
            for word in style.lower().split():
                style_features[i, word_to_idx[word]] = 1
    
    gender_features = mlb.fit_transform(items_df['gender'].str.split(','))
    size_features = mlb.fit_transform(items_df['size'].str.split(','))
    
    color_features = np.array([list(map(int, color.split(','))) for color in items_df['color']])
    color_features_normalized = color_features / 255.0
    
    return np.hstack((style_features, gender_features, size_features, color_features_normalized))

def calculate_time_decay(timestamps, half_life_days=30):
    current_time = datetime.now()
    timestamps = pd.to_datetime(timestamps)
    time_diff = (current_time - timestamps).dt.total_seconds() / (24 * 3600)
    return np.exp(-np.log(2) * time_diff / half_life_days)

def get_advanced_recommendations(username, n_recommendations=5, collab_weight=0.7):
    logging.info(f"Generating advanced recommendations for user: {username}")
    ensure_user_preferences_file()
    items_df = load_clothing_items()
    preferences_df = pd.read_csv('data/user_preferences.csv')
    
    if username not in preferences_df['username'].unique():
        logging.warning(f"No preferences found for user: {username}. Using fallback method.")
        return get_fallback_recommendations(items_df, n_recommendations)
    
    if 'timestamp' not in preferences_df.columns:
        preferences_df['timestamp'] = datetime.now()
    
    user_prefs = preferences_df[preferences_df['username'] == username]
    time_weights = calculate_time_decay(user_prefs['timestamp'])
    
    user_item_matrix = preferences_df.pivot(index='username', columns='item_id', values='timestamp')
    user_item_matrix = user_item_matrix.notna().astype(float)
    
    user_idx = user_item_matrix.index.get_loc(username)
    user_item_matrix.iloc[user_idx] *= time_weights
    
    user_item_matrix_sparse = csr_matrix(user_item_matrix.values)
    best_score = float('-inf')
    best_n_components = 30
    
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    for n_comp in [20, 30, 40, 50]:
        scores = []
        for train_idx, val_idx in kf.split(user_item_matrix_sparse):
            svd = TruncatedSVD(n_components=n_comp, random_state=42)
            train = user_item_matrix_sparse[train_idx]
            val = user_item_matrix_sparse[val_idx]
            
            user_item_matrix_reduced = svd.fit_transform(train)
            pred = user_item_matrix_reduced @ svd.components_
            score = np.mean((val.toarray() - pred[len(train_idx):]) ** 2)
            scores.append(-score)
        
        avg_score = np.mean(scores)
        if avg_score > best_score:
            best_score = avg_score
            best_n_components = n_comp
    
    svd = TruncatedSVD(n_components=best_n_components, random_state=42)
    user_item_matrix_reduced = svd.fit_transform(user_item_matrix_sparse)
    item_features = svd.components_.T
    
    item_content_features = get_item_features(items_df)
    
    user_liked_items = preferences_df[preferences_df['username'] == username]['item_id'].tolist()
    user_liked_features = item_content_features[items_df['id'].isin(user_liked_items)]
    
    if len(user_liked_features) > 0:
        user_profile = np.average(user_liked_features, weights=time_weights, axis=0)
    else:
        user_profile = np.mean(item_content_features, axis=0)
    
    content_based_similarities = cosine_similarity([user_profile], item_content_features)[0]
    
    user_vector = user_item_matrix_reduced[user_idx]
    collaborative_scores = np.dot(user_vector, item_features.T)
    
    combined_scores = collab_weight * collaborative_scores + (1 - collab_weight) * content_based_similarities
    
    top_indices = []
    candidate_indices = combined_scores.argsort()[::-1]
    
    for idx in candidate_indices:
        item_id = items_df.iloc[idx]['id']
        if item_id not in user_liked_items:
            if not top_indices or not any(
                cosine_similarity([item_content_features[idx]], 
                                item_content_features[top_indices]).flatten() > 0.8
            ):
                top_indices.append(idx)
                if len(top_indices) == n_recommendations:
                    break
    
    recommended_items = items_df.iloc[top_indices]
    
    logging.info(f"Generated {len(recommended_items)} recommendations for user: {username}")
    return recommended_items[['id', 'type', 'style', 'gender', 'size', 'image_path', 'hyperlink']]

def get_fallback_recommendations(items_df, n_recommendations):
    logging.info("Using fallback recommendation method")
    return items_df.sample(n_recommendations)

def load_saved_outfits(username):
    if os.path.exists('data/saved_outfits.csv'):
        saved_outfits_df = pd.read_csv('data/saved_outfits.csv')
        user_outfits = saved_outfits_df[saved_outfits_df['username'] == username].to_dict('records')
        return user_outfits
    return []

def delete_outfit(outfit_id):
    saved_outfits_df = pd.read_csv('data/saved_outfits.csv')
    outfit_to_delete = saved_outfits_df[saved_outfits_df['outfit_id'] == outfit_id].iloc[0]
    
    if os.path.exists(outfit_to_delete['image_path']):
        os.remove(outfit_to_delete['image_path'])
    
    saved_outfits_df = saved_outfits_df[saved_outfits_df['outfit_id'] != outfit_id]
    saved_outfits_df.to_csv('data/saved_outfits.csv', index=False)

def edit_clothing_item(item_id, color, styles, genders, sizes, hyperlink):
    items_df = load_clothing_items()
    
    if item_id not in items_df['id'].values:
        return False, f"Item with ID {item_id} not found."
    
    item_index = items_df.index[items_df['id'] == item_id].tolist()[0]
    
    items_df.at[item_index, 'color'] = f"{color[0]},{color[1]},{color[2]}"
    items_df.at[item_index, 'style'] = ','.join(styles)
    items_df.at[item_index, 'gender'] = ','.join(genders)
    items_df.at[item_index, 'size'] = ','.join(sizes)
    items_df.at[item_index, 'hyperlink'] = hyperlink
    
    items_df.to_csv('data/clothing_items.csv', index=False)
    
    return True, f"Item with ID {item_id} updated successfully."

def delete_clothing_item(item_id):
    items_df = load_clothing_items()
    
    if item_id not in items_df['id'].values:
        return False, f"Item with ID {item_id} not found."
    
    item_to_delete = items_df[items_df['id'] == item_id].iloc[0]
    
    if os.path.exists(item_to_delete['image_path']):
        os.remove(item_to_delete['image_path'])
    
    items_df = items_df[items_df['id'] != item_id]
    items_df.to_csv('data/clothing_items.csv', index=False)
    
    return True, f"Item with ID {item_id} deleted successfully."