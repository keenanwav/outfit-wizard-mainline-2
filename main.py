import streamlit as st
from middleware import error_middleware
import os
import logging
import time
from error_pages import init_error_handlers, handle_error

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Load custom CSS with error handling
def load_custom_css():
    """Load custom CSS with improved error handling"""
    try:
        with open('static/style.css', 'r') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        logging.error(f"Error loading CSS: {str(e)}")
        handle_error('500')

def test_error_pages():
    """Test different error pages"""
    st.title("Error Pages Test")
    
    # Load CSS for error pages
    load_custom_css()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Test Error Pages")
        if st.button("Test 404 Error"):
            st.session_state.error_state = '404'
            st.rerun()
            
        if st.button("Test 500 Error"):
            st.session_state.error_state = '500'
            st.rerun()
            
        if st.button("Test WebSocket Error"):
            st.session_state.error_state = 'websocket'
            st.rerun()
            
        if st.button("Test Maintenance Mode"):
            st.session_state.error_state = 'maintenance'
            st.rerun()
            
    with col2:
        st.subheader("Current State")
        st.write(f"Error State: {st.session_state.error_state}")
        if st.button("Clear Error State"):
            st.session_state.error_state = None
            st.rerun()

# Main application with error handling decorator
@error_middleware
def main():
    try:
        # Initialize session state
        if 'error_state' not in st.session_state:
            st.session_state.error_state = None
            
        # Initialize error handlers
        init_error_handlers()
        
        # Set page config
        st.set_page_config(
            page_title="OutfitWiz",
            page_icon="👕",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Load CSS first to ensure styles are available
        load_custom_css()
        
        # Check for error state
        if st.session_state.error_state:
            handle_error(st.session_state.error_state)
            return
        
        # Add a navigation sidebar
        page = st.sidebar.radio(
            "Navigation",
            ["Home", "Test Error Pages"]
        )
        
        if page == "Test Error Pages":
            test_error_pages()
        else:
            st.title("OutfitWiz")
            st.write("Welcome to OutfitWiz! Use the sidebar to navigate.")
            st.write("Try the 'Test Error Pages' section to see custom error handling in action.")

    except Exception as e:
        logging.error(f"Error in main application: {str(e)}")
        handle_error('500')

if __name__ == "__main__":
    main()
