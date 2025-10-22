#!/usr/bin/env python3
"""
Test script to verify student data exists and test the portal
"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, parent_dir)

try:
    from app import create_app
    from database import db
    from models.student import Student, StudentEnrollment
    from models.academic import Subject, Course
    
    print("Testing main database connection...")
    app = create_app()
    
    with app.app_context():
        # Check students
        student_count = Student.query.count()
        print(f"Total students in database: {student_count}")
        
        if student_count > 0:
            # Get first student
            student = Student.query.first()
            print(f"Sample student: {student.roll_number} - {student.name}")
            
            # Check enrollments
            enrollments = StudentEnrollment.query.filter_by(student_id=student.id, is_active=True).all()
            print(f"Enrolled subjects: {len(enrollments)}")
            
            for enrollment in enrollments:
                subject = enrollment.subject
                print(f"  - {subject.name} ({subject.code})")
            
            # Test student service
            print("\nTesting student service...")
            sys.path.append(os.path.dirname(__file__))
            from services.student_service import student_service
            student_service.init_app(app)
            
            stats = student_service.get_student_dashboard_stats(student.roll_number)
            print(f"Student name from service: {stats.get('student', {}).get('name', 'No data')}")
            print(f"Enrolled subjects from service: {len(stats.get('enrolled_subjects', []))}")
            
        else:
            print("No students found in database!")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
