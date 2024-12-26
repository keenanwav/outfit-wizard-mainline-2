import streamlit as st
from outfit_generator import is_valid_image
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
import random
from datetime import datetime, timedelta
import joblib
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import execute_values, execute_batch
from contextlib import contextmanager
import time
from functools import wraps
from typing import Tuple, List, Dict
from concurrent.futures import ThreadPoolExecutor

# Initialize connection pool
MIN_CONNECTIONS = 1
MAX_CONNECTIONS = 20
POOL_TIMEOUT = 30
STATEMENT_TIMEOUT = 30000  # 30 seconds statement timeout

# Statement cache for prepared statements
PREPARED_STATEMENTS = {
    'insert_item': """
        INSERT INTO user_clothing_items 
        (type, color, style, gender, size, image_path, hyperlink, price)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """,
    'update_item': """
        UPDATE user_clothing_items 
        SET color = %s, style = %s, gender = %s, size = %s, hyperlink = %s, price = %s
        WHERE id = %s
        RETURNING id
    """,
    'delete_item': "DELETE FROM user_clothing_items WHERE id = %s",
    'select_items': """
        SELECT id, type, color, style, gender, size, image_path, hyperlink, tags, season, notes, price
        FROM user_clothing_items
        ORDER BY type, created_at DESC
    """
}

