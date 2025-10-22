from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
import threading
from datetime import datetime
from config.database import mongodb_config
from services.auth_service import auth_service
from services.student_service import student_service
from secrets import token_hex

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Custom Jinja2 filters
def format_mark(value):
    """Format mark to show integer if decimal is .0, otherwise show as is"""
    if value is None:
        return '0'
    try:
        float_val = float(value)
        if float_val == int(float_val):
            return str(int(float_val))
        else:
            return str(float_val)
    except (ValueError, TypeError):
        return str(value)

def format_assessment_type(value):
    """Format assessment type to add space between words and numbers"""
    if not value:
        return value
    import re
    # Add space between letters and numbers (e.g., "Internal1" -> "Internal 1")
    formatted = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', str(value))
    return formatted

def format_percentage(value):
    """Format percentage to show integer if decimal is .00, otherwise show as is"""
    if value is None:
        return '0%'
    try:
        float_val = float(value)
        if float_val == int(float_val):
            return f"{int(float_val)}%"
        else:
            return f"{float_val:.2f}%"
    except (ValueError, TypeError):
        return f"{value}%"

# Register custom filters
app.jinja_env.filters['format_mark'] = format_mark
app.jinja_env.filters['format_assessment_type'] = format_assessment_type
app.jinja_env.filters['format_percentage'] = format_percentage

# Configuration
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session timeout

# Initialize MongoDB connection
def initialize_database():
    """Initialize database connection"""
    if not mongodb_config.connect():
        print("Warning: MongoDB connection failed. Student authentication will not work.")

# Initialize database when app starts
initialize_database()

# Initialize student service against read-only instance DB
def init_student_service():
    try:
        import os
        # Point to the instance database (4MB database you attached)
        instance_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'moulya_college.db')
        print(f"Initializing student service with database: {instance_db}")
        student_service.init_app(db_path=instance_db)
    except Exception as e:
        print(f"Warning: Could not initialize student service (read-only): {e}")

init_student_service()


