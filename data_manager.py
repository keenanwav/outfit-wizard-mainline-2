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

# Keep all existing functions below this line
[... rest of the existing functions ...]
