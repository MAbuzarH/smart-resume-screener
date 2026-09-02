"""
Authentication routes for login, registration, and logout.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import User
from app import db
import re

bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration page.
    GET: Display registration form.
    POST: Process registration and create user account.
    """
    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'applicant')
        
        # Validate full name
        if not full_name:
            flash('Full name is required.', 'danger')
            return render_template('register.html', title='Register')
        
        if len(full_name) < 2:
            flash('Full name must be at least 2 characters.', 'danger')
            return render_template('register.html', title='Register')
        
        if len(full_name) > 200:
            flash('Full name is too long.', 'danger')
            return render_template('register.html', title='Register')
        
        # Validate email
        if not email:
            flash('Email address is required.', 'danger')
            return render_template('register.html', title='Register')
        
        # Basic email validation
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('register.html', title='Register')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'danger')
            return render_template('register.html', title='Register')
        
        # Validate password
        if not password:
            flash('Password is required.', 'danger')
            return render_template('register.html', title='Register')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html', title='Register')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', title='Register')
        
        # Validate role
        if role not in ['applicant', 'employer']:
            flash('Invalid role selected.', 'danger')
            return render_template('register.html', title='Register')
        
        # Create user
        user = User(
            full_name=full_name,
            email=email,
            role=role
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('register.html', title='Register')
    
    return render_template('register.html', title='Register')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login page.
    GET: Display login form.
    POST: Process login and create session.
    """
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        # Validate input
        if not email or not password:
            flash('Please provide both email and password.', 'danger')
            return render_template('login.html', title='Login')
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        # Verify credentials
        if not user or not user.check_password(password):
            flash('Invalid email or password.', 'danger')
            return render_template('login.html', title='Login')
        
        if not user.is_active:
            flash('Your account is inactive. Please contact support.', 'danger')
            return render_template('login.html', title='Login')
        
        # Create session
        session['user_id'] = user.id
        session['user_name'] = user.full_name
        session['user_email'] = user.email
        session['user_role'] = user.role
        
        flash(f'Welcome back, {user.full_name}!', 'success')
        
        # Redirect based on role
        if user.role == 'employer':
            return redirect(url_for('main.dashboard'))
        elif user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('main.index'))
    
    return render_template('login.html', title='Login')


@bp.route('/logout')
def logout():
    """
    User logout page.
    Clears session and redirects to home.
    """
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))