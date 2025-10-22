#!/usr/bin/env python3
"""
Test the complete student portal flow:
1. MongoDB login (roll_number + date_of_birth)
2. SQL database data fetching (subjects, attendance, marks)
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

def test_mongodb_login():
    """Test MongoDB authentication"""
    print("=== Testing MongoDB Login ===")
    try:
        from services.auth_service import auth_service
        
        # Test with a sample roll number and date of birth
        # You can change these to match your MongoDB data
        test_roll = "BCA25001"  # From our earlier test
        test_dob = "123456"     # Default DOB format
        
        print(f"Testing login with roll_number: {test_roll}, date_of_birth: {test_dob}")
        
        student = auth_service.authenticate_student(test_roll, test_dob)
        
        if student:
            print("[OK] MongoDB Login: SUCCESS")
            print(f"   Student data: {student}")
            return test_roll
        else:
            print("[ERROR] MongoDB Login: FAILED")
            print("   Try with different roll_number/date_of_birth")
            return None
            
    except Exception as e:
        print(f"[ERROR] MongoDB Login Error: {e}")
        return None

def test_sql_data_fetch(roll_number):
    """Test SQL database data fetching"""
    print(f"\n=== Testing SQL Data Fetch for {roll_number} ===")
    try:
        from services.student_service import student_service
        
        # Initialize with instance database
        instance_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'moulya_college.db')
        print(f"Using database: {instance_db}")
        
        if not os.path.exists(instance_db):
            print(f"[ERROR] Database file not found: {instance_db}")
            return False
            
        student_service.init_app(db_path=instance_db)
        
        # Test student data fetch
        print(f"Fetching data for roll_number: {roll_number}")
        stats = student_service.get_student_dashboard_stats(roll_number)
        
        if stats and stats.get('student'):
            print("[OK] SQL Data Fetch: SUCCESS")
            student = stats['student']
            print(f"   Student Name: {student.get('name', 'N/A')}")
            print(f"   Course: {student.get('course_name', 'N/A')}")
            print(f"   Academic Year: {student.get('academic_year', 'N/A')}")
            print(f"   Overall Attendance: {student.get('overall_attendance', 0)}%")
            
            # Test enrolled subjects
            subjects = stats.get('enrolled_subjects', [])
            print(f"   Enrolled Subjects: {len(subjects)}")
            
            for i, subject in enumerate(subjects[:5]):  # Show first 5 subjects
                print(f"     {i+1}. {subject['name']} ({subject['code']})")
                print(f"        Attendance: {subject['attendance_percentage']}%")
                
            return True
        else:
            print("[ERROR] SQL Data Fetch: FAILED - No student data found")
            return False
            
    except Exception as e:
        print(f"[ERROR] SQL Data Fetch Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complete_flow():
    """Test the complete flow"""
    print("Testing Complete Student Portal Flow")
    print("=" * 50)
    
    # Step 1: Test MongoDB login
    roll_number = test_mongodb_login()
    
    if not roll_number:
        print("\n[ERROR] Cannot proceed without successful MongoDB login")
        return False
    
    # Step 2: Test SQL data fetch with same roll_number
    sql_success = test_sql_data_fetch(roll_number)
    
    if sql_success:
        print("\n[SUCCESS] COMPLETE FLOW: SUCCESS!")
        print("[OK] MongoDB handles authentication")
        print("[OK] SQL database provides student data")
        print("[OK] Same roll_number used for both")
        return True
    else:
        print("\n[ERROR] COMPLETE FLOW: FAILED")
        return False

if __name__ == "__main__":
    success = test_complete_flow()
    
    if success:
        print("\n" + "=" * 50)
        print("Student Portal is ready!")
        print("Login with roll_number and date_of_birth from MongoDB")
        print("Dashboard will show data from SQL database")
        print("SQL database is read-only (no writes possible)")
        print("Only MongoDB can be written to (change password)")
    else:
        print("\n" + "=" * 50)
        print("Student Portal needs configuration")
        print("1. Check MongoDB connection and credentials")
        print("2. Verify instance/moulya_college.db exists")
        print("3. Ensure roll_number exists in both databases")
