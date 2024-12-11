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

st.set_page_config(page_title="User Profile", layout="wide")

# Custom CSS to match the design
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #f8f9fa;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        background-color: white;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e9ecef;
    }
    div[data-testid="stVerticalBlock"] > div:has(div.stButton) {
        text-align: right;
    }
    </style>
""", unsafe_allow_html=True)

# Main title with styling
st.title("User Profile")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Profile", "Subscription", "Usage", "Settings"])

with tab1:
    st.subheader("Profile")
    st.caption("Manage your profile information")
    
    # Avatar and user info in columns
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
        st.caption("SaaS User")
    
    # Profile form
    with st.form("profile_form"):
        name = st.text_input("Name", value=st.session_state.user_data["name"])
        email = st.text_input("Email", value=st.session_state.user_data["email"], type="default")
        
        submit = st.form_submit_button("Update Profile", type="primary")
        if submit:
            st.session_state.user_data.update({
                "name": name,
                "email": email
            })
            st.success("Profile updated successfully!")

with tab2:
    st.subheader("Subscription Details")
    st.caption("Manage your subscription plan")
    
    # Current plan and status
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("##### Current Plan")
        st.markdown(f"### {st.session_state.user_data['subscription']['plan']}")
    with col2:
        status = st.session_state.user_data['subscription']['status']
        st.markdown(
            f"""<div style='background-color: #d4edda; 
            color: #155724; padding: 10px; 
            border-radius: 4px; text-align: center;'>
            {status}</div>""", 
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    # Subscription details
    st.markdown("📅 Renews on " + st.session_state.user_data['subscription']['renewal_date'])
    st.markdown("💳 Visa ending in 1234")
    
    st.button("Upgrade Plan", type="primary", use_container_width=True)

with tab3:
    st.subheader("Usage Statistics")
    st.caption("Monitor your resource usage")
    
    # Storage usage
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("##### Storage")
        st.progress(st.session_state.user_data["usage"]["storage"] / 100)
    with col2:
        st.markdown("")  # Spacing
        st.markdown(f"{st.session_state.user_data['usage']['storage']}%")
    
    # API calls
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("##### API Calls")
        st.progress(st.session_state.user_data["usage"]["api_calls"] / 10000)
    with col2:
        st.markdown("")  # Spacing
        st.markdown(f"{st.session_state.user_data['usage']['api_calls']}/10000")
    
    # Projects
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("##### Projects")
        st.progress(st.session_state.user_data["usage"]["projects"] / 15)
    with col2:
        st.markdown("")  # Spacing
        st.markdown(f"{st.session_state.user_data['usage']['projects']}/15")

with tab4:
    st.subheader("Account Settings")
    st.caption("Manage your account preferences")
    
    # Two-Factor Authentication
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("##### Two-Factor Authentication")
        st.caption("Add an extra layer of security to your account")
    with col2:
        st.button("Enable", key="2fa_enable")
    
    st.markdown("---")
    
    # Email Notifications
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("##### Email Notifications")
        st.caption("Receive updates about your account activity")
    with col2:
        st.button("Configure", key="email_config")
    
    st.markdown("---")
    
    # Delete Account
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("##### Delete Account")
        st.caption("Permanently remove your account and all data")
    with col2:
        st.button("Delete", key="delete_account", type="secondary")
