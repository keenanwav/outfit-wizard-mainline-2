import os
import bcrypt
import streamlit as st
from datetime import datetime, timedelta
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from typing import Optional, Dict, Tuple
import pyotp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string

# Initialize connection pool with better error handling
def create_connection_pool():
    try:
        return SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=os.environ['DATABASE_URL'],
            connect_timeout=30
        )
    except Exception as e:
        st.error(f"Failed to create database pool: {str(e)}")
        raise

# Initialize connection pool
connection_pool = create_connection_pool()

def send_verification_email(email: str, code: str) -> bool:
    """Send verification email with the provided code"""
    try:
        sender_email = os.environ.get('EMAIL_SENDER')
        sender_password = os.environ.get('EMAIL_PASSWORD')

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = 'Your Verification Code'

        body = f"""
        Your verification code is: {code}

        This code will expire in 10 minutes.
        If you didn't request this code, please ignore this email.
        """
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send verification email: {str(e)}")
        return False

def generate_verification_code() -> str:
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def store_verification_code(user_id: int, code: str) -> bool:
    """Store verification code in database with expiration time"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                expiration = datetime.now() + timedelta(minutes=10)
                cur.execute("""
                    UPDATE users 
                    SET verification_code = %s, verification_code_expires = %s
                    WHERE id = %s
                """, (code, expiration, user_id))
                conn.commit()
                return True
            finally:
                cur.close()
    except Exception as e:
        st.error(f"Error storing verification code: {str(e)}")
        return False

def verify_code(user_id: int, code: str) -> bool:
    """Verify the provided code against stored code"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    SELECT verification_code, verification_code_expires
                    FROM users
                    WHERE id = %s
                """, (user_id,))
                result = cur.fetchone()

                if not result:
                    return False

                stored_code, expiration = result

                if (stored_code == code and 
                    expiration and 
                    expiration > datetime.now()):
                    # Mark email as verified
                    cur.execute("""
                        UPDATE users
                        SET email_verified = TRUE,
                            verification_code = NULL,
                            verification_code_expires = NULL
                        WHERE id = %s
                    """, (user_id,))
                    conn.commit()
                    return True
                return False
            finally:
                cur.close()
    except Exception as e:
        st.error(f"Error verifying code: {str(e)}")
        return False

def setup_2fa(user_id: int) -> Tuple[bool, Optional[str]]:
    """Set up 2FA for a user"""
    try:
        # Generate a random secret key
        secret = pyotp.random_base32()

        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    UPDATE users 
                    SET two_factor_secret = %s, two_factor_enabled = TRUE
                    WHERE id = %s
                    RETURNING email
                """, (secret, user_id))

                result = cur.fetchone()
                if result:
                    conn.commit()
                    return True, secret
                return False, None
            finally:
                cur.close()
    except Exception as e:
        st.error(f"Error setting up 2FA: {str(e)}")
        return False, None

def verify_2fa(user_id: int, token: str) -> bool:
    """Verify 2FA token"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    SELECT two_factor_secret
                    FROM users
                    WHERE id = %s AND two_factor_enabled = TRUE
                """, (user_id,))

                result = cur.fetchone()
                if not result:
                    return False

                secret = result[0]
                totp = pyotp.TOTP(secret)
                return totp.verify(token)
            finally:
                cur.close()
    except Exception as e:
        st.error(f"Error verifying 2FA token: {str(e)}")
        return False

def disable_2fa(user_id: int) -> bool:
    """Disable 2FA for a user"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    UPDATE users 
                    SET two_factor_secret = NULL, two_factor_enabled = FALSE
                    WHERE id = %s
                    RETURNING id
                """, (user_id,))

                if cur.fetchone():
                    conn.commit()
                    return True
                return False
            finally:
                cur.close()
    except Exception as e:
        st.error(f"Error disabling 2FA: {str(e)}")
        return False

# Keep existing functions but update authenticate_user to handle 2FA
def authenticate_user(email: str, password: str) -> Tuple[bool, Dict]:
    """Authenticate a user and handle 2FA if enabled"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    SELECT id, username, password_hash, role, two_factor_enabled, email_verified
                    FROM users 
                    WHERE email = %s
                """, (email,))
                result = cur.fetchone()

                if result and verify_password(password, result[2]) and result[5]: #check email verification
                    # Update last login time
                    cur.execute(
                        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                        (result[0],)
                    )
                    conn.commit()

                    return True, {
                        "id": result[0],
                        "username": result[1],
                        "role": result[3],
                        "requires_2fa": result[4]
                    }
                return False, {}
            finally:
                cur.close()
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False, {}

