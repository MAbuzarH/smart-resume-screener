"""
Authentication helpers and decorators for user access control.
"""

from functools import wraps
from flask import session, redirect, url_for, flash
from app.models import User


def login_required(f):
    """
    Decorator to require user authentication.
    Redirects to login page if user is not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    """
    Decorator to require specific user roles.
    Redirects to appropriate page if user doesn't have required role.
    
    Args:
        *allowed_roles: Variable number of allowed role strings
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            user = User.query.get(session['user_id'])
            if not user or not user.is_active:
                session.clear()
                flash('Your account is inactive. Please contact support.', 'danger')
                return redirect(url_for('auth.login'))
            
            if user.role not in allowed_roles:
                flash('You do not have permission to access this page.', 'danger')
                # Redirect based on current role
                if user.role == 'applicant':
                    return redirect(url_for('main.index'))
                elif user.role == 'employer':
                    return redirect(url_for('main.dashboard'))
                elif user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                else:
                    return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user():
    """
    Get the currently authenticated user from session.
    
    Returns:
        User object if authenticated, None otherwise
    """
    if 'user_id' not in session:
        return None
    
    return User.query.get(session['user_id'])