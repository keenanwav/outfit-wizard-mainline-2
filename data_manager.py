[Previous content remains the same until line 326, then add:]

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
            SELECT outfit_id, tags, season, notes 
            FROM saved_outfits 
            WHERE outfit_id = %s
        """, (outfit_id,))
        
        result = cur.fetchone()
        if result:
            return {
                'outfit_id': result[0],
                'tags': result[1] if result[1] else [],
                'season': result[2],
                'notes': result[3]
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
