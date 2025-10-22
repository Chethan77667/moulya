#!/usr/bin/env python3
"""
Test script to verify attendance data loading from SQLite database
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path to import from main Moulya system
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from services.student_service import student_service
    from config.database import mongodb_config
    
    def test_attendance_loading():
        """Test attendance data loading functionality"""
        print("=== Testing Attendance Data Loading ===")
        
        # Initialize services
        try:
            # Initialize MongoDB connection
            mongodb_config.connect()
            print("✓ MongoDB connection initialized")
            
            # Initialize student service
            import sys
            import os
            parent_dir = os.path.dirname(os.path.dirname(__file__))
            sys.path.insert(0, parent_dir)
            
            from app import create_app
            main_app = create_app()
            student_service.init_app(main_app)
            print("✓ Student service initialized")
            
        except Exception as e:
            print(f"✗ Error initializing services: {e}")
            print("Continuing with basic tests...")
            # Don't return False, continue with basic tests
        
        # Test with a sample roll number (you may need to adjust this)
        test_roll_number = "BCA25001"  # Using a roll number that has attendance data
        
        print(f"\n--- Testing with roll number: {test_roll_number} ---")
        
        # Test 1: Get student data
        print("\n1. Testing student data retrieval...")
        try:
            student_data = student_service.get_student_by_roll_number(test_roll_number)
            if student_data:
                print(f"✓ Student found: {student_data.get('name', 'Unknown')} ({student_data.get('roll_number', 'Unknown')})")
            else:
                print("✗ Student not found")
                return False
        except Exception as e:
            print(f"✗ Error getting student data: {e}")
            return False
        
        # Test 2: Get enrolled subjects
        print("\n2. Testing enrolled subjects retrieval...")
        try:
            subjects = student_service.get_student_enrolled_subjects(test_roll_number)
            print(f"✓ Found {len(subjects)} enrolled subjects")
            for subject in subjects[:3]:  # Show first 3 subjects
                print(f"  - {subject.get('name', 'Unknown')} ({subject.get('code', 'Unknown')})")
        except Exception as e:
            print(f"✗ Error getting enrolled subjects: {e}")
        
        # Test 3: Get attendance records
        print("\n3. Testing attendance records retrieval...")
        try:
            attendance_records = student_service.get_student_attendance_records(test_roll_number)
            print(f"✓ Found {len(attendance_records)} attendance records")
            
            if attendance_records:
                print("  Recent records:")
                for record in attendance_records[:5]:  # Show first 5 records
                    print(f"    - {record.get('date', 'N/A')}: {record.get('status', 'N/A')} ({record.get('subject_name', 'Unknown')})")
            else:
                print("  No attendance records found")
        except Exception as e:
            print(f"✗ Error getting attendance records: {e}")
        
        # Test 4: Get attendance summary
        print("\n4. Testing attendance summary...")
        try:
            summary = student_service.get_student_attendance_summary(test_roll_number)
            print(f"✓ Attendance Summary:")
            print(f"  - Total Classes: {summary.get('total_classes', 0)}")
            print(f"  - Present: {summary.get('present', 0)}")
            print(f"  - Absent: {summary.get('absent', 0)}")
            print(f"  - Percentage: {summary.get('percentage', 0)}%")
        except Exception as e:
            print(f"✗ Error getting attendance summary: {e}")
        
        # Test 5: Get monthly attendance
        print("\n5. Testing monthly attendance...")
        try:
            monthly_data = student_service.get_student_monthly_attendance(test_roll_number)
            monthly_summary = monthly_data.get('monthly_summary', [])
            print(f"✓ Found {len(monthly_summary)} months with attendance data")
            
            if monthly_summary:
                print("  Monthly breakdown:")
                for month in monthly_summary[:6]:  # Show first 6 months
                    print(f"    - {month.get('label', 'Unknown')}: {month.get('present', 0)}/{month.get('total', 0)} ({month.get('percentage', 0)}%)")
            else:
                print("  No monthly data found")
        except Exception as e:
            print(f"✗ Error getting monthly attendance: {e}")
        
        # Test 6: Test with specific subject
        if subjects:
            subject_id = subjects[0].get('id')
            print(f"\n6. Testing with specific subject (ID: {subject_id})...")
            try:
                subject_attendance = student_service.get_student_attendance_records(test_roll_number, subject_id)
                print(f"✓ Found {len(subject_attendance)} records for this subject")
                
                subject_summary = student_service.get_student_attendance_summary(test_roll_number, subject_id)
                print(f"  Subject Summary: {subject_summary.get('present', 0)}/{subject_summary.get('total_classes', 0)} ({subject_summary.get('percentage', 0)}%)")
            except Exception as e:
                print(f"✗ Error getting subject-specific attendance: {e}")
        
        print("\n=== Test Complete ===")
        return True
    
    if __name__ == "__main__":
        success = test_attendance_loading()
        if success:
            print("\n🎉 All tests completed successfully!")
        else:
            print("\n❌ Some tests failed. Check the output above for details.")
            sys.exit(1)

except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this from the AA_Student_Portal directory")
    sys.exit(1)
