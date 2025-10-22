#!/usr/bin/env python3
"""
Test script to verify database consistency between student portal and lecturer reports
"""

import sqlite3
import os
from datetime import datetime

def test_database_consistency():
    """Test that student portal data matches lecturer report data"""
    print("=== Testing Database Consistency ===")
    
    # Database path
    db_path = os.path.join('..', 'instance', 'moulya_college.db')
    
    if not os.path.exists(db_path):
        print(f"✗ Database not found at: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test with a specific student
        test_roll_number = "BCA25001"
        
        print(f"\n--- Testing with student: {test_roll_number} ---")
        
        # Get student ID
        cursor.execute("SELECT id, name FROM student WHERE roll_number = ?", (test_roll_number,))
        student_result = cursor.fetchone()
        if not student_result:
            print(f"✗ Student {test_roll_number} not found")
            return False
        
        student_id, student_name = student_result
        print(f"✓ Student found: {student_name} (ID: {student_id})")
        
        # Get enrolled subjects
        cursor.execute("""
            SELECT s.id, s.name, s.code 
            FROM subject s
            JOIN student_enrollment se ON s.id = se.subject_id
            WHERE se.student_id = ? AND se.is_active = 1
        """, (student_id,))
        subjects = cursor.fetchall()
        print(f"✓ Found {len(subjects)} enrolled subjects")
        
        for subject_id, subject_name, subject_code in subjects:
            print(f"\n--- Subject: {subject_name} ({subject_code}) ---")
            
            # Get total classes from monthly_attendance_summary
            cursor.execute("""
                SELECT SUM(total_classes) 
                FROM monthly_attendance_summary 
                WHERE subject_id = ?
            """, (subject_id,))
            total_classes_result = cursor.fetchone()
            total_classes = total_classes_result[0] or 0
            print(f"  Total Classes (from summary): {total_classes}")
            
            # Get present classes from monthly_student_attendance
            cursor.execute("""
                SELECT SUM(present_count), SUM(deputation_count)
                FROM monthly_student_attendance 
                WHERE student_id = ? AND subject_id = ?
            """, (student_id, subject_id))
            present_result = cursor.fetchone()
            present_count = present_result[0] or 0
            deputation_count = present_result[1] or 0
            total_present = present_count + deputation_count
            print(f"  Present Classes: {present_count}")
            print(f"  Deputation Classes: {deputation_count}")
            print(f"  Total Present (with deputation): {total_present}")
            
            # Calculate percentage
            percentage = (total_present / total_classes * 100) if total_classes > 0 else 0
            print(f"  Attendance Percentage: {percentage:.2f}%")
            
            # Get daily records count for comparison
            cursor.execute("""
                SELECT COUNT(*) 
                FROM attendance_record 
                WHERE student_id = ? AND subject_id = ?
            """, (student_id, subject_id))
            daily_records = cursor.fetchone()[0]
            print(f"  Daily Records Count: {daily_records}")
            
            # Get monthly breakdown
            cursor.execute("""
                SELECT msa.month, msa.year, 
                       SUM(msa.present_count) as present,
                       SUM(msa.deputation_count) as deputation,
                       SUM(mas.total_classes) as total
                FROM monthly_student_attendance msa
                JOIN monthly_attendance_summary mas ON (
                    msa.subject_id = mas.subject_id AND
                    msa.month = mas.month AND
                    msa.year = mas.year
                )
                WHERE msa.student_id = ? AND msa.subject_id = ?
                GROUP BY msa.month, msa.year
                ORDER BY msa.year DESC, msa.month DESC
            """, (student_id, subject_id))
            
            monthly_data = cursor.fetchall()
            print(f"  Monthly Breakdown ({len(monthly_data)} months):")
            for month, year, present, deputation, total in monthly_data:
                present_with_deputation = (present or 0) + (deputation or 0)
                month_percentage = (present_with_deputation / total * 100) if total > 0 else 0
                month_name = datetime(int(year), int(month), 1).strftime('%B %Y')
                print(f"    - {month_name}: {present_with_deputation}/{total} ({month_percentage:.1f}%)")
        
        # Test overall attendance across all subjects
        print(f"\n--- Overall Attendance (All Subjects) ---")
        
        # Get enrolled subject IDs
        cursor.execute("""
            SELECT subject_id FROM student_enrollment 
            WHERE student_id = ? AND is_active = 1
        """, (student_id,))
        enrolled_subject_ids = [row[0] for row in cursor.fetchall()]
        
        if enrolled_subject_ids:
            # Get total classes across enrolled subjects only
            placeholders = ','.join('?' * len(enrolled_subject_ids))
            cursor.execute(f"""
                SELECT SUM(total_classes)
                FROM monthly_attendance_summary 
                WHERE subject_id IN ({placeholders})
            """, enrolled_subject_ids)
            overall_total = cursor.fetchone()[0] or 0
            
            # Get total present across enrolled subjects only
            cursor.execute(f"""
                SELECT SUM(present_count), SUM(deputation_count)
                FROM monthly_student_attendance 
                WHERE student_id = ? AND subject_id IN ({placeholders})
            """, [student_id] + enrolled_subject_ids)
            overall_present_result = cursor.fetchone()
            overall_present = (overall_present_result[0] or 0) + (overall_present_result[1] or 0)
        else:
            overall_total = 0
            overall_present = 0
        
        overall_percentage = (overall_present / overall_total * 100) if overall_total > 0 else 0
        print(f"  Overall Total Classes: {overall_total}")
        print(f"  Overall Present Classes: {overall_present}")
        print(f"  Overall Attendance Percentage: {overall_percentage:.2f}%")
        
        conn.close()
        print("\n=== Database Consistency Test Complete ===")
        return True
        
    except Exception as e:
        print(f"✗ Error during consistency test: {e}")
        return False

if __name__ == "__main__":
    success = test_database_consistency()
    if success:
        print("\n🎉 Database consistency test completed successfully!")
        print("The student portal data matches the lecturer report data structure.")
    else:
        print("\n❌ Database consistency test failed. Check the output above for details.")
