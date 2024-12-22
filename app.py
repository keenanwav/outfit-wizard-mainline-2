from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User
import re
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Ensure the instance folder exists
instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)
    logger.info(f"Created instance directory at {instance_path}")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
db.init_app(app)

def init_db():
    try:
        with app.app_context():
            logger.info("Creating database tables...")
            db.create_all()
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            # Validate email format
            if not re.match(r"[^@]+@[^@]+\.[^@]+", username):
                flash('Invalid email format', 'error')
                return render_template('register.html')

            # Check if user already exists
            if User.query.filter_by(username=username).first():
                flash('Email already registered', 'error')
                return render_template('register.html')

            # Validate password
            if not (len(password) >= 5 and len(password) <= 16 and
                    re.search(r"[A-Z]", password) and
                    re.search(r"[a-z]", password) and
                    re.search(r"[0-9]", password) and
                    re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)):
                flash('Password does not meet requirements', 'error')
                return render_template('register.html')

            # Create new user
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"New user registered: {username}")

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            db.session.rollback()
            flash('An error occurred during registration', 'error')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                session['user_id'] = user.id
                logger.info(f"User logged in: {username}")
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            flash('An error occurred during login', 'error')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        user = User.query.get(session['user_id'])
        if user:
            return render_template('dashboard.html', user=user)
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Error accessing dashboard: {str(e)}")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    try:
        init_db()
        logger.info("Starting Flask server...")
        app.run(host='0.0.0.0', port=5001, debug=True)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")