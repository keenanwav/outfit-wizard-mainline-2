import os
import uuid
from PIL import Image
import psycopg2
from psycopg2.extras import Json
import logging
import shutil
from datetime import datetime

logging.basicConfig(level=logging.INFO)

def get_db_connection():
    """Get database connection using environment variables"""
    return psycopg2.connect(os.environ['DATABASE_URL'])

def create_user_items_table():
    """Create necessary database tables if they don't exist"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create user_items table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_items (
                id SERIAL PRIMARY KEY,
                type VARCHAR(50),
                color VARCHAR(50),
                style TEXT[],
                gender TEXT[],
                size TEXT[],
                image_path TEXT,
                hyperlink TEXT,
                tags TEXT[],
                season VARCHAR(10),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create saved_outfits table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS saved_outfits (
                outfit_id TEXT PRIMARY KEY,
                image_path TEXT,
                tags TEXT[],
                season VARCHAR(10),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logging.info("Database tables created successfully")
        
    except Exception as e:
        logging.error(f"Error creating tables: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def add_user_clothing_item(item_type, color, styles, genders, sizes, image_path, hyperlink=None):
    """Add a new clothing item to the database"""
    conn = None
    try:
        # Create wardrobe directory if it doesn't exist
        wardrobe_dir = 'wardrobe'
        if not os.path.exists(wardrobe_dir):
            os.makedirs(wardrobe_dir)
        
        # Copy image to wardrobe directory
        filename = f"{uuid.uuid4()}_{os.path.basename(image_path)}"
        wardrobe_path = os.path.join(wardrobe_dir, filename)
        shutil.copy2(image_path, wardrobe_path)
        
        # Insert into database
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO user_items (type, color, style, gender, size, image_path, hyperlink)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            item_type,
            ','.join(map(str, color)),
            styles,
            genders,
            sizes,
            wardrobe_path,
            hyperlink
        ))
        
        item_id = cur.fetchone()[0]
        conn.commit()
        
        return True, f"Item added successfully with ID: {item_id}"
        
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error adding item: {str(e)}")
        return False, f"Error adding item: {str(e)}"
        
    finally:
        if conn:
            conn.close()

def load_clothing_items():
    """Load all clothing items from database"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM user_items")
        columns = [desc[0] for desc in cur.description]
        items = cur.fetchall()
        
        return pd.DataFrame(items, columns=columns)
        
    except Exception as e:
        logging.error(f"Error loading items: {str(e)}")
        return pd.DataFrame()
        
    finally:
        if conn:
            conn.close()

def delete_clothing_item(item_id):
    """Delete a clothing item and its image"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get image path before deletion
        cur.execute("SELECT image_path FROM user_items WHERE id = %s", (item_id,))
        result = cur.fetchone()
        
        if result:
            image_path = result[0]
            # Delete from database
            cur.execute("DELETE FROM user_items WHERE id = %s", (item_id,))
            conn.commit()
            
            # Delete image file
            if os.path.exists(image_path):
                os.remove(image_path)
            
            return True, "Item deleted successfully"
        return False, "Item not found"
        
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error deleting item: {str(e)}")
        return False, f"Error deleting item: {str(e)}"
        
    finally:
        if conn:
            conn.close()

def update_item_details(item_id, tags=None, season=None, notes=None):
    """Update item details in the database"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        updates = []
        values = []
        
        if tags is not None:
            updates.append("tags = %s")
            values.append(tags)
        if season is not None:
            updates.append("season = %s")
            values.append(season)
        if notes is not None:
            updates.append("notes = %s")
            values.append(notes)
            
        if updates:
            query = f"""
                UPDATE user_items 
                SET {', '.join(updates)}
                WHERE id = %s
            """
            values.append(item_id)
            
            cur.execute(query, values)
            conn.commit()
            
            return True, "Item updated successfully"
        return False, "No updates provided"
        
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error updating item: {str(e)}")
        return False, f"Error updating item: {str(e)}"
        
    finally:
        if conn:
            conn.close()

