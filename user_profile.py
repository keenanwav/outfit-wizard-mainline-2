import streamlit as st
import os
from datetime import datetime

# Initialize session states
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'editing_item' not in st.session_state:
    st.session_state.editing_item = None
if 'editing_image' not in st.session_state:
    st.session_state.editing_image = None
if 'editing_color' not in st.session_state:
    st.session_state.editing_color = None

# Page configuration
st.set_page_config(
    page_title="User Profile",
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon="👤"
)

# Custom CSS to match dark theme design
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
        max-width: 800px;
        margin: 0 auto;
    }
    
    /* Form styling */
    .stTextInput > div > div, .stTextArea > div > div {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 4px;
        color: white;
    }
    
    .stTextInput input, .stTextArea textarea {
        color: white !important;
    }
    
    .stButton > button {
        width: 100%;
        padding: 0.75rem 1.5rem;
        background-color: #2D7FF9;
        color: white;
        border-radius: 4px;
        margin-top: 1rem;
        border: none;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #2567cc;
    }
    
    /* Profile container */
    .profile-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 2rem;
    }
    
    /* Section styling */
    .section-header {
        color: white;
        font-size: 1.2rem;
        font-weight: 500;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Profile picture */
    .profile-picture {
        width: 150px;
        height: 150px;
        border-radius: 50%;
        margin: 0 auto;
        display: block;
        object-fit: cover;
        border: 3px solid #2D7FF9;
    }
    
    /* Stats container */
    .stats-container {
        background: rgba(45, 127, 249, 0.1);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Labels */
    .stSelectbox label, .stTextInput label {
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
    
    /* Success message */
    .success-msg {
        color: #4ecdc4;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        background: rgba(78, 205, 196, 0.1);
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

def user_profile():
    st.markdown('<div class="profile-container">', unsafe_allow_html=True)
    
    # Profile Header
    st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>My Profile</h1>", unsafe_allow_html=True)
    
    # Profile Picture
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("static/default_profile.png", use_column_width=True, caption="Profile Picture")
        st.button("Change Profile Picture")
    
    # Personal Information Section
    st.markdown("<div class='section-header'>Personal Information</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Full Name", value="John Doe")
        st.text_input("Email", value="john@example.com")
    with col2:
        st.text_input("Username", value="johndoe")
        st.text_input("Phone", value="+1 234 567 8900")
    
    # Preferences Section
    st.markdown("<div class='section-header'>Style Preferences</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Preferred Style", ["Casual", "Formal", "Sport", "Beach"])
        st.selectbox("Size", ["S", "M", "L", "XL"])
    with col2:
        st.selectbox("Gender", ["Male", "Female", "Unisex"])
        st.text_area("Additional Notes", "I prefer dark colors and comfortable fits.")
    
    # Statistics Section
    st.markdown("<div class='section-header'>Wardrobe Statistics</div>", unsafe_allow_html=True)
    st.markdown('<div class="stats-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Items", "42")
    with col2:
        st.metric("Outfits Created", "15")
    with col3:
        st.metric("Favorite Style", "Casual")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Save Changes Button
    if st.button("Save Changes"):
        st.success("Profile updated successfully!")
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    user_profile()