@contextmanager
def get_db_connection():
    """Context manager for database connections with proper error handling"""
    conn = None
    try:
        conn = connection_pool.getconn()
        yield conn
    finally:
        if conn:
            if not conn.closed:
                conn.commit()
            connection_pool.putconn(conn)

def init_auth_tables():
    """Initialize authentication and profile tables"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Create users table with additional profile fields
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(64) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash BYTEA NOT NULL,
                    role VARCHAR(10) NOT NULL DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    full_name VARCHAR(100),
                    bio TEXT,
                    profile_picture_path VARCHAR(255),
                    preferences JSONB DEFAULT '{}',
                    last_login TIMESTAMP,
                    verification_code VARCHAR(6),
                    verification_code_expires TIMESTAMP,
                    two_factor_secret VARCHAR(255),
                    two_factor_enabled BOOLEAN DEFAULT FALSE,
                    email_verified BOOLEAN DEFAULT FALSE,
                    CHECK (role IN ('admin', 'user'))
                )
            """)
            conn.commit()
            st.success("Successfully initialized auth tables")
        except Exception as e:
            st.error(f"Failed to initialize auth tables: {str(e)}")
            conn.rollback()
            raise
        finally:
            cur.close()

def hash_password(password: str) -> bytes:
    """Hash a password using bcrypt with proper encoding"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password: str, password_hash: bytes) -> bool:
    """Verify a password against its hash with proper type handling"""
    try:
        # Convert memoryview to bytes if necessary
        if isinstance(password_hash, memoryview):
            password_hash = password_hash.tobytes()
        return bcrypt.checkpw(password.encode('utf-8'), password_hash)
    except Exception as e:
        st.error(f"Password verification error: {str(e)}")
        return False

def create_user(username: str, email: str, password: str, role: str = 'user') -> bool:
    """Create a new user with specified role"""
    try:
        if role not in ('admin', 'user'):
            raise ValueError("Invalid role specified")

        password_hash = hash_password(password)
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                    (username, email, password_hash, role)
                )
                conn.commit()
                return True
            except psycopg2.Error as e:
                st.error(f"Database error: {str(e)}")
                return False
            finally:
                cur.close()
    except Exception as e:
        st.error(f"Error creating user: {str(e)}")
        return False


def update_user_profile(user_id: int, data: Dict) -> bool:
    """Update user profile information"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                # Build update query dynamically based on provided fields
                update_fields = []
                params = []
                for key, value in data.items():
                    if key in ['full_name', 'bio', 'profile_picture_path', 'preferences']:
                        update_fields.append(f"{key} = %s")
                        params.append(value)

                if update_fields:
                    params.append(user_id)
                    query = f"""
                        UPDATE users 
                        SET {', '.join(update_fields)}
                        WHERE id = %s
                        RETURNING id
                    """
                    cur.execute(query, params)

                    if cur.fetchone():
                        conn.commit()
                        return True
                return False
            finally:
                cur.close()
    except Exception as e:
        st.error(f"Error updating profile: {str(e)}")
        return False

def get_user_profile(user_id: int) -> Optional[Dict]:
    """Get user profile information"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    SELECT username, email, full_name, bio, 
                           profile_picture_path, preferences, last_login
                    FROM users 
                    WHERE id = %s
                    """,
                    (user_id,)
                )
                result = cur.fetchone()

                if result:
                    return {
                        "username": result[0],
                        "email": result[1],
                        "full_name": result[2],
                        "bio": result[3],
                        "profile_picture_path": result[4],
                        "preferences": result[5],
                        "last_login": result[6]
                    }
                return None
            finally:
                cur.close()
    except Exception as e:
        st.error(f"Error fetching profile: {str(e)}")
        return None

def init_session_state():
    """Initialize session state variables for authentication"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'auth_status' not in st.session_state:
        st.session_state.auth_status = None

def logout_user():
    """Log out the current user"""
    st.session_state.user = None
    st.session_state.auth_status = None