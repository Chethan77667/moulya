from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
from datetime import datetime
from config.database import mongodb_config
from services.auth_service import auth_service
from services.student_service import student_service

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

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

# Initialize student service with main Moulya database
def init_student_service():
    """Initialize student service with main Moulya database"""
    try:
        # Use absolute path to ensure we find the correct database
        import os
        repo_root = os.path.dirname(os.path.dirname(__file__))
        instance_db = os.path.join(repo_root, 'instance', 'moulya_college.db')
        
        print(f"Initializing student service with database: {instance_db}")
        student_service.init_app(db_path=instance_db)
        print("Successfully initialized student service with main database")
        
    except Exception as e:
        print(f"Warning: Could not initialize student service with main database: {e}")
        # Continue without the main database connection
        print("Student service will work with limited functionality")

# Initialize the service
init_student_service()

def is_authenticated():
    """Check if user is authenticated"""
    return session.get('student_logged_in', False)

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
        date_of_birth = request.form.get('date_of_birth', '').strip()
        
        # Validate input
        if not roll_number or not date_of_birth:
            flash('Please enter both username and password.', 'error')
            return render_template('login.html')
        
        # Validate format
        if not auth_service.validate_roll_number_format(roll_number):
            flash('Invalid username format.', 'error')
            return render_template('login.html')
        
        if not auth_service.validate_date_of_birth(date_of_birth):
            flash('Invalid password format.', 'error')
            return render_template('login.html')
        
        # Authenticate student
        student = auth_service.authenticate_student(roll_number, date_of_birth)
        
        if student:
            # Print user data in backend when login is successful
            print(f"\n{'='*60}")
            print(f"STUDENT LOGIN SUCCESSFUL")
            print(f"{'='*60}")
            print(f"Roll Number: {student['roll_number']}")
            print(f"Login Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Session ID: student_{student['roll_number']}_{datetime.now().strftime('%Y%m%d%H%M%S')}")
            print(f"Source Database: {student.get('source_database', 'Unknown')}")
            print(f"Migrated At: {student.get('migrated_at', 'Unknown')}")
            print(f"{'='*60}")
            
            # Get additional student data from main database
            try:
                student_info = student_service.get_student_by_roll_number(roll_number)
                if student_info:
                    print(f"STUDENT DETAILS FROM MAIN DATABASE:")
                    print(f"Name: {student_info.get('name', 'Unknown')}")
                    print(f"Course: {student_info.get('course_name', 'Unknown')}")
                    print(f"Academic Year: {student_info.get('academic_year', 'Unknown')}")
                    print(f"Current Semester: {student_info.get('current_semester', 'Unknown')}")
                    print(f"Email: {student_info.get('email', 'Not provided')}")
                    print(f"Phone: {student_info.get('phone', 'Not provided')}")
                    print(f"Overall Attendance: {student_info.get('overall_attendance', 0)}%")
                    print(f"Overall Marks: {student_info.get('overall_marks', 0)}%")
                    
                    # Get enrolled subjects
                    subjects = student_service.get_student_enrolled_subjects(roll_number)
                    print(f"Enrolled Subjects: {len(subjects)}")
                    for subject in subjects[:3]:  # Show first 3 subjects
                        print(f"  - {subject.get('name', 'Unknown')} ({subject.get('code', 'Unknown')})")
                    
                    # Get attendance summary
                    attendance_summary = student_service.get_student_attendance_summary(roll_number)
                    print(f"ATTENDANCE SUMMARY:")
                    print(f"Total Classes: {attendance_summary.get('total_classes', 0)}")
                    print(f"Present: {attendance_summary.get('present', 0)}")
                    print(f"Absent: {attendance_summary.get('absent', 0)}")
                    print(f"Percentage: {attendance_summary.get('percentage', 0)}%")
                    
                    # Get monthly attendance
                    monthly_data = student_service.get_student_monthly_attendance(roll_number)
                    monthly_summary = monthly_data.get('monthly_summary', [])
                    print(f"MONTHLY ATTENDANCE ({len(monthly_summary)} months):")
                    for month in monthly_summary[:6]:  # Show first 6 months
                        print(f"  - {month.get('label', 'Unknown')}: {month.get('present', 0)}/{month.get('total', 0)} ({month.get('percentage', 0)}%)")
                    
                else:
                    print("Could not retrieve additional student data from main database")
            except Exception as e:
                print(f"Error retrieving additional student data: {e}")
            
            print(f"{'='*60}\n")
            
            # Store student data in session with proper session management
            session.permanent = True  # Make session permanent
            session['student_logged_in'] = True
            session['student_roll_number'] = student['roll_number']
            session['student_data'] = student
            session['login_time'] = datetime.now().isoformat()
            session['session_id'] = f"student_{student['roll_number']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            flash(f'Welcome, {student["roll_number"]}', 'success')
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
    
    # Fetch comprehensive data from main Moulya database
    dashboard_stats = {}
    if roll_number:
        try:
            dashboard_stats = student_service.get_student_dashboard_stats(roll_number)
        except Exception as e:
            print(f"Error fetching dashboard stats: {e}")
            flash('Unable to fetch some data from the main database.', 'warning')
    
    return render_template('dashboard.html', 
                         student=student_data, 
                         stats=dashboard_stats)

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
    """Student attendance view with monthly breakdown (monthly only)"""
    student_data = session.get('student_data', {})
    roll_number = student_data.get('roll_number')
    subject_id = request.args.get('subject_id', type=int)
    selected_month = request.args.get('month')
    
    # Print current user data when accessing attendance page
    print(f"\n{'='*50}")
    print(f"ATTENDANCE PAGE ACCESSED")
    print(f"{'='*50}")
    print(f"Roll Number: {roll_number}")
    print(f"Access Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Subject ID: {subject_id if subject_id else 'All Subjects'}")
    print(f"Selected Month: {selected_month if selected_month else 'All Months'}")
    print(f"{'='*50}")
    
    # Initialize default values
    subject_info = None
    attendance_summary = {'total_classes': 0, 'present': 0, 'absent': 0, 'percentage': 0.0}
    monthly_summary = []
    months_options = []
    monthly_stat = None
    
    if roll_number:
        try:
            # Get attendance summary (monthly model)
            attendance_summary = student_service.get_student_attendance_summary(roll_number, subject_id)
            print(f"[DEBUG] Attendance Summary from service: {attendance_summary}")
            
            # Get monthly attendance data (monthly model)
            monthly_data = student_service.get_student_monthly_attendance(roll_number, subject_id)
            monthly_summary = monthly_data.get('monthly_summary', [])
            print(f"[DEBUG] Monthly Summary from service: {len(monthly_summary)} months")
            
            # Get subject info if subject_id is provided
            if subject_id:
                enrolled_subjects = student_service.get_student_enrolled_subjects(roll_number)
                for subject in enrolled_subjects:
                    if subject.get('id') == subject_id:
                        subject_info = subject
                        break
            
            # Create months options for dropdown
            months_options = [{'value': month['month_key'], 'label': month['label']} for month in monthly_summary]
            
            # If a specific month is selected, pick its stat
            if selected_month:
                for month_data in monthly_summary:
                    if month_data['month_key'] == selected_month:
                        monthly_stat = month_data
                        break
            
            # Print monthly data to backend console
            print(f"\n=== MONTHLY ATTENDANCE DATA FOR {roll_number} ===")
            print(f"Overall Summary:")
            print(f"  - Total Classes: {attendance_summary.get('total_classes', 0)}")
            print(f"  - Present: {attendance_summary.get('present', 0)}")
            print(f"  - Absent: {attendance_summary.get('absent', 0)}")
            print(f"  - Percentage: {attendance_summary.get('percentage', 0)}%")
            print(f"Monthly Summary: {len(monthly_summary)} months")
            for month in monthly_summary:
                print(f"  - {month['label']}: {month['present']}/{month['total']} ({month['percentage']}%)")
            print("=" * 60)
            
            # Debug template data
            print(f"[DEBUG] Template Data:")
            print(f"  attendance_summary: {attendance_summary}")
            print(f"  monthly_summary: {len(monthly_summary)} items")
            print(f"  subject_info: {subject_info}")
        except Exception as e:
            print(f"Error fetching attendance monthly data: {e}")
            flash('Unable to fetch attendance data from the main database.', 'warning')
    
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
    if roll_number:
        try:
            marks_records = student_service.get_student_marks_records(roll_number, subject_id)
        except Exception as e:
            print(f"Error fetching marks records: {e}")
            flash('Unable to fetch marks data from the main database.', 'warning')
    
    return render_template('marks.html', 
                         student=student_data, 
                         marks_records=marks_records,
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

@app.route('/api/attendance/monthly')
@require_auth
def api_monthly_attendance():
    """API endpoint to get monthly attendance data"""
    student_data = session.get('student_data', {})
    roll_number = student_data.get('roll_number')
    subject_id = request.args.get('subject_id', type=int)
    
    if not roll_number:
        return jsonify({'error': 'Student not found'}), 404
    
    try:
        # Get monthly attendance data
        monthly_data = student_service.get_student_monthly_attendance(roll_number, subject_id)
        
        return jsonify({
            'success': True,
            'data': monthly_data
        })
    except Exception as e:
        print(f"Error in API monthly attendance: {e}")
        return jsonify({'error': 'Failed to fetch attendance data'}), 500

@app.route('/api/attendance/records')
@require_auth
def api_attendance_records():
    """API endpoint to get attendance records for a specific month"""
    student_data = session.get('student_data', {})
    roll_number = student_data.get('roll_number')
    subject_id = request.args.get('subject_id', type=int)
    month = request.args.get('month')  # Format: YYYY-MM
    
    if not roll_number:
        return jsonify({'error': 'Student not found'}), 404
    
    try:
        # Get all attendance records
        attendance_records = student_service.get_student_attendance_records(roll_number, subject_id)
        
        # Filter by month if specified
        monthly_records = []
        if month:
            from datetime import datetime
            try:
                sel_year, sel_month = month.split('-')
                sel_year = int(sel_year)
                sel_month = int(sel_month)
                
                for record in attendance_records:
                    if record.get('date'):
                        try:
                            record_date = datetime.fromisoformat(record['date'].replace('Z', '+00:00'))
                            if record_date.year == sel_year and record_date.month == sel_month:
                                monthly_records.append(record)
                        except:
                            continue
            except Exception as e:
                print(f"Error parsing month filter: {e}")
                monthly_records = attendance_records
        else:
            monthly_records = attendance_records
        
        return jsonify({
            'success': True,
            'data': {
                'records': monthly_records,
                'total': len(monthly_records)
            }
        })
    except Exception as e:
        print(f"Error in API attendance records: {e}")
        return jsonify({'error': 'Failed to fetch attendance records'}), 500

