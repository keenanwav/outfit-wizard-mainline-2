import streamlit as st
from firebase_config import verify_firebase_token, set_current_user, clear_current_user

def handle_auth_callback():
    """Handle Firebase authentication callback"""
    try:
        # Get the ID token from the URL parameters
        params = st.experimental_get_query_params()
        id_token = params.get('token', [None])[0]
        
        if id_token:
            # Verify the Firebase ID token
            decoded_token = verify_firebase_token(id_token)
            if decoded_token:
                # Set user in session state
                user_data = {
                    'uid': decoded_token['uid'],
                    'email': decoded_token.get('email'),
                    'name': decoded_token.get('name'),
                    'picture': decoded_token.get('picture')
                }
                set_current_user(user_data)
                st.success('Successfully logged in!')
                # Redirect to main page
                st.experimental_set_query_params()
                st.rerun()
            else:
                st.error('Invalid authentication token')
                clear_current_user()
    except Exception as e:
        st.error(f'Authentication error: {str(e)}')
        clear_current_user()

def handle_logout():
    """Handle user logout"""
    clear_current_user()
    st.success('Successfully logged out!')
    st.rerun()
