
from flask_login import LoginManager, UserMixin, login_user, logout_user
from google.oauth2 import id_token
from google.auth.transport import requests
import json
from functools import wraps
from flask import redirect, url_for, session, flash
import os
from data_manager import get_db_connection

login_manager = LoginManager()

class User(UserMixin):
    def __init__(self, user_id, email, role='user'):
        self.id = user_id
        self.email = email
        self.role = role

def create_auth_tables():
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    role VARCHAR(50) DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        finally:
            cur.close()

def get_user_by_email(email):
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, email, role FROM users WHERE email = %s", (email,))
            user_data = cur.fetchone()
            if user_data:
                return User(user_data[0], user_data[1], user_data[2])
            return None
        finally:
            cur.close()

def create_user(email, role='user'):
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (email, role) VALUES (%s, %s) RETURNING id",
                (email, role)
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            return User(user_id, email, role)
        finally:
            cur.close()

@login_manager.user_loader
def load_user(user_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, email, role FROM users WHERE id = %s", (user_id,))
            user_data = cur.fetchone()
            if user_data:
                return User(user_data[0], user_data[1], user_data[2])
            return None
        finally:
            cur.close()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user') or session['user'].get('role') != 'admin':
            flash('Admin access required')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
