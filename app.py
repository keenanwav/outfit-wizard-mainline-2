from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import re
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload configuration
UPLOAD_FOLDER = 'static/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
from extensions import db
db.init_app(app)

# Import models after db initialization
from models import User

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            # Validate email format
            if not re.match(r"[^@]+@[^@]+\.[^@]+", username):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'status': 'error', 'message': 'Invalid email format'}), 400
                flash('Invalid email format', 'error')
                return render_template('register.html')

            # Check if user already exists
            if User.query.filter_by(username=username).first():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'status': 'error', 'message': 'Email already registered'}), 400
                flash('Email already registered', 'error')
                return render_template('register.html')

            # Validate password requirements
            if not (len(password) >= 5 and len(password) <= 16 and
                    re.search(r"[A-Z]", password) and
                    re.search(r"[a-z]", password) and
                    re.search(r"[0-9]", password) and
                    re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'status': 'error', 'message': 'Password does not meet requirements'}), 400
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
                user.update_last_login()
                logger.info(f"User logged in: {username}")
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            flash('An error occurred during login', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login to access the dashboard', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        flash('User not found', 'error')
        return redirect(url_for('login'))

    return render_template('dashboard.html', user=user)

# Profile management routes
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please login to access your profile', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))

    return render_template('profile.html', current_user=user)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Please login'}), 401

    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    try:
        user.first_name = request.form.get('first_name', '').strip()
        user.last_name = request.form.get('last_name', '').strip()
        user.bio = request.form.get('bio', '').strip()

        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating profile: {str(e)}")
        flash('An error occurred while updating your profile', 'error')

    return redirect(url_for('profile'))

@app.route('/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Please login'}), 401

    if 'profile_picture' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('profile'))

    file = request.files['profile_picture']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('profile'))

    user = User.query.get(session['user_id'])
    if file and allowed_file(file.filename):
        try:
            # Delete old profile picture if it exists and is not the default
            if user.profile_picture != 'default.png':
                old_picture = os.path.join(app.config['UPLOAD_FOLDER'], user.profile_picture)
                if os.path.exists(old_picture):
                    os.remove(old_picture)

            # Save new profile picture
            filename = secure_filename(f"user_{user.id}_{int(datetime.utcnow().timestamp())}.{file.filename.rsplit('.', 1)[1].lower()}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            user.profile_picture = filename
            db.session.commit()
            flash('Profile picture updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error uploading profile picture: {str(e)}")
            flash('An error occurred while uploading your profile picture', 'error')
    else:
        flash('Invalid file type. Please use PNG, JPG, JPEG, or GIF', 'error')

    return redirect(url_for('profile'))

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Please login'}), 401

    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not user.check_password(current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('profile'))

    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('profile'))

    # Password validation
    if not (len(new_password) >= 5 and len(new_password) <= 16 and
            re.search(r"[A-Z]", new_password) and
            re.search(r"[a-z]", new_password) and
            re.search(r"[0-9]", new_password) and
            re.search(r"[!@#$%^&*(),.?\":{}|<>]", new_password)):
        flash('Password does not meet requirements', 'error')
        return redirect(url_for('profile'))

    try:
        user.set_password(new_password)
        db.session.commit()
        flash('Password changed successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error changing password: {str(e)}")
        flash('An error occurred while changing your password', 'error')

    return redirect(url_for('profile'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)