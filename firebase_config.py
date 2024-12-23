import os
import firebase_admin
from firebase_admin import credentials, auth
import streamlit as st

def initialize_firebase():
    """Initialize Firebase Admin SDK with environment variables"""
    try:
        # Check if Firebase is already initialized
        firebase_admin.get_app()
    except ValueError:
        # Get required environment variables
        project_id = os.environ.get("FIREBASE_PROJECT_ID")
        if not project_id:
            st.error("Firebase Project ID is not configured. Please set the FIREBASE_PROJECT_ID environment variable.")
            return False

        # Initialize Firebase with minimal required credentials
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": project_id
        })

        # Initialize with storage bucket if available
        storage_bucket = os.environ.get("FIREBASE_STORAGE_BUCKET")
        options = {'storageBucket': storage_bucket} if storage_bucket else {}

        try:
            firebase_admin.initialize_app(cred, options)
            return True
        except Exception as e:
            st.error(f"Failed to initialize Firebase: {str(e)}")
            return False
    return True

def get_firebase_config():
    """Get Firebase configuration for client-side initialization"""
    required_vars = [
        "FIREBASE_API_KEY",
        "FIREBASE_AUTH_DOMAIN",
        "FIREBASE_PROJECT_ID"
    ]

    # Check for required variables
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        st.error(f"Missing required Firebase configuration: {', '.join(missing_vars)}")
        return None

    return {
        'apiKey': os.environ.get("FIREBASE_API_KEY"),
        'authDomain': os.environ.get("FIREBASE_AUTH_DOMAIN"),
        'projectId': os.environ.get("FIREBASE_PROJECT_ID"),
        'storageBucket': os.environ.get("FIREBASE_STORAGE_BUCKET"),
        'messagingSenderId': os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
        'appId': os.environ.get("FIREBASE_APP_ID"),
        'measurementId': os.environ.get("FIREBASE_MEASUREMENT_ID")
    }

def verify_firebase_token(id_token):
    """Verify Firebase ID token"""
    if not id_token:
        return None

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        st.error(f"Error verifying token: {str(e)}")
        return None

def get_current_user():
    """Get current user from session state"""
    return st.session_state.get('user', None)

def set_current_user(user_data):
    """Set current user in session state"""
    st.session_state['user'] = user_data

def clear_current_user():
    """Clear current user from session state"""
    if 'user' in st.session_state:
        del st.session_state['user']