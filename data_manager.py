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
from datetime import datetime, timedelta
import joblib
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import execute_values, execute_batch
from contextlib import contextmanager
import time
from functools import wraps

# Initialize connection pool
MIN_CONNECTIONS = 1
MAX_CONNECTIONS = 20
POOL_TIMEOUT = 30
STATEMENT_TIMEOUT = 30000  # 30 seconds statement timeout

# Statement cache for prepared statements
PREPARED_STATEMENTS = {
    'insert_item': """
        INSERT INTO user_clothing_items 
        (type, color, style, gender, size, image_path, hyperlink)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """,
    'update_item': """
        UPDATE user_clothing_items 
        SET color = %s, style = %s, gender = %s, size = %s, hyperlink = %s
        WHERE id = %s
        RETURNING id
    """,
    'delete_item': "DELETE FROM user_clothing_items WHERE id = %s",
    'select_items': """
        SELECT id, type, color, style, gender, size, image_path, hyperlink, tags, season, notes
        FROM user_clothing_items
        ORDER BY type, created_at DESC
    """
}

def create_connection_pool():
    """Create and return a connection pool with optimized settings"""
    try:
        return SimpleConnectionPool(
            MIN_CONNECTIONS,
            MAX_CONNECTIONS,
            host=os.environ['PGHOST'],
            database=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5,
            options=f'-c statement_timeout={STATEMENT_TIMEOUT}'
        )
    except Exception as e:
        logging.error(f"Error creating connection pool: {str(e)}")
        raise

# Create the connection pool
connection_pool = create_connection_pool()

@contextmanager
def get_db_connection():
    """Context manager for handling database connections from the pool with timeout"""
    conn = None
    try:
        conn = connection_pool.getconn()
        if conn:
            conn.set_session(autocommit=False)  # Explicit transaction control
            yield conn
    except psycopg2.OperationalError as e:
        logging.error(f"Database connection timeout: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Database connection error: {str(e)}")
        raise
    finally:
        if conn:
            try:
                conn.rollback()  # Ensure no hanging transactions
            except Exception:
                pass
            connection_pool.putconn(conn)

def create_user_items_table():
    """Create necessary database tables with indexes"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Create tables with proper indexes
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
            
            # Add indexes for frequently queried columns
            cur.execute('CREATE INDEX IF NOT EXISTS idx_type ON user_clothing_items(type)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_style ON user_clothing_items(style)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_tags ON user_clothing_items USING gin(tags)')
            
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
            
            # Add indexes for saved_outfits
            cur.execute('CREATE INDEX IF NOT EXISTS idx_outfit_id ON saved_outfits(outfit_id)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_outfit_tags ON saved_outfits USING gin(tags)')
            
            conn.commit()
        finally:
            cur.close()

def retry_on_error(max_retries=3, delay=1):
    """Decorator for retrying database operations with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except psycopg2.OperationalError as e:
                    last_error = e
                    if "statement timeout" in str(e):
                        logging.error(f"Statement timeout in {func.__name__}: {str(e)}")
                        raise
                    if attempt < max_retries - 1:
                        sleep_time = delay * (2 ** attempt)
                        time.sleep(sleep_time)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        sleep_time = delay * (2 ** attempt)
                        time.sleep(sleep_time)
            logging.error(f"Operation failed after {max_retries} attempts: {str(last_error)}")
            if last_error:
                raise last_error
            raise Exception("Operation failed with unknown error")
        return wrapper
    return decorator

