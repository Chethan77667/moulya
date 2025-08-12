"""
Management service for Moulya College Management System
Business logic for management portal operations
"""

from models.user import Lecturer
from models.academic import Course, Subject, AcademicYear
from models.student import Student, StudentEnrollment
from models.assignments import SubjectAssignment
from database import db
from utils.db_helpers import safe_add_and_commit, bulk_insert
from utils.validators import *
from services.auth_service import AuthService
import openpyxl
from io import BytesIO

class ManagementService:
    """Management service class"""
    
    @staticmethod
    def get_dashboard_stats():
        """Get dashboard statistics"""
        try:
            stats = {
                'total_lecturers': Lecturer.query.filter_by(is_active=True).count(),
                'total_students': Student.query.filter_by(is_active=True).count(),
                'total_courses': Course.query.filter_by(is_active=True).count(),
                'total_subjects': Subject.query.filter_by(is_active=True).count(),
                'recent_lecturers': Lecturer.query.filter_by(is_active=True).order_by(Lecturer.created_at.desc()).limit(5).all(),
                'recent_students': Student.query.filter_by(is_active=True).order_by(Student.created_at.desc()).limit(5).all()
            }
            return stats
        except Exception as e:
            return {}
    
    @staticmethod
    def get_lecturers_paginated(page=1, search='', per_page=20):
        """Get paginated lecturers list"""
        try:
            query = Lecturer.query.filter_by(is_active=True)
            
            if search:
                query = query.filter(
                    db.or_(
                        Lecturer.name.contains(search),
                        Lecturer.lecturer_id.contains(search),
                        Lecturer.username.contains(search)
                    )
                )
            
            pagination = query.order_by(Lecturer.name).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'lecturers': pagination.items,
                'pagination': pagination
            }
        except Exception as e:
            return {'lecturers': [], 'pagination': None}
    
    @staticmethod
    def get_students_paginated(page=1, search='', course_id=None, per_page=20):
        """Get paginated students list"""
        try:
            query = Student.query.filter_by(is_active=True)
            
            if search:
                query = query.filter(
                    db.or_(
                        Student.name.contains(search),
                        Student.roll_number.contains(search)
                    )
                )
            
            if course_id:
                query = query.filter_by(course_id=course_id)
            
            pagination = query.order_by(Student.name).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'students': pagination.items,
                'pagination': pagination
            }
        except Exception as e:
            return {'students': [], 'pagination': None}
    
    @staticmethod
    def get_subjects_by_course(course_id=None):
        """Get subjects filtered by course"""
        try:
            if course_id:
                return Subject.query.filter_by(course_id=course_id, is_active=True).order_by(Subject.year, Subject.semester).all()
            else:
                return Subject.query.filter_by(is_active=True).order_by(Subject.year, Subject.semester).all()
        except Exception as e:
            return []
    
    @staticmethod
    def add_lecturer(lecturer_data):
        """Add single lecturer"""
        try:
            # Validate data
            is_valid, message = validate_lecturer_id(lecturer_data.get('lecturer_id'))
            if not is_valid:
                return False, message
            
            is_valid, message = validate_name(lecturer_data.get('name'))
            if not is_valid:
                return False, message
            
            # Check if lecturer ID already exists
            existing = Lecturer.query.filter_by(lecturer_id=lecturer_data['lecturer_id']).first()
            if existing:
                return False, "Lecturer ID already exists"
            
            # Generate credentials
            success, username, password, msg = AuthService.generate_lecturer_credentials(
                lecturer_data['name'], 
                lecturer_data['lecturer_id'],
                lecturer_data.get('username'),
                lecturer_data.get('password')
            )
            
            if not success:
                return False, msg
            
            # Create lecturer
            lecturer = Lecturer(
                lecturer_id=lecturer_data['lecturer_id'],
                name=lecturer_data['name'],
                username=username,
                course_id=lecturer_data.get('course_id')
            )
            lecturer.set_password(password)
            
            success, message = safe_add_and_commit(lecturer)
            if success:
                return True, f"Lecturer added successfully. Username: {username}, Password: {password}"
            else:
                return False, message
                
        except Exception as e:
            return False, f"Error adding lecturer: {str(e)}"
    
    @staticmethod
    def bulk_add_lecturers(file_data):
        """Bulk add lecturers from Excel file"""
        try:
            workbook = openpyxl.load_workbook(BytesIO(file_data))
            sheet = workbook.active
            
            lecturers = []
            errors = []
            credentials = []
            
            # Expected columns: lecturer_id, name, email, phone, department
            for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if not any(row):  # Skip empty rows
                    continue
                
                try:
                    lecturer_id = str(row[0]).strip() if row[0] else None
                    name = str(row[1]).strip() if row[1] else None
                    course_code = str(row[2]).strip() if row[2] and row[2] != 'None' else None
                    
                    if not lecturer_id or not name:
                        errors.append(f"Row {row_num}: Lecturer ID and Name are required")
                        continue
                    
                    # Find course by code if provided
                    course_id = None
                    if course_code:
                        course = Course.query.filter_by(code=course_code, is_active=True).first()
                        if course:
                            course_id = course.id
                        else:
                            errors.append(f"Row {row_num}: Course code {course_code} not found")
                            continue
                    
                    # Validate data
                    is_valid, message = validate_lecturer_id(lecturer_id)
                    if not is_valid:
                        errors.append(f"Row {row_num}: {message}")
                        continue
                    
                    is_valid, message = validate_name(name)
                    if not is_valid:
                        errors.append(f"Row {row_num}: {message}")
                        continue
                    
                    # Check for duplicates
                    if Lecturer.query.filter_by(lecturer_id=lecturer_id).first():
                        errors.append(f"Row {row_num}: Lecturer ID {lecturer_id} already exists")
                        continue
                    
                    # Generate credentials
                    success, username, password, msg = AuthService.generate_lecturer_credentials(name, lecturer_id)
                    if not success:
                        errors.append(f"Row {row_num}: {msg}")
                        continue
                    
                    lecturer = Lecturer(
                        lecturer_id=lecturer_id,
                        name=name,
                        username=username,
                        course_id=course_id
                    )
                    lecturer.set_password(password)
                    
                    lecturers.append(lecturer)
                    credentials.append({
                        'lecturer_id': lecturer_id,
                        'name': name,
                        'username': username,
                        'password': password
                    })
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: Error processing data - {str(e)}")
            
            if lecturers:
                success, message = bulk_insert(lecturers)
                if success:
                    return True, f"Successfully added {len(lecturers)} lecturers", credentials, errors
                else:
                    return False, message, [], errors
            else:
                return False, "No valid lecturers found to add", [], errors
                
        except Exception as e:
            return False, f"Error processing Excel file: {str(e)}", [], []
    
    @staticmethod
    def add_student(student_data):
        """Add single student"""
        try:
            # Validate data
            is_valid, message = validate_roll_number(student_data.get('roll_number'))
            if not is_valid:
                return False, message
            
            is_valid, message = validate_name(student_data.get('name'))
            if not is_valid:
                return False, message
            
            is_valid, message = validate_academic_year(student_data.get('academic_year'))
            if not is_valid:
                return False, message
            
            # Check if roll number already exists
            existing = Student.query.filter_by(roll_number=student_data['roll_number']).first()
            if existing:
                return False, "Roll number already exists"
            
            # Validate course exists
            course = Course.query.get(student_data.get('course_id'))
            if not course:
                return False, "Invalid course selected"
            
            # Create student
            student = Student(
                roll_number=student_data['roll_number'],
                name=student_data['name'],
                course_id=student_data['course_id'],
                academic_year=student_data['academic_year'],
                current_semester=student_data.get('current_semester', 1),
                email=student_data.get('email')
            )
            
            success, message = safe_add_and_commit(student)
            return success, message
                
        except Exception as e:
            return False, f"Error adding student: {str(e)}"
    
    @staticmethod
    def bulk_add_students(file_data):
        """Bulk add students from Excel file"""
        try:
            workbook = openpyxl.load_workbook(BytesIO(file_data))
            sheet = workbook.active
            
            students = []
            errors = []
            
            # Expected columns: roll_number, name, course_code, academic_year, email, phone
            for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if not any(row):  # Skip empty rows
                    continue
                
                try:
                    roll_number = str(row[0]).strip() if row[0] else None
                    name = str(row[1]).strip() if row[1] else None
                    course_code = str(row[2]).strip() if row[2] else None
                    academic_year = int(row[3]) if row[3] else None
                    email = str(row[4]).strip() if row[4] and row[4] != 'None' else None
                    
                    if not all([roll_number, name, course_code, academic_year]):
                        errors.append(f"Row {row_num}: Roll number, name, course code, and academic year are required")
                        continue
                    
                    # Validate data
                    is_valid, message = validate_roll_number(roll_number)
                    if not is_valid:
                        errors.append(f"Row {row_num}: {message}")
                        continue
                    
                    is_valid, message = validate_name(name)
                    if not is_valid:
                        errors.append(f"Row {row_num}: {message}")
                        continue
                    
                    is_valid, message = validate_academic_year(academic_year)
                    if not is_valid:
                        errors.append(f"Row {row_num}: {message}")
                        continue
                    
                    # Find course by code
                    course = Course.query.filter_by(code=course_code, is_active=True).first()
                    if not course:
                        errors.append(f"Row {row_num}: Course code {course_code} not found")
                        continue
                    
                    # Check for duplicates
                    if Student.query.filter_by(roll_number=roll_number).first():
                        errors.append(f"Row {row_num}: Roll number {roll_number} already exists")
                        continue
                    
                    student = Student(
                        roll_number=roll_number,
                        name=name,
                        course_id=course.id,
                        academic_year=academic_year,
                        email=email
                    )
                    
                    students.append(student)
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: Error processing data - {str(e)}")
            
            if students:
                success, message = bulk_insert(students)
                if success:
                    return True, f"Successfully added {len(students)} students", errors
                else:
                    return False, message, errors
            else:
                return False, "No valid students found to add", errors
                
        except Exception as e:
            return False, f"Error processing Excel file: {str(e)}", []
    
    @staticmethod
    def create_course(course_data):
        """Create new course"""
        try:
            # Validate data
            is_valid, message = validate_course_code(course_data.get('code'))
            if not is_valid:
                return False, message
            
            is_valid, message = validate_name(course_data.get('name'), "Course name")
            if not is_valid:
                return False, message
            
            # Check if course code already exists
            existing = Course.query.filter_by(code=course_data['code']).first()
            if existing:
                return False, "Course code already exists"
            
            course = Course(
                name=course_data['name'],
                code=course_data['code'],
                description=course_data.get('description'),
                duration_years=course_data.get('duration_years', 3),
                total_semesters=course_data.get('total_semesters', 6)
            )
            
            success, message = safe_add_and_commit(course)
            return success, message
            
        except Exception as e:
            return False, f"Error creating course: {str(e)}"
    
    @staticmethod
    def create_subject(subject_data):
        """Create new subject"""
        try:
            # Validate data
            is_valid, message = validate_subject_code(subject_data.get('code'))
            if not is_valid:
                return False, message
            
            is_valid, message = validate_name(subject_data.get('name'), "Subject name")
            if not is_valid:
                return False, message
            
            is_valid, message = validate_academic_year(subject_data.get('year'))
            if not is_valid:
                return False, message
            
            is_valid, message = validate_semester(subject_data.get('semester'))
            if not is_valid:
                return False, message
            
            # Validate course exists
            course = Course.query.get(subject_data.get('course_id'))
            if not course:
                return False, "Invalid course selected"
            
            # Check if subject code already exists for this course
            existing = Subject.query.filter_by(
                code=subject_data['code'], 
                course_id=subject_data['course_id']
            ).first()
            if existing:
                return False, "Subject code already exists for this course"
            
            subject = Subject(
                name=subject_data['name'],
                code=subject_data['code'],
                course_id=subject_data['course_id'],
                semester=subject_data['semester'],
                year=subject_data['year'],
                description=subject_data.get('description')
            )
            
            success, message = safe_add_and_commit(subject)
            return success, message
            
        except Exception as e:
            return False, f"Error creating subject: {str(e)}"
    