def save_outfit(outfit):
    """Save outfit to database and filesystem with improved error handling"""
    conn = None
    cur = None
    try:
        # Create wardrobe directory if it doesn't exist
        wardrobe_dir = 'wardrobe'
        if not os.path.exists(wardrobe_dir):
            os.makedirs(wardrobe_dir)
            logging.info(f"Created directory: {wardrobe_dir}")
        
        # Generate outfit ID and filename
        outfit_id = str(uuid.uuid4())
        outfit_filename = f"outfit_{outfit_id}.png"
        outfit_path = os.path.join(wardrobe_dir, outfit_filename)
        
        # Save outfit image
        try:
            if 'merged_image_path' in outfit and os.path.exists(outfit['merged_image_path']):
                logging.info(f"Saving merged outfit image to {outfit_path}")
                shutil.copy2(outfit['merged_image_path'], outfit_path)
            else:
                logging.error("No merged image found")
                return None
        except Exception as e:
            logging.error(f"Error saving outfit image: {str(e)}")
            raise
        
        # Database operations with transaction handling
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # Start transaction
            cur.execute("BEGIN")
            
            # Insert outfit record
            cur.execute("""
                INSERT INTO saved_outfits 
                (outfit_id, image_path, created_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                RETURNING outfit_id
            """, (outfit_id, outfit_path))
            
            # Commit transaction
            conn.commit()
            logging.info(f"Successfully saved outfit with ID: {outfit_id}")
            return outfit_path
            
        except Exception as e:
            if conn:
                conn.rollback()
            logging.error(f"Database error while saving outfit: {str(e)}")
            # Clean up saved image if database operation failed
            if os.path.exists(outfit_path):
                try:
                    os.remove(outfit_path)
                    logging.info(f"Cleaned up outfit image after failed save: {outfit_path}")
                except Exception as cleanup_error:
                    logging.error(f"Error cleaning up outfit image: {str(cleanup_error)}")
            raise
            
    except Exception as e:
        logging.error(f"Error in save_outfit: {str(e)}")
        return None
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def load_saved_outfits():
    """Load all saved outfits from database"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM saved_outfits ORDER BY created_at DESC")
        columns = [desc[0] for desc in cur.description]
        outfits = cur.fetchall()
        
        return [dict(zip(columns, outfit)) for outfit in outfits]
        
    except Exception as e:
        logging.error(f"Error loading saved outfits: {str(e)}")
        return []
        
    finally:
        if conn:
            conn.close()

def update_outfit_details(outfit_id, tags=None, season=None, notes=None):
    """Update outfit details in the database"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        updates = []
        values = []
        
        if tags is not None:
            updates.append("tags = %s")
            values.append(tags)
        if season is not None:
            updates.append("season = %s")
            values.append(season)
        if notes is not None:
            updates.append("notes = %s")
            values.append(notes)
            
        if updates:
            query = f"""
                UPDATE saved_outfits 
                SET {', '.join(updates)}
                WHERE outfit_id = %s
            """
            values.append(outfit_id)
            
            cur.execute(query, values)
            conn.commit()
            
            return True, "Outfit updated successfully"
        return False, "No updates provided"
        
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error updating outfit: {str(e)}")
        return False, f"Error updating outfit: {str(e)}"
        
    finally:
        if conn:
            conn.close()

def delete_saved_outfit(outfit_id):
    """Delete a saved outfit and its image"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get image path before deletion
        cur.execute("SELECT image_path FROM saved_outfits WHERE outfit_id = %s", (outfit_id,))
        result = cur.fetchone()
        
        if result:
            image_path = result[0]
            # Delete from database
            cur.execute("DELETE FROM saved_outfits WHERE outfit_id = %s", (outfit_id,))
            conn.commit()
            
            # Delete image file
            if os.path.exists(image_path):
                os.remove(image_path)
            
            return True, "Outfit deleted successfully"
        return False, "Outfit not found"
        
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error deleting outfit: {str(e)}")
        return False, f"Error deleting outfit: {str(e)}"
        
    finally:
        if conn:
            conn.close()
