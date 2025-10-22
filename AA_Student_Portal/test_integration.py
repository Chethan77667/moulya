#!/usr/bin/env python3
"""
Test script for Student Portal integration with main Moulya database
"""

import sys
import os

# Add the parent directory to the path to import from main Moulya system
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def test_database_connection():
    """Test if we can connect to the main Moulya database"""
    try:
        from database import db
        from models.student import Student
        from models.academic import Subject, Course
        print("[OK] Successfully imported main Moulya models")
        
        # Try to create a test app context
        from flask import Flask
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///E:/Moulya_2025-27/moulya_college.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        
        with app.app_context():
            # Test database connection
            student_count = Student.query.count()
            subject_count = Subject.query.count()
            course_count = Course.query.count()
            
            print(f"[OK] Database connection successful")
            print(f"  - Students: {student_count}")
            print(f"  - Subjects: {subject_count}")
            print(f"  - Courses: {course_count}")
            
            # Test student service
            from services.student_service import student_service
            student_service.init_app(app)
            
            # Test with a sample roll number (if any students exist)
            if student_count > 0:
                sample_student = Student.query.first()
                print(f"[OK] Testing with sample student: {sample_student.roll_number}")
                
                # Test getting student data
                student_data = student_service.get_student_by_roll_number(sample_student.roll_number)
                if student_data:
                    print(f"[OK] Successfully fetched student data: {student_data['name']}")
                else:
                    print("[ERROR] Failed to fetch student data")
                
                # Test getting enrolled subjects
                subjects = student_service.get_student_enrolled_subjects(sample_student.roll_number)
                print(f"[OK] Found {len(subjects)} enrolled subjects")
                
                for subject in subjects[:3]:  # Show first 3 subjects
                    print(f"  - {subject['name']} ({subject['code']})")
            else:
                print("! No students found in database")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False

def test_student_portal():
    """Test student portal components"""
    try:
        from services.auth_service import auth_service
        from services.student_service import student_service
        print("[OK] Successfully imported student portal services")
        
        # Test MongoDB connection
        if auth_service.collection is not None:
            print("[OK] MongoDB connection available")
        else:
            print("[WARNING] MongoDB connection not available")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Student portal test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Student Portal Integration with Main Moulya Database")
    print("=" * 60)
    
    print("\n1. Testing main database connection...")
    db_success = test_database_connection()
    
    print("\n2. Testing student portal services...")
    portal_success = test_student_portal()
    
    print("\n" + "=" * 60)
    if db_success and portal_success:
        print("[OK] All tests passed! Integration should work correctly.")
    else:
        print("[ERROR] Some tests failed. Check the errors above.")
    
    print("\nTo run the student portal:")
    print("  cd AA_Student_Portal")
    print("  python app.py")
