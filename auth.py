import streamlit as st
import bcrypt
import psycopg2
import os

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.environ['PGHOST'],
        database=os.environ['PGDATABASE'],
        user=os.environ['PGUSER'],
        password=os.environ['PGPASSWORD']
    )

# Create users table if not exists
def create_users_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

# Verify password
def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

# Authenticate user
def authenticate_user(username, password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE username = %s", (username,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result:
        return verify_password(password, result[0].encode('utf-8'))
    return False

# Streamlit login form
def auth_form():
    create_users_table()
    if 'username' not in st.session_state:
        st.session_state.username = None

    if st.session_state.username:
        st.sidebar.write(f"Logged in as {st.session_state.username}")
        if st.sidebar.button("Logout"):
            st.session_state.username = None
            st.experimental_rerun()
    else:
        st.header("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if authenticate_user(username, password):
                st.session_state.username = username
                st.success("Logged in successfully!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

# Require login decorator
def require_login(func):
    def wrapper(*args, **kwargs):
        if 'username' not in st.session_state or not st.session_state.username:
            st.error("Please log in to access this page.")
            return
        return func(*args, **kwargs)
    return wrapper
