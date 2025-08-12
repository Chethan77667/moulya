"""
Validation utilities for Moulya College Management System
"""

import re
from datetime import datetime, date

def validate_lecturer_id(lecturer_id):
    """Validate lecturer ID format"""
    if not lecturer_id or len(lecturer_id.strip()) == 0:
        return False, "Lecturer ID is required"
    
    if len(lecturer_id) > 20:
        return False, "Lecturer ID must be 20 characters or less"
    
    # Allow alphanumeric and some special characters
    if not re.match(r'^[A-Za-z0-9_-]+$', lecturer_id):
        return False, "Lecturer ID can only contain letters, numbers, hyphens, and underscores"
    
    return True, "Valid lecturer ID"

def validate_roll_number(roll_number):
    """Validate student roll number format"""
    if not roll_number or len(roll_number.strip()) == 0:
        return False, "Roll number is required"
    
    if len(roll_number) > 20:
        return False, "Roll number must be 20 characters or less"
    
    # Allow alphanumeric and some special characters
    if not re.match(r'^[A-Za-z0-9_-]+$', roll_number):
        return False, "Roll number can only contain letters, numbers, hyphens, and underscores"
    
    return True, "Valid roll number"

def validate_name(name, field_name="Name"):
    """Validate person name"""
    if not name or len(name.strip()) == 0:
        return False, f"{field_name} is required"
    
    if len(name) > 100:
        return False, f"{field_name} must be 100 characters or less"
    
    # Allow letters, spaces, and common name characters
    if not re.match(r'^[A-Za-z\s\.\-\']+$', name):
        return False, f"{field_name} can only contain letters, spaces, periods, hyphens, and apostrophes"
    
    return True, f"Valid {field_name.lower()}"

def validate_username(username):
    """Validate username format"""
    if not username or len(username.strip()) == 0:
        return False, "Username is required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 80:
        return False, "Username must be 80 characters or less"
    
    # Allow alphanumeric and underscore
    if not re.match(r'^[A-Za-z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    
    return True, "Valid username"

def validate_password(password):
    """Validate password strength"""
    if not password:
        return False, "Password is required"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if len(password) > 128:
        return False, "Password must be 128 characters or less"
    
    return True, "Valid password"

def validate_course_code(course_code):
    """Validate course code format"""
    if not course_code or len(course_code.strip()) == 0:
        return False, "Course code is required"
    
    if len(course_code) > 20:
        return False, "Course code must be 20 characters or less"
    
    # Allow alphanumeric and some special characters
    if not re.match(r'^[A-Za-z0-9_-]+$', course_code):
        return False, "Course code can only contain letters, numbers, hyphens, and underscores"
    
    return True, "Valid course code"

def validate_subject_code(subject_code):
    """Validate subject code format"""
    if not subject_code or len(subject_code.strip()) == 0:
        return False, "Subject code is required"
    
    if len(subject_code) > 20:
        return False, "Subject code must be 20 characters or less"
    
    # Allow alphanumeric and some special characters
    if not re.match(r'^[A-Za-z0-9_-]+$', subject_code):
        return False, "Subject code can only contain letters, numbers, hyphens, and underscores"
    
    return True, "Valid subject code"

def validate_academic_year(year):
    """Validate academic year (1, 2, or 3)"""
    try:
        year_int = int(year)
        if year_int not in [1, 2, 3]:
            return False, "Academic year must be 1, 2, or 3"
        return True, "Valid academic year"
    except (ValueError, TypeError):
        return False, "Academic year must be a number"

def validate_semester(semester):
    """Validate semester number"""
    try:
        sem_int = int(semester)
        if sem_int < 1 or sem_int > 8:
            return False, "Semester must be between 1 and 8"
        return True, "Valid semester"
    except (ValueError, TypeError):
        return False, "Semester must be a number"

def validate_marks(marks, max_marks):
    """Validate marks against maximum marks"""
    try:
        marks_float = float(marks)
        max_marks_float = float(max_marks)
        
        if marks_float < 0:
            return False, "Marks cannot be negative"
        
        if marks_float > max_marks_float:
            return False, f"Marks cannot exceed maximum marks ({max_marks_float})"
        
        return True, "Valid marks"
    except (ValueError, TypeError):
        return False, "Marks must be a valid number"

def validate_attendance_status(status):
    """Validate attendance status"""
    valid_statuses = ['present', 'absent']
    if status not in valid_statuses:
        return False, f"Attendance status must be one of: {', '.join(valid_statuses)}"
    
    return True, "Valid attendance status"

def validate_date(date_str):
    """Validate date format"""
    try:
        if isinstance(date_str, str):
            datetime.strptime(date_str, '%Y-%m-%d')
        elif isinstance(date_str, date):
            pass  # Already a date object
        else:
            return False, "Invalid date format"
        
        return True, "Valid date"
    except ValueError:
        return False, "Date must be in YYYY-MM-DD format"