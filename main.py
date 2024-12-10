import streamlit as st
import os
from auth import (
    render_login_ui, create_auth_tables, handle_callback,
    is_admin, admin_required
)

# Initialize the authentication tables
create_auth_tables()

# Set up the page configuration
st.set_page_config(
    page_title="Outfit Wizard - Authentication",
    page_icon="🔐",
    layout="centered"
)

def main():
    # Check for OAuth callback
    if "code" in st.experimental_get_query_params():
        handle_callback()
        
    # Show login UI if not authenticated
    if not st.session_state.get("authenticated", False):
        render_login_ui()
        return

    # Show different content based on user role
    if is_admin():
        st.title("Admin Dashboard")
        st.success(f"Welcome, Admin {st.session_state.user['name']}!")
        
        # Add admin-specific functionality
        st.subheader("User Management")
        st.write("Here you can manage users and their roles.")
        
        # Example admin action
        if st.button("View All Users"):
            st.write("Feature coming soon...")
    else:
        st.title("User Dashboard")
        st.success(f"Welcome, {st.session_state.user['name']}!")
        st.write("Access your personalized content here.")
        
        # Example user action
        if st.button("View My Profile"):
            st.write("Feature coming soon...")

if __name__ == "__main__":
    main()