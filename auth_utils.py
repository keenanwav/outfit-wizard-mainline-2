import os
import bcrypt
import streamlit as st
from datetime import datetime, timedelta
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Declare global connection pool
connection_pool = None

def create_connection_pool(max_retries=3, retry_delay=5):
    """Create database connection pool with retry logic"""
    global connection_pool
    retries = 0
    last_exception = None

    while retries < max_retries:
        try:
            if connection_pool is not None:
                try:
                    connection_pool.closeall()
                except Exception:
                    pass

            connection_pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=os.environ['DATABASE_URL'],
                # Add SSL parameters for more reliable connections
                sslmode='prefer',
                connect_timeout=10,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5
            )
            logging.info("Successfully created database connection pool")
            return connection_pool
        except psycopg2.Error as e:
            last_exception = e
            logging.error(f"Database connection attempt {retries + 1} failed: {str(e)}")
            retries += 1
            if retries < max_retries:
                time.sleep(retry_delay)

    logging.error(f"Database connection timeout after {max_retries} attempts: {str(last_exception)}")
    return None

@contextmanager
def get_db_connection():
    """Context manager for database connections with retry logic"""
    global connection_pool
    conn = None
    try:
        # Ensure pool exists
        if connection_pool is None:
            connection_pool = create_connection_pool()
        if connection_pool is None:
            raise RuntimeError("Failed to create database connection pool")

        conn = connection_pool.getconn()
        yield conn
        if conn.closed == 0:  # If connection is still open
            conn.commit()
    except psycopg2.OperationalError as e:
        logging.error(f"Database operation failed: {str(e)}")
        if conn and not conn.closed:
            conn.rollback()
        # Try to reinitialize the connection pool
        connection_pool = create_connection_pool()
        raise
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        if conn and not conn.closed:
            conn.rollback()
        raise
    finally:
        if conn is not None:
            if not conn.closed:
                connection_pool.putconn(conn)

def init_auth_tables():
    """Initialize authentication tables"""
    try:
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
                logging.info("Successfully initialized auth tables")
    except Exception as e:
        logging.error(f"Failed to initialize auth tables: {str(e)}")
        raise

def hash_password(password: str) -> bytes:
    """Hash a password using bcrypt"""
    try:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    except Exception as e:
        logging.error(f"Error hashing password: {str(e)}")
        raise

def verify_password(password: str, password_hash: memoryview) -> bool:
    """Verify a password against its hash"""
    try:
        # Convert memoryview to bytes for bcrypt comparison
        if isinstance(password_hash, memoryview):
            password_hash_bytes = bytes(password_hash)
        else:
            password_hash_bytes = password_hash

        return bcrypt.checkpw(password.encode('utf-8'), password_hash_bytes)
    except Exception as e:
        logging.error(f"Password verification error: {str(e)}")
        return False

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
        if isinstance(e, psycopg2.errors.UniqueViolation):
            st.error("Username or email already exists")
        else:
            logging.error(f"Error creating user: {str(e)}")
            st.error(f"Error creating user: {str(e)}")
        return False

def authenticate_user(email: str, password: str) -> tuple[bool, dict]:
    """Authenticate a user"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, username, password_hash, role FROM users WHERE email = %s",
                    (email,)
                )
                result = cur.fetchone()

                if result and verify_password(password, result[2]):
                    return True, {"id": result[0], "username": result[1], "role": result[3]}
                return False, {}
    except psycopg2.Error as e:
        logging.error(f"Error authenticating user: {str(e)}")
        st.error(f"Error authenticating user: {str(e)}")
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