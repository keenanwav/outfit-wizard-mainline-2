import streamlit as st
import time
import logging
from datetime import datetime
import random

def show_404_error():
    """Display 404 error page with improved styling"""
    st.markdown("""
    <div class="error-container not-found-container">
        <div class="error-header">
            <span class="error-icon">🔍</span>
            <h2 class="error-title">Page Not Found</h2>
        </div>
        <div class="error-message">
            <p>We couldn't find what you're looking for.</p>
            
            <div class="quick-links">
                <h3>Quick Navigation:</h3>
                <ul>
                    <li><a href="/">Return to Home</a></li>
                    <li><a href="/My%20Items">Browse Wardrobe</a></li>
                    <li><a href="/">Generate Outfit</a></li>
                </ul>
            </div>
        </div>
        <div class="error-actions">
            <a href="/" class="retry-button">Return Home</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_500_error():
    """Display 500 error page with improved styling"""
    st.markdown("""
    <div class="error-container server-error-container">
        <div class="error-header">
            <span class="error-icon">⚠️</span>
            <h2 class="error-title">Oops! Something Went Wrong</h2>
        </div>
        <div class="error-message">
            <p>We're experiencing technical difficulties with OutfitWiz.</p>
            
            <div class="troubleshooting-tips">
                <h3>Quick Fixes:</h3>
                <ul>
                    <li>Clear your browser cache</li>
                    <li>Refresh the page</li>
                    <li>Try again in a few moments</li>
                </ul>
            </div>
        </div>
        <div class="loading-spinner"></div>
        <div class="error-actions">
            <button onclick="window.location.reload()" class="retry-button">Try Again</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_websocket_error():
    """Display WebSocket connection error page with enhanced retry mechanism"""
    status = st.session_state.get('connection_status', {
        'retry_count': 0,
        'max_retries': 3,
        'backoff_time': 1.0
    })
    
    progress = min((status['retry_count'] / status['max_retries']) * 100, 100)
    
    st.markdown(f"""
    <div class="error-container websocket-error">
        <div class="error-header">
            <span class="error-icon">🔄</span>
            <h2 class="error-title">Reconnecting to OutfitWiz...</h2>
        </div>
        <div class="error-message">
            <p>We're trying to restore your connection.</p>
            
            <div class="connection-status">
                <p>Attempt {status['retry_count']} of {status['max_retries']}</p>
                <p>Next retry in {status['backoff_time']:.1f} seconds</p>
            </div>
            
            <div class="troubleshooting-tips">
                <h3>Connection Tips:</h3>
                <ul>
                    <li>Check your internet connection</li>
                    <li>Clear browser cache</li>
                    <li>Try a different browser</li>
                </ul>
            </div>
        </div>
        <div class="progress-bar">
            <div class="progress-bar-fill" style="width: {progress}%"></div>
        </div>
        <div class="error-actions">
            <button onclick="window.location.reload()" class="retry-button">Retry Now</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    time.sleep(status['backoff_time'])
    st.rerun()

def show_maintenance_mode():
    """Display maintenance mode page with improved styling"""
    st.markdown("""
    <div class="error-container maintenance-container">
        <div class="error-header">
            <span class="error-icon">🛠️</span>
            <h2 class="error-title">Quick Maintenance Break</h2>
        </div>
        <div class="error-message">
            <p>OutfitWiz is getting a quick update to serve you better!</p>
            
            <div class="maintenance-status">
                <h3>Status Update:</h3>
                <ul>
                    <li>System maintenance in progress</li>
                    <li>Expected duration: 1-2 minutes</li>
                    <li>Your wardrobe data is safe</li>
                </ul>
            </div>
            
            <p class="maintenance-note">The app will refresh automatically when ready.</p>
        </div>
        <div class="loading-spinner"></div>
        <div class="progress-bar">
            <div class="progress-bar-fill maintenance-progress"></div>
        </div>
        <div class="error-actions">
            <button onclick="window.location.reload()" class="retry-button">Check Status</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    time.sleep(3)
    st.rerun()

def init_error_handlers():
    """Initialize error handling in Streamlit app"""
    if 'error_state' not in st.session_state:
        st.session_state.error_state = None
    
    if 'connection_status' not in st.session_state:
        st.session_state.connection_status = {
            'retry_count': 0,
            'max_retries': 3,
            'backoff_time': 1.0,
            'last_retry': None,
            'last_successful': time.time()
        }
    
    logging.info("Error handlers initialized successfully")

def handle_error(error_type):
    """Route to appropriate error handler"""
    try:
        error_handlers = {
            '404': show_404_error,
            '500': show_500_error,
            'websocket': show_websocket_error,
            'maintenance': show_maintenance_mode
        }
        
        if error_type in error_handlers:
            error_handlers[error_type]()
            return True
        
        show_500_error()
        return True
        
    except Exception as e:
        logging.error(f"Error in error handler: {str(e)}")
        show_500_error()
        return True
