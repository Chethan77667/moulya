#!/usr/bin/env python3
"""
Sample data generator for Moulya College Management System
Creates sample data for testing and demonstration
"""

from app import create_app
from database import db
from models.user import Management, Lecturer
from models.academic import Course, Subject, AcademicYear
from models.student import Student, StudentEnrollment
from models.assignments import SubjectAssignment
from datetime import date, datetime

def create_sample_data():
    """Create sample data for the system"""
    app = create_app()
    
    with app.app_context():
        print("Creating sample data...")
        
        # Create management user (already exists from init_db.py)
        print("✓ Management user already exists (admin/admin123)")
        
        # Create courses
        courses_data = [
            {'name': 'Computer Science Engineering', 'code': 'CSE', 'duration_years': 3, 'total_semesters': 6},
            {'name': 'Information Technology', 'code': 'IT', 'duration_years': 3, 'total_semesters': 6},
            {'name': 'Electronics and Communication', 'code': 'ECE', 'duration_years': 3, 'total_semesters': 6}
        ]
        
        courses = []
        for course_data in courses_data:
            course = Course(**course_data)
            db.session.add(course)
            courses.append(course)
        
        db.session.commit()
        print(f"✓ Created {len(courses)} courses")
        
        # Create subjects
        subjects_data = [
            # CSE subjects
            {'name': 'Python Programming', 'code': 'CSE101', 'course_id': courses[0].id, 'year': 1, 'semester': 1},
            {'name': 'Data Structures', 'code': 'CSE102', 'course_id': courses[0].id, 'year': 1, 'semester': 2},
            {'name': 'Database Management', 'code': 'CSE201', 'course_id': courses[0].id, 'year': 2, 'semester': 3},
            {'name': 'Web Development', 'code': 'CSE202', 'course_id': courses[0].id, 'year': 2, 'semester': 4},
            
            # IT subjects
            {'name': 'Java Programming', 'code': 'IT101', 'course_id': courses[1].id, 'year': 1, 'semester': 1},
            {'name': 'Computer Networks', 'code': 'IT102', 'course_id': courses[1].id, 'year': 1, 'semester': 2},
            
            # ECE subjects
            {'name': 'Digital Electronics', 'code': 'ECE101', 'course_id': courses[2].id, 'year': 1, 'semester': 1},
            {'name': 'Microprocessors', 'code': 'ECE102', 'course_id': courses[2].id, 'year': 1, 'semester': 2}
        ]
        
        subjects = []
        for subject_data in subjects_data:
            subject = Subject(**subject_data)
            db.session.add(subject)
            subjects.append(subject)
        
        db.session.commit()
        print(f"✓ Created {len(subjects)} subjects")
        
        # Create lecturers
        lecturers_data = [
            {'lecturer_id': 'LEC001', 'name': 'Dr. John Smith', 'username': 'bbhc_john_lec001', 'course_id': courses[0].id},
            {'lecturer_id': 'LEC002', 'name': 'Prof. Sarah Johnson', 'username': 'bbhc_sarah_lec002', 'course_id': courses[1].id},
            {'lecturer_id': 'LEC003', 'name': 'Dr. Michael Brown', 'username': 'bbhc_michael_lec003', 'course_id': courses[2].id},
            {'lecturer_id': 'LEC004', 'name': 'Prof. Emily Davis', 'username': 'bbhc_emily_lec004', 'course_id': courses[0].id}
        ]
        
        lecturers = []
        for lecturer_data in lecturers_data:
            lecturer = Lecturer(**lecturer_data)
            lecturer.set_password('password123')  # Default password for all lecturers
            db.session.add(lecturer)
            lecturers.append(lecturer)
        
        db.session.commit()
        print(f"✓ Created {len(lecturers)} lecturers (password: password123)")
        
        # Create students
        students_data = [
            # CSE students
            {'roll_number': 'CSE001', 'name': 'Alice Johnson', 'course_id': courses[0].id, 'academic_year': 1, 'email': 'alice@student.edu'},
            {'roll_number': 'CSE002', 'name': 'Bob Smith', 'course_id': courses[0].id, 'academic_year': 1, 'email': 'bob@student.edu'},
            {'roll_number': 'CSE003', 'name': 'Charlie Brown', 'course_id': courses[0].id, 'academic_year': 2, 'email': 'charlie@student.edu'},
            {'roll_number': 'CSE004', 'name': 'Diana Wilson', 'course_id': courses[0].id, 'academic_year': 2, 'email': 'diana@student.edu'},
            
            # IT students
            {'roll_number': 'IT001', 'name': 'Eve Davis', 'course_id': courses[1].id, 'academic_year': 1, 'email': 'eve@student.edu'},
            {'roll_number': 'IT002', 'name': 'Frank Miller', 'course_id': courses[1].id, 'academic_year': 1, 'email': 'frank@student.edu'},
            
            # ECE students
            {'roll_number': 'ECE001', 'name': 'Grace Lee', 'course_id': courses[2].id, 'academic_year': 1, 'email': 'grace@student.edu'},
            {'roll_number': 'ECE002', 'name': 'Henry Taylor', 'course_id': courses[2].id, 'academic_year': 1, 'email': 'henry@student.edu'}
        ]
        
        students = []
        for student_data in students_data:
            student = Student(**student_data)
            db.session.add(student)
            students.append(student)
        
        db.session.commit()
        print(f"✓ Created {len(students)} students")
        
        # Create subject assignments (assign lecturers to subjects)
        assignments_data = [
            {'lecturer_id': lecturers[0].id, 'subject_id': subjects[0].id, 'academic_year': 2024},  # John -> Python
            {'lecturer_id': lecturers[0].id, 'subject_id': subjects[1].id, 'academic_year': 2024},  # John -> Data Structures
            {'lecturer_id': lecturers[3].id, 'subject_id': subjects[2].id, 'academic_year': 2024},  # Emily -> Database
            {'lecturer_id': lecturers[3].id, 'subject_id': subjects[3].id, 'academic_year': 2024},  # Emily -> Web Dev
            {'lecturer_id': lecturers[1].id, 'subject_id': subjects[4].id, 'academic_year': 2024},  # Sarah -> Java
            {'lecturer_id': lecturers[1].id, 'subject_id': subjects[5].id, 'academic_year': 2024},  # Sarah -> Networks
            {'lecturer_id': lecturers[2].id, 'subject_id': subjects[6].id, 'academic_year': 2024},  # Michael -> Digital Electronics
            {'lecturer_id': lecturers[2].id, 'subject_id': subjects[7].id, 'academic_year': 2024}   # Michael -> Microprocessors
        ]
        
        for assignment_data in assignments_data:
            assignment = SubjectAssignment(**assignment_data)
            db.session.add(assignment)
        
        db.session.commit()
        print(f"✓ Created {len(assignments_data)} subject assignments")
        
        # Create student enrollments
        enrollments_data = [
            # CSE students in CSE subjects
            {'student_id': students[0].id, 'subject_id': subjects[0].id, 'academic_year': 2024},  # Alice -> Python
            {'student_id': students[1].id, 'subject_id': subjects[0].id, 'academic_year': 2024},  # Bob -> Python
            {'student_id': students[2].id, 'subject_id': subjects[2].id, 'academic_year': 2024},  # Charlie -> Database
            {'student_id': students[3].id, 'subject_id': subjects[2].id, 'academic_year': 2024},  # Diana -> Database
            
            # IT students in IT subjects
            {'student_id': students[4].id, 'subject_id': subjects[4].id, 'academic_year': 2024},  # Eve -> Java
            {'student_id': students[5].id, 'subject_id': subjects[4].id, 'academic_year': 2024},  # Frank -> Java
            
            # ECE students in ECE subjects
            {'student_id': students[6].id, 'subject_id': subjects[6].id, 'academic_year': 2024},  # Grace -> Digital Electronics
            {'student_id': students[7].id, 'subject_id': subjects[6].id, 'academic_year': 2024}   # Henry -> Digital Electronics
        ]
        
        for enrollment_data in enrollments_data:
            enrollment = StudentEnrollment(**enrollment_data)
            db.session.add(enrollment)
        
        db.session.commit()
        print(f"✓ Created {len(enrollments_data)} student enrollments")
        
        # Create academic year
        academic_year = AcademicYear(
            year=2024,
            start_date=date(2024, 6, 1),
            end_date=date(2025, 5, 31),
            is_current=True
        )
        db.session.add(academic_year)
        db.session.commit()
        print("✓ Created academic year 2024")
        
        print("\n🎉 Sample data creation completed!")
        print("\nLogin credentials:")
        print("Management: admin / admin123")
        print("Lecturers: [username] / password123")
        print("  - bbhc_john_lec001 / password123")
        print("  - bbhc_sarah_lec002 / password123")
        print("  - bbhc_michael_lec003 / password123")
        print("  - bbhc_emily_lec004 / password123")

if __name__ == '__main__':
    create_sample_data()