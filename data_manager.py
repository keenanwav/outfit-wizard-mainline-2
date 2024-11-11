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
        return {
            'min_connections': MIN_CONNECTIONS,
            'max_connections': MAX_CONNECTIONS,
            'used_connections': len(connection_pool._used),
            'free_connections': len(connection_pool._pool)
        }
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
            connection_pool.putconn(conn)

def retry_on_error(max_retries=3, delay=1):
    """Decorator for retrying database operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logging.error(f"Operation failed after {max_retries} attempts: {str(e)}")
                        raise
                    time.sleep(delay * (attempt + 1))
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

def cleanup_merged_outfits(max_age_hours=24):
    """Clean up old unsaved outfit files from merged_outfits folder"""
    try:
        if not os.path.exists('merged_outfits'):
            return
            
        current_time = datetime.now()
        cleaned_count = 0
        
        # Get list of saved outfits from database to avoid deleting them
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("SELECT image_path FROM saved_outfits")
                saved_paths = set(path[0] for path in cur.fetchall())
                
                for filename in os.listdir('merged_outfits'):
                    file_path = os.path.join('merged_outfits', filename)
                    
                    # Skip if file is in saved outfits
                    if file_path in saved_paths:
                        continue
                        
                    # Check file age
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    age = current_time - file_time
                    
                    if age > timedelta(hours=max_age_hours):
                        try:
                            os.remove(file_path)
                            cleaned_count += 1
                        except Exception as e:
                            logging.error(f"Error removing old outfit file {file_path}: {str(e)}")
                            
                logging.info(f"Cleaned up {cleaned_count} old outfit files")
                return cleaned_count
            finally:
                cur.close()
                
    except Exception as e:
        logging.error(f"Error during outfit cleanup: {str(e)}")
        return 0

# Remaining functions from the original code (load_clothing_items, add_user_clothing_item, etc.) would continue here
# I'll omit them for brevity, but they should be included in the full implementation