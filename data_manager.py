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

def create_connection_pool():
    """Create and return a connection pool"""
    try:
        return SimpleConnectionPool(
            MIN_CONNECTIONS,
            MAX_CONNECTIONS,
            host=os.environ['PGHOST'],
            database=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD']
        )
    except Exception as e:
        logging.error(f"Error creating connection pool: {str(e)}")
        raise

# Create the connection pool
try:
    connection_pool = create_connection_pool()
except Exception as e:
    logging.error(f"Failed to create initial connection pool: {str(e)}")
    connection_pool = None

def get_pool_status():
    """Get current status of the connection pool"""
    if connection_pool:
        try:
            # Use direct pool access for performance
            used_count = sum(1 for conn in connection_pool._pool if not conn.closed)
            return {
                'min_connections': MIN_CONNECTIONS,
                'max_connections': MAX_CONNECTIONS,
                'used_connections': used_count,
                'free_connections': MAX_CONNECTIONS - used_count
            }
        except Exception as e:
            logging.error(f"Error getting pool status: {str(e)}")
    return None

@contextmanager
def get_db_connection():
    """Context manager for handling database connections from the pool"""
    conn = None
    try:
        if not connection_pool:
            raise Exception("Database connection pool not initialized")
        conn = connection_pool.getconn()
        yield conn
    except Exception as e:
        logging.error(f"Database connection error: {str(e)}")
        raise
    finally:
        if conn:
            try:
                connection_pool.putconn(conn)
            except Exception as e:
                logging.error(f"Error returning connection to pool: {str(e)}")

def retry_on_error(max_retries=3, delay=1):
    """Decorator for retrying database operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt == max_retries - 1:
                        logging.error(f"Operation failed after {max_retries} attempts: {str(e)}")
                        raise
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return None
        return wrapper
    return decorator

def is_numpy_integer(value):
    """Helper function to check if a value is a numpy integer"""
    return hasattr(value, 'dtype') and np.issubdtype(value.dtype, np.integer)

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

@retry_on_error()
def load_clothing_items():
    """Load clothing items with optimized query and connection pooling"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute('''
                SELECT id, type, color, style, gender, size, image_path, hyperlink, 
                       tags, season, notes
                FROM user_clothing_items
                ORDER BY type, created_at DESC
            ''')
            columns = ['id', 'type', 'color', 'style', 'gender', 'size', 
                      'image_path', 'hyperlink', 'tags', 'season', 'notes']
            data = cur.fetchall()
            df = pd.DataFrame(data, columns=columns)
            return df
        finally:
            cur.close()
    return pd.DataFrame()

@retry_on_error()
def save_outfit(outfit_data):
    """Save outfit to database and copy image to permanent storage"""
    try:
        # Generate a unique outfit ID
        outfit_id = str(uuid.uuid4())
        
        # Copy merged image to a permanent location if it exists
        image_path = outfit_data.get('merged_image_path')
        if image_path and os.path.exists(image_path):
            # Save outfit image to database
            with get_db_connection() as conn:
                cur = conn.cursor()
                try:
                    cur.execute("""
                        INSERT INTO saved_outfits (outfit_id, image_path)
                        VALUES (%s, %s)
                        RETURNING id
                    """, (outfit_id, image_path))
                    conn.commit()
                    return image_path
                finally:
                    cur.close()
        return None
    except Exception as e:
        logging.error(f"Error saving outfit: {str(e)}")
        return None

# Add batch operations support
def batch_insert_items(items_data):
    """Batch insert multiple clothing items"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            execute_values(
                cur,
                """
                INSERT INTO user_clothing_items 
                (type, color, style, gender, size, image_path, hyperlink)
                VALUES %s
                RETURNING id
                """,
                items_data
            )
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error in batch insert: {str(e)}")
            return False
        finally:
            cur.close()

@retry_on_error()
def load_saved_outfits():
    """Load saved outfits with optimized query and connection pooling"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute('''
                SELECT outfit_id, image_path, tags, season, notes, created_at
                FROM saved_outfits
                ORDER BY created_at DESC
            ''')
            columns = ['outfit_id', 'image_path', 'tags', 'season', 'notes', 'created_at']
            data = cur.fetchall()
            return [dict(zip(columns, row)) for row in data]
        finally:
            cur.close()
    return []

@retry_on_error()
def batch_update_outfits(updates):
    """Batch update multiple outfits"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            execute_batch(
                cur,
                """
                UPDATE saved_outfits 
                SET tags = %(tags)s,
                    season = %(season)s,
                    notes = %(notes)s
                WHERE outfit_id = %(outfit_id)s
                """,
                updates
            )
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error in batch update: {str(e)}")
            return False
        finally:
            cur.close()

@retry_on_error()
def update_outfit_details(outfit_id, tags=None, season=None, notes=None):
    """Update outfit details with optimized connection handling"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    UPDATE saved_outfits 
                    SET tags = COALESCE(%s, tags),
                        season = COALESCE(%s, season),
                        notes = COALESCE(%s, notes)
                    WHERE outfit_id = %s
                    RETURNING id
                """, (tags, season, notes, outfit_id))
                conn.commit()
                return True, "Outfit details updated successfully"
            finally:
                cur.close()
    except Exception as e:
        return False, f"Error updating outfit details: {str(e)}"

@retry_on_error()
def delete_saved_outfit(outfit_id):
    """Delete a saved outfit with proper connection handling"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                # Get the image path first
                cur.execute("SELECT image_path FROM saved_outfits WHERE outfit_id = %s", (outfit_id,))
                result = cur.fetchone()
                if result:
                    image_path = result[0]
                    
                    # Delete from database
                    cur.execute("DELETE FROM saved_outfits WHERE outfit_id = %s", (outfit_id,))
                    conn.commit()
                    
                    # Delete the image file if it exists
                    if os.path.exists(image_path):
                        os.remove(image_path)
                    
                    return True, "Outfit deleted successfully"
                return False, "Outfit not found"
            finally:
                cur.close()
    except Exception as e:
        return False, f"Error deleting outfit: {str(e)}"