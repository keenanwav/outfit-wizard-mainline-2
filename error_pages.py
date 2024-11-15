import streamlit as st
import sys
import time
import logging
from datetime import datetime

def track_error(error_type, error_info=None):
    """Track error occurrences with timestamp"""
    error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_log = f"{error_time} - {error_type}"
    if error_info:
        error_log += f": {error_info}"
    
    if 'error_history' not in st.session_state:
        st.session_state.error_history = []
    st.session_state.error_history.append(error_log)
    
    # Keep only last 100 errors
    st.session_state.error_history = st.session_state.error_history[-100:]

def show_error_page(error_code, message, submessage=None, retry_action=None):
    """Generic error page display function with enhanced styling and retry action"""
    st.markdown("""
    <style>
    .error-container {
        text-align: center;
        padding: 50px;
        margin: 50px auto;
        max-width: 800px;
        background: rgba(255, 75, 75, 0.1);
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
        animation: fadeIn 0.5s ease-in-out;
    }
    .error-code {
        font-size: 72px;
        color: #FF4B4B;
        margin-bottom: 20px;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
        animation: pulse 2s infinite;
    }
    .error-message {
        font-size: 24px;
        color: #FAFAFA;
        margin-bottom: 30px;
        font-weight: 500;
    }
    .error-submessage {
        font-size: 18px;
        color: #CCCCCC;
        margin-bottom: 30px;
        line-height: 1.5;
    }
    .action-button {
        background-color: #FF4B4B;
        color: white;
        padding: 12px 24px;
        border-radius: 5px;
        text-decoration: none;
        margin: 10px;
        display: inline-block;
        cursor: pointer;
        font-weight: 500;
        transition: all 0.3s ease;
        border: none;
        outline: none;
    }
    .action-button:hover {
        background-color: #FF6B6B;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    .loading-spinner {
        margin: 20px auto;
        width: 40px;
        height: 40px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #FF4B4B;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .error-details {
        font-family: monospace;
        background: rgba(0, 0, 0, 0.2);
        padding: 15px;
        border-radius: 5px;
        margin-top: 20px;
        text-align: left;
        font-size: 14px;
        color: #CCCCCC;
        max-height: 200px;
        overflow-y: auto;
    }
    .retry-countdown {
        font-size: 16px;
        color: #CCCCCC;
        margin-top: 10px;
        animation: fadeIn 0.3s ease-in-out;
    }
    </style>
    """, unsafe_allow_html=True)
    
    track_error(error_code, message)
    
    st.markdown(f"""
    <div class="error-container">
        <div class="error-code">{error_code}</div>
        <div class="error-message">{message}</div>
        {f'<div class="error-submessage">{submessage}</div>' if submessage else ''}
        {f'<div class="loading-spinner"></div>' if retry_action else ''}
    </div>
    """, unsafe_allow_html=True)
    
    if retry_action:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Retry Connection", key="retry_button", help="Attempt to reconnect to the server"):
                retry_action()
        with col2:
            if st.button("Return to Home", key="home_button"):
                st.switch_page("main.py")
    else:
        if st.button("Return to Home", key="home_button", use_container_width=True):
            st.switch_page("main.py")
    
    if st.session_state.get('show_error_details', False):
        st.markdown("<div class='error-details'>", unsafe_allow_html=True)
        for error in st.session_state.get('error_history', []):
            st.markdown(f"```\n{error}\n```")
        st.markdown("</div>", unsafe_allow_html=True)

def show_404_page():
    """Display 404 error page"""
    show_error_page(
        404,
        "Page Not Found",
        "The outfit you're looking for seems to be missing from our wardrobe. Let's help you find something else!"
    )

def show_500_page():
    """Display 500 error page"""
    show_error_page(
        500,
        "Internal Server Error",
        "Our wardrobe is experiencing technical difficulties. Our fashion experts are working on it!"
    )

def show_websocket_error(retry_count=0):
    """Display WebSocket connection error page with enhanced retry mechanism"""
    max_retries = 3
    if retry_count < max_retries:
        def retry_action():
            # Exponential backoff with max delay of 8 seconds
            backoff_time = min(2 ** retry_count, 8)
            time.sleep(backoff_time)
            st.session_state.connection_healthy = True
            st.session_state.websocket_retry_count = 0
            st.rerun()
        
        show_error_page(
            1006,
            "Connection Error",
            f"Having trouble connecting to our fashion network. Attempting to reconnect... (Try {retry_count + 1}/{max_retries})",
            retry_action=retry_action
        )
        
        # Show countdown for next retry
        if retry_count > 0:
            st.markdown(f"""
            <div class="retry-countdown">
                Next retry in {min(2 ** retry_count, 8)} seconds...
            </div>
            """, unsafe_allow_html=True)
    else:
        show_error_page(
            1006,
            "Connection Lost",
            "Unable to establish a stable connection. Please check your internet connection and try again later."
        )

def show_asset_404_error():
    """Display 404 error for missing static assets"""
    show_error_page(
        404,
        "Asset Not Found",
        "The requested image or resource could not be found. It may have been moved or deleted."
    )

def show_maintenance_error():
    """Display maintenance mode error page"""
    show_error_page(
        503,
        "Under Maintenance",
        "We're making our wardrobe even better! Please check back in a few minutes."
    )

def handle_error(error_type, error_info=None):
    """Enhanced error handler with logging and retry mechanism"""
    logger = logging.getLogger(__name__)
    
    if 'error_retry_count' not in st.session_state:
        st.session_state.error_retry_count = 0
    if 'connection_healthy' not in st.session_state:
        st.session_state.connection_healthy = True
    
    error_map = {
        404: show_404_page,
        500: show_500_page,
        503: show_maintenance_error,
        'websocket': lambda: show_websocket_error(st.session_state.error_retry_count),
        'asset_404': show_asset_404_error
    }
    
    if error_info:
        logger.error(f"Error type: {error_type}, Details: {error_info}")
    
    if error_type == 'websocket':
        st.session_state.connection_healthy = False
        st.session_state.error_retry_count += 1
        if st.session_state.error_retry_count > 3:
            st.session_state.error_retry_count = 0
            st.session_state.connection_healthy = True
    
    error_func = error_map.get(error_type, show_500_page)
    error_func()
    
    return False

# Initialize error tracking in development mode
if not st.session_state.get('error_tracking_initialized', False):
    st.session_state.show_error_details = False
    st.session_state.error_history = []
    st.session_state.error_tracking_initialized = True
