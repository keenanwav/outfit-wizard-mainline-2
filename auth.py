import streamlit as st
import bcrypt
import psycopg2
from psycopg2.pool import SimpleConnectionPool
import os
from datetime import datetime, timedelta
import logging
from typing import Optional, Tuple, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database connection pool
def get_connection_pool():
    """Create database connection pool"""
    try:
        return SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=os.environ['DATABASE_URL']
        )
    except Exception as e:
        logger.error(f"Error creating connection pool: {e}")
        raise

# Global connection pool
try:
    conn_pool = get_connection_pool()
except Exception as e:
    logger.error(f"Failed to initialize connection pool: {e}")
    conn_pool = None

def init_auth():
    """Initialize authentication tables"""
    if 'user_auth_initialized' not in st.session_state:
        create_auth_tables()
        st.session_state.user_auth_initialized = True

def create_auth_tables():
    """Create authentication related tables if they don't exist"""
    try:
        conn = conn_pool.getconn()
        with conn.cursor() as cur:
            # Create users table with role field
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash BYTEA NOT NULL,
                    role VARCHAR(50) NOT NULL DEFAULT 'user',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP WITH TIME ZONE
                )
            """)
            conn.commit()
    except Exception as e:
        logger.error(f"Error creating auth tables: {e}")
        raise
    finally:
        if conn:
            conn_pool.putconn(conn)

def hash_password(password: str) -> bytes:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password: str, password_hash: bytes) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash)
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

def create_user(email: str, password: str, role: str = 'user') -> bool:
    """Create a new user"""
    try:
        conn = conn_pool.getconn()
        with conn.cursor() as cur:
            # Check if user already exists
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone() is not None:
                return False
            
            # Create new user
            password_hash = hash_password(password)
            cur.execute(
                """
                INSERT INTO users (email, password_hash, role)
                VALUES (%s, %s, %s)
                """,
                (email, password_hash, role)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return False
    finally:
        if conn:
            conn_pool.putconn(conn)

def authenticate_user(email: str, password: str) -> Tuple[bool, Optional[Dict]]:
    """Authenticate a user and return user data if successful"""
    try:
        conn = conn_pool.getconn()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, password_hash, role
                FROM users
                WHERE email = %s
                """,
                (email,)
            )
            user_data = cur.fetchone()
            
            if user_data and verify_password(password, user_data[2]):
                # Update last login timestamp
                cur.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                    (user_data[0],)
                )
                conn.commit()
                
                return True, {
                    'id': user_data[0],
                    'email': user_data[1],
                    'role': user_data[3]
                }
            return False, None
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        return False, None
    finally:
        if conn:
            conn_pool.putconn(conn)

def render_login_ui():
    """Render the login user interface"""
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'show_login_page' not in st.session_state:
        st.session_state.show_login_page = False
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = 'login'
    
    # If not authenticated and login page is requested
    if not st.session_state.authenticated and st.session_state.show_login_page:
        # Apply custom CSS
        st.markdown("""
            <style>
                .stButton button {
                    width: 100%;
                    background-color: #1E1E1E;
                    color: white;
                    border: 1px solid #333;
                    padding: 0.75rem;
                    border-radius: 4px;
                }
                .stButton button:hover {
                    background-color: #333;
                }
                .stTextInput input {
                    background-color: #2D2D2D;
                    color: white;
                    border: 1px solid #333;
                }
                .stTextInput input:focus {
                    border-color: #ff4b4b;
                }
                div[data-testid="stVerticalBlock"] {
                    background: #1E1E1E;
                    padding: 2rem;
                    border-radius: 8px;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Clear any existing content and set up the auth page
        st.empty()
        
        # Center the content
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<h1 class="auth-title">Welcome to Outfit Wizard</h1>', unsafe_allow_html=True)
            
            # Custom tab buttons
            cols = st.columns(2)
            with cols[0]:
                if st.button("Login", key="tab_login", use_container_width=True):
                    st.session_state.active_tab = 'login'
            with cols[1]:
                if st.button("Sign Up", key="tab_signup", use_container_width=True):
                    st.session_state.active_tab = 'signup'
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Login form
            if st.session_state.active_tab == 'login':
                login_email = st.text_input("Email", key="login_email")
                login_password = st.text_input("Password", type="password", key="login_password")
                
                if st.button("Login", key="login_button", use_container_width=True):
                    if login_email and login_password:
                        success, user_info = authenticate_user(login_email, login_password)
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.user_info = user_info
                            st.session_state.show_login_page = False
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid email or password")
                    else:
                        st.warning("Please enter both email and password")
            
            # Sign Up form
            else:
                signup_email = st.text_input("Email", key="signup_email")
                signup_password = st.text_input("Password", type="password", key="signup_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
                
                if st.button("Sign Up", key="signup_button", use_container_width=True):
                    if signup_email and signup_password and confirm_password:
                        if signup_password != confirm_password:
                            st.error("Passwords do not match")
                        elif len(signup_password) < 8:
                            st.error("Password must be at least 8 characters long")
                        else:
                            if create_user(signup_email, signup_password, role="user"):
                                st.success("Account created successfully! Please login.")
                                st.session_state.active_tab = 'login'
                                st.session_state.signup_email = ""
                                st.session_state.signup_password = ""
                                st.session_state.confirm_password = ""
                                st.rerun()
                            else:
                                st.error("Email already exists or error creating account")
                    else:
                        st.warning("Please fill in all fields")
    
    return st.session_state.authenticated, st.session_state.user_info

def logout():
    """Log out the current user"""
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.rerun()

def check_admin_role():
    """Check if the current user has admin role"""
    return (
        st.session_state.authenticated and 
        st.session_state.user_info and 
        st.session_state.user_info.get('role') == 'admin'
    )
