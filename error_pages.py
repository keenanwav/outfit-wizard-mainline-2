import streamlit as st
import os

def render_404_page():
    st.markdown("""
    <style>
    .error-container {
        text-align: center;
        padding: 50px;
        background-color: var(--secondary-background-color);
        border-radius: 10px;
        margin: 50px auto;
        max-width: 600px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .error-code {
        font-size: 72px;
        color: var(--primary-color);
        margin-bottom: 20px;
        font-weight: bold;
    }
    .error-message {
        font-size: 24px;
        color: var(--text-color);
        margin-bottom: 30px;
    }
    .error-action {
        margin-top: 20px;
    }
    .error-action a, .error-action button {
        color: var(--primary-color);
        text-decoration: none;
        padding: 10px 20px;
        border: 2px solid var(--primary-color);
        border-radius: 5px;
        transition: all 0.3s ease;
        cursor: pointer;
        background: none;
        font-size: 16px;
    }
    .error-action a:hover, .error-action button:hover {
        background-color: var(--primary-color);
        color: white;
    }
    .error-description {
        color: var(--text-color);
        opacity: 0.8;
        max-width: 400px;
        margin: 0 auto 20px;
        line-height: 1.5;
    }
    .error-suggestions {
        text-align: left;
        max-width: 400px;
        margin: 20px auto;
        padding: 15px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 5px;
    }
    .error-suggestions ul {
        margin: 10px 0;
        padding-left: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="error-container">
        <div class="error-code">404</div>
        <div class="error-message">Page Not Found</div>
        <div class="error-description">
            The page you're looking for doesn't exist or has been moved.
        </div>
        <div class="error-suggestions">
            <strong>You might want to:</strong>
            <ul>
                <li>Check the URL for typos</li>
                <li>Return to the homepage</li>
                <li>Browse your wardrobe</li>
            </ul>
        </div>
        <div class="error-action">
            <a href="/" target="_self">Return to Home</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_500_page():
    st.markdown("""
    <div class="error-container">
        <div class="error-code">500</div>
        <div class="error-message">Internal Server Error</div>
        <div class="error-description">
            We're experiencing some technical difficulties. Our team has been notified and is working on the issue.
        </div>
        <div class="error-suggestions">
            <strong>What you can do:</strong>
            <ul>
                <li>Refresh the page</li>
                <li>Try again in a few minutes</li>
                <li>Clear your browser cache</li>
            </ul>
        </div>
        <div class="error-action">
            <a href="/" target="_self">Return to Home</a>
            <button onclick="location.reload()" style="margin-left: 10px">Refresh Page</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_maintenance_page():
    st.markdown("""
    <div class="error-container">
        <div class="error-code">🔧</div>
        <div class="error-message">Scheduled Maintenance</div>
        <div class="error-description">
            We're currently performing system upgrades to improve your experience.
            This maintenance window is scheduled for 15-30 minutes.
        </div>
        <div class="error-suggestions">
            <strong>Maintenance Details:</strong>
            <ul>
                <li>System upgrades and optimizations</li>
                <li>Performance improvements</li>
                <li>Security updates</li>
            </ul>
        </div>
        <div id="maintenance-status" class="error-description" style="margin-top: 20px;">
            Checking system status...
        </div>
        <div class="error-action">
            <button onclick="checkMaintenanceStatus()">Check Status</button>
        </div>
        <script>
            function checkMaintenanceStatus() {
                const statusElement = document.getElementById('maintenance-status');
                statusElement.innerHTML = 'Checking system status...';
                
                fetch(window.location.origin + '/_stcore/health')
                    .then(response => {
                        if (response.ok) {
                            statusElement.innerHTML = 'System is back online! Reloading page...';
                            setTimeout(() => location.reload(), 1500);
                        } else {
                            statusElement.innerHTML = 'System is still under maintenance. Please check back in a few minutes.';
                        }
                    })
                    .catch(() => {
                        statusElement.innerHTML = 'Unable to check status. Please try again in a few minutes.';
                    });
            }
            
            // Auto-check status every 30 seconds
            setInterval(checkMaintenanceStatus, 30000);
        </script>
    </div>
    """, unsafe_allow_html=True)

def render_websocket_error():
    st.markdown("""
    <div class="error-container">
        <div class="error-code">⚠️</div>
        <div class="error-message">Connection Error</div>
        <p>Lost connection to the server. Attempting to reconnect...</p>
        <div id="connection-status" class="status-message">Initializing reconnection...</div>
        <div class="progress-bar">
            <div id="reconnection-progress" class="progress-bar-inner"></div>
        </div>
        <div class="error-action">
            <button onclick="manualReconnect()" id="manual-reconnect">Retry Connection</button>
        </div>
        <script>
            const MAX_RETRIES = 5;
            const BASE_DELAY = 1000;
            const MAX_DELAY = 16000;
            let currentAttempt = 0;
            let reconnectionTimer = null;
            
            function updateStatus(message) {
                const statusElement = document.getElementById('connection-status');
                if (statusElement) {
                    statusElement.textContent = message;
                }
            }
            
            function updateProgressBar(progress) {
                const progressBar = document.getElementById('reconnection-progress');
                if (progressBar) {
                    progressBar.style.width = `${progress}%`;
                }
            }
            
            function resetReconnection() {
                currentAttempt = 0;
                if (reconnectionTimer) {
                    clearTimeout(reconnectionTimer);
                }
                updateProgressBar(0);
                updateStatus('Initializing reconnection...');
            }
            
            function calculateDelay() {
                return Math.min(BASE_DELAY * Math.pow(2, currentAttempt), MAX_DELAY);
            }
            
            async function checkServerHealth() {
                try {
                    const response = await fetch(window.location.origin + '/_stcore/health');
                    return response.ok;
                } catch (e) {
                    return false;
                }
            }
            
            async function attemptReconnection() {
                if (currentAttempt >= MAX_RETRIES) {
                    updateStatus('Maximum retry attempts reached. Please try manual reconnection.');
                    updateProgressBar(100);
                    document.getElementById('manual-reconnect').style.display = 'inline-block';
                    return;
                }
                
                const delay = calculateDelay();
                const progress = (currentAttempt / MAX_RETRIES) * 100;
                updateProgressBar(progress);
                
                updateStatus(`Reconnection attempt ${currentAttempt + 1}/${MAX_RETRIES} in ${delay/1000} seconds...`);
                
                reconnectionTimer = setTimeout(async () => {
                    const isHealthy = await checkServerHealth();
                    if (isHealthy) {
                        updateStatus('Connection restored! Reloading page...');
                        setTimeout(() => window.location.reload(), 1000);
                    } else {
                        currentAttempt++;
                        attemptReconnection();
                    }
                }, delay);
            }
            
            function manualReconnect() {
                resetReconnection();
                attemptReconnection();
            }
            
            // Initialize reconnection attempt
            attemptReconnection();
            
            // Setup WebSocket monitoring
            window.addEventListener('load', function() {
                let wsConnection = window._stcore.WebsocketConnection;
                if (wsConnection) {
                    wsConnection.addEventListener('open', function() {
                        updateStatus('Connected');
                        updateProgressBar(100);
                    });
                    
                    wsConnection.addEventListener('close', function() {
                        resetReconnection();
                        attemptReconnection();
                    });
                }
            });
        </script>
    </div>
    """, unsafe_allow_html=True)

def init_error_handling():
    """Initialize error handling middleware"""
    if 'error_state' not in st.session_state:
        st.session_state.error_state = None
        
    # Add error handling middleware to detect connection issues
    st.markdown("""
        <script>
            let connectionTimeout = null;
            const TIMEOUT_DURATION = 30000; // 30 seconds timeout
            
            function initializeWebSocketHandling() {
                let wsConnection = window._stcore.WebsocketConnection;
                if (wsConnection) {
                    // Reset connection timeout on successful message
                    wsConnection.addEventListener('message', function() {
                        if (connectionTimeout) {
                            clearTimeout(connectionTimeout);
                        }
                        connectionTimeout = setTimeout(handleConnectionTimeout, TIMEOUT_DURATION);
                    });
                    
                    // Handle connection errors
                    wsConnection.addEventListener('error', function(event) {
                        console.error('WebSocket error:', event);
                        handleConnectionError();
                    });
                    
                    // Handle connection close
                    wsConnection.addEventListener('close', function() {
                        handleConnectionError();
                    });
                    
                    // Initialize connection timeout
                    connectionTimeout = setTimeout(handleConnectionTimeout, TIMEOUT_DURATION);
                }
            }
            
            function handleConnectionTimeout() {
                console.error('WebSocket connection timed out');
                handleConnectionError();
            }
            
            function handleConnectionError() {
                if (!document.getElementById('websocket-error-handler')) {
                    const errorDiv = document.createElement('div');
                    errorDiv.id = 'websocket-error-handler';
                    document.body.appendChild(errorDiv);
                    window.location.href = '/?error=websocket';
                }
            }
            
            // Initialize WebSocket handling on page load
            window.addEventListener('load', initializeWebSocketHandling);
        </script>
    """, unsafe_allow_html=True)