import os
import bcrypt
import streamlit as st
from datetime import datetime, timedelta
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from typing import Optional, Dict, Tuple

# Initialize connection pool with better error handling
def create_connection_pool():
    try:
        return SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=os.environ['DATABASE_URL'],
            connect_timeout=30
        )
    except Exception as e:
        st.error(f"Failed to create database pool: {str(e)}")
        raise

# Initialize connection pool
connection_pool = create_connection_pool()

@contextmanager
def get_db_connection():
    """Context manager for database connections with proper error handling"""
    conn = None
    try:
        conn = connection_pool.getconn()
        yield conn
    finally:
        if conn:
            if not conn.closed:
                conn.commit()
            connection_pool.putconn(conn)

def init_auth_tables():
    """Initialize authentication and profile tables"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Create users table with additional profile fields
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(64) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash BYTEA NOT NULL,
                    role VARCHAR(10) NOT NULL DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    full_name VARCHAR(100),
                    bio TEXT,
                    profile_picture_path VARCHAR(255),
                    preferences JSONB DEFAULT '{}',
                    last_login TIMESTAMP,
                    CHECK (role IN ('admin', 'user'))
                )
            """)
            conn.commit()
            st.success("Successfully initialized auth tables")
        except Exception as e:
            st.error(f"Failed to initialize auth tables: {str(e)}")
            conn.rollback()
            raise
        finally:
            cur.close()

def hash_password(password: str) -> bytes:
    """Hash a password using bcrypt with proper encoding"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password: str, password_hash: bytes) -> bool:
    """Verify a password against its hash with proper type handling"""
    try:
        # Convert memoryview to bytes if necessary
        if isinstance(password_hash, memoryview):
            password_hash = password_hash.tobytes()
        return bcrypt.checkpw(password.encode('utf-8'), password_hash)
    except Exception as e:
        st.error(f"Password verification error: {str(e)}")
        return False

def create_user(username: str, email: str, password: str, role: str = 'user') -> bool:
    """Create a new user with specified role"""
    try:
        if role not in ('admin', 'user'):
            raise ValueError("Invalid role specified")

        password_hash = hash_password(password)
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                    (username, email, password_hash, role)
                )
                conn.commit()
                return True
            except psycopg2.Error as e:
                st.error(f"Database error: {str(e)}")
                return False
            finally:
                cur.close()
    except Exception as e:
        st.error(f"Error creating user: {str(e)}")
        return False

def authenticate_user(email: str, password: str) -> Tuple[bool, Dict]:
    """Authenticate a user and update last login time"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    SELECT id, username, password_hash, role 
                    FROM users 
                    WHERE email = %s
                    """,
                    (email,)
                )
                result = cur.fetchone()

                if result and verify_password(password, result[2]):
                    # Update last login time
                    cur.execute(
                        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                        (result[0],)
                    )
                    conn.commit()
                    return True, {
                        "id": result[0],
                        "username": result[1],
                        "role": result[3]
                    }
                return False, {}
            finally:
                cur.close()
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False, {}

def update_user_profile(user_id: int, data: Dict) -> bool:
    """Update user profile information"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                # Build update query dynamically based on provided fields
                update_fields = []
                params = []
                for key, value in data.items():
                    if key in ['full_name', 'bio', 'profile_picture_path', 'preferences']:
                        update_fields.append(f"{key} = %s")
                        params.append(value)

                if update_fields:
                    params.append(user_id)
                    query = f"""
                        UPDATE users 
                        SET {', '.join(update_fields)}
                        WHERE id = %s
                        RETURNING id
                    """
                    cur.execute(query, params)

                    if cur.fetchone():
                        conn.commit()
                        return True
                return False
            finally:
                cur.close()
    except Exception as e:
        st.error(f"Error updating profile: {str(e)}")
        return False

def get_user_profile(user_id: int) -> Optional[Dict]:
    """Get user profile information"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    SELECT username, email, full_name, bio, 
                           profile_picture_path, preferences, last_login
                    FROM users 
                    WHERE id = %s
                    """,
                    (user_id,)
                )
                result = cur.fetchone()

                if result:
                    return {
                        "username": result[0],
                        "email": result[1],
                        "full_name": result[2],
                        "bio": result[3],
                        "profile_picture_path": result[4],
                        "preferences": result[5],
                        "last_login": result[6]
                    }
                return None
            finally:
                cur.close()
    except Exception as e:
        st.error(f"Error fetching profile: {str(e)}")
        return None

def init_session_state():
    """Initialize session state variables for authentication"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'auth_status' not in st.session_state:
        st.session_state.auth_status = None

def is_admin(user_data: Optional[Dict]) -> bool:
    """Check if the current user has admin role"""
    if not user_data:
        return False
    return user_data.get('role') == 'admin'

def require_admin(func):
    """Decorator to require admin role for accessing certain features"""
    def wrapper(*args, **kwargs):
        if not st.session_state.user or not is_admin(st.session_state.user):
            st.error("Access Denied: This feature requires admin privileges.")
            return None
        return func(*args, **kwargs)
    return wrapper

def logout_user():
    """Log out the current user"""
    st.session_state.user = None
    st.session_state.auth_status = None