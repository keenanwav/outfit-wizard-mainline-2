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
import psycopg2
from psycopg2.extras import execute_values

def get_db_connection():
    return psycopg2.connect(
        host=os.environ['PGHOST'],
        database=os.environ['PGDATABASE'],
        user=os.environ['PGUSER'],
        password=os.environ['PGPASSWORD']
    )

def create_user_items_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_clothing_items (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(50),
            type VARCHAR(50),
            color VARCHAR(50),
            style VARCHAR(255),
            gender VARCHAR(50),
            size VARCHAR(50),
            image_path VARCHAR(255),
            hyperlink VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

def ensure_user_preferences_file():
    if not os.path.exists('data/user_preferences.csv'):
        df = pd.DataFrame(columns=['username', 'item_id', 'timestamp'])
        df.to_csv('data/user_preferences.csv', index=False)

def load_clothing_items(username=None):
    if not os.path.exists('data/clothing_items.csv'):
        # Create empty DataFrame with required columns
        items_df = pd.DataFrame(columns=['id', 'type', 'color', 'style', 'gender', 'size', 'image_path', 'hyperlink'])
        items_df.to_csv('data/clothing_items.csv', index=False)
    else:
        items_df = pd.read_csv('data/clothing_items.csv')
    
    if username:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, type, color, style, gender, size, image_path, hyperlink 
            FROM user_clothing_items 
            WHERE user_id = %s
        """, (username,))
        user_items = cur.fetchall()
        cur.close()
        conn.close()

        if user_items:
            user_items_df = pd.DataFrame(user_items, 
                columns=['id', 'type', 'color', 'style', 'gender', 'size', 'image_path', 'hyperlink'])
            items_df = pd.concat([items_df, user_items_df], ignore_index=True)
    
    return items_df

def add_clothing_item(item_type, color, styles, genders, sizes, image_path, hyperlink=""):
    if not os.path.exists('data/clothing_items.csv'):
        items_df = pd.DataFrame(columns=['id', 'type', 'color', 'style', 'gender', 'size', 'image_path', 'hyperlink'])
    else:
        items_df = pd.read_csv('data/clothing_items.csv')
    
    new_item = {
        'id': len(items_df) + 1,
        'type': item_type,
        'color': f"{color[0]},{color[1]},{color[2]}",
        'style': ','.join(styles),
        'gender': ','.join(genders),
        'size': ','.join(sizes),
        'image_path': image_path,
        'hyperlink': hyperlink
    }
    
    items_df = pd.concat([items_df, pd.DataFrame([new_item])], ignore_index=True)
    items_df.to_csv('data/clothing_items.csv', index=False)
    return True, f"New {item_type} added successfully"

def add_user_clothing_item(username, item_type, color, styles, genders, sizes, image_file, hyperlink=""):
    if not os.path.exists(f"user_images/{username}"):
        os.makedirs(f"user_images/{username}", exist_ok=True)
    
    image_filename = f"{item_type}_{uuid.uuid4()}.png"
    image_path = os.path.join(f"user_images/{username}", image_filename)
    
    with Image.open(image_file) as img:
        img.save(image_path)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO user_clothing_items 
            (user_id, type, color, style, gender, size, image_path, hyperlink)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            username, 
            item_type, 
            f"{color[0]},{color[1]},{color[2]}", 
            ','.join(styles),
            ','.join(genders),
            ','.join(sizes),
            image_path,
            hyperlink
        ))
        new_id = cur.fetchone()[0]
        conn.commit()
        return True, f"New {item_type} added successfully with ID: {new_id}"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()

def update_csv_structure():
    if not os.path.exists('data'):
        os.makedirs('data')
    
    if not os.path.exists('data/clothing_items.csv'):
        items_df = pd.DataFrame(columns=['id', 'type', 'color', 'style', 'gender', 'size', 'image_path', 'hyperlink'])
        items_df.to_csv('data/clothing_items.csv', index=False)

def store_user_preference(username, item_id):
    ensure_user_preferences_file()
    preferences_df = pd.read_csv('data/user_preferences.csv')
    new_preference = {
        'username': username,
        'item_id': item_id,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    preferences_df = pd.concat([preferences_df, pd.DataFrame([new_preference])], ignore_index=True)
    preferences_df.to_csv('data/user_preferences.csv', index=False)

def get_advanced_recommendations(username, n_recommendations=5, collab_weight=0.7):
    logging.info(f"Generating advanced recommendations for user: {username}")
    ensure_user_preferences_file()
    
    try:
        preferences_df = pd.read_csv('data/user_preferences.csv')
        items_df = load_clothing_items()
        
        if username not in preferences_df['username'].unique():
            logging.warning(f"No preferences found for user: {username}")
            return items_df.sample(n=n_recommendations)
        
        user_prefs = preferences_df[preferences_df['username'] == username]
        timestamps = pd.to_datetime(user_prefs['timestamp'])
        time_diff = (datetime.now() - timestamps).dt.total_seconds() / (24 * 3600)
        time_weights = np.exp(-time_diff / 30)
        
        item_features = []
        for _, item in items_df.iterrows():
            color = list(map(int, item['color'].split(',')))
            color_normalized = [c/255 for c in color]
            
            style_features = [1 if style in item['style'].split(',') else 0 
                            for style in ['Casual', 'Formal', 'Sporty']]
            gender_features = [1 if gender in item['gender'].split(',') else 0 
                             for gender in ['Male', 'Female', 'Unisex']]
            size_features = [1 if size in item['size'].split(',') else 0 
                           for size in ['XS', 'S', 'M', 'L', 'XL']]
            
            features = color_normalized + style_features + gender_features + size_features
            item_features.append(features)
        
        item_features = np.array(item_features)
        
        user_liked_items = user_prefs['item_id'].values
        user_liked_indices = [items_df[items_df['id'] == item_id].index[0] 
                            for item_id in user_liked_items if item_id in items_df['id'].values]
        
        if user_liked_indices:
            user_profile = np.average(item_features[user_liked_indices], weights=time_weights, axis=0)
        else:
            user_profile = np.mean(item_features, axis=0)
        
        similarity_scores = cosine_similarity([user_profile], item_features)[0]
        
        recommended_indices = []
        for idx in similarity_scores.argsort()[::-1]:
            item_id = items_df.iloc[idx]['id']
            if item_id not in user_liked_items:
                recommended_indices.append(idx)
                if len(recommended_indices) == n_recommendations:
                    break
        
        recommended_items = items_df.iloc[recommended_indices]
        return recommended_items
        
    except Exception as e:
        logging.error(f"Error generating recommendations: {str(e)}")
        return items_df.sample(n=n_recommendations)

def save_outfit(outfit, username):
    try:
        if not os.path.exists('wardrobe'):
            os.makedirs('wardrobe')
        
        outfit_id = str(uuid.uuid4())
        outfit_filename = f"outfit_{outfit_id}.png"
        outfit_path = os.path.join('wardrobe', outfit_filename)
        
        total_width = 600
        height = 200
        outfit_img = Image.new('RGB', (total_width, height), (255, 255, 255))
        
        for i, item_type in enumerate(['shirt', 'pants', 'shoes']):
            if item_type in outfit:
                item_img = Image.open(outfit[item_type]['image_path'])
                item_img = item_img.resize((200, 200))
                outfit_img.paste(item_img, (i * 200, 0))
        
        outfit_img.save(outfit_path)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS saved_outfits (
                    id SERIAL PRIMARY KEY,
                    outfit_id VARCHAR(50),
                    username VARCHAR(50),
                    image_path VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                INSERT INTO saved_outfits (outfit_id, username, image_path)
                VALUES (%s, %s, %s)
            """, (outfit_id, username, outfit_path))
            
            conn.commit()
            return outfit_path
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
            
    except Exception as e:
        logging.error(f"Error saving outfit: {str(e)}")
        return None

