#!/usr/bin/env python3
"""
Simple test to verify attendance data in SQLite database
"""

import sqlite3
import os
from datetime import datetime

def test_attendance_database():
    """Test attendance data directly from SQLite database"""
    print("=== Testing Attendance Database ===")
    
    # Database path
    db_path = os.path.join('..', 'instance', 'moulya_college.db')
    
    if not os.path.exists(db_path):
        print(f"✗ Database not found at: {db_path}")
        return False
    
    print(f"✓ Database found at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test 1: Check students
        print("\n1. Checking students...")
        cursor.execute("SELECT COUNT(*) FROM student")
        student_count = cursor.fetchone()[0]
        print(f"✓ Found {student_count} students")
        
        # Get a sample student
        cursor.execute("SELECT id, roll_number, name FROM student LIMIT 1")
        student = cursor.fetchone()
        if student:
            student_id, roll_number, name = student
            print(f"✓ Sample student: {name} ({roll_number}) - ID: {student_id}")
        else:
            print("✗ No students found")
            return False
        
        # Test 2: Check attendance records
        print("\n2. Checking attendance records...")
        cursor.execute("SELECT COUNT(*) FROM attendance_record")
        attendance_count = cursor.fetchone()[0]
        print(f"✓ Found {attendance_count} attendance records")
        
        if attendance_count > 0:
            # Get sample attendance records
            cursor.execute("""
                SELECT ar.id, ar.student_id, ar.subject_id, ar.date, ar.status, 
                       s.name as student_name, s.roll_number,
                       sub.name as subject_name, sub.code as subject_code
                FROM attendance_record ar
                LEFT JOIN student s ON ar.student_id = s.id
                LEFT JOIN subject sub ON ar.subject_id = sub.id
                ORDER BY ar.date DESC
                LIMIT 5
            """)
            
            records = cursor.fetchall()
            print("✓ Sample attendance records:")
            for record in records:
                record_id, stud_id, subj_id, date, status, stud_name, roll_num, subj_name, subj_code = record
                print(f"  - {date}: {stud_name} ({roll_num}) - {subj_name} ({subj_code}) - {status}")
        
        # Test 3: Check monthly attendance for sample student
        print(f"\n3. Checking monthly attendance for {roll_number}...")
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', date) as month,
                COUNT(*) as total_classes,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent
            FROM attendance_record 
            WHERE student_id = ?
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month DESC
        """, (student_id,))
        
        monthly_data = cursor.fetchall()
        if monthly_data:
            print(f"✓ Found attendance data for {len(monthly_data)} months:")
            for month, total, present, absent in monthly_data:
                percentage = round((present / total * 100), 2) if total > 0 else 0
                print(f"  - {month}: {present}/{total} ({percentage}%)")
        else:
            print("✗ No monthly attendance data found")
        
        # Test 4: Check subjects
        print("\n4. Checking subjects...")
        cursor.execute("SELECT COUNT(*) FROM subject")
        subject_count = cursor.fetchone()[0]
        print(f"✓ Found {subject_count} subjects")
        
        # Test 5: Check student enrollments
        print("\n5. Checking student enrollments...")
        cursor.execute("SELECT COUNT(*) FROM student_enrollment WHERE is_active = 1")
        enrollment_count = cursor.fetchone()[0]
        print(f"✓ Found {enrollment_count} active enrollments")
        
        conn.close()
        print("\n=== Database Test Complete ===")
        return True
        
    except Exception as e:
        print(f"✗ Error accessing database: {e}")
        return False

if __name__ == "__main__":
    success = test_attendance_database()
    if success:
        print("\n🎉 Database test completed successfully!")
    else:
        print("\n❌ Database test failed. Check the output above for details.")
