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
            password VARCHAR(255) NOT NULL
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

# Hash password
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Verify password
def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

# Register user
def register_user(username, password):
    conn = get_db_connection()
    cur = conn.cursor()
    hashed_password = hash_password(password)
    try:
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
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
        choice = st.sidebar.selectbox("Login/Signup", ["Login", "Sign Up"])
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")

        if choice == "Sign Up":
            if st.sidebar.button("Create Account"):
                if register_user(username, password):
                    st.sidebar.success("Account created successfully. You can now log in.")
                else:
                    st.sidebar.error("Username already exists. Please choose a different username.")
        else:
            if st.sidebar.button("Login"):
                if authenticate_user(username, password):
                    st.session_state.username = username
                    st.experimental_rerun()
                else:
                    st.sidebar.error("Invalid username or password")

# Require login decorator
def require_login(func):
    def wrapper(*args, **kwargs):
        if 'username' not in st.session_state or not st.session_state.username:
            st.error("Please log in to access this page.")
            return
        return func(*args, **kwargs)
    return wrapper
