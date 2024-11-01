import streamlit as st
import bcrypt
import psycopg2
import os
import logging

logging.basicConfig(level=logging.INFO)

def get_db_connection():
    try:
        return psycopg2.connect(
            host=os.environ['PGHOST'],
            database=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD']
        )
    except Exception as e:
        logging.error(f"Database connection error: {str(e)}")
        return None

def create_users_table():
    conn = get_db_connection()
    if not conn:
        return False
    
    cur = conn.cursor()
    try:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE
            );
        ''')
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Error creating users table: {str(e)}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    try:
        if isinstance(hashed, str):
            hashed = hashed.encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    except Exception as e:
        logging.error(f"Password verification error: {str(e)}")
        return False

def admin_exists():
    conn = get_db_connection()
    if not conn:
        return False
    
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM users WHERE is_admin = TRUE")
        count = cur.fetchone()[0]
        return count > 0
    except Exception as e:
        logging.error(f"Error checking admin existence: {str(e)}")
        return False
    finally:
        cur.close()
        conn.close()

def register_user(username, password, is_admin=False):
    if not username or not password:
        return False, "Username and password are required"
    
    conn = get_db_connection()
    if not conn:
        return False, "Database connection error"
    
    cur = conn.cursor()
    try:
        hashed_password = hash_password(password)
        cur.execute(
            "INSERT INTO users (username, password, is_admin) VALUES (%s, %s, %s)",
            (username, hashed_password, is_admin)
        )
        conn.commit()
        return True, "Registration successful"
    except psycopg2.IntegrityError:
        conn.rollback()
        return False, "Username already exists"
    except Exception as e:
        conn.rollback()
        logging.error(f"Registration error: {str(e)}")
        return False, "Registration failed"
    finally:
        cur.close()
        conn.close()

def authenticate_user(username, password):
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cur = conn.cursor()
        cur.execute("SELECT password, is_admin FROM users WHERE username = %s", (username,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result and verify_password(password, result[0]):
            return True
        return False
    except Exception as e:
        logging.error(f"Authentication error: {str(e)}")
        return False

def auth_form():
    if not create_users_table():
        st.error("Error connecting to database. Please try again later.")
        return
    
    if 'username' not in st.session_state:
        st.session_state.username = None

    if st.session_state.username:
        st.sidebar.write(f"Logged in as {st.session_state.username}")
        if st.sidebar.button("Logout"):
            st.session_state.username = None
            st.success("Logged out successfully!")
            st.experimental_rerun()
    else:
        st.header("Login / Register")
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Login"):
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    if authenticate_user(username, password):
                        st.session_state.username = username
                        st.success("Logged in successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("Invalid username or password")

        with col2:
            if st.button("Register"):
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    success, message = register_user(username, password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

        with col3:
            if st.button("Create Admin Account"):
                if not username or not password:
                    st.error("Please enter both username and password")
                elif admin_exists():
                    st.error("An admin account already exists")
                else:
                    success, message = register_user(username, password, is_admin=True)
                    if success:
                        st.success("Admin account created successfully")
                    else:
                        st.error(message)

def require_login(func):
    def wrapper(*args, **kwargs):
        if 'username' not in st.session_state or not st.session_state.username:
            st.error("Please log in to access this page.")
            return
        return func(*args, **kwargs)
    return wrapper
