[Previous code up to line 286 remains the same]

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

[Rest of the code remains the same]
