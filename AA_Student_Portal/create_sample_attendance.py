#!/usr/bin/env python3
"""
Create sample attendance data for testing the attendance system
"""

import sqlite3
import os
import random
from datetime import datetime, timedelta

def create_sample_attendance():
    """Create sample attendance data"""
    print("=== Creating Sample Attendance Data ===")
    
    # Database path
    db_path = os.path.join('..', 'instance', 'moulya_college.db')
    
    if not os.path.exists(db_path):
        print(f"✗ Database not found at: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get some students and subjects
        print("1. Getting students and subjects...")
        cursor.execute("""
            SELECT s.id, s.roll_number, s.name, se.subject_id, sub.name as subject_name, sub.code as subject_code
            FROM student s
            JOIN student_enrollment se ON s.id = se.student_id
            JOIN subject sub ON se.subject_id = sub.id
            WHERE se.is_active = 1
            LIMIT 20
        """)
        
        enrollments = cursor.fetchall()
        print(f"✓ Found {len(enrollments)} student-subject enrollments")
        
        if not enrollments:
            print("✗ No enrollments found")
            return False
        
        # Get lecturers for subjects
        print("2. Getting lecturers...")
        cursor.execute("""
            SELECT DISTINCT sa.lecturer_id, l.name as lecturer_name
            FROM subject_assignment sa
            JOIN lecturer l ON sa.lecturer_id = l.id
            WHERE sa.is_active = 1
            LIMIT 10
        """)
        
        lecturers = cursor.fetchall()
        print(f"✓ Found {len(lecturers)} lecturers")
        
        if not lecturers:
            print("✗ No lecturers found")
            return False
        
        # Create attendance records for the last 3 months
        print("3. Creating attendance records...")
        
        # Generate dates for the last 3 months
        today = datetime.now()
        start_date = today - timedelta(days=90)  # 3 months ago
        
        records_created = 0
        
        for enrollment in enrollments:
            student_id, roll_number, student_name, subject_id, subject_name, subject_code = enrollment
            
            # Get a random lecturer for this subject
            lecturer_id, lecturer_name = random.choice(lecturers)
            
            # Generate 15-25 attendance records per student-subject combination
            num_records = random.randint(15, 25)
            
            for i in range(num_records):
                # Random date within the last 3 months
                days_ago = random.randint(0, 90)
                attendance_date = start_date + timedelta(days=days_ago)
                
                # Random status (80% present, 20% absent)
                status = 'present' if random.random() < 0.8 else 'absent'
                
                # Insert attendance record
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO attendance_record 
                        (student_id, subject_id, lecturer_id, date, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        student_id,
                        subject_id,
                        lecturer_id,
                        attendance_date.date(),
                        status,
                        datetime.now(),
                        datetime.now()
                    ))
                    records_created += 1
                except Exception as e:
                    print(f"  Warning: Could not insert record for {roll_number}: {e}")
                    continue
        
        # Commit changes
        conn.commit()
        print(f"✓ Created {records_created} attendance records")
        
        # Verify the data
        print("4. Verifying created data...")
        cursor.execute("SELECT COUNT(*) FROM attendance_record")
        total_records = cursor.fetchone()[0]
        print(f"✓ Total attendance records in database: {total_records}")
        
        # Show sample monthly data
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', date) as month,
                COUNT(*) as total_classes,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent
            FROM attendance_record 
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month DESC
        """)
        
        monthly_data = cursor.fetchall()
        print("✓ Monthly attendance summary:")
        for month, total, present, absent in monthly_data:
            percentage = round((present / total * 100), 2) if total > 0 else 0
            print(f"  - {month}: {present}/{total} ({percentage}%)")
        
        conn.close()
        print("\n=== Sample Data Creation Complete ===")
        return True
        
    except Exception as e:
        print(f"✗ Error creating sample data: {e}")
        return False

if __name__ == "__main__":
    success = create_sample_attendance()
    if success:
        print("\n🎉 Sample attendance data created successfully!")
        print("You can now test the attendance system in the student portal.")
    else:
        print("\n❌ Failed to create sample data. Check the output above for details.")
