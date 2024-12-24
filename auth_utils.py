import os
import bcrypt
import streamlit as st
from datetime import datetime, timedelta
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
import logging
import time
import random

# Initialize connection pool settings
MIN_CONNECTIONS = 1
MAX_CONNECTIONS = 10
POOL_TIMEOUT = 30
STATEMENT_TIMEOUT = 30000  # 30 seconds statement timeout

def create_connection_pool():
    """Create and return a connection pool with optimized settings"""
    try:
        return SimpleConnectionPool(
            MIN_CONNECTIONS,
            MAX_CONNECTIONS,
            host=os.environ['PGHOST'],
            database=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            sslmode='require',  # Changed from verify-full to require
            connect_timeout=10,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5,
            options=f'-c statement_timeout={STATEMENT_TIMEOUT}',
            application_name='outfit_wizard_auth',
            client_encoding='UTF8'
        )
    except Exception as e:
        logging.error(f"Error creating auth connection pool: {str(e)}")
        raise

# Create the connection pool with retry logic
def get_connection_pool():
    """Get or create connection pool with retry logic"""
    global connection_pool
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            if connection_pool is None:
                connection_pool = create_connection_pool()
            return connection_pool
        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(f"Failed to create auth connection pool after {max_retries} attempts: {str(e)}")
                raise
            time.sleep(retry_delay * (2 ** attempt))

connection_pool = None
connection_pool = get_connection_pool()

@contextmanager
def get_db_connection():
    """Context manager for database connections with enhanced error handling"""
    conn = None
    try:
        pool = get_connection_pool()
        conn = pool.getconn()
        if conn:
            # Test the connection before using it
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
            conn.set_session(autocommit=False)
            yield conn
    except psycopg2.OperationalError as e:
        if conn:
            conn.close()  # Explicitly close bad connections
            if connection_pool:
                connection_pool.putconn(conn, close=True)
        if "SSL connection has been closed unexpectedly" in str(e):
            # Force recreation of pool on SSL errors
            global connection_pool
            connection_pool = None
        logging.error(f"Database connection error in auth_utils: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected database error in auth_utils: {str(e)}")
        raise
    finally:
        if conn:
            try:
                conn.rollback()  # Ensure no hanging transactions
            except Exception:
                pass
            if connection_pool:
                try:
                    connection_pool.putconn(conn)
                except Exception as e:
                    logging.error(f"Error returning connection to pool in auth_utils: {str(e)}")
                    try:
                        conn.close()
                    except Exception:
                        pass

def init_auth_tables():
    """Initialize authentication tables with retry logic"""
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
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
                    return
        except psycopg2.OperationalError as e:
            if "SSL connection has been closed unexpectedly" in str(e):
                global connection_pool
                connection_pool = None
            if attempt == max_retries - 1:
                logging.error(f"Failed to initialize auth tables after {max_retries} attempts: {str(e)}")
                raise
            jitter = random.uniform(0, 0.1 * retry_delay)
            time.sleep((retry_delay * (2 ** attempt)) + jitter)
        except Exception as e:
            logging.error(f"Error initializing auth tables: {str(e)}")
            raise

def hash_password(password: str) -> bytes:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password: str, password_hash: bytes) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash)

def create_user(username: str, email: str, password: str, role: str = 'user') -> bool:
    """Create a new user with specified role and retry logic"""
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
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
        except psycopg2.OperationalError as e:
            if "SSL connection has been closed unexpectedly" in str(e):
                global connection_pool
                connection_pool = None
            if attempt == max_retries - 1:
                st.error(f"Error creating user: {str(e)}")
                return False
            jitter = random.uniform(0, 0.1 * retry_delay)
            time.sleep((retry_delay * (2 ** attempt)) + jitter)
        except Exception as e:
            st.error(f"Error creating user: {str(e)}")
            return False

def authenticate_user(email: str, password: str) -> tuple[bool, dict]:
    """Authenticate a user with retry logic"""
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
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
        except psycopg2.OperationalError as e:
            if "SSL connection has been closed unexpectedly" in str(e):
                global connection_pool
                connection_pool = None
            if attempt == max_retries - 1:
                st.error(f"Error authenticating user: {str(e)}")
                return False, {}
            jitter = random.uniform(0, 0.1 * retry_delay)
            time.sleep((retry_delay * (2 ** attempt)) + jitter)
        except Exception as e:
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