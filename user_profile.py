import streamlit as st
import os
import requests
import bcrypt
from datetime import datetime

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Page configuration
st.set_page_config(
    page_title="Login",
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon="🔒"
)

# Set dark theme
st.markdown("""
    <script>
        var observer = new MutationObserver(function(mutations) {
            document.body.classList.add('dark');
        });
        observer.observe(document.body, { attributes: true });
    </script>
""", unsafe_allow_html=True)

# Custom CSS to match existing design
st.markdown("""
    <style>
    /* Global styles */
    body {
        background-color: #1a1f2e;
        color: white;
    }
    
    /* Main container styling */
    .main > div {
        padding: 2rem;
        max-width: 400px;
        margin: 0 auto;
    }
    
    /* Form styling */
    .stTextInput > div > div {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 4px;
        color: white;
    }
    
    .stTextInput input {
        color: white !important;
    }
    
    .stButton > button {
        width: 100%;
        padding: 0.75rem 1.5rem;
        background-color: #2D7FF9;
        color: white;
        border-radius: 4px;
        margin-top: 1.5rem;
        border: none;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #2567cc;
    }
    
    /* Login container */
    .login-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 2rem;
    }
    
    /* Logo styling */
    .logo-container {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .logo-container img {
        max-width: 150px;
        margin-bottom: 1rem;
    }
    
    /* Labels */
    .stTextInput label {
        color: rgba(255, 255, 255, 0.8);
    }
    
    /* Error message */
    .error-msg {
        color: #ff4d4d;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        background: rgba(255, 77, 77, 0.1);
        border-radius: 4px;
    }
    
    /* Links */
    a {
        color: #2D7FF9;
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
    </style>
""", unsafe_allow_html=True)

# Load and display logo
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("static/login_logo.png", use_column_width=True)

# Login container
st.markdown('<div class="login-container">', unsafe_allow_html=True)

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center; margin-bottom: 2rem;'>Welcome Back</h2>", unsafe_allow_html=True)
    
    # Login form
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Sign In"):
            # Here you would normally verify against a database
            # For now, we'll use a simple check
            if email == "demo@example.com" and password == "password":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid email or password")
    
    # Additional options
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div style='text-align: left'><a href='#'>Forgot password?</a></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='text-align: right'><a href='#'>Create account</a></div>", unsafe_allow_html=True)

else:
    st.success("Successfully logged in!")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)