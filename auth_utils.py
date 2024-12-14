import os
import bcrypt
import streamlit as st
from datetime import datetime, timedelta
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager

# Initialize connection pool
connection_pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=os.environ['DATABASE_URL']
)

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)

def init_auth_tables():
    """Initialize authentication tables"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Create users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(64) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash BYTEA NOT NULL,
                    role VARCHAR(10) NOT NULL DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (role IN ('admin', 'user'))
                )
            """)
            conn.commit()

def hash_password(password: str) -> bytes:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password: str, password_hash: bytes) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash)

def create_user(username: str, email: str, password: str, role: str = 'user') -> bool:
    """Create a new user with specified role"""
    try:
        if role not in ('admin', 'user'):
            raise ValueError("Invalid role specified")
            
        password_hash = hash_password(password)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                    (username, email, password_hash, role)
                )
                conn.commit()
        return True
    except psycopg2.Error as e:
        st.error(f"Error creating user: {e}")
        return False

def authenticate_user(email: str, password: str) -> tuple[bool, dict]:
    """Authenticate a user"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, username, password_hash FROM users WHERE email = %s",
                    (email,)
                )
                result = cur.fetchone()
                
                cur.execute(
                    "SELECT id, username, password_hash, role FROM users WHERE email = %s",
                    (email,)
                )
                result = cur.fetchone()
                
                if result and verify_password(password, result[2]):
                    return True, {"id": result[0], "username": result[1], "role": result[3]}
        return False, {}
    except psycopg2.Error as e:
        st.error(f"Error authenticating user: {e}")
        return False, {}

def init_session_state():
    """Initialize session state variables for authentication"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'auth_status' not in st.session_state:
        st.session_state.auth_status = None

def logout_user():
    """Log out the current user"""
    st.session_state.user = None
    st.session_state.auth_status = None
