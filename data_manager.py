# Global connection pool
connection_pool = None

import logging
import os
from PIL import Image
import uuid
from datetime import datetime, timedelta
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import execute_values, execute_batch
from contextlib import contextmanager
import time
from functools import wraps
from typing import Tuple, Optional, Dict, Any, List
import random

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_manager')

try:
    import pandas as pd
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler
    from sklearn.decomposition import TruncatedSVD
    from scipy.sparse import csr_matrix
    from sklearn.neighbors import NearestNeighbors
    import joblib
except ImportError as e:
    logger.error(f"Error importing scientific computing libraries: {str(e)}")
    pass

# Initialize connection pool settings
MIN_CONNECTIONS = 1
MAX_CONNECTIONS = 10
POOL_TIMEOUT = 30
STATEMENT_TIMEOUT = 30000  # 30 seconds statement timeout

def validate_connection(conn) -> bool:
    """Validate database connection is still alive and usable"""
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
            result = cur.fetchone()
            return result is not None and result[0] == 1
    except Exception as e:
        logger.error(f"Connection validation failed: {str(e)}")
        return False

def create_connection_pool():
    """Create and return a connection pool with optimized settings"""
    logger.info("Attempting to create new connection pool")
    try:
        pool = SimpleConnectionPool(
            MIN_CONNECTIONS,
            MAX_CONNECTIONS,
            host=os.environ.get('PGHOST'),
            database=os.environ.get('PGDATABASE'),
            user=os.environ.get('PGUSER'),
            password=os.environ.get('PGPASSWORD'),
            sslmode='require',
            connect_timeout=10,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5,
            options=f'-c statement_timeout={STATEMENT_TIMEOUT}',
            application_name='outfit_wizard',
            client_encoding='UTF8'
        )
        logger.info("Successfully created new connection pool")
        return pool
    except Exception as e:
        logger.error(f"Failed to create connection pool: {str(e)}")
        raise

def get_connection_pool():
    """Get or create connection pool with retry logic"""
    global connection_pool
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            if not connection_pool:
                logger.info(f"Initializing connection pool (attempt {attempt + 1}/{max_retries})")
                connection_pool = create_connection_pool()
            return connection_pool
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to create connection pool after {max_retries} attempts: {str(e)}")
                raise
            logger.warning(f"Connection pool creation failed (attempt {attempt + 1}): {str(e)}")
            time.sleep(retry_delay * (2 ** attempt))

