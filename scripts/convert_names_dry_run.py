#!/usr/bin/env python3
"""
Dry run script to preview student name conversions
=================================================

This script shows what changes would be made without actually updating the database.

Usage:
    python scripts/convert_names_dry_run.py
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
    print("Student Name Uppercase Converter - DRY RUN")
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
    
    # Analyze what changes would be made
    print("\nAnalyzing changes...")
    print("-" * 40)
    
    would_update = 0
    already_uppercase = 0
    empty_names = 0
    examples = []
    
    for student in collection.find({}):
        current_name = student.get('name', '')
        new_name = current_name.upper()
        
        if not current_name.strip():
            empty_names += 1
        elif current_name == new_name:
            already_uppercase += 1
        else:
            would_update += 1
            if len(examples) < 10:  # Store first 10 examples
                examples.append({
                    'roll_number': student.get('roll_number', 'Unknown'),
                    'old_name': current_name,
                    'new_name': new_name
                })
    
    # Print analysis results
    print(f"Students that would be updated: {would_update}")
    print(f"Students already uppercase: {already_uppercase}")
    print(f"Students with empty names: {empty_names}")
    
    if examples:
        print(f"\nExamples of changes that would be made:")
        print("-" * 50)
        for i, example in enumerate(examples, 1):
            print(f"{i:2d}. {example['roll_number']}: '{example['old_name']}' -> '{example['new_name']}'")
    
    print(f"\nTo actually perform the conversion, run:")
    print(f"python scripts/convert_names_clean.py")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
