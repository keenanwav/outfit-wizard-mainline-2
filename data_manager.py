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
            type VARCHAR(50),
            color VARCHAR(50),
            style VARCHAR(255),
            gender VARCHAR(50),
            size VARCHAR(50),
            image_path VARCHAR(255),
            hyperlink VARCHAR(255),
            tags TEXT[],
            season VARCHAR(10),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS saved_outfits (
            id SERIAL PRIMARY KEY,
            outfit_id VARCHAR(50),
            image_path VARCHAR(255),
            tags TEXT[],
            season VARCHAR(10),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()

def load_clothing_items():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, type, color, style, gender, size, image_path, hyperlink, tags, season, notes
        FROM user_clothing_items
    """)
    user_items = cur.fetchall()
    cur.close()
    conn.close()

    columns = ['id', 'type', 'color', 'style', 'gender', 'size', 'image_path', 'hyperlink', 'tags', 'season', 'notes']
    items_df = pd.DataFrame(user_items, columns=columns)
    return items_df

def add_user_clothing_item(item_type, color, styles, genders, sizes, image_file, hyperlink=""):
    if not os.path.exists("user_images"):
        os.makedirs("user_images", exist_ok=True)
    
    image_filename = f"{item_type}_{uuid.uuid4()}.png"
    image_path = os.path.join("user_images", image_filename)
    
    with Image.open(image_file) as img:
        img.save(image_path)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO user_clothing_items 
            (type, color, style, gender, size, image_path, hyperlink)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
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

def update_outfit_details(outfit_id, tags=None, season=None, notes=None):
    """Update outfit organization details"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        update_fields = []
        params = []
        
        if tags is not None:
            update_fields.append("tags = %s")
            params.append(tags)
        
        if season is not None:
            update_fields.append("season = %s")
            params.append(season)
            
        if notes is not None:
            update_fields.append("notes = %s")
            params.append(notes)
            
        if update_fields:
            params.append(outfit_id)
            query = f"""
                UPDATE saved_outfits 
                SET {', '.join(update_fields)}
                WHERE outfit_id = %s
                RETURNING outfit_id
            """
            cur.execute(query, params)
            
            if cur.fetchone():
                conn.commit()
                return True, f"Outfit {outfit_id} updated successfully"
            return False, f"Outfit {outfit_id} not found"
            
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()

def get_outfit_details(outfit_id):
    """Get outfit organization details"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT outfit_id, tags, season, notes, image_path, created_at
            FROM saved_outfits 
            WHERE outfit_id = %s
        """, (outfit_id,))
        
        result = cur.fetchone()
        if result:
            return {
                'outfit_id': result[0],
                'tags': result[1] if result[1] else [],
                'season': result[2],
                'notes': result[3],
                'image_path': result[4],
                'date': result[5].strftime("%Y-%m-%d %H:%M:%S") if result[5] else None
            }
        return None
        
    finally:
        cur.close()
        conn.close()

def update_item_details(item_id, tags=None, season=None, notes=None):
    """Update item organization details"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        update_fields = []
        params = []
        
        if tags is not None:
            update_fields.append("tags = %s")
            params.append(tags)
        
        if season is not None:
            update_fields.append("season = %s")
            params.append(season)
            
        if notes is not None:
            update_fields.append("notes = %s")
            params.append(notes)
            
        if update_fields:
            params.append(int(item_id) if isinstance(item_id, (np.int64, np.integer)) else item_id)
            query = f"""
                UPDATE user_clothing_items 
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id
            """
            cur.execute(query, params)
            
            if cur.fetchone():
                conn.commit()
                return True, f"Item {item_id} updated successfully"
            return False, f"Item {item_id} not found"
            
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
            int(item_id) if isinstance(item_id, (np.int64, np.integer)) else item_id
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
        item_id = int(item_id) if isinstance(item_id, (np.int64, np.integer)) else item_id
        
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

def save_outfit(outfit):
    """Save outfit to wardrobe and database with enhanced error handling"""
    try:
        if not os.path.exists('wardrobe'):
            os.makedirs('wardrobe')
        
        outfit_id = str(uuid.uuid4())
        outfit_filename = f"outfit_{outfit_id}.png"
        outfit_path = os.path.join('wardrobe', outfit_filename)
        
        # Save the outfit image
        try:
            if 'merged_image_path' in outfit and os.path.exists(outfit['merged_image_path']):
                Image.open(outfit['merged_image_path']).save(outfit_path)
            else:
                total_width = 600
                height = 200
                outfit_img = Image.new('RGB', (total_width, height), (255, 255, 255))
                
                for i, item_type in enumerate(['shirt', 'pants', 'shoes']):
                    if item_type in outfit:
                        item_img = Image.open(outfit[item_type]['image_path'])
                        item_img = item_img.resize((200, 200))
                        outfit_img.paste(item_img, (i * 200, 0))
                
                outfit_img.save(outfit_path)
        except Exception as e:
            logging.error(f"Error saving outfit image: {str(e)}")
            return None, False
        
        # Save to database
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO saved_outfits (outfit_id, image_path)
                VALUES (%s, %s)
                RETURNING outfit_id
            """, (outfit_id, outfit_path))
            
            conn.commit()
            return outfit_path, True
            
        except Exception as e:
            conn.rollback()
            logging.error(f"Database error saving outfit: {str(e)}")
            if os.path.exists(outfit_path):
                os.remove(outfit_path)  # Clean up the saved image if database operation fails
            return None, False
        finally:
            cur.close()
            conn.close()
            
    except Exception as e:
        logging.error(f"Error in save_outfit: {str(e)}")
        return None, False

def load_saved_outfits():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT outfit_id, image_path, tags, season, notes, created_at 
            FROM saved_outfits 
            ORDER BY created_at DESC
        """)
        
        outfits = cur.fetchall()
        if outfits:
            return [
                {
                    'outfit_id': outfit[0],
                    'image_path': outfit[1],
                    'tags': outfit[2] if outfit[2] else [],
                    'season': outfit[3],
                    'notes': outfit[4],
                    'date': outfit[5].strftime("%Y-%m-%d %H:%M:%S")
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

def delete_saved_outfit(outfit_id):
    """Delete a saved outfit and its associated image"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get the image path before deleting
        cur.execute("SELECT image_path FROM saved_outfits WHERE outfit_id = %s", (outfit_id,))
        outfit = cur.fetchone()
        
        if outfit and outfit[0]:
            image_path = outfit[0]
            # Delete from database
            cur.execute("DELETE FROM saved_outfits WHERE outfit_id = %s", (outfit_id,))
            conn.commit()
            
            # Delete image file if it exists
            if os.path.exists(image_path):
                os.remove(image_path)
            
            return True, f"Outfit {outfit_id} deleted successfully"
        return False, f"Outfit {outfit_id} not found"
        
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()