def prefetch_and_cache_student(roll_number: str):
    """Background task: fetch dashboard data from SQLite and cache it in MongoDB."""
    try:
        # Fetch latest dashboard data from the main SQLite DB
        data = student_service.get_student_dashboard_stats(roll_number) or {}
    except Exception as e:
        print(f"Prefetch error (SQLite fetch failed) for {roll_number}: {e}")
        return

    try:
        # Upsert into MongoDB cache collection if available
        if getattr(mongodb_config, 'db', None) is not None:
            cache_coll = mongodb_config.db["student_dashboard_cache"]
            cache_coll.update_one(
                {"roll_number": roll_number},
                {
                    "$set": {
                        "roll_number": roll_number,
                        "data": data,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                },
                upsert=True,
            )
    except Exception as e:
        print(f"Prefetch error (Mongo upsert failed) for {roll_number}: {e}")

def is_authenticated():
    """Check if user is authenticated"""
    return session.get('student_logged_in', False)

# Minimal CSRF helper for templates and form validation
def _ensure_csrf_token():
    if not session.get('csrf_token'):
        session['csrf_token'] = token_hex(16)
    return session['csrf_token']

app.jinja_env.globals['csrf_token'] = _ensure_csrf_token

def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Home page for student portal"""
    # Check if user is already logged in
    if is_authenticated():
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Student login page"""
    # Check if user is already logged in
    if is_authenticated():
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        roll_number = request.form.get('roll_number', '').strip()
        # Accept either 'password' (preferred) or legacy 'date_of_birth' field name
        password = (request.form.get('password') or request.form.get('date_of_birth') or '').strip()
        
        # Validate input
        if not roll_number or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('login.html')
        
        # Validate format
        if not auth_service.validate_roll_number_format(roll_number):
            flash('Invalid username format.', 'error')
            return render_template('login.html')
        
        if not auth_service.validate_password(password):
            flash('Invalid password format.', 'error')
            return render_template('login.html')
        
        # Authenticate student
        student = auth_service.authenticate_student(roll_number, password)
        
        if student:
            # Get full student data including name from the main database
            try:
                full_student_data = student_service.get_student_by_roll_number(student['roll_number'])
                if full_student_data:
                    # Merge auth data with full student data
                    student.update(full_student_data)
            except Exception as e:
                print(f"Error fetching full student data: {e}")
                # Fallback to just roll number if we can't get full data
                student['name'] = student['roll_number']
            
            # Store student data in session with proper session management
            session.permanent = True  # Make session permanent
            session['student_logged_in'] = True
            session['student_roll_number'] = student['roll_number']
            session['student_data'] = student
            session['login_time'] = datetime.now().isoformat()
            session['session_id'] = f"student_{student['roll_number']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Kick off background prefetch to warm SQLite data and cache to MongoDB
            try:
                threading.Thread(
                    target=prefetch_and_cache_student,
                    args=(student['roll_number'],),
                    daemon=True,
                ).start()
            except Exception as e:
                print(f"Failed to start prefetch thread: {e}")
            
            # Use student name if available, otherwise fallback to roll number
            student_name = student.get('name', student['roll_number'])
            flash(f'Welcome, {student_name.upper()}', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/dashboard')
@require_auth
def dashboard():
    """Student dashboard"""
    student_data = session.get('student_data', {})
    roll_number = student_data.get('roll_number')
    
    # Always fetch from main SQLite database (do not render from Mongo cache)
    dashboard_stats = {}
    if roll_number:
        try:
            dashboard_stats = student_service.get_student_dashboard_stats(roll_number)
            # Optionally refresh cache in background, but UI never reads from cache
            try:
                threading.Thread(
                    target=prefetch_and_cache_student,
                    args=(roll_number,),
                    daemon=True,
                ).start()
            except Exception as e:
                print(f"Failed to start cache refresh thread: {e}")
        except Exception as e:
            print(f"Error fetching dashboard stats: {e}")
            flash('Unable to fetch some data from the main database.', 'warning')
    print(student_data)
    return render_template('dashboard.html', 
                         student=student_data, 
                         stats=dashboard_stats)

@app.route('/api/student/dashboard')
@require_auth
def api_student_dashboard():
    """JSON API: Student dashboard stats (read-only)"""
    student_data = session.get('student_data', {})
    roll_number = student_data.get('roll_number')
    if not roll_number:
        return jsonify({'error': 'No roll number in session'}), 400
    try:
        dashboard_stats = student_service.get_student_dashboard_stats(roll_number) or {}
        return jsonify({'ok': True, 'data': dashboard_stats})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/profile')
@require_auth
def profile():
    """Student profile page"""
    student_data = session.get('student_data', {})
    roll_number = student_data.get('roll_number')
    
    # Fetch comprehensive student data from main Moulya database
    student_info = {}
    if roll_number:
        try:
            student_info = student_service.get_student_by_roll_number(roll_number)
        except Exception as e:
            print(f"Error fetching student profile: {e}")
            flash('Unable to fetch profile data from the main database.', 'warning')
    
    return render_template('profile.html', 
                         student=student_data, 
                         student_info=student_info)

@app.route('/attendance')
@require_auth
def attendance():
    """Student attendance view"""
    student_data = session.get('student_data', {})
    roll_number = student_data.get('roll_number')
    subject_id = request.args.get('subject_id', type=int)
    
    # Initialize default values
    subject_info = None
    attendance_summary = {'total_classes': 0, 'present': 0, 'deputation': 0, 'absent': 0, 'percentage': 0.0}
    monthly_summary = []
    
    if roll_number:
        try:
            # Get attendance summary using the correct service method
            attendance_summary = student_service.get_student_attendance_summary(roll_number, subject_id)
            print(f"[DEBUG] Attendance Summary: {attendance_summary}")
        
            # Get monthly attendance data using the correct service method
            monthly_data = student_service.get_student_monthly_attendance(roll_number, subject_id)
            monthly_summary = monthly_data.get('monthly_summary', [])
            print(f"[DEBUG] Monthly Summary: {len(monthly_summary)} months")
            
            # Get subject info if subject_id is provided
            if subject_id:
                enrolled_subjects = student_service.get_student_enrolled_subjects(roll_number)
                for subject in enrolled_subjects:
                    if subject.get('id') == subject_id:
                        subject_info = subject
                        break
            
            # Print data to backend console for debugging
            print(f"\n=== ATTENDANCE DATA FOR {roll_number} ===")
            print(f"Overall Summary:")
            print(f"  - Total Classes: {attendance_summary.get('total_classes', 0)}")
            print(f"  - Present: {attendance_summary.get('present', 0)}")
            print(f"  - Deputation: {attendance_summary.get('deputation', 0)}")
            print(f"  - Absent: {attendance_summary.get('absent', 0)}")
            print(f"  - Percentage: {attendance_summary.get('percentage', 0)}%")
            print(f"Monthly Summary: {len(monthly_summary)} months")
            for month in monthly_summary:
                print(f"  - {month['label']}: {month['present']}/{month['total']} ({month['percentage']}%)")
            print("=" * 60)
            
        except Exception as e:
            print(f"Error fetching attendance data: {e}")
            import traceback
            traceback.print_exc()
            flash('Unable to fetch attendance data from the main database.', 'warning')
            # Ensure we have default values even on error
            attendance_summary = {'total_classes': 0, 'present': 0, 'deputation': 0, 'absent': 0, 'percentage': 0.0}
            monthly_summary = []
    
    return render_template('attendance.html', 
                         student=student_data, 
                         subject=subject_info,
                         attendance_summary=attendance_summary,
                         monthly_summary=monthly_summary,
                         subject_id=subject_id)

@app.route('/marks')
@require_auth
def marks():
    """Student marks view"""
    student_data = session.get('student_data', {})
    roll_number = student_data.get('roll_number')
    subject_id = request.args.get('subject_id', type=int)
    
    # Fetch marks data from main Moulya database
    marks_records = []
    subject_info = None
    overall = { 'obtained': 0, 'max': 0, 'percentage': 0.0 }
    if roll_number:
        try:
            marks_records = student_service.get_student_marks_records(roll_number, subject_id)
            # Subject info
            enrolled = student_service.get_student_enrolled_subjects(roll_number) or []
            if subject_id:
                for s in enrolled:
                    if s.get('id') == subject_id:
                        subject_info = s
                        break
            # Compute overall
            total_obt = sum((r.get('marks_obtained') or 0) for r in marks_records)
            total_max = sum((r.get('max_marks') or 0) for r in marks_records)
            pct = round((total_obt/total_max)*100, 2) if total_max else 0.0
            overall = { 'obtained': total_obt, 'max': total_max, 'percentage': pct }
        except Exception as e:
            print(f"Error fetching marks records: {e}")
            flash('Unable to fetch marks data from the main database.', 'warning')
    
    return render_template('marks.html', 
                         student=student_data, 
                         marks_records=marks_records,
                         subject=subject_info,
                         overall=overall,
                         subject_id=subject_id)

@app.route('/assignments')
@require_auth
def assignments():
    """Student assignments view"""
    student_data = session.get('student_data', {})
    return render_template('assignments.html', student=student_data)

@app.route('/logout')
def logout():
    """Logout functionality"""
    student_roll = session.get('student_roll_number', 'Student')
    session.clear()
    flash(f'{student_roll} has been logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/api/check-roll-number/<roll_number>')
def check_roll_number(roll_number):
    """API endpoint to check if roll number exists"""
    if not session.get('student_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    student = auth_service.get_student_by_roll_number(roll_number)
    return jsonify({'exists': student is not None})


@app.route('/reset-password', methods=['GET', 'POST'])
@require_auth
def reset_password():
    """Allow a logged-in student to change their MongoDB password."""
    student_data = session.get('student_data', {})
    roll_number = student_data.get('roll_number')
    if request.method == 'POST':
        # Basic CSRF validation
        submitted_csrf = request.form.get('csrf_token')
        if not submitted_csrf or submitted_csrf != session.get('csrf_token'):
            flash('Invalid or missing CSRF token. Please try again.', 'error')
            return render_template('change_password.html')
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not current_password or not new_password or not confirm_password:
            flash('All fields are required.', 'error')
            return render_template('change_password.html')

        if new_password != confirm_password:
            flash('New password and confirmation do not match.', 'error')
            return render_template('change_password.html')

        if not auth_service.validate_password(new_password):
            flash('Password must be at least 4 characters.', 'error')
            return render_template('change_password.html')

        ok = auth_service.update_password(roll_number, current_password, new_password)
        if ok:
            flash('Password updated successfully.', 'success')
            # Update session copy (masking value)
            session['student_data'] = { **student_data }
            return redirect(url_for('dashboard'))
        else:
            flash('Current password incorrect.', 'error')
            return render_template('change_password.html')

    return render_template('change_password.html')

