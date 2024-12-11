import streamlit as st
import os
import requests
from datetime import datetime

# Initialize session state
if 'user_data' not in st.session_state:
    st.session_state.user_data = {
        "name": "Alex Johnson",
        "email": "alex@example.com",
        "avatar_url": "https://api.dicebear.com/6.x/avataaars/svg?seed=Alex",
        "subscription": {
            "plan": "Pro",
            "status": "Active",
            "renewal_date": "2023-12-31"
        },
        "usage": {
            "storage": 75,
            "api_calls": 8500,
            "projects": 12
        }
    }

# Page configuration
st.set_page_config(
    page_title="User Profile",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS to match design
st.markdown("""
    <style>
    /* Main container styling */
    .main > div {
        padding: 2rem;
        max-width: 800px;
        margin: 0 auto;
    }
    
    /* Tabs styling */
    .stTabs {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.5rem;
        font-size: 0.9rem;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: white;
        border-radius: 4px;
        font-weight: 600;
    }
    
    /* Form styling */
    .stTextInput > div > div {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
    }
    
    .stButton > button {
        width: auto;
        padding: 0.5rem 1.5rem;
        background-color: black;
        color: white;
        border-radius: 4px;
    }
    
    /* Profile section styling */
    .profile-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .user-info h1 {
        margin: 0;
        font-size: 1.5rem;
    }
    
    .user-info p {
        margin: 0;
        color: #6c757d;
    }
    
    /* Card styling */
    .stCard {
        padding: 1.5rem;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        background-color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Profile", "Subscription", "Usage", "Settings"])

with tab1:
    # Profile Section
    st.markdown("### Profile")
    st.markdown("Manage your profile information")
    
    # Profile header with avatar and name
    col1, col2 = st.columns([1, 3])
    
    with col1:
        try:
            response = requests.get(st.session_state.user_data["avatar_url"])
            if response.status_code == 200:
                st.image(st.session_state.user_data["avatar_url"], width=100)
            else:
                st.warning("Using default avatar")
        except Exception:
            st.warning("Unable to load avatar")
            
    with col2:
        st.markdown(f"### {st.session_state.user_data['name']}")
        st.markdown("<p style='color: #6c757d;'>SaaS User</p>", unsafe_allow_html=True)
    
    # Profile form
    with st.form("profile_form"):
        st.text_input("Name", value=st.session_state.user_data["name"], key="name")
        st.text_input("Email", value=st.session_state.user_data["email"], key="email")
        
        col1, col2, col3 = st.columns([3, 3, 1])
        with col3:
            submit = st.form_submit_button("Update Profile")
        
        if submit:
            st.session_state.user_data.update({
                "name": st.session_state.name,
                "email": st.session_state.email
            })
            st.success("Profile updated successfully!")

with tab2:
    st.markdown("### Subscription Details")
    st.markdown("Manage your subscription plan")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**Current Plan**")
        st.markdown(f"### {st.session_state.user_data['subscription']['plan']}")
    with col2:
        st.markdown(
            f"""<div style='background-color: #d4edda; 
            color: #155724; padding: 8px 16px; 
            border-radius: 4px; text-align: center; 
            margin-top: 1rem;'>
            {st.session_state.user_data['subscription']['status']}</div>""", 
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    st.markdown("📅 Renews on " + st.session_state.user_data['subscription']['renewal_date'])
    st.markdown("💳 Visa ending in 1234")
    
    st.button("Upgrade Plan", type="primary", use_container_width=True)

with tab3:
    st.markdown("### Usage Statistics")
    st.markdown("Monitor your resource usage")
    
    # Storage usage
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("**Storage**")
        st.progress(st.session_state.user_data["usage"]["storage"] / 100)
    with col2:
        st.markdown(f"{st.session_state.user_data['usage']['storage']}%")
    
    # API calls
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("**API Calls**")
        st.progress(st.session_state.user_data["usage"]["api_calls"] / 10000)
    with col2:
        st.markdown(f"{st.session_state.user_data['usage']['api_calls']}/10000")
    
    # Projects
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("**Projects**")
        st.progress(st.session_state.user_data["usage"]["projects"] / 15)
    with col2:
        st.markdown(f"{st.session_state.user_data['usage']['projects']}/15")

with tab4:
    st.markdown("### Account Settings")
    st.markdown("Manage your account preferences")
    
    # Two-Factor Authentication
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**Two-Factor Authentication**")
        st.markdown("Add an extra layer of security to your account")
    with col2:
        st.button("Enable", key="2fa_enable")
    
    st.markdown("---")
    
    # Email Notifications
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**Email Notifications**")
        st.markdown("Receive updates about your account activity")
    with col2:
        st.button("Configure", key="email_config")
    
    st.markdown("---")
    
    # Delete Account
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**Delete Account**")
        st.markdown("Permanently remove your account and all data")
    with col2:
        st.button("Delete", key="delete_account", type="secondary")
