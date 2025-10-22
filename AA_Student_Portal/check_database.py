import sqlite3
import os

print("Checking AA_Student_Portal database...")

# Check if database file exists
db_path = 'moulya_college.db'
if os.path.exists(db_path):
    print(f"Database file exists: {db_path}")
    file_size = os.path.getsize(db_path)
    print(f"File size: {file_size} bytes")
    
    if file_size > 0:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print(f"Tables in database: {len(tables)}")
            for table in tables:
                print(f"  - {table[0]}")
            
            # Check if student table exists
            if ('student',) in tables:
                cursor.execute("SELECT COUNT(*) FROM student;")
                count = cursor.fetchone()[0]
                print(f"Number of students: {count}")
                
                if count > 0:
                    cursor.execute("SELECT roll_number, name FROM student LIMIT 3;")
                    students = cursor.fetchall()
                    print("Sample students:")
                    for student in students:
                        print(f"  - {student[0]}: {student[1]}")
            else:
                print("Student table does not exist!")
            
            conn.close()
        except Exception as e:
            print(f"Error reading database: {e}")
    else:
        print("Database file is empty!")
else:
    print(f"Database file does not exist: {db_path}")

# Check main database
main_db_path = '../moulya_college.db'
if os.path.exists(main_db_path):
    print(f"\nMain database file exists: {main_db_path}")
    file_size = os.path.getsize(main_db_path)
    print(f"File size: {file_size} bytes")
    
    if file_size > 0:
        try:
            conn = sqlite3.connect(main_db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print(f"Tables in main database: {len(tables)}")
            for table in tables:
                print(f"  - {table[0]}")
            
            conn.close()
        except Exception as e:
            print(f"Error reading main database: {e}")
    else:
        print("Main database file is empty!")
else:
    print(f"Main database file does not exist: {main_db_path}")
