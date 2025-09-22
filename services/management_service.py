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
                username=username
            )
            lecturer.set_password(password)
            
            success, message = safe_add_and_commit(lecturer)
            if success:
                # Create subject assignments if subjects were provided
                subject_ids = lecturer_data.get('subject_ids', [])
                if subject_ids:
                    from models.assignments import SubjectAssignment
                    from datetime import datetime
                    
                    current_year = datetime.now().year
                    assignments = []
                    
                    for subject_id in subject_ids:
                        # Check if assignment already exists
                        existing = SubjectAssignment.query.filter_by(
                            lecturer_id=lecturer.id,
                            subject_id=int(subject_id),
                            academic_year=current_year
                        ).first()
                        
                        if not existing:
                            assignment = SubjectAssignment(
                                lecturer_id=lecturer.id,
                                subject_id=int(subject_id),
                                academic_year=current_year
                            )
                            assignments.append(assignment)
                    
                    if assignments:
                        for assignment in assignments:
                            safe_add_and_commit(assignment)
                
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
                    subject_codes = str(row[2]).strip() if row[2] and str(row[2]).strip() and str(row[2]).strip().lower() != 'none' else None
                    
                    # Debug: log what we read
                    print(f"Row {row_num}: lecturer_id='{lecturer_id}', name='{name}', subject_codes='{subject_codes}'")
                    
                    if not lecturer_id or not name:
                        errors.append(f"Row {row_num}: Lecturer ID ('{lecturer_id}') and Name ('{name}') are required")
                        continue
                    
                    # Parse subject codes (comma-separated)
                    subject_ids = []
                    if subject_codes:
                        print(f"Row {row_num}: Processing subject codes: '{subject_codes}'")
                        subject_code_list = [code.strip() for code in subject_codes.split(',') if code.strip()]
                        print(f"Row {row_num}: Subject code list: {subject_code_list}")
                        for code in subject_code_list:
                            subject = Subject.query.filter_by(code=code, is_active=True).first()
                            if subject:
                                subject_ids.append(subject.id)
                                print(f"Row {row_num}: Found subject '{code}' with ID {subject.id}")
                            else:
                                errors.append(f"Row {row_num}: Subject code '{code}' not found")
                                print(f"Row {row_num}: Subject code '{code}' not found")
                    
                    print(f"Row {row_num}: Final subject_ids: {subject_ids}")
                    
                    # Validate data
                    is_valid, message = validate_lecturer_id(lecturer_id)
                    if not is_valid:
                        errors.append(f"Row {row_num}: Lecturer ID '{lecturer_id}' - {message}")
                        continue
                    
                    is_valid, message = validate_name(name)
                    if not is_valid:
                        errors.append(f"Row {row_num}: Name '{name}' - {message}")
                        continue
                    
                    # Check for duplicates (only active lecturers)
                    existing_active_lecturer = Lecturer.query.filter_by(lecturer_id=lecturer_id, is_active=True).first()
                    if existing_active_lecturer:
                        errors.append(f"Row {row_num}: Lecturer ID {lecturer_id} already exists (active)")
                        continue
                    
                    # Check if there's an inactive lecturer with the same ID - if so, we'll replace it
                    existing_inactive_lecturer = Lecturer.query.filter_by(lecturer_id=lecturer_id, is_active=False).first()
                    if existing_inactive_lecturer:
                        # Delete all subject assignments for this lecturer first to avoid foreign key constraint violations
                        from models.assignments import SubjectAssignment
                        SubjectAssignment.query.filter_by(lecturer_id=existing_inactive_lecturer.id).delete()
                        # Delete the inactive lecturer so we can create a new one with the same ID
                        db.session.delete(existing_inactive_lecturer)
                    
                    # Generate credentials for new lecturer
                    success, username, password, msg = AuthService.generate_lecturer_credentials(name, lecturer_id)
                    if not success:
                        errors.append(f"Row {row_num}: {msg}")
                        continue
                    
                    print(f"Row {row_num}: Lecturer '{name}' (ID: {lecturer_id}) passed validation, adding to list")
                    
                    lecturer = Lecturer(
                        lecturer_id=lecturer_id,
                        name=name,
                        username=username
                    )
                    lecturer.set_password(password)
                    
                    # Store subject IDs for later assignment
                    lecturer._temp_subject_ids = subject_ids
                    
                    lecturers.append(lecturer)
                    credentials.append({
                        'lecturer_id': lecturer_id,
                        'name': name,
                        'username': username,
                        'password': password
                    })
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: Error processing data - {str(e)}")
                    print(f"Row {row_num}: Exception - {str(e)}")
            
            print(f"Processing complete: {len(lecturers)} lecturers to add, {len(errors)} errors")
            for error in errors:
                print(f"Error: {error}")
            
            if lecturers:
                # Add all lecturers to session (all are new now)
                for lecturer in lecturers:
                    db.session.add(lecturer)
                
                try:
                    db.session.commit()
                    message = f"Successfully added {len(lecturers)} lecturer{'s' if len(lecturers) > 1 else ''}"
                    
                    # Create subject assignments for lecturers that have subjects
                    from models.assignments import SubjectAssignment
                    from datetime import datetime
                    
                    current_year = datetime.now().year
                    assignments = []
                    
                    for lecturer in lecturers:
                        if hasattr(lecturer, '_temp_subject_ids') and lecturer._temp_subject_ids:
                            for subject_id in lecturer._temp_subject_ids:
                                # Check if assignment already exists
                                existing = SubjectAssignment.query.filter_by(
                                    lecturer_id=lecturer.id,
                                    subject_id=subject_id,
                                    academic_year=current_year
                                ).first()
                                
                                if not existing:
                                    assignment = SubjectAssignment(
                                        lecturer_id=lecturer.id,
                                        subject_id=subject_id,
                                        academic_year=current_year
                                    )
                                    assignments.append(assignment)
                    
                    if assignments:
                        success_assign, message_assign = bulk_insert(assignments)
                        if not success_assign:
                            # Log but don't fail the whole operation
                            print(f"Warning: Failed to create some subject assignments: {message_assign}")
                    
                    return True, message, credentials, errors
                    
                except Exception as e:
                    db.session.rollback()
                    return False, f"Database error: {str(e)}", [], errors
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

            # Read header row and map columns by header name (case-insensitive)
            header_row = [str(c.value).strip() if c.value is not None else '' for c in next(sheet.iter_rows(min_row=1, max_row=1))]
            header_to_index = {h.lower(): i for i, h in enumerate(header_row) if h}

            def find_col(*possible_names):
                for name in possible_names:
                    idx = header_to_index.get(name.lower())
                    if idx is not None:
                        return idx
                return None

            col_roll = find_col('roll number', 'roll_number', 'rollno', 'roll', 'roll no')
            col_name = find_col('name', 'full name', 'student name')
            col_course_code = find_col('course code', 'course', 'course_code', 'course name', 'course short code')
            col_ac_year = find_col('academic year', 'year', 'year level', 'class year')
            col_email = find_col('email', 'email id', 'e-mail')

            # If headers are missing, fall back to legacy fixed positions (A..E)
            if col_roll is None:
                col_roll = 0
            if col_name is None:
                col_name = 1
            if col_course_code is None:
                col_course_code = 2
            if col_ac_year is None:
                col_ac_year = 3
            if col_email is None:
                col_email = 4

            import re

            def parse_year(value):
                if value is None:
                    return None
                try:
                    # Try numeric directly
                    return int(value)
                except Exception:
                    # Extract first digit 1-3 from strings like "1", "1st", "Year 1"
                    match = re.search(r"([1-3])", str(value))
                    return int(match.group(1)) if match else None

            for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if not any(row):
                    continue

                try:
                    roll_number = str(row[col_roll]).strip() if col_roll < len(row) and row[col_roll] else None
                    name = str(row[col_name]).strip() if col_name < len(row) and row[col_name] else None
                    course_code_raw = str(row[col_course_code]).strip() if col_course_code < len(row) and row[col_course_code] else None
                    course_code = course_code_raw.upper() if course_code_raw else None
                    academic_year = parse_year(row[col_ac_year] if col_ac_year < len(row) else None)
                    email_val = row[col_email] if col_email < len(row) else None
                    email = str(email_val).strip() if email_val and str(email_val).strip().lower() not in ['none', 'na', 'n/a'] else None

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

                    # Find course by code (case-insensitive). If not found, try using alphabetic prefix (e.g., BCA301 -> BCA)
                    course = Course.query.filter(
                        db.func.lower(Course.code) == course_code.lower(),
                        Course.is_active == True
                    ).first()
                    if not course:
                        prefix_match = re.match(r"^[A-Za-z]+", course_code)
                        if prefix_match:
                            prefix = prefix_match.group(0)
                            # Try existing course with prefix (e.g., BCA)
                            course = Course.query.filter(
                                db.func.lower(Course.code) == prefix.lower(),
                                Course.is_active == True
                            ).first()
                            # If still not found, create a minimal course for this prefix
                            if not course:
                                try:
                                    new_course = Course(
                                        name=prefix,
                                        code=prefix,
                                        description=f"Auto-created from bulk upload for prefix {prefix}",
                                        duration_years=3,
                                        total_semesters=6,
                                        is_active=True
                                    )
                                    db.session.add(new_course)
                                    db.session.commit()
                                    course = new_course
                                except Exception:
                                    db.session.rollback()
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
    
    @staticmethod
    def assign_subjects_to_lecturer(lecturer_id, subject_ids):
        """Assign subjects to an existing lecturer"""
        try:
            lecturer = Lecturer.query.get(lecturer_id)
            if not lecturer:
                return False, "Lecturer not found"
            
            from models.assignments import SubjectAssignment
            from datetime import datetime
            
            current_year = datetime.now().year
            assignments_created = 0
            
            for subject_id in subject_ids:
                # 1) If an active assignment exists, skip
                existing_active = SubjectAssignment.query.filter_by(
                    lecturer_id=lecturer_id,
                    subject_id=int(subject_id),
                    academic_year=current_year,
                    is_active=True
                ).first()

                if existing_active:
                    continue

                # 2) If an inactive assignment exists for this year, reactivate it
                existing_any = SubjectAssignment.query.filter_by(
                    lecturer_id=lecturer_id,
                    subject_id=int(subject_id),
                    academic_year=current_year
                ).first()

                if existing_any:
                    existing_any.is_active = True
                    try:
                        db.session.commit()
                        assignments_created += 1
                    except Exception as e:
                        db.session.rollback()
                        return False, f"Error reactivating assignment for subject {subject_id}: {str(e)}"
                    continue

                # 3) Otherwise create a fresh assignment
                assignment = SubjectAssignment(
                    lecturer_id=lecturer_id,
                    subject_id=int(subject_id),
                    academic_year=current_year
                )
                success, message = safe_add_and_commit(assignment)
                if success:
                    assignments_created += 1
                else:
                    return False, f"Error creating assignment for subject {subject_id}: {message}"
            
            if assignments_created > 0:
                return True, f"Successfully assigned {assignments_created} subject(s) to {lecturer.name}"
            else:
                return True, f"No new subjects assigned to {lecturer.name} (subjects were already assigned)"
                
        except Exception as e:
            return False, f"Error assigning subjects: {str(e)}"
    
    @staticmethod
    def unassign_subject_from_lecturer(lecturer_id, subject_id):
        """Unassign (deactivate) a subject from a lecturer for current academic year"""
        try:
            lecturer = Lecturer.query.get(lecturer_id)
            if not lecturer:
                return False, "Lecturer not found"

            from datetime import datetime
            current_year = datetime.now().year

            assignment = SubjectAssignment.query.filter_by(
                lecturer_id=lecturer_id,
                subject_id=int(subject_id),
                academic_year=current_year,
                is_active=True
            ).first()

            if not assignment:
                # Check if it exists but already inactive
                existing_inactive = SubjectAssignment.query.filter_by(
                    lecturer_id=lecturer_id,
                    subject_id=int(subject_id),
                    academic_year=current_year,
                    is_active=False
                ).first()
                if existing_inactive:
                    return True, "Subject already unassigned for this year"
                return False, "Assignment not found for this year"

            assignment.is_active = False
            db.session.commit()
            return True, f"Unassigned subject successfully from {lecturer.name}"

        except Exception as e:
            db.session.rollback()
            return False, f"Error unassigning subject: {str(e)}"