def load_saved_outfits(username):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT outfit_id, image_path, created_at 
            FROM saved_outfits 
            WHERE username = %s 
            ORDER BY created_at DESC
        """, (username,))
        
        outfits = cur.fetchall()
        if outfits:
            return [
                {
                    'outfit_id': outfit[0],
                    'image_path': outfit[1],
                    'date': outfit[2].strftime("%Y-%m-%d %H:%M:%S")
                }
                for outfit in outfits
            ]
        return []
        
    except Exception as e:
        logging.error(f"Error loading saved outfits: {str(e)}")
        return []
    finally:
        cur.close()
        conn.close()

def delete_outfit(outfit_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT image_path FROM saved_outfits WHERE outfit_id = %s", (outfit_id,))
        outfit = cur.fetchone()
        
        if outfit and outfit[0]:
            if os.path.exists(outfit[0]):
                os.remove(outfit[0])
            
            cur.execute("DELETE FROM saved_outfits WHERE outfit_id = %s", (outfit_id,))
            conn.commit()
            return True, "Outfit deleted successfully"
        
        return False, "Outfit not found"
        
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()

def edit_clothing_item(item_id, color, styles, genders, sizes, hyperlink):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE user_clothing_items 
            SET color = %s, style = %s, gender = %s, size = %s, hyperlink = %s
            WHERE id = %s
            RETURNING id
        """, (
            f"{color[0]},{color[1]},{color[2]}",
            ','.join(styles),
            ','.join(genders),
            ','.join(sizes),
            hyperlink,
            item_id
        ))
        
        if cur.fetchone():
            conn.commit()
            return True, f"Item with ID {item_id} updated successfully"
        return False, f"Item with ID {item_id} not found"
        
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()

def delete_clothing_item(item_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT image_path FROM user_clothing_items WHERE id = %s", (item_id,))
        item = cur.fetchone()
        
        if item and item[0]:
            if os.path.exists(item[0]):
                os.remove(item[0])
            
            cur.execute("DELETE FROM user_clothing_items WHERE id = %s", (item_id,))
            conn.commit()
            return True, f"Item with ID {item_id} deleted successfully"
        
        return False, f"Item with ID {item_id} not found"
        
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()
