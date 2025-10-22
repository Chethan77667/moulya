#!/usr/bin/env python3
"""
Simple script to convert student names to uppercase
==================================================

This is a simplified version of the name converter script.
Run this to convert all student names in the MongoDB collection to uppercase.

Usage:
    python scripts/convert_names_simple.py
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from services.mongodb_service import MongoDBService
except ImportError as e:
    print(f"Error importing MongoDB service: {e}")
    sys.exit(1)

def main():
    print("Student Name Uppercase Converter (Simple)")
    print("=" * 50)
    
    # Initialize MongoDB service
    mongodb_service = MongoDBService()
    collection = mongodb_service.get_collection('login_credentials')
    
    # Get total count
    total_students = collection.count_documents({})
    print(f"Total students found: {total_students}")
    
    if total_students == 0:
        print("No students found. Exiting.")
        return
    
    # Preview first 5 students
    print("\nPreview of changes:")
    print("-" * 40)
    
    students = list(collection.find({}).limit(5))
    for i, student in enumerate(students, 1):
        current_name = student.get('name', 'N/A')
        new_name = current_name.upper() if current_name != 'N/A' else 'N/A'
        print(f"{i}. {student.get('roll_number', 'N/A')}: '{current_name}' → '{new_name}'")
    
    # Ask for confirmation
    print(f"\nWARNING: This will update {total_students} student records.")
    confirmation = input("Do you want to proceed? (yes/no): ").lower().strip()
    
    if confirmation != 'yes':
        print("Operation cancelled.")
        return
    
    # Convert names
    print("\nConverting names...")
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for student in collection.find({}):
        try:
            current_name = student.get('name', '')
            new_name = current_name.upper()
            
            # Skip if already uppercase or empty
            if current_name == new_name or not current_name.strip():
                skipped_count += 1
                continue
            
            # Update the name
            result = collection.update_one(
                {'_id': student['_id']},
                {
                    '$set': {
                        'name': new_name,
                        'updatedAt': datetime.now()
                    }
                }
            )
            
            if result.modified_count > 0:
                updated_count += 1
                print(f"Updated {student.get('roll_number', 'Unknown')}: '{current_name}' -> '{new_name}'")
            else:
                skipped_count += 1
                
        except Exception as e:
            error_count += 1
            print(f"Error updating {student.get('roll_number', 'Unknown')}: {e}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total students: {total_students}")
    print(f"Updated: {updated_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Errors: {error_count}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
