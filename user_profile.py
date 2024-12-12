import streamlit as st
import os
from datetime import datetime

# Initialize session states
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'profile_edit_mode' not in st.session_state:
    st.session_state.profile_edit_mode = False

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
    .stApp {
        background-color: #1a1f2e !important;
        color: #ffffff !important;
    }
    
    /* Main container styling */
    .main > div {
        padding: 2rem;
        max-width: 800px;
        margin: 0 auto;
    }
    
    /* Form styling */
    .stTextInput > div > div, .stTextArea > div > div, .stSelectbox > div > div {
        background-color: #2a2f3e !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 4px !important;
        color: white !important;
    }
    
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        color: white !important;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        padding: 0.75rem 1.5rem;
        background-color: #2D7FF9 !important;
        color: white !important;
        border-radius: 4px !important;
        margin-top: 1rem;
        border: none !important;
        font-weight: 500;
        transition: background-color 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #2567cc !important;
        transform: translateY(-1px);
    }
    
    /* Profile container */
    .profile-container {
        background: rgba(42, 47, 62, 0.95) !important;
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Section styling */
    .section-header {
        color: #ffffff !important;
        font-size: 1.2rem;
        font-weight: 600;
        margin: 2rem 0 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #2D7FF9;
        text-transform: uppercase;
        letter-spacing: 0.05em;
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
        box-shadow: 0 0 20px rgba(45, 127, 249, 0.3);
    }
    
    /* Stats container */
    .stats-container {
        background: rgba(45, 127, 249, 0.1) !important;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border: 1px solid rgba(45, 127, 249, 0.2);
    }
    
    /* Labels and text */
    .stSelectbox label, .stTextInput label, .stTextArea label {
        color: #ffffff !important;
        font-weight: 500;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Metrics styling */
    .css-1wivap2 {
        background-color: rgba(42, 47, 62, 0.95) !important;
        border: 1px solid rgba(45, 127, 249, 0.2) !important;
        padding: 1rem !important;
        border-radius: 8px !important;
    }
    
    .css-1wivap2 label {
        color: #ffffff !important;
    }
    
    .css-1wivap2 .css-81oif8 {
        color: #2D7FF9 !important;
        font-size: 1.5rem !important;
    }
    
    /* Error message */
    .error-msg {
        color: #ff4d4d;
        padding: 0.75rem;
        margin: 0.75rem 0;
        font-size: 0.9rem;
        background: rgba(255, 77, 77, 0.1);
        border-radius: 4px;
        border-left: 4px solid #ff4d4d;
    }
    
    /* Success message */
    .success-msg {
        color: #4ecdc4;
        padding: 0.75rem;
        margin: 0.75rem 0;
        font-size: 0.9rem;
        background: rgba(78, 205, 196, 0.1);
        border-radius: 4px;
        border-left: 4px solid #4ecdc4;
    }
    
    /* Additional UI improvements */
    .stMarkdown {
        color: #ffffff !important;
    }
    
    .streamlit-expanderHeader {
        background-color: #2a2f3e !important;
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

def user_profile():
    if not st.session_state.logged_in:
        st.warning("Please log in to view your profile")
        return

    st.markdown('<div class="profile-container">', unsafe_allow_html=True)
    
    # Profile Header
    st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>My Profile</h1>", unsafe_allow_html=True)
    
    # Profile Picture Section
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("static/default_profile.png", width=150, caption="Profile Picture")
        if st.button("Change Profile Picture", key="change_pic"):
            st.info("Profile picture upload feature coming soon!")
    
    # Edit/View Mode Toggle
    edit_mode = st.toggle("Edit Profile", value=st.session_state.profile_edit_mode)
    st.session_state.profile_edit_mode = edit_mode
    
    # Personal Information Section
    st.markdown("<div class='section-header'>Personal Information</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        if edit_mode:
            full_name = st.text_input("Full Name", value="John Doe", key="name_edit")
            email = st.text_input("Email", value="john@example.com", key="email_edit")
        else:
            st.markdown("**Full Name:** John Doe")
            st.markdown("**Email:** john@example.com")
            
    with col2:
        if edit_mode:
            username = st.text_input("Username", value="johndoe", key="username_edit")
            phone = st.text_input("Phone", value="+1 234 567 8900", key="phone_edit")
        else:
            st.markdown("**Username:** johndoe")
            st.markdown("**Phone:** +1 234 567 8900")
    
    # Style Preferences Section
    st.markdown("<div class='section-header'>Style Preferences</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        if edit_mode:
            preferred_style = st.selectbox("Preferred Style", 
                                         ["Casual", "Formal", "Sport", "Beach"],
                                         key="style_edit")
            size = st.selectbox("Size", ["S", "M", "L", "XL"], key="size_edit")
        else:
            st.markdown("**Preferred Style:** Casual")
            st.markdown("**Size:** M")
            
    with col2:
        if edit_mode:
            gender = st.selectbox("Gender", 
                                ["Male", "Female", "Unisex"],
                                key="gender_edit")
            notes = st.text_area("Additional Notes", 
                               "I prefer dark colors and comfortable fits.",
                               key="notes_edit")
        else:
            st.markdown("**Gender:** Male")
            st.markdown("**Additional Notes:** I prefer dark colors and comfortable fits.")
    
    # Account Statistics (Read-only)
    st.markdown("<div class='section-header'>Account Statistics</div>", unsafe_allow_html=True)
    st.markdown('<div class="stats-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Wardrobe Items", "42")
    with col2:
        st.metric("Outfits Created", "15")
    with col3:
        st.metric("Days Active", "30")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Save Changes Button (only in edit mode)
    if edit_mode:
        if st.button("Save Changes", type="primary"):
            st.success("Profile updated successfully!")
            st.session_state.profile_edit_mode = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    user_profile()