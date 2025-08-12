"""
Authentication routes for Moulya College Management System
Handles login, logout, and authentication redirects
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.auth_service import AuthService, SessionManager
from utils.validators import validate_username, validate_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    """Landing page with login options"""
    # Redirect if already logged in
    if SessionManager.is_authenticated(session):
        if SessionManager.is_management(session):
            return redirect(url_for('management.dashboard'))
        elif SessionManager.is_lecturer(session):
            return redirect(url_for('lecturer.dashboard'))
    
    return render_template('auth/index.html')

@auth_bp.route('/management/login', methods=['GET', 'POST'])
def management_login():
    """Management login page and handler"""
    # Redirect if already logged in as management
    if SessionManager.is_authenticated(session) and SessionManager.is_management(session):
        return redirect(url_for('management.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validate input
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('auth/management_login.html')
        
        # Validate username format
        is_valid, message = validate_username(username)
        if not is_valid:
            flash(message, 'error')
            return render_template('auth/management_login.html')
        
        # Authenticate user
        success, user, message = AuthService.authenticate_management(username, password)
        
        if success:
            # Create session
            SessionManager.create_session(session, 'management', user.id, user.username)
            flash('Login successful', 'success')
            return redirect(url_for('management.dashboard'))
        else:
            flash(message, 'error')
    
    return render_template('auth/management_login.html')

@auth_bp.route('/lecturer/login', methods=['GET', 'POST'])
def lecturer_login():
    """Lecturer login page and handler"""
    # Redirect if already logged in as lecturer
    if SessionManager.is_authenticated(session) and SessionManager.is_lecturer(session):
        return redirect(url_for('lecturer.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validate input
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('auth/lecturer_login.html')
        
        # Validate username format
        is_valid, message = validate_username(username)
        if not is_valid:
            flash(message, 'error')
            return render_template('auth/lecturer_login.html')
        
        # Authenticate user
        success, user, message = AuthService.authenticate_lecturer(username, password)
        
        if success:
            # Create session
            SessionManager.create_session(session, 'lecturer', user.id, user.username)
            flash('Login successful', 'success')
            return redirect(url_for('lecturer.dashboard'))
        else:
            flash(message, 'error')
    
    return render_template('auth/lecturer_login.html')

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout handler for both user types"""
    user_type = session.get('user_type')
    SessionManager.clear_session(session)
    flash('You have been logged out successfully', 'success')
    
    # Redirect to appropriate login page
    if user_type == 'management':
        return redirect(url_for('auth.management_login'))
    elif user_type == 'lecturer':
        return redirect(url_for('auth.lecturer_login'))
    else:
        return redirect(url_for('auth.index'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    """Change password for authenticated users"""
    if not SessionManager.is_authenticated(session):
        flash('Please log in to change your password', 'error')
        return redirect(url_for('auth.index'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate input
        if not all([current_password, new_password, confirm_password]):
            flash('All password fields are required', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('auth/change_password.html')
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            flash(message, 'error')
            return render_template('auth/change_password.html')
        
        # Change password
        user_type = session.get('user_type')
        user_id = session.get('user_id')
        
        success, message = AuthService.change_password(
            user_type, user_id, current_password, new_password
        )
        
        if success:
            flash(message, 'success')
            # Redirect to appropriate dashboard
            if user_type == 'management':
                return redirect(url_for('management.dashboard'))
            else:
                return redirect(url_for('lecturer.dashboard'))
        else:
            flash(message, 'error')
    
    return render_template('auth/change_password.html')

# Authentication decorator
def login_required(user_type=None):
    """Decorator to require authentication"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if not SessionManager.is_authenticated(session):
                flash('Please log in to access this page', 'error')
                return redirect(url_for('auth.index'))
            
            if user_type:
                if user_type == 'management' and not SessionManager.is_management(session):
                    flash('Access denied. Management login required.', 'error')
                    return redirect(url_for('auth.management_login'))
                elif user_type == 'lecturer' and not SessionManager.is_lecturer(session):
                    flash('Access denied. Lecturer login required.', 'error')
                    return redirect(url_for('auth.lecturer_login'))
            
            return f(*args, **kwargs)
        
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

# Context processor to make session info available in templates
@auth_bp.app_context_processor
def inject_user():
    """Inject user information into template context"""
    return {
        'current_user': SessionManager.get_session_info(session),
        'is_authenticated': SessionManager.is_authenticated(session),
        'is_management': SessionManager.is_management(session),
        'is_lecturer': SessionManager.is_lecturer(session)
    }