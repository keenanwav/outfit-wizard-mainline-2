import os
import streamlit as st
from google.oauth2 import id_token
from google.auth.transport import requests
from google_auth_oauthlib.flow import Flow
import extra_streamlit_components as stx
from data_manager import get_db_connection

# Initialize session states for authentication
if 'user' not in st.session_state:
    st.session_state.user = None
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'token_info' not in st.session_state:
    st.session_state.token_info = None

def create_auth_tables():
    """Create necessary authentication tables in the database"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Create users table with role-based access control
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255),
                    role VARCHAR(50) DEFAULT 'user',
                    google_id VARCHAR(255) UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # Create default admin user if not exists
            cur.execute('''
                INSERT INTO users (email, name, role, google_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
            ''', ('admin@example.com', 'Admin', 'admin', 'admin'))
            
            conn.commit()
        finally:
            cur.close()

def get_user_by_email(email):
    """Get user by email from database"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT id, email, name, role, google_id FROM users WHERE email = %s",
                (email,)
            )
            user = cur.fetchone()
            if user:
                return {
                    'id': user[0],
                    'email': user[1],
                    'name': user[2],
                    'role': user[3],
                    'google_id': user[4]
                }
            return None
        finally:
            cur.close()

def create_user(email, name=None, google_id=None):
    """Create a new user in the database"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO users (email, name, google_id)
                VALUES (%s, %s, %s)
                RETURNING id, email, name, role, google_id
                """,
                (email, name, google_id)
            )
            user = cur.fetchone()
            conn.commit()
            return {
                'id': user[0],
                'email': user[1],
                'name': user[2],
                'role': user[3],
                'google_id': user[4]
            }
        finally:
            cur.close()

def init_google_auth():
    """Initialize Google OAuth flow"""
    client_config = {
        "web": {
            "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [f"https://{os.getenv('REPL_SLUG')}.{os.getenv('REPL_OWNER')}.repl.co/callback"]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 
                'https://www.googleapis.com/auth/userinfo.profile'],
        redirect_uri=client_config["web"]["redirect_uris"][0]
    )
    return flow

def verify_google_token(token):
    """Verify the Google OAuth token"""
    try:
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(),
            os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        )
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
            
        return {
            'google_id': idinfo['sub'],
            'email': idinfo['email'],
            'name': idinfo.get('name', idinfo['email'].split('@')[0])
        }
    except Exception as e:
        st.error(f"Token verification failed: {str(e)}")
        return None

def render_login_ui():
    """Render the login interface in Streamlit"""
    st.title("Login")
    
    if not st.session_state.authenticated:
        if st.button("Login with Google"):
            flow = init_google_auth()
            authorization_url, _ = flow.authorization_url(prompt="consent")
            st.markdown(f'<a href="{authorization_url}" target="_self"><button>Confirm Google Login</button></a>', unsafe_allow_html=True)
    else:
        st.success(f"Logged in as {st.session_state.user['name']}")
        if st.button("Logout"):
            logout()

def handle_callback():
    """Handle the OAuth callback"""
    try:
        state = st.experimental_get_query_params().get("state", [None])[0]
        code = st.experimental_get_query_params().get("code", [None])[0]
        
        if code:
            flow = init_google_auth()
            flow.fetch_token(code=code)
            
            credentials = flow.credentials
            token_info = verify_google_token(credentials.id_token)
            
            if token_info:
                user = get_user_by_email(token_info['email'])
                if not user:
                    user = create_user(
                        email=token_info['email'],
                        name=token_info['name'],
                        google_id=token_info['google_id']
                    )
                
                st.session_state.user = user
                st.session_state.authenticated = True
                st.session_state.token_info = token_info
                
                # Update last login time
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    try:
                        cur.execute(
                            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                            (user['id'],)
                        )
                        conn.commit()
                    finally:
                        cur.close()
                
                st.success("Successfully logged in!")
                return True
    except Exception as e:
        st.error(f"Authentication failed: {str(e)}")
    return False

def admin_required(func):
    """Decorator to require admin role for specific pages"""
    def wrapper(*args, **kwargs):
        if not st.session_state.user or st.session_state.user['role'] != 'admin':
            st.error("Admin access required")
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def is_admin():
    """Check if current user is an admin"""
    return (st.session_state.user is not None and 
            st.session_state.user.get('role') == 'admin')

def logout():
    """Log out the current user"""
    st.session_state.user = None
    st.session_state.authenticated = False
    st.session_state.token_info = None
    st.rerun()