@contextmanager
def get_db_connection():
    """Context manager for database connections with enhanced error handling and validation"""
    conn = None
    pool = None
    try:
        pool = get_connection_pool()
        conn = pool.getconn()
        logger.debug("Retrieved connection from pool")

        # Validate connection before use
        if not validate_connection(conn):
            logger.error("Retrieved invalid connection from pool")
            raise psycopg2.OperationalError("Invalid connection from pool")

        conn.set_session(autocommit=False)
        yield conn
    except psycopg2.OperationalError as e:
        if conn:
            logger.error(f"Database operational error with connection: {str(e)}")
            conn.close()
        if "SSL connection has been closed unexpectedly" in str(e):
            logger.warning("SSL connection error detected, recreating pool")
            global connection_pool
            connection_pool = None
        raise
    except Exception as e:
        logger.error(f"Unexpected database error: {str(e)}")
        raise
    finally:
        if conn:
            try:
                conn.rollback()
                logger.debug("Connection rollback completed")
            except Exception as e:
                logger.error(f"Error during connection rollback: {str(e)}")
            try:
                if pool:
                    pool.putconn(conn)
                    logger.debug("Connection returned to pool")
            except Exception as e:
                logger.error(f"Error returning connection to pool: {str(e)}")
                conn.close()

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
                        logger.error(f"Statement timeout in {func.__name__}: {str(e)}")
                        raise
                    if "SSL connection has been closed unexpectedly" in str(e):
                        logger.error(f"SSL connection error in {func.__name__}: {str(e)}")
                        # Force recreation of connection pool on SSL errors
                        global connection_pool
                        try:
                            connection_pool = create_connection_pool()
                        except Exception as pool_error:
                            logger.error(f"Failed to recreate connection pool: {str(pool_error)}")
                    if attempt < max_retries - 1:
                        sleep_time = delay * (2 ** attempt)  # Exponential backoff
                        jitter = random.uniform(0, 0.1 * sleep_time)  # Add jitter
                        time.sleep(sleep_time + jitter)
                except (psycopg2.InterfaceError, psycopg2.InternalError) as e:
                    last_error = e
                    logger.error(f"Database interface error in {func.__name__}: {str(e)}")
                    if attempt < max_retries - 1:
                        sleep_time = delay * (2 ** attempt)
                        time.sleep(sleep_time)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        sleep_time = delay * (2 ** attempt)
                        time.sleep(sleep_time)
            logger.error(f"Operation failed after {max_retries} attempts: {str(last_error)}")
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
        logger.error(f"Error saving outfit: {str(e)}")
        return None

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
def update_cleanup_settings(max_age_hours=None, cleanup_interval_hours=None, 
                          batch_size=None, max_workers=None):
    """Update cleanup configuration settings"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            update_fields = []
            params = []
            
            if max_age_hours is not None:
                update_fields.append("max_age_hours = %s")
                params.append(max_age_hours)
            
            if cleanup_interval_hours is not None:
                update_fields.append("cleanup_interval_hours = %s")
                params.append(cleanup_interval_hours)
            
            if batch_size is not None:
                update_fields.append("batch_size = %s")
                params.append(batch_size)
            
            if max_workers is not None:
                update_fields.append("max_workers = %s")
                params.append(max_workers)
            
            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                query = f"""
                    UPDATE cleanup_settings 
                    SET {', '.join(update_fields)}
                    WHERE id = (SELECT id FROM cleanup_settings ORDER BY created_at DESC LIMIT 1)
                    RETURNING id
                """
                cur.execute(query, params)
                
                if cur.fetchone():
                    conn.commit()
                    return True, "Cleanup settings updated successfully"
                return False, "Failed to update cleanup settings"
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
def get_cleanup_statistics():
    """Get cleanup statistics from the database"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Get cleanup settings
            cur.execute("""
                SELECT max_age_hours, cleanup_interval_hours, batch_size, 
                       max_workers, last_cleanup 
                FROM cleanup_settings 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            settings = cur.fetchone()
            
            if not settings:
                return None
            
            # Get total files in merged_outfits
            total_files = 0
            if os.path.exists('merged_outfits'):
                total_files = len(os.listdir('merged_outfits'))
            
            # Get saved outfits count
            cur.execute("SELECT COUNT(*) FROM saved_outfits")
            saved_count = cur.fetchone()[0]
            
            return {
                'settings': {
                    'max_age_hours': settings[0],
                    'cleanup_interval_hours': settings[1],
                    'batch_size': settings[2],
                    'max_workers': settings[3],
                    'last_cleanup': settings[4]
                },
                'statistics': {
                    'total_files': total_files,
                    'saved_outfits': saved_count,
                    'temporary_files': max(0, total_files - saved_count)
                }
            }
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
            logger.error(f"Error recording color change: {str(e)}")
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
                        logger.warning(f"Failed to delete old image {old_image_path}: {str(e)}")
                
                # Delete the temporary uploaded image
                if os.path.exists(new_image_path):
                    try:
                        os.remove(new_image_path)
                    except Exception as e:
                        logger.warning(f"Failed to delete temporary image {new_image_path}: {str(e)}")
                
                return True, "Image updated successfully"
                
            finally:
                cur.close()
                
    except Exception as e:
        logger.error(f"Error updating item image: {str(e)}")
        return False, f"Failed to update image: {str(e)}"

@retry_on_error()
def add_user_clothing_item(item_type, color, styles, genders, sizes, image_file, hyperlink="", price=None):
    """Add clothing item with prepared statement and initial price history"""
    if not os.path.exists("user_images"):
        os.makedirs("user_images", exist_ok=True)
    
    image_filename = f"{item_type}_{uuid.uuid4()}.png"
    image_path = os.path.join("user_images", image_filename)
    
    with Image.open(image_file) as img:
        img.save(image_path)
    
    # Use item-specific color detection
    if item_type == 'pants':
        from color_utils import get_pants_colors
        color =get_pants_colors(image_path)
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
def get_price_history(item_id):
    """Get price history for an item"""
    with get_db_connection() as conn:
        cur =conn.cursor()
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
                logger.warning(f"Found {len(orphaned_items)} orphaned entries in database")
                for item_id, item_type, path in orphaned_items:
                    logger.info(f"Orphaned {item_type} (ID: {item_id}): {path}")
                
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
            logger.error(f"Error during orphaned entries cleanup: {str(e)}")
            return False, f"Cleanup failed: {str(e)}"
        finally:
            cur.close()