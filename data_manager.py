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

def ensure_user_preferences_file():
    if not os.path.exists('data/user_preferences.csv'):
        df = pd.DataFrame(columns=['username', 'item_id'])
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
    
    new_preference = pd.DataFrame({'username': [username], 'item_id': [item_id]})
    preferences_df = pd.concat([preferences_df, new_preference], ignore_index=True)
    
    preferences_df.to_csv('data/user_preferences.csv', index=False)

def get_item_features(items_df):
    mlb = MultiLabelBinarizer()
    style_features = mlb.fit_transform(items_df['style'].str.split(','))
    gender_features = mlb.fit_transform(items_df['gender'].str.split(','))
    size_features = mlb.fit_transform(items_df['size'].str.split(','))
    
    color_features = np.array([list(map(int, color.split(','))) for color in items_df['color']])
    
    return np.hstack((style_features, gender_features, size_features, color_features))

def get_recommendations(username, n_recommendations=5):
    ensure_user_preferences_file()
    items_df = load_clothing_items()
    preferences_df = pd.read_csv('data/user_preferences.csv')
    
    user_item_matrix = preferences_df.pivot(index='username', columns='item_id', values='item_id').notna().astype(int)
    
    if username not in user_item_matrix.index or user_item_matrix.shape[0] <= 1:
        return items_df.sample(n_recommendations)
    
    n_neighbors = min(20, user_item_matrix.shape[0] - 1)
    
    user_item_matrix_sparse = csr_matrix(user_item_matrix.values)
    
    model_knn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=n_neighbors, n_jobs=-1)
    model_knn.fit(user_item_matrix_sparse)
    
    distances, indices = model_knn.kneighbors(user_item_matrix.loc[username].values.reshape(1, -1), n_neighbors=n_neighbors)
    
    similar_users = user_item_matrix.index[indices.flatten()[1:]]
    
    similar_users_preferences = preferences_df[preferences_df['username'].isin(similar_users)]
    
    item_score = similar_users_preferences.groupby('item_id').size().sort_values(ascending=False)
    
    user_items = preferences_df[preferences_df['username'] == username]['item_id'].unique()
    
    recommended_items = item_score[~item_score.index.isin(user_items)].head(n_recommendations)
    
    if len(recommended_items) < n_recommendations:
        additional_items = items_df[~items_df['id'].isin(recommended_items.index) & ~items_df['id'].isin(user_items)].sample(n_recommendations - len(recommended_items))
        recommended_items = pd.concat([recommended_items, pd.Series(additional_items['id'], index=additional_items['id'])])
    
    recommendations = items_df[items_df['id'].isin(recommended_items.index)]
    
    return recommendations[['id', 'type', 'style', 'gender', 'size', 'image_path', 'hyperlink']]

def get_advanced_recommendations(username, n_recommendations=5, collab_weight=0.7):
    logging.info(f"Generating advanced recommendations for user: {username}")
    ensure_user_preferences_file()
    items_df = load_clothing_items()
    preferences_df = pd.read_csv('data/user_preferences.csv')
    
    if username not in preferences_df['username'].unique():
        logging.warning(f"No preferences found for user: {username}. Using fallback method.")
        return get_fallback_recommendations(items_df, n_recommendations)
    
    # Collaborative Filtering
    user_item_matrix = preferences_df.pivot(index='username', columns='item_id', values='item_id').notna().astype(int)
    user_item_matrix_sparse = csr_matrix(user_item_matrix.values)
    
    # Matrix Factorization using Truncated SVD
    n_components = min(30, user_item_matrix_sparse.shape[1] - 1)
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    user_item_matrix_reduced = svd.fit_transform(user_item_matrix_sparse)
    item_features = svd.components_.T
    
    # Find similar users
    user_similarity = cosine_similarity(user_item_matrix_reduced)
    user_similarity_df = pd.DataFrame(user_similarity, index=user_item_matrix.index, columns=user_item_matrix.index)
    similar_users = user_similarity_df.loc[username].sort_values(ascending=False)[1:6].index.tolist()
    
    # Content-based Filtering
    item_content_features = get_item_content_features(items_df)
    
    # Get user's liked items
    user_liked_items = preferences_df[preferences_df['username'] == username]['item_id'].tolist()
    user_liked_features = item_content_features[items_df['id'].isin(user_liked_items)]
    
    if len(user_liked_features) > 0:
        user_profile = np.mean(user_liked_features, axis=0)
    else:
        user_profile = np.mean(item_content_features, axis=0)
    
    # Calculate similarity between user profile and all items
    content_based_similarities = cosine_similarity([user_profile], item_content_features)[0]
    
    # Collaborative filtering scores
    user_vector = user_item_matrix_reduced[user_item_matrix.index.get_loc(username)]
    collaborative_scores = np.dot(user_vector, item_features.T)
    
    # Combine collaborative and content-based scores
    combined_scores = collab_weight * collaborative_scores + (1 - collab_weight) * content_based_similarities
    
    # Get top N recommendations
    top_indices = combined_scores.argsort()[::-1]
    recommended_items = []
    for idx in top_indices:
        item_id = items_df.iloc[idx]['id']
        if item_id not in user_liked_items and len(recommended_items) < n_recommendations:
            recommended_items.append(item_id)
    
    recommendations = items_df[items_df['id'].isin(recommended_items)]
    
    logging.info(f"Generated {len(recommendations)} recommendations for user: {username}")
    return recommendations[['id', 'type', 'style', 'gender', 'size', 'image_path', 'hyperlink']]

def get_item_content_features(items_df):
    mlb = MultiLabelBinarizer()
    style_features = mlb.fit_transform(items_df['style'].str.split(','))
    gender_features = mlb.fit_transform(items_df['gender'].str.split(','))
    size_features = mlb.fit_transform(items_df['size'].str.split(','))
    color_features = np.array([list(map(int, color.split(','))) for color in items_df['color']])
    
    item_content_features = np.hstack((style_features, gender_features, size_features, color_features))
    
    scaler = StandardScaler()
    item_content_features_normalized = scaler.fit_transform(item_content_features)
    
    return item_content_features_normalized

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
    print(f"Debug: Starting edit_clothing_item function for item ID {item_id}")
    items_df = load_clothing_items()
    
    if item_id not in items_df['id'].values:
        return False, f"Item with ID {item_id} not found."
    
    item_index = items_df.index[items_df['id'] == item_id].tolist()[0]
    
    print(f"Debug: Before updating DataFrame for item ID {item_id}")
    items_df.at[item_index, 'color'] = f"{color[0]},{color[1]},{color[2]}"
    items_df.at[item_index, 'style'] = ','.join(styles)
    items_df.at[item_index, 'gender'] = ','.join(genders)
    items_df.at[item_index, 'size'] = ','.join(sizes)
    items_df.at[item_index, 'hyperlink'] = hyperlink
    
    print(f"Debug: Before saving CSV file for item ID {item_id}")
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