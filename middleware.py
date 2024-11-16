import streamlit as st
from functools import wraps
import logging
from error_pages import handle_error, init_error_handlers
from typing import Callable, Any
import time
import random
from datetime import datetime, timedelta

def error_middleware(func: Callable) -> Callable:
    """Middleware to handle errors and display appropriate error pages"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            # Initialize error handlers if not already initialized
            if 'error_handlers_initialized' not in st.session_state:
                init_error_handlers()
                st.session_state.error_handlers_initialized = True
            
            # Handle request with improved error handling
            return handle_request(func, args, kwargs)
                
        except Exception as e:
            error_message = str(e).lower()
            logging.error(f"Application error: {str(e)}")
            
            # Enhanced error type detection with more specific patterns
            if any(err in error_message for err in [
                "websocket", "connection refused", "network unreachable",
                "timeout", "socket.gaierror", "connection reset",
                "broken pipe", "connection aborted", "502", "503", "504"
            ]):
                st.session_state.error_state = 'websocket'
                return handle_websocket_error()
            elif "404" in error_message or "not found" in error_message:
                st.session_state.error_state = '404'
                return handle_error('404')
            else:
                st.session_state.error_state = '500'
                return handle_error('500')
            
    return wrapper

def handle_request(func: Callable, args: tuple, kwargs: dict) -> Any:
    """Handle request with improved error handling and connection management"""
    # Initialize connection status if not exists
    if 'connection_status' not in st.session_state:
        st.session_state.connection_status = {
            'last_successful': time.time(),
            'retry_count': 0,
            'last_retry': None,
            'backoff_time': 1.0,
            'max_retries': 3,
            'retry_delay': 5
        }
    
    try:
        result = func(*args, **kwargs)
        # Reset connection status on success
        st.session_state.connection_status.update({
            'last_successful': time.time(),
            'retry_count': 0,
            'backoff_time': 1.0,
            'last_retry': None
        })
        st.session_state.error_state = None
        return result
    except Exception as e:
        error_message = str(e).lower()
        if isinstance(e, (ConnectionError, TimeoutError)) or any(err in error_message for err in [
            "websocket", "502", "503", "504"
        ]):
            return handle_websocket_error()
        raise

def handle_websocket_error() -> Any:
    """Handle WebSocket related errors with improved retry mechanism"""
    # Initialize or get connection status
    if 'connection_status' not in st.session_state:
        st.session_state.connection_status = {
            'last_successful': time.time(),
            'retry_count': 0,
            'last_retry': None,
            'backoff_time': 1.0,
            'max_retries': 3,
            'retry_delay': 5
        }
    
    status = st.session_state.connection_status
    current_time = time.time()
    
    # Update retry count and timestamp
    status['retry_count'] += 1
    status['last_retry'] = current_time
    
    # Calculate backoff time with jitter
    jitter = random.uniform(0, 0.1)
    status['backoff_time'] = min(status['retry_delay'] * (2 ** (status['retry_count'] - 1)) + jitter, 30.0)
    
    # Check if we should enter maintenance mode
    time_since_success = current_time - status['last_successful']
    if time_since_success > 30 or status['retry_count'] >= status['max_retries']:
        st.session_state.error_state = 'maintenance'
        return handle_error('maintenance')
    
    # Show WebSocket error page
    st.session_state.error_state = 'websocket'
    return handle_error('websocket')