import streamlit as st
import os

def render_404_page():
    """Render 404 error page"""
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
    .error-action a {
        color: var(--primary-color);
        text-decoration: none;
        padding: 10px 20px;
        border: 2px solid var(--primary-color);
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    .error-action a:hover {
        background-color: var(--primary-color);
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="error-container">
        <div class="error-code">404</div>
        <div class="error-message">Page Not Found</div>
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
                    const protocol = window.location.protocol;
                    const hostname = window.location.hostname;
                    const port = '8501';
                    const basePath = window._stcore.basePathname || '';
                    const healthUrl = `${protocol}//${hostname}:${port}${basePath}/_stcore/health`;
                    const response = await fetch(healthUrl);
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
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const hostname = window.location.hostname;
                const port = '8501';
                const basePath = window._stcore.basePathname || '';
                const wsUrl = `${protocol}//${hostname}:${port}${basePath}/_stcore/stream`;
                
                let wsConnection = new WebSocket(wsUrl);
                
                wsConnection.addEventListener('open', function() {
                    updateStatus('Connected');
                    updateProgressBar(100);
                });
                
                wsConnection.addEventListener('close', function() {
                    resetReconnection();
                    attemptReconnection();
                });
                
                wsConnection.addEventListener('error', function(event) {
                    console.error('WebSocket error:', event);
                    resetReconnection();
                    attemptReconnection();
                });
            });
        </script>
    </div>
    """, unsafe_allow_html=True)

def init_error_handling():
    """Initialize error handling middleware"""
    if 'error_state' not in st.session_state:
        st.session_state.error_state = None
        
    st.markdown("""
        <script>
            let ws = null;
            let reconnectTimeout = null;
            let reconnectAttempts = 0;
            const MAX_RECONNECT_ATTEMPTS = 5;
            const INITIAL_RETRY_DELAY = 1000;
            const MAX_RETRY_DELAY = 16000;
            
            function connect() {
                if (ws) {
                    ws.close();
                }
                
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const hostname = window.location.hostname;
                const port = '8501';  // Use the specific port
                const basePath = window._stcore.basePathname || '';
                const wsUrl = `${protocol}//${hostname}:${port}${basePath}/_stcore/stream`;
                
                console.log('Attempting WebSocket connection to:', wsUrl);
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    console.log('WebSocket Connected Successfully');
                    reconnectAttempts = 0;
                    if (reconnectTimeout) {
                        clearTimeout(reconnectTimeout);
                        reconnectTimeout = null;
                    }
                };
                
                ws.onclose = function(event) {
                    console.log('WebSocket Closed:', event.code, event.reason);
                    scheduleReconnect();
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket Error:', error);
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.close();
                    }
                };
                
                ws.onmessage = function(event) {
                    reconnectAttempts = 0;
                    if (reconnectTimeout) {
                        clearTimeout(reconnectTimeout);
                        reconnectTimeout = null;
                    }
                };
            }
            
            function scheduleReconnect() {
                if (reconnectTimeout) {
                    clearTimeout(reconnectTimeout);
                }
                
                if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                    const delay = Math.min(INITIAL_RETRY_DELAY * Math.pow(2, reconnectAttempts), MAX_RETRY_DELAY);
                    console.log(`Scheduling reconnect attempt ${reconnectAttempts + 1} in ${delay}ms`);
                    
                    reconnectTimeout = setTimeout(() => {
                        reconnectAttempts++;
                        connect();
                    }, delay);
                } else {
                    console.log('Max reconnection attempts reached');
                    // Reset attempts after a longer delay
                    setTimeout(() => {
                        reconnectAttempts = 0;
                        connect();
                    }, MAX_RETRY_DELAY * 2);
                }
            }
            
            // Initialize connection when the page loads
            window.addEventListener('load', connect);
            
            // Cleanup on page unload
            window.addEventListener('unload', () => {
                if (ws) {
                    ws.close();
                }
                if (reconnectTimeout) {
                    clearTimeout(reconnectTimeout);
                }
            });
            
            // Handle visibility change to reconnect when tab becomes visible
            document.addEventListener('visibilitychange', () => {
                if (document.visibilityState === 'visible') {
                    if (!ws || ws.readyState !== WebSocket.OPEN) {
                        reconnectAttempts = 0;  // Reset attempts on visibility change
                        connect();
                    }
                }
            });

            // Handle network status changes
            window.addEventListener('online', () => {
                console.log('Network connection restored');
                reconnectAttempts = 0;
                connect();
            });
        </script>
    """, unsafe_allow_html=True)