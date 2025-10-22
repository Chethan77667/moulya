#!/usr/bin/env python3
"""
Test student service directly
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def test_student_service():
    """Test student service functionality"""
    print("=== Testing Student Service ===")
    
    try:
        # Import and initialize student service
        from AA_Student_Portal.services.student_service import StudentService
        
        # Create a simple Flask app for testing
        from flask import Flask
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join("..", "instance", "moulya_college.db")}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize student service
        student_service = StudentService()
        student_service.init_app(app)
        
        print("✓ Student service initialized")
        
        # Test with a roll number that has attendance data
        test_roll_number = "BCA25001"
        
        print(f"\n--- Testing with roll number: {test_roll_number} ---")
        
        # Test 1: Get student data
        print("\n1. Testing student data retrieval...")
        student_data = student_service.get_student_by_roll_number(test_roll_number)
        if student_data:
            print(f"✓ Student found: {student_data.get('name', 'Unknown')} ({student_data.get('roll_number', 'Unknown')})")
        else:
            print("✗ Student not found")
            return False
        
        # Test 2: Get enrolled subjects
        print("\n2. Testing enrolled subjects...")
        subjects = student_service.get_student_enrolled_subjects(test_roll_number)
        print(f"✓ Found {len(subjects)} enrolled subjects")
        for subject in subjects[:3]:
            print(f"  - {subject.get('name', 'Unknown')} ({subject.get('code', 'Unknown')})")
        
        # Test 3: Get attendance records
        print("\n3. Testing attendance records...")
        attendance_records = student_service.get_student_attendance_records(test_roll_number)
        print(f"✓ Found {len(attendance_records)} attendance records")
        
        if attendance_records:
            print("  Recent records:")
            for record in attendance_records[:5]:
                print(f"    - {record.get('date', 'N/A')}: {record.get('status', 'N/A')} ({record.get('subject_name', 'Unknown')})")
        
        # Test 4: Get attendance summary
        print("\n4. Testing attendance summary...")
        summary = student_service.get_student_attendance_summary(test_roll_number)
        print(f"✓ Attendance Summary:")
        print(f"  - Total Classes: {summary.get('total_classes', 0)}")
        print(f"  - Present: {summary.get('present', 0)}")
        print(f"  - Absent: {summary.get('absent', 0)}")
        print(f"  - Percentage: {summary.get('percentage', 0)}%")
        
        # Test 5: Get monthly attendance
        print("\n5. Testing monthly attendance...")
        monthly_data = student_service.get_student_monthly_attendance(test_roll_number)
        monthly_summary = monthly_data.get('monthly_summary', [])
        print(f"✓ Found {len(monthly_summary)} months with attendance data")
        
        if monthly_summary:
            print("  Monthly breakdown:")
            for month in monthly_summary[:6]:
                print(f"    - {month.get('label', 'Unknown')}: {month.get('present', 0)}/{month.get('total', 0)} ({month.get('percentage', 0)}%)")
        
        print("\n=== Student Service Test Complete ===")
        return True
        
    except Exception as e:
        print(f"✗ Error testing student service: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_student_service()
    if success:
        print("\n🎉 Student service test completed successfully!")
    else:
        print("\n❌ Student service test failed. Check the output above for details.")
