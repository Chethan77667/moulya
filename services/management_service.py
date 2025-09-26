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
            # If an ACTIVE lecturer exists, block; if an INACTIVE one exists, remove it to allow re-adding
            existing_active = Lecturer.query.filter_by(lecturer_id=lecturer_data['lecturer_id'], is_active=True).first()
            if existing_active:
                return False, "Lecturer ID already exists"

            existing_inactive = Lecturer.query.filter_by(lecturer_id=lecturer_data['lecturer_id'], is_active=False).first()
            if existing_inactive:
                try:
                    # Remove dependent rows and the inactive lecturer to free unique constraints
                    from models.assignments import SubjectAssignment
                    SubjectAssignment.query.filter_by(lecturer_id=existing_inactive.id).delete(synchronize_session=False)
                    from models.attendance import AttendanceRecord, MonthlyAttendanceSummary
                    from models.marks import StudentMarks
                    AttendanceRecord.query.filter_by(lecturer_id=existing_inactive.id).delete(synchronize_session=False)
                    MonthlyAttendanceSummary.query.filter_by(lecturer_id=existing_inactive.id).delete(synchronize_session=False)
                    StudentMarks.query.filter_by(lecturer_id=existing_inactive.id).delete(synchronize_session=False)
                    db.session.delete(existing_inactive)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    return False, f"Error replacing inactive lecturer with same ID: {str(e)}"
            
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
        """Bulk upsert lecturers from Excel file.

        Behavior:
        - If a lecturer with the same `lecturer_id` exists and is active, update their `name`.
        - If they do not exist, create a new lecturer and generate credentials.
        - If subject codes are provided for a row:
          - Ensure those subjects are assigned for the current academic year (create missing assignments).
          - Deactivate assignments for the current academic year that are not in the uploaded list.
        - If the existing record is inactive, replace/reactivate by removing the inactive record and creating a new one.
        """
        try:
            workbook = openpyxl.load_workbook(BytesIO(file_data))
            sheet = workbook.active
            
            lecturers_to_create = []
            errors = []
            credentials = []
            updates_applied = 0
            
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
                    
                    # Upsert by lecturer_id
                    existing_active_lecturer = Lecturer.query.filter_by(lecturer_id=lecturer_id, is_active=True).first()
                    if existing_active_lecturer:
                        # Update name if changed
                        if existing_active_lecturer.name != name:
                            existing_active_lecturer.name = name
                            updates_applied += 1
                        # Handle subject assignments for current year based on provided list
                        if subject_ids:
                            from models.assignments import SubjectAssignment
                            from datetime import datetime
                            current_year = datetime.now().year
                            # Fetch existing assignments for the year
                            existing_assignments = SubjectAssignment.query.filter_by(
                                lecturer_id=existing_active_lecturer.id,
                                academic_year=current_year
                            ).all()
                            existing_subject_ids = {a.subject_id for a in existing_assignments if a.is_active}
                            desired_subject_ids = set(int(sid) for sid in subject_ids)

                            # Add new ones
                            to_add = desired_subject_ids - existing_subject_ids
                            for sid in to_add:
                                assignment = SubjectAssignment(
                                    lecturer_id=existing_active_lecturer.id,
                                    subject_id=int(sid),
                                    academic_year=current_year
                                )
                                db.session.add(assignment)

                            # Deactivate those not desired
                            to_deactivate = existing_subject_ids - desired_subject_ids
                            if to_deactivate:
                                for a in existing_assignments:
                                    if a.subject_id in to_deactivate and a.is_active:
                                        a.is_active = False
                        # No credentials for updates
                    else:
                        # Check inactive and remove to free unique
                        existing_inactive_lecturer = Lecturer.query.filter_by(lecturer_id=lecturer_id, is_active=False).first()
                        if existing_inactive_lecturer:
                            from models.assignments import SubjectAssignment
                            SubjectAssignment.query.filter_by(lecturer_id=existing_inactive_lecturer.id).delete()
                            db.session.delete(existing_inactive_lecturer)

                        # Generate credentials for new lecturer
                        success, username, password, msg = AuthService.generate_lecturer_credentials(name, lecturer_id)
                        if not success:
                            errors.append(f"Row {row_num}: {msg}")
                            continue

                        lecturer = Lecturer(
                            lecturer_id=lecturer_id,
                            name=name,
                            username=username
                        )
                        lecturer.set_password(password)

                        # Store subject IDs for later assignment
                        lecturer._temp_subject_ids = subject_ids

                        lecturers_to_create.append(lecturer)
                        credentials.append({
                            'lecturer_id': lecturer_id,
                            'name': name,
                            'username': username,
                            'password': password
                        })
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: Error processing data - {str(e)}")
                    print(f"Row {row_num}: Exception - {str(e)}")
            
            print(f"Processing complete: {len(lecturers_to_create)} lecturers to add, {updates_applied} updates, {len(errors)} errors")
            for error in errors:
                print(f"Error: {error}")
            
            if lecturers_to_create or updates_applied > 0:
                try:
                    # Commit updates to existing lecturers first
                    if updates_applied > 0:
                        db.session.commit()
                    
                    # Add all new lecturers to session
                    for lecturer in lecturers_to_create:
                        db.session.add(lecturer)
                    
                    # Commit new lecturers
                    if lecturers_to_create:
                        db.session.commit()
                    
                    message = []
                    if lecturers_to_create:
                        message.append(f"added {len(lecturers_to_create)}")
                    if updates_applied:
                        message.append(f"updated {updates_applied}")
                    message = "Successfully " + ", ".join(message) + " lecturer(s)"
                    
                    # Create subject assignments for lecturers that have subjects
                    from models.assignments import SubjectAssignment
                    from datetime import datetime
                    
                    current_year = datetime.now().year
                    assignments = []
                    
                    for lecturer in lecturers_to_create:
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
                return False, "No valid lecturer changes found", [], errors
                
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
            existing_active = Student.query.filter_by(roll_number=student_data['roll_number'], is_active=True).first()
            if existing_active:
                return False, "Roll number already exists"

            # Remove inactive duplicate if present
            existing_inactive = Student.query.filter_by(roll_number=student_data['roll_number'], is_active=False).first()
            if existing_inactive:
                ok, msg = ManagementService.delete_student_permanently(existing_inactive.id)
                if not ok:
                    return False, msg
            
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
        """Bulk upsert students from Excel file.

        Behavior:
        - Match by `roll_number`.
        - If student exists (active), update fields: name, course, academic_year, email.
        - If student does not exist, create a new one.
        - If a course code is new (e.g., prefix-based), auto-create minimal course if needed.
        """
        try:
            workbook = openpyxl.load_workbook(BytesIO(file_data))
            sheet = workbook.active

            students_to_create = []
            errors = []
            updates_applied = 0

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
            # Try exact-name matches first
            col_class = find_col('class', 'class name', 'year/class', 'year & course', 'class section', 'class & section')
            # If still not found, choose first header containing the word 'class'
            if col_class is None:
                for h, idx in header_to_index.items():
                    if 'class' in h:
                        col_class = idx
                        break
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

            ROMAN_TO_INT = { 'I': 1, 'II': 2, 'III': 3 }

            def parse_class(value):
                """Parse strings like 'II BCA B' → (course_code='BCA', academic_year=2).
                Section (e.g., 'B') is currently ignored.
                """
                if not value:
                    return None, None
                text = str(value).strip()
                # Try split by spaces, handle roman numerals or digits
                parts = text.split()
                year_val = None
                course_val = None
                if parts:
                    first = parts[0].upper()
                    if first in ROMAN_TO_INT:
                        year_val = ROMAN_TO_INT[first]
                        if len(parts) > 1:
                            course_val = re.sub(r"[^A-Za-z]", "", parts[1]).upper() or None
                    else:
                        # Try digits anywhere
                        y = parse_year(first)
                        if y:
                            year_val = y
                            if len(parts) > 1:
                                course_val = re.sub(r"[^A-Za-z]", "", parts[1]).upper() or None
                        else:
                            # Maybe 'BCA II B' format → find alpha block and roman/digit
                            m_course = re.search(r"([A-Za-z]+)", text)
                            m_year = re.search(r"\b(I{1,3}|[1-3])\b", text, re.IGNORECASE)
                            if m_year:
                                yr = m_year.group(1).upper()
                                year_val = ROMAN_TO_INT.get(yr, parse_year(yr))
                            if m_course:
                                course_val = m_course.group(1).upper()
                return course_val, year_val

            ROMAN_SET = { 'I', 'II', 'III' }

            def normalize_course_code(raw: str):
                """Extract a likely course code from values like 'II_BCA_B' -> 'BCA'.
                Picks the longest alphabetic token that is not a roman year indicator.
                """
                if not raw:
                    return None
                tokens = re.findall(r"[A-Za-z]+", str(raw).upper())
                # Filter out roman numerals used for year
                tokens = [t for t in tokens if t not in ROMAN_SET]
                if not tokens:
                    return None
                # Prefer the longest token
                tokens.sort(key=len, reverse=True)
                return tokens[0]

            for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if not any(row):
                    continue

                try:
                    roll_number = str(row[col_roll]).strip() if (col_roll is not None and col_roll < len(row) and row[col_roll]) else None
                    name = str(row[col_name]).strip() if col_name < len(row) and row[col_name] else None
                    course_code_raw = str(row[col_course_code]).strip() if (col_course_code is not None and col_course_code < len(row) and row[col_course_code]) else None
                    # Normalize complex codes such as 'II_BCA_B' -> 'BCA'
                    course_code = normalize_course_code(course_code_raw) if course_code_raw else None
                    academic_year = parse_year(row[col_ac_year] if (col_ac_year is not None and col_ac_year < len(row)) else None)
                    # If missing, try parsing from combined class column
                    if (course_code is None or academic_year is None) and col_class is not None and col_class < len(row):
                        cc_from_class, year_from_class = parse_class(row[col_class])
                        if course_code is None:
                            course_code = cc_from_class
                        if academic_year is None:
                            academic_year = year_from_class

                    # As final fallback for course, try extracting letters from roll number prefix (e.g., BCA23081 -> BCA)
                    if course_code is None and roll_number:
                        m_prefix = re.match(r"^[A-Za-z]+", roll_number)
                        if m_prefix:
                            course_code = normalize_course_code(m_prefix.group(0))

                    # If academic year is still None, default to 1 (so initial bulk upload doesn't drop rows)
                    if academic_year is None:
                        academic_year = 1
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

                    # Find course by normalized code; auto-create if not found
                    course = Course.query.filter(
                        db.func.lower(Course.code) == course_code.lower(),
                        Course.is_active == True
                    ).first()
                    if not course and course_code:
                        try:
                            new_course = Course(
                                name=course_code,
                                code=course_code,
                                description=f"Auto-created from bulk upload",
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

                    existing = Student.query.filter_by(roll_number=roll_number, is_active=True).first()
                    if existing:
                        # Update existing fields if changed
                        changed = False
                        if existing.name != name:
                            existing.name = name
                            changed = True
                        if existing.course_id != course.id:
                            existing.course_id = course.id
                            changed = True
                        if existing.academic_year != academic_year:
                            existing.academic_year = academic_year
                            changed = True
                        if (email or None) != (existing.email or None):
                            existing.email = email
                            changed = True
                        if changed:
                            updates_applied += 1
                    else:
                        # If inactive exists, hard-delete to free unique key, then create
                        existing_inactive = Student.query.filter_by(roll_number=roll_number, is_active=False).first()
                        if existing_inactive:
                            ok, msg = ManagementService.delete_student_permanently(existing_inactive.id)
                            if not ok:
                                errors.append(f"Row {row_num}: {msg}")
                                continue

                        student = Student(
                            roll_number=roll_number,
                            name=name,
                            course_id=course.id,
                            academic_year=academic_year,
                            email=email
                        )

                        students_to_create.append(student)

                except Exception as e:
                    errors.append(f"Row {row_num}: Error processing data - {str(e)}")
            print(students_to_create)
            print(updates_applied)
            print(errors)
            if students_to_create or updates_applied > 0:
                try:
                    # Commit updates to existing students
                    if updates_applied > 0:
                        db.session.commit()
                    
                    # Add new students
                    if students_to_create:
                        success, message = bulk_insert(students_to_create)
                        if not success:
                            return False, message, errors
                    
                    response_msg = []
                    if students_to_create:
                        response_msg.append(f"added {len(students_to_create)}")
                    if updates_applied:
                        response_msg.append(f"updated {updates_applied}")
                    return True, f"Successfully {', '.join(response_msg)} student(s)", errors
                except Exception as e:
                    db.session.rollback()
                    return False, f"Database error: {str(e)}", errors
            else:
                return False, "No valid student changes found", errors

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
            existing_active = Course.query.filter_by(code=course_data['code'], is_active=True).first()
            if existing_active:
                return False, "Course code already exists"

            # Remove inactive duplicate course (same code)
            existing_inactive = Course.query.filter_by(code=course_data['code'], is_active=False).first()
            if existing_inactive:
                ok, msg = ManagementService.delete_course_permanently(existing_inactive.id)
                if not ok:
                    return False, msg
            
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
            existing_active = Subject.query.filter_by(
                code=subject_data['code'], 
                course_id=subject_data['course_id'],
                is_active=True
            ).first()
            if existing_active:
                return False, "Subject code already exists for this course"

            # Remove inactive duplicate if present for same course/code
            existing_inactive = Subject.query.filter_by(
                code=subject_data['code'],
                course_id=subject_data['course_id'],
                is_active=False
            ).first()
            if existing_inactive:
                ok, msg = ManagementService.delete_subject_permanently(existing_inactive.id)
                if not ok:
                    return False, msg
            
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


    @staticmethod
    def delete_lecturer_permanently(lecturer_id):
        """Hard-delete a lecturer and all dependent records referencing the lecturer.

        Removes:
        - Subject assignments
        - Attendance records and monthly summaries
        - Student marks
        Finally deletes the lecturer row itself.
        """
        try:
            lecturer = Lecturer.query.get(lecturer_id)
            if not lecturer:
                return False, "Lecturer not found"

            # Delete dependent rows explicitly to satisfy FK constraints
            from models.assignments import SubjectAssignment
            from models.attendance import AttendanceRecord, MonthlyAttendanceSummary
            from models.marks import StudentMarks

            SubjectAssignment.query.filter_by(lecturer_id=lecturer.id).delete(synchronize_session=False)
            AttendanceRecord.query.filter_by(lecturer_id=lecturer.id).delete(synchronize_session=False)
            MonthlyAttendanceSummary.query.filter_by(lecturer_id=lecturer.id).delete(synchronize_session=False)
            StudentMarks.query.filter_by(lecturer_id=lecturer.id).delete(synchronize_session=False)

            db.session.delete(lecturer)
            db.session.commit()
            return True, "Lecturer permanently deleted"
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting lecturer: {str(e)}"

    @staticmethod
    def delete_student_permanently(student_id):
        """Hard-delete a student and dependent rows (enrollments, attendance, marks)."""
        try:
            student = Student.query.get(student_id)
            if not student:
                return False, "Student not found"

            from models.student import StudentEnrollment
            from models.attendance import AttendanceRecord
            from models.marks import StudentMarks

            StudentEnrollment.query.filter_by(student_id=student.id).delete(synchronize_session=False)
            AttendanceRecord.query.filter_by(student_id=student.id).delete(synchronize_session=False)
            StudentMarks.query.filter_by(student_id=student.id).delete(synchronize_session=False)

            db.session.delete(student)
            db.session.commit()
            return True, "Student permanently deleted"
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting student: {str(e)}"

    @staticmethod
    def delete_subject_permanently(subject_id):
        """Hard-delete a subject and all dependent rows (assignments, enrollments, attendance, summaries, marks)."""
        try:
            subject = Subject.query.get(subject_id)
            if not subject:
                return False, "Subject not found"

            from models.assignments import SubjectAssignment
            from models.student import StudentEnrollment
            from models.attendance import AttendanceRecord, MonthlyAttendanceSummary
            from models.marks import StudentMarks

            SubjectAssignment.query.filter_by(subject_id=subject.id).delete(synchronize_session=False)
            StudentEnrollment.query.filter_by(subject_id=subject.id).delete(synchronize_session=False)
            AttendanceRecord.query.filter_by(subject_id=subject.id).delete(synchronize_session=False)
            MonthlyAttendanceSummary.query.filter_by(subject_id=subject.id).delete(synchronize_session=False)
            StudentMarks.query.filter_by(subject_id=subject.id).delete(synchronize_session=False)

            db.session.delete(subject)
            db.session.commit()
            return True, "Subject permanently deleted"
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting subject: {str(e)}"

    @staticmethod
    def delete_course_permanently(course_id):
        """Hard-delete a course by first deleting its subjects and associated data, then the course itself."""
        try:
            course = Course.query.get(course_id)
            if not course:
                return False, "Course not found"

            # Delete all subjects under the course (and their dependencies)
            subjects = Subject.query.filter_by(course_id=course.id).all()
            for subj in subjects:
                ok, msg = ManagementService.delete_subject_permanently(subj.id)
                if not ok:
                    return False, msg

            db.session.delete(course)
            db.session.commit()
            return True, "Course permanently deleted"
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting course: {str(e)}"