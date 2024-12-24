import os
import logging
import time
import random
from datetime import datetime, timedelta
from contextlib import contextmanager

# Configure logging for auth module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('auth_utils')

# Initialize connection pool settings
MIN_CONNECTIONS = 1
MAX_CONNECTIONS = 10
POOL_TIMEOUT = 30
STATEMENT_TIMEOUT = 30000  # 30 seconds statement timeout

# Global connection pool
connection_pool = None

# Import database libraries
try:
    import psycopg2
    from psycopg2.pool import SimpleConnectionPool
    import bcrypt
    import streamlit as st
    logger.info("Successfully imported all required libraries")
except ImportError as e:
    logger.error(f"Failed to import required libraries: {e}")
    raise

def create_connection_pool():
    """Create and return a connection pool with optimized settings"""
    global connection_pool
    try:
        if connection_pool is not None:
            logger.info("Reusing existing connection pool")
            return connection_pool

        logger.info("Attempting to create database connection pool")

        # Get database credentials from environment
        db_params = {
            'host': os.environ.get('PGHOST'),
            'database': os.environ.get('PGDATABASE'),
            'user': os.environ.get('PGUSER'),
            'password': os.environ.get('PGPASSWORD'),
            'sslmode': 'require'
        }

        # Validate database parameters
        missing_params = [k for k, v in db_params.items() if not v]
        if missing_params:
            raise ValueError(f"Missing required database parameters: {', '.join(missing_params)}")

        # Create connection pool with optimized settings
        connection_pool = SimpleConnectionPool(
            MIN_CONNECTIONS,
            MAX_CONNECTIONS,
            **db_params,
            connect_timeout=10,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5,
            options=f'-c statement_timeout={STATEMENT_TIMEOUT}',
            application_name='outfit_wizard_auth',
            client_encoding='UTF8'
        )

        # Test the connection
        with connection_pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
                logger.info("Database connection test successful")
            connection_pool.putconn(conn)

        logger.info("Successfully created database connection pool")
        return connection_pool
    except Exception as e:
        logger.error(f"Failed to create database connection pool: {str(e)}")
        raise

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
                logger.error(f"Failed to get connection pool after {max_retries} attempts: {str(e)}")
                raise
            jitter = random.uniform(0, 0.1 * retry_delay)
            time.sleep((retry_delay * (2 ** attempt)) + jitter)
            logger.warning(f"Retrying connection pool creation (attempt {attempt + 1})")

@contextmanager
def get_db_connection():
    """Context manager for database connections with enhanced error handling"""
    conn = None
    pool = None
    try:
        pool = get_connection_pool()
        conn = pool.getconn()
        conn.set_session(autocommit=False)
        yield conn
    except psycopg2.OperationalError as e:
        if conn:
            conn.close()
        if "SSL connection has been closed unexpectedly" in str(e):
            # Force recreation of pool on SSL errors
            global connection_pool
            connection_pool = None
        logger.error(f"Database connection error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected database error: {str(e)}")
        raise
    finally:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
            if pool:
                try:
                    pool.putconn(conn)
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {str(e)}")
                    conn.close()

def init_auth_tables():
    """Initialize authentication tables with retry logic"""
    logger.info("Starting authentication tables initialization")
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
                    logger.info("Successfully initialized auth tables")
                    return True
        except psycopg2.OperationalError as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to initialize auth tables after {max_retries} attempts: {str(e)}")
                raise
            jitter = random.uniform(0, 0.1 * retry_delay)
            time.sleep((retry_delay * (2 ** attempt)) + jitter)
            logger.warning(f"Retrying auth tables initialization (attempt {attempt + 1})")
    return False

def hash_password(password: str) -> bytes:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password: str, password_hash: bytes) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash)

def init_session_state():
    """Initialize session state variables for authentication"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'auth_status' not in st.session_state:
        st.session_state.auth_status = None
    logger.info("Session state initialized")

def create_user(username: str, email: str, password: str, role: str = 'user') -> bool:
    """Create a new user with specified role"""
    if role not in ('admin', 'user'):
        raise ValueError("Invalid role specified")

    try:
        password_hash = hash_password(password)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                    (username, email, password_hash, role)
                )
                conn.commit()
                logger.info(f"Successfully created user: {username}")
        return True
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return False

def authenticate_user(email: str, password: str) -> tuple[bool, dict]:
    """Authenticate a user with retry logic"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, username, password_hash, role FROM users WHERE email = %s",
                    (email,)
                )
                result = cur.fetchone()

                if result and verify_password(password, result[2]):
                    logger.info(f"Successfully authenticated user: {result[1]}")
                    return True, {"id": result[0], "username": result[1], "role": result[3]}
                logger.warning(f"Failed authentication attempt for email: {email}")
                return False, {}
    except Exception as e:
        logger.error(f"Error authenticating user: {str(e)}")
        return False, {}

def logout_user():
    """Log out the current user"""
    st.session_state.user = None
    st.session_state.auth_status = None
    logger.info("User logged out successfully")