@retry_on_error()
def load_clothing_items():
    """Load clothing items with optimized query"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(PREPARED_STATEMENTS['select_items'])
            user_items = cur.fetchall()
            
            columns = ['id', 'type', 'color', 'style', 'gender', 'size', 'image_path', 'hyperlink', 'tags', 'season', 'notes']
            items_df = pd.DataFrame.from_records(user_items, columns=columns)
            return items_df
        finally:
            cur.close()

@retry_on_error()
def add_user_clothing_item(item_type, color, styles, genders, sizes, image_file, hyperlink=""):
    """Add clothing item with prepared statement and improved color detection"""
    if not os.path.exists("user_images"):
        os.makedirs("user_images", exist_ok=True)
    
    image_filename = f"{item_type}_{uuid.uuid4()}.png"
    image_path = os.path.join("user_images", image_filename)
    
    with Image.open(image_file) as img:
        img.save(image_path)
    
    # Use item-specific color detection
    if item_type == 'pants':
        from color_utils import get_pants_colors
        colors = get_pants_colors(image_path)
        if colors is None:
            return False, "Failed to detect pants color"
        # Convert multiple colors to string format
        color_str = '[' + '],['.join(','.join(map(str, c)) for c in colors) + ']'
    else:
        color_str = f"{color[0]},{color[1]},{color[2]}"
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(PREPARED_STATEMENTS['insert_item'], (
                item_type, 
                color_str,
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

@retry_on_error()
def update_outfit_details(outfit_id, tags=None, season=None, notes=None):
    """Update outfit details with optimized query"""
    with get_db_connection() as conn:
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
        finally:
            cur.close()

@retry_on_error()
def get_outfit_details(outfit_id):
    """Get outfit details with prepared statement"""
    with get_db_connection() as conn:
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

@retry_on_error()
def update_item_details(item_id, tags=None, season=None, notes=None):
    """Update item details with optimized query"""
    with get_db_connection() as conn:
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
                params.append(int(item_id) if hasattr(item_id, 'item') else item_id)
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
        finally:
            cur.close()

@retry_on_error()
def edit_clothing_item(item_id, color, styles, genders, sizes, hyperlink):
    """Edit clothing item with prepared statement"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(PREPARED_STATEMENTS['update_item'], (
                f"{color[0]},{color[1]},{color[2]}",
                ','.join(styles),
                ','.join(genders),
                ','.join(sizes),
                hyperlink,
                int(item_id) if hasattr(item_id, 'item') else item_id
            ))
            
            if cur.fetchone():
                conn.commit()
                return True, f"Item with ID {item_id} updated successfully"
            return False, f"Item with ID {item_id} not found"
        finally:
            cur.close()

@retry_on_error()
def delete_clothing_item(item_id):
    """Delete clothing item with prepared statement"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            item_id = int(item_id) if hasattr(item_id, 'item') else item_id
            
            cur.execute("SELECT image_path FROM user_clothing_items WHERE id = %s", (item_id,))
            item = cur.fetchone()
            
            if item and item[0]:
                if os.path.exists(item[0]):
                    os.remove(item[0])
                
                cur.execute(PREPARED_STATEMENTS['delete_item'], (item_id,))
                conn.commit()
                return True, f"Item with ID {item_id} deleted successfully"
            
            return False, f"Item with ID {item_id} not found"
        finally:
            cur.close()

@retry_on_error()
def save_outfit(outfit):
    """Save outfit with optimized file handling and database operations"""
    try:
        if not os.path.exists('wardrobe'):
            os.makedirs('wardrobe')
        
        outfit_id = str(uuid.uuid4())
        outfit_filename = f"outfit_{outfit_id}.png"
        outfit_path = os.path.join('wardrobe', outfit_filename)
        
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
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    INSERT INTO saved_outfits (outfit_id, image_path)
                    VALUES (%s, %s)
                    RETURNING outfit_id
                """, (outfit_id, outfit_path))
                
                conn.commit()
                return outfit_path
            finally:
                cur.close()
                
    except Exception as e:
        logging.error(f"Error saving outfit: {str(e)}")
        return None

@retry_on_error()
def load_saved_outfits():
    """Load saved outfits with optimized query"""
    with get_db_connection() as conn:
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
        finally:
            cur.close()

@retry_on_error()
def delete_saved_outfit(outfit_id):
    """Delete saved outfit with prepared statement"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT image_path FROM saved_outfits WHERE outfit_id = %s", (outfit_id,))
            outfit = cur.fetchone()
            
            if outfit and outfit[0]:
                image_path = outfit[0]
                cur.execute("DELETE FROM saved_outfits WHERE outfit_id = %s", (outfit_id,))
                conn.commit()
                
                if os.path.exists(image_path):
                    os.remove(image_path)
                
                return True, f"Outfit {outfit_id} deleted successfully"
            return False, f"Outfit {outfit_id} not found"
        finally:
            cur.close()