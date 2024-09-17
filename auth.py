import streamlit as st
import psycopg2
import bcrypt
import os

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.environ['PGHOST'],
        database=os.environ['PGDATABASE'],
        user=os.environ['PGUSER'],
        password=os.environ['PGPASSWORD'],
        port=os.environ['PGPORT']
    )

# Create users table if not exists
def create_users_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

# Register new user
def register_user(username, password):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password.decode('utf-8')))
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        return False
    finally:
        cur.close()
        conn.close()

# Authenticate user
def authenticate_user(username, password):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT password FROM users WHERE username = %s", (username,))
    result = cur.fetchone()
    
    if result:
        stored_password = result[0].encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_password):
            cur.close()
            conn.close()
            return True
    
    cur.close()
    conn.close()
    return False

# Initialize session state
def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ''

# Login user
def login(username, password):
    if authenticate_user(username, password):
        st.session_state.logged_in = True
        st.session_state.username = username
        st.rerun()
        return True
    return False

# Logout user
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ''
    st.rerun()

# Display login/register form
def auth_form():
    init_session_state()
    
    if not st.session_state.logged_in:
        st.sidebar.subheader("Login / Register")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        col1, col2 = st.sidebar.columns(2)
        
        if col1.button("Login"):
            if login(username, password):
                pass  # Remove the success message
            else:
                st.sidebar.error("Invalid username or password")
        
        if col2.button("Register"):
            if register_user(username, password):
                st.sidebar.success("Registration successful. Please log in.")
            else:
                st.sidebar.error("Username already exists")
    else:
        st.sidebar.text(f"Logged in as {st.session_state.username}")
        if st.sidebar.button("Logout"):
            logout()
            # Remove the info message

# Ensure user is logged in
def require_login():
    if not st.session_state.logged_in:
        st.warning("Please log in to access this feature")
        st.stop()

# Create users table on startup
create_users_table()