def create_connection_pool():
    """Create and return a connection pool with optimized settings and enhanced SSL configuration"""
    try:
        return SimpleConnectionPool(
            MIN_CONNECTIONS,
            MAX_CONNECTIONS,
            host=os.environ['PGHOST'],
            database=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            sslmode='verify-full',
            sslrootcert='system',
            connect_timeout=30,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5,
            options=f'-c statement_timeout={STATEMENT_TIMEOUT}',
            application_name='outfit_wizard',
            tcp_user_timeout=30000,
            client_encoding='UTF8'
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
                    price DECIMAL(10, 2),
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
                    user_id INTEGER,
                    image_path VARCHAR(255),
                    tags TEXT[],
                    season VARCHAR(10),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Add indexes for saved_outfits
            cur.execute('CREATE INDEX IF NOT EXISTS idx_outfit_id ON saved_outfits(outfit_id)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_outfit_tags ON saved_outfits USING gin(tags)')
            
            cur.execute('''
                CREATE TABLE IF NOT EXISTS cleanup_settings (
                    id SERIAL PRIMARY KEY,
                    max_age_hours INT,
                    cleanup_interval_hours INT,
                    batch_size INT,
                    max_workers INT,
                    last_cleanup TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
        finally:
            cur.close()

def retry_on_error(max_retries=3, delay=1):
    """Decorator for retrying database operations with exponential backoff and enhanced error handling"""
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
                    if "SSL connection has been closed unexpectedly" in str(e):
                        logging.error(f"SSL connection error in {func.__name__}: {str(e)}")
                        # Force recreation of connection pool on SSL errors
                        global connection_pool
                        try:
                            connection_pool = create_connection_pool()
                        except Exception as pool_error:
                            logging.error(f"Failed to recreate connection pool: {str(pool_error)}")
                    if attempt < max_retries - 1:
                        sleep_time = delay * (2 ** attempt)  # Exponential backoff
                        jitter = random.uniform(0, 0.1 * sleep_time)  # Add jitter
                        time.sleep(sleep_time + jitter)
                except (psycopg2.InterfaceError, psycopg2.InternalError) as e:
                    last_error = e
                    logging.error(f"Database interface error in {func.__name__}: {str(e)}")
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
            cur.execute("""
                SELECT id, type, color, style, gender, size, image_path, hyperlink, tags, season, notes, price
                FROM user_clothing_items
                ORDER BY type, created_at DESC
            """)
            user_items = cur.fetchall()
            
            columns = ['id', 'type', 'color', 'style', 'gender', 'size', 'image_path', 'hyperlink', 'tags', 'season', 'notes', 'price']
            items_df = pd.DataFrame.from_records(user_items, columns=columns)
            return items_df
        finally:
            cur.close()

@retry_on_error()
def add_user_clothing_item(item_type, color, styles, genders, sizes, image_file, hyperlink="", price=None):
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
        color = get_pants_colors(image_path)
        if color is None:
            return False, "Failed to detect pants color"
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(PREPARED_STATEMENTS['insert_item'], (
                item_type, 
                f"{color[0]},{color[1]},{color[2]}", 
                ','.join(styles),
                ','.join(genders),
                ','.join(sizes),
                image_path,
                hyperlink,
                price
            ))
            new_id = cur.fetchone()[0]
            
            # Record initial price if provided
            if price is not None:
                cur.execute("""
                    INSERT INTO item_price_history (item_id, price)
                    VALUES (%s, %s)
                """, (new_id, price))
            
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
def edit_clothing_item(item_id, color, styles, genders, sizes, hyperlink, price=None):
    """Edit clothing item with prepared statement and price history tracking"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Get current color before update
            cur.execute("SELECT color FROM user_clothing_items WHERE id = %s", (item_id,))
            result = cur.fetchone()
            if result:
                old_color = result[0]
                new_color = f"{color[0]},{color[1]},{color[2]}"
                
                # Record color change if different
                if old_color != new_color:
                    record_color_change(item_id, old_color, new_color)
            
            # Record price change if price is provided and different
            if price is not None:
                record_price_change(item_id, price)
            
            cur.execute(PREPARED_STATEMENTS['update_item'], (
                f"{color[0]},{color[1]},{color[2]}",
                ','.join(styles),
                ','.join(genders),
                ','.join(sizes),
                hyperlink,
                price,
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

def get_user_wardrobe_path(user_id):
    """Get the wardrobe path for a specific user"""
    user_path = os.path.join('wardrobe', f'user_{user_id}')
    if not os.path.exists(user_path):
        os.makedirs(user_path, exist_ok=True)
    return user_path

@retry_on_error()
def save_outfit(outfit):
    """Save outfit with user-specific folder structure"""
    try:
        if 'user' not in st.session_state:
            return None, "User not logged in"
        
        user_id = st.session_state.user['id']
        user_wardrobe = get_user_wardrobe_path(user_id)
        
        outfit_id = str(uuid.uuid4())
        outfit_filename = f"outfit_{outfit_id}.png"
        outfit_path = os.path.join(user_wardrobe, outfit_filename)
        
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
                    INSERT INTO saved_outfits (outfit_id, user_id, image_path)
                    VALUES (%s, %s, %s)
                    RETURNING outfit_id
                """, (outfit_id, user_id, outfit_path))
                
                conn.commit()
                return outfit_path, "Outfit saved successfully"
            finally:
                cur.close()
        
    except Exception as e:
        logging.error(f"Error saving outfit: {str(e)}")
        return None, f"Error saving outfit: {str(e)}"

@retry_on_error()
def load_saved_outfits(user_id: int = None):
    """Load saved outfits with user-specific filtering"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            if user_id:
                cur.execute("""
                    SELECT outfit_id, image_path, tags, season, notes, created_at 
                    FROM saved_outfits 
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
            else:
                cur.execute("""
                    SELECT outfit_id, image_path, tags, season, notes, created_at 
                    FROM saved_outfits 
                    ORDER BY created_at DESC
                """)
            
            outfits = cur.fetchall()
            if outfits:
                return [{
                    'outfit_id': outfit[0],
                    'image_path': outfit[1],
                    'tags': outfit[2] if outfit[2] else [],
                    'season': outfit[3],
                    'notes': outfit[4],
                    'date': outfit[5].strftime("%Y-%m-%d %H:%M:%S")
                } for outfit in outfits]
            return []
        finally:
            cur.close()

@retry_on_error()
def share_outfit(outfit_id: int, shared_by_user_id: int, shared_with_user_id: int) -> Tuple[bool, str]:
    """Share an outfit with another user"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Verify the outfit exists and belongs to the sharing user
            cur.execute("""
                SELECT id FROM saved_outfits 
                WHERE id = %s AND user_id = %s
            """, (outfit_id, shared_by_user_id))
            
            if not cur.fetchone():
                return False, "Outfit not found or you don't have permission to share it"
            
            # Check if outfit is already shared with this user
            cur.execute("""
                SELECT id FROM shared_outfits 
                WHERE outfit_id = %s 
                AND shared_with_user_id = %s
            """, (outfit_id, shared_with_user_id))
            
            if cur.fetchone():
                return False, "Outfit already shared with this user"
            
            # Share the outfit
            cur.execute("""
                INSERT INTO shared_outfits 
                (outfit_id, shared_by_user_id, shared_with_user_id)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (outfit_id, shared_by_user_id, shared_with_user_id))
            
            conn.commit()
            return True, "Outfit shared successfully"
        
    except Exception as e:
        logging.error(f"Error sharing outfit: {str(e)}")
        return False, f"Error sharing outfit: {str(e)}"

@retry_on_error()
def get_shared_outfits(user_id: int) -> List[Dict]:
    """Get outfits shared with the user"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    so.outfit_id,
                    so.shared_by_user_id,
                    u.name as shared_by_name,
                    so.shared_at,
                    s.image_path,
                    s.tags,
                    s.season,
                    s.notes
                FROM shared_outfits so
                JOIN users u ON so.shared_by_user_id = u.id
                JOIN saved_outfits s ON so.outfit_id = s.id
                WHERE so.shared_with_user_id = %s
                ORDER BY so.shared_at DESC
            """, (user_id,))
            
            shared_outfits = cur.fetchall()
            if shared_outfits:
                return [{
                    'outfit_id': outfit[0],
                    'shared_by_user_id': outfit[1],
                    'shared_by_name': outfit[2],
                    'shared_at': outfit[3].strftime("%Y-%m-%d %H:%M:%S"),
                    'image_path': outfit[4],
                    'tags': outfit[5] if outfit[5] else [],
                    'season': outfit[6],
                    'notes': outfit[7]
                } for outfit in shared_outfits]
            return []
        
    except Exception as e:
        logging.error(f"Error getting shared outfits: {str(e)}")
        return []

@retry_on_error()
def remove_shared_outfit(outfit_id: int, shared_by_user_id: int, shared_with_user_id: int) -> Tuple[bool, str]:
    """Remove a shared outfit"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("""
                DELETE FROM shared_outfits 
                WHERE outfit_id = %s 
                AND shared_by_user_id = %s 
                AND shared_with_user_id = %s
                RETURNING id
            """, (outfit_id, shared_by_user_id, shared_with_user_id))
            
            if cur.fetchone():
                conn.commit()
                return True, "Shared outfit removed successfully"
            return False, "Shared outfit not found"
        
    except Exception as e:
        logging.error(f"Error removing shared outfit: {str(e)}")
        return False, f"Error removing shared outfit: {str(e)}"

@retry_on_error()
def get_sharable_users(current_user_id: int) -> List[Dict]:
    """Get list of users that outfits can be shared with"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, name, email 
                FROM users 
                WHERE id != %s
                ORDER BY name
            """, (current_user_id,))
            
            users = cur.fetchall()
            return [{
                'id': user[0],
                'name': user[1],
                'email': user[2]
            } for user in users]
        
    except Exception as e:
        logging.error(f"Error getting sharable users: {str(e)}")
        return []

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


@retry_on_error()
def get_cleanup_settings():
    """Get cleanup settings from database"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM cleanup_settings ORDER BY created_at DESC LIMIT 1")
            result = cur.fetchone()
            
            if result:
                return {
                    'max_age_hours': result[1],
                    'cleanup_interval_hours': result[2],
                    'batch_size': result[3],
                    'max_workers': result[4],
                    'last_cleanup': result[5]
                }
            else:
                # Insert default settings if none exist
                cur.execute("""
                    INSERT INTO cleanup_settings 
                    (max_age_hours, cleanup_interval_hours, batch_size, max_workers)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *
                """, (24, 12, 100, 4))
                
                result = cur.fetchone()
                conn.commit()
                
                return {
                    'max_age_hours': result[1],
                    'cleanup_interval_hours': result[2],
                    'batch_size': result[3],
                    'max_workers': result[4],
                    'last_cleanup': result[5]
                }
        finally:
            cur.close()

@retry_on_error()
def update_last_cleanup_time():
    """Update the last cleanup timestamp"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE cleanup_settings 
                SET last_cleanup = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = (SELECT id FROM cleanup_settings ORDER BY created_at DESC LIMIT 1)
            """)
            conn.commit()
        finally:
            cur.close()

@retry_on_error()
def load_saved_outfits():
    """Load all saved outfits with their details"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT outfit_id, image_path, tags, season, notes, created_at
                FROM saved_outfits
                ORDER BY created_at DESC
            """)
            outfits = cur.fetchall()
            
            return [{
                'outfit_id': outfit[0],
                'image_path': outfit[1],
                'tags': outfit[2] if outfit[2] else [],
                'season': outfit[3],
                'notes': outfit[4],
                'date': outfit[5].strftime("%Y-%m-%d %H:%M:%S") if outfit[5] else None
            } for outfit in outfits]
        finally:
            cur.close()

@retry_on_error()
def cleanup_orphaned_entries():
    """Clean up database entries that have missing or invalid image files"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Get all items with their image paths
            cur.execute("""
                SELECT id, type, image_path 
                FROM user_clothing_items 
                WHERE image_path IS NOT NULL
            """)
            items = cur.fetchall()
            
            orphaned_items = []
            for item_id, item_type, image_path in items:
                # Check if image file exists and is valid
                if not os.path.exists(image_path) or not is_valid_image(image_path):
                    orphaned_items.append((item_id, item_type, image_path))
            
            if orphaned_items:
                # Log orphaned items before processing
                logging.warning(f"Found {len(orphaned_items)} orphaned entries in database")
                for item_id, item_type, path in orphaned_items:
                    logging.info(f"Orphaned {item_type} (ID: {item_id}): {path}")
                
                # Move orphaned entries to audit table for reference
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS orphaned_items_audit (
                        id SERIAL PRIMARY KEY,
                        original_id INTEGER,
                        type VARCHAR(50),
                        image_path VARCHAR(255),
                        removed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert into audit table and mark as orphaned
                execute_values(cur, """
                    INSERT INTO orphaned_items_audit (original_id, type, image_path)
                    VALUES %s
                """, [(id, type, path) for id, type, path in orphaned_items])
                
                # Update main table to mark these items as orphaned
                cur.execute("""
                    UPDATE user_clothing_items 
                    SET image_path = NULL 
                    WHERE id = ANY(%s)
                """, ([item[0] for item in orphaned_items],))
                
                conn.commit()
                return True, f"Processed {len(orphaned_items)} orphaned entries"
            
            return True, "No orphaned entries found"
            
        except Exception as e:
            conn.rollback()
            logging.error(f"Error during orphaned entries cleanup: {str(e)}")
            return False, f"Cleanup failed: {str(e)}"
        finally:
            cur.close()

@retry_on_error()
def get_price_history(item_id):
    """Get price history for an item"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT price, created_at
                FROM item_price_history
                WHERE item_id = %s
                ORDER BY created_at DESC
            """, (item_id,))
            
            history = cur.fetchall()
            return [(float(price), date) for price, date in history] if history else []
        finally:
            cur.close()

@retry_on_error()
def record_price_change(item_id, new_price):
    """Record a price change in history"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Get the current price
            cur.execute("SELECT price FROM user_clothing_items WHERE id = %s", (item_id,))
            current_price = cur.fetchone()
            
            if current_price and current_price[0] != new_price:
                # Record the new price in history
                cur.execute("""
                    INSERT INTO item_price_history (item_id, price)
                    VALUES (%s, %s)
                """, (item_id, new_price))
                conn.commit()
                return True
            return False
        finally:
            cur.close()

@retry_on_error()
def record_color_change(item_id, old_color, new_color):
    """Record a color change in history"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO item_color_history (item_id, old_color, new_color)
                VALUES (%s, %s, %s)
            """, (item_id, old_color, new_color))
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error recording color change: {str(e)}")
            return False
        finally:
            cur.close()

@retry_on_error()
def get_color_history(item_id):
    """Get color history for an item"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT old_color, new_color, changed_at
                FROM item_color_history
                WHERE item_id = %s
                ORDER BY changed_at DESC
            """, (item_id,))
            return cur.fetchall()
        finally:
            cur.close()

@retry_on_error()
def update_item_image(item_id: int, new_image_path: str) -> Tuple[bool, str]:
    """Update the image of an existing clothing item"""
    try:
        # Get the current image path first
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "SELECT image_path FROM user_clothing_items WHERE id = %s",
                    (item_id,)
                )
                result = cur.fetchone()
                if not result:
                    return False, f"Item with ID {item_id} not found"
                
                old_image_path = result[0]
                
                # Generate new image path
                new_filename = f"updated_{uuid.uuid4()}.png"
                final_image_path = os.path.join("user_images", new_filename)
                
                # Save the new image
                with Image.open(new_image_path) as img:
                    img.save(final_image_path)
                
                # Update the database with new image path
                cur.execute(
                    "UPDATE user_clothing_items SET image_path = %s WHERE id = %s",
                    (final_image_path, item_id)
                )
                
                conn.commit()
                
                # Delete the old image if it exists
                if old_image_path and os.path.exists(old_image_path):
                    try:
                        os.remove(old_image_path)
                    except Exception as e:
                        logging.warning(f"Failed to delete old image {old_image_path}: {str(e)}")
                
                # Delete the temporary uploaded image
                if os.path.exists(new_image_path):
                    try:
                        os.remove(new_image_path)
                    except Exception as e:
                        logging.warning(f"Failed to delete temporary image {new_image_path}: {str(e)}")
                
                return True, "Image updated successfully"
                
            finally:
                cur.close()
                
    except Exception as e:
        logging.error(f"Error updating item image: {str(e)}")
        return False, f"Failed to update image: {str(e)}"

@retry_on_error()
def get_price_history(item_id):
    """Get price history for an item"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT price, created_at
                FROM item_price_history
                WHERE item_id = %s
                ORDER BY created_at DESC
            """, (item_id,))
            
            history = cur.fetchall()
            return [(float(price), date) for price, date in history] if history else []
        finally:
            cur.close()

@retry_on_error()
def get_cleanup_settings():
    """Get cleanup settings from database"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM cleanup_settings ORDER BY created_at DESC LIMIT 1")
            result = cur.fetchone()
            
            if result:
                return {
                    'max_age_hours': result[1],
                    'cleanup_interval_hours': result[2],
                    'batch_size': result[3],
                    'max_workers': result[4],
                    'last_cleanup': result[5]
                }
            else:
                # Insert default settings if none exist
                cur.execute("""
                    INSERT INTO cleanup_settings 
                    (max_age_hours, cleanup_interval_hours, batch_size, max_workers)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *
                """, (24, 12, 100, 4))
                
                result = cur.fetchone()
                conn.commit()
                
                return {
                    'max_age_hours': result[1],
                    'cleanup_interval_hours': result[2],
                    'batch_size': result[3],
                    'max_workers': result[4],
                    'last_cleanup': result[5]
                }
        finally:
            cur.close()

@retry_on_error()
def update_last_cleanup_time():
    """Update the last cleanup timestamp"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE cleanup_settings 
                SET last_cleanup = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = (SELECT id FROM cleanup_settings ORDER BY created_at DESC LIMIT 1)
            """)
            conn.commit()
        finally:
            cur.close()

@retry_on_error()
def load_saved_outfits():
    """Load all saved outfits with their details"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT outfit_id, image_path, tags, season, notes, created_at
                FROM saved_outfits
                ORDER BY created_at DESC
            """)
            outfits = cur.fetchall()
            
            return [{
                'outfit_id': outfit[0],
                'image_path': outfit[1],
                'tags': outfit[2] if outfit[2] else [],
                'season': outfit[3],
                'notes': outfit[4],
                'date': outfit[5].strftime("%Y-%m-%d %H:%M:%S") if outfit[5] else None
            } for outfit in outfits]
        finally:
            cur.close()

@retry_on_error()
def cleanup_orphaned_entries():
    """Clean up database entries that have missing or invalid image files"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Get all items with their image paths
            cur.execute("""
                SELECT id, type, image_path 
                FROM user_clothing_items 
                WHERE image_path IS NOT NULL
            """)
            items = cur.fetchall()
            
            orphaned_items = []
            for item_id, item_type, image_path in items:
                # Check if image file exists and is valid
                if not os.path.exists(image_path) or not is_valid_image(image_path):
                    orphaned_items.append((item_id, item_type, image_path))
            
            if orphaned_items:
                # Log orphaned items before processing
                logging.warning(f"Found {len(orphaned_items)} orphaned entries in database")
                for item_id, item_type, path in orphaned_items:
                    logging.info(f"Orphaned {item_type} (ID: {item_id}): {path}")
                
                # Move orphaned entries to audit table for reference
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS orphaned_items_audit (
                        id SERIAL PRIMARY KEY,
                        original_id INTEGER,
                        type VARCHAR(50),
                        image_path VARCHAR(255),
                        removed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert into audit table and mark as orphaned
                execute_values(cur, """
                    INSERT INTO orphaned_items_audit (original_id, type, image_path)
                    VALUES %s
                """, [(id, type, path) for id, type, path in orphaned_items])
                
                # Update main table to mark these items as orphaned
                cur.execute("""
                    UPDATE user_clothing_items 
                    SET image_path = NULL 
                    WHERE id = ANY(%s)
                """, ([item[0] for item in orphaned_items],))
                
                conn.commit()
                return True, f"Processed {len(orphaned_items)} orphaned entries"
            
            return True, "No orphaned entries found"
            
        except Exception as e:
            conn.rollback()
            logging.error(f"Error during orphaned entries cleanup: {str(e)}")
            return False, f"Cleanup failed: {str(e)}"
        finally:
            cur.close()

@retry_on_error()
def get_price_history(item_id):
    """Get price history for an item"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT price, created_at
                FROM item_price_history
                WHERE item_id = %s
                ORDER BY created_at DESC
            """, (item_id,))
            
            history = cur.fetchall()
            return [(float(price), date) for price, date in history] if history else []
        finally:
            cur.close()

@retry_on_error()
def get_cleanup_settings():
    """Get cleanup settings from database"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM cleanup_settings ORDER BY created_at DESC LIMIT 1")
            result = cur.fetchone()
            
            if result:
                return {
                    'max_age_hours': result[1],
                    'cleanup_interval_hours': result[2],
                    'batch_size': result[3],
                    'max_workers': result[4],
                    'last_cleanup': result[5]
                }
            else:
                # Insert default settings if none exist
                cur.execute("""
                    INSERT INTO cleanup_settings 
                    (max_age_hours, cleanup_interval_hours, batch_size, max_workers)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *
                """, (24, 12, 100, 4))
                
                result = cur.fetchone()
                conn.commit()
                
                return {
                    'max_age_hours': result[1],
                    'cleanup_interval_hours': result[2],
                    'batch_size': result[3],
                    'max_workers': result[4],
                    'last_cleanup': result[5]
                }
        finally:
            cur.close()

@retry_on_error()
def update_last_cleanup_time():
    """Update the last cleanup timestamp"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE cleanup_settings 
                SET last_cleanup = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = (SELECT id FROM cleanup_settings ORDER BY created_at DESC LIMIT 1)
            """)
            conn.commit()
        finally:
            cur.close()

@retry_on_error()
def load_saved_outfits():
    """Load all saved outfits with their details"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT outfit_id, image_path, tags, season, notes, created_at
                FROM saved_outfits
                ORDER BY created_at DESC
            """)
            outfits = cur.fetchall()
            
            return [{
                'outfit_id': outfit[0],
                'image_path': outfit[1],
                'tags': outfit[2] if outfit[2] else [],
                'season': outfit[3],
                'notes': outfit[4],
                'date': outfit[5].strftime("%Y-%m-%d %H:%M:%S") if outfit[5] else None
            } for outfit in outfits]
        finally:
            cur.close()

@retry_on_error()
def cleanup_orphaned_entries():
    """Clean up database entries that have missing or invalid image files"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Get all items with their image paths
            cur.execute("""
                SELECT id, type, image_path 
                FROM user_clothing_items 
                WHERE image_path IS NOT NULL
            """)
            items = cur.fetchall()
            
            orphaned_items = []
            for item_id, item_type, image_path in items:
                # Check if image file exists and is valid
                if not os.path.exists(image_path) or not is_valid_image(image_path):
                    orphaned_items.append((item_id, item_type, image_path))
            
            if orphaned_items:
                # Log orphaned items before processing
                logging.warning(f"Found {len(orphaned_items)} orphaned entries in database")
                for item_id, item_type, path in orphaned_items:
                    logging.info(f"Orphaned {item_type} (ID: {item_id}): {path}")
                
                # Move orphaned entries to audit table for reference
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS orphaned_items_audit (
                        id SERIAL PRIMARY KEY,
                        original_id INTEGER,
                        type VARCHAR(50),
                        image_path VARCHAR(255),
                        removed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert into audit table and mark as orphaned
                execute_values(cur, """
                    INSERT INTO orphaned_items_audit (original_id, type, image_path)
                    VALUES %s
                """, [(id, type, path) for id, type, path in orphaned_items])
                
                # Update main table to mark these items as orphaned
                cur.execute("""
                    UPDATE user_clothing_items 
                    SET image_path = NULL 
                    WHERE id = ANY(%s)
                """, ([item[0] for item in orphaned_items],))
                
                conn.commit()
                return True, f"Processed {len(orphaned_items)} orphaned entries"
            
            return True, "No orphaned entries found"
            
        except Exception as e:
            conn.rollback()
            logging.error(f"Error during orphaned entries cleanup: {str(e)}")
            return False, f"Cleanup failed: {str(e)}"
        finally:
            cur.close()

@retry_on_error()
def bulk_delete_items(item_ids: List[int]) -> Tuple[bool, str, Dict]:
    """Delete multiple clothing items in bulk with their associated files

    Args:
        item_ids: List of item IDs to delete

    Returns:
        Tuple containing:
        - Success status (bool)
        - Status message (str)
        - Statistics dictionary with counts of successes and failures
    """
    if not item_ids:
        return True, "No items to delete", {"deleted": 0, "failed": 0}

    stats = {
        "deleted": 0,
        "failed": 0,
        "errors": []
    }

    # Process deletions in batches using thread pool
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Split into reasonable batch sizes
        batch_size = 10
        batches = [item_ids[i:i + batch_size] for i in range(0, len(item_ids), batch_size)]

        # Process each batch
        for batch in batches:
            try:
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    try:
                        # Get image paths for the batch
                        placeholders = ','.join(['%s'] * len(batch))
                        cur.execute(f"""
                            SELECT id, image_path 
                            FROM user_clothing_items 
                            WHERE id IN ({placeholders})
                        """, tuple(batch))
                        items = cur.fetchall()

                        for item_id, image_path in items:
                            try:
                                # Delete the image file if it exists
                                if image_path and os.path.exists(image_path):
                                    os.remove(image_path)

                                # Delete from database
                                cur.execute("""
                                    DELETE FROM user_clothing_items 
                                    WHERE id = %s
                                """, (item_id,))

                                stats["deleted"] += 1
                                logging.info(f"Successfully deleted item {item_id}")

                            except Exception as e:
                                stats["failed"] += 1
                                error_msg = f"Failed to delete item {item_id}: {str(e)}"
                                stats["errors"].append(error_msg)
                                logging.error(error_msg)

                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        raise
                    finally:
                        cur.close()

            except Exception as e:
                batch_error = f"Batch processing error: {str(e)}"
                stats["errors"].append(batch_error)
                logging.error(batch_error)
                stats["failed"] += len(batch)

    # Prepare result message
    message = f"Deleted {stats['deleted']} items"
    if stats["failed"] > 0:
        message += f", {stats['failed']} failed"

    success = stats["failed"] == 0

    if stats["errors"]:
        logging.warning("Bulk delete errors:\n" + "\n".join(stats["errors"]))

    return success, message, stats