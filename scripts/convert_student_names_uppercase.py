#!/usr/bin/env python3
"""
Script to convert all student names in MongoDB collection to uppercase
====================================================================

This script connects to the MongoDB database and updates all student names
in the login_credentials collection to uppercase format.

Usage:
    python scripts/convert_student_names_uppercase.py

Features:
- Connects to MongoDB using the same configuration as the main application
- Updates all student names to uppercase
- Provides detailed logging of the conversion process
- Shows before/after examples
- Handles errors gracefully
- Provides summary statistics

Author: Moulya College System
Date: 2025
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path to import from main Moulya system
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from services.mongodb_service import MongoDBService
    from pymongo import MongoClient
    import pymongo
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this script from the project root directory")
    sys.exit(1)

class StudentNameConverter:
    def __init__(self):
        self.mongodb_service = MongoDBService()
        self.collection = None
        self.stats = {
            'total_students': 0,
            'updated_students': 0,
            'skipped_students': 0,
            'errors': 0,
            'examples': []
        }
    
    def connect_to_database(self):
        """Connect to MongoDB and get the login_credentials collection"""
        try:
            self.collection = self.mongodb_service.get_collection('login_credentials')
            print("Successfully connected to MongoDB")
            return True
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return False
    
    def get_student_count(self):
        """Get total number of students in the collection"""
        try:
            count = self.collection.count_documents({})
            self.stats['total_students'] = count
            print(f"📊 Total students found: {count}")
            return count
        except Exception as e:
            print(f"❌ Error counting students: {e}")
            return 0
    
    def preview_changes(self, limit=5):
        """Preview what changes will be made (first few students)"""
        print(f"\n🔍 Preview of changes (showing first {limit} students):")
        print("-" * 80)
        
        try:
            students = list(self.collection.find({}).limit(limit))
            
            if not students:
                print("No students found in the collection")
                return
            
            for i, student in enumerate(students, 1):
                current_name = student.get('name', 'N/A')
                new_name = current_name.upper() if current_name != 'N/A' else 'N/A'
                
                print(f"{i}. Roll: {student.get('roll_number', 'N/A')}")
                print(f"   Current: '{current_name}'")
                print(f"   Updated: '{new_name}'")
                print(f"   Changed: {'Yes' if current_name != new_name else 'No'}")
                print()
                
        except Exception as e:
            print(f"❌ Error previewing changes: {e}")
    
    def convert_names_to_uppercase(self, dry_run=False):
        """Convert all student names to uppercase"""
        print(f"\n{'🔍 DRY RUN - ' if dry_run else '🔄 '}Converting student names to uppercase...")
        print("-" * 80)
        
        try:
            # Get all students
            students = list(self.collection.find({}))
            
            if not students:
                print("No students found in the collection")
                return
            
            for student in students:
                try:
                    roll_number = student.get('roll_number', 'Unknown')
                    current_name = student.get('name', '')
                    new_name = current_name.upper()
                    
                    # Skip if name is already uppercase or empty
                    if current_name == new_name or not current_name.strip():
                        self.stats['skipped_students'] += 1
                        if not dry_run:
                            print(f"⏭️  Skipped {roll_number}: '{current_name}' (already uppercase or empty)")
                        continue
                    
                    if dry_run:
                        print(f"📝 Would update {roll_number}: '{current_name}' → '{new_name}'")
                        self.stats['examples'].append({
                            'roll_number': roll_number,
                            'old_name': current_name,
                            'new_name': new_name
                        })
                    else:
                        # Update the student name
                        result = self.collection.update_one(
                            {'_id': student['_id']},
                            {
                                '$set': {
                                    'name': new_name,
                                    'updatedAt': datetime.now()
                                }
                            }
                        )
                        
                        if result.modified_count > 0:
                            self.stats['updated_students'] += 1
                            print(f"✅ Updated {roll_number}: '{current_name}' → '{new_name}'")
                            
                            # Store example for summary
                            if len(self.stats['examples']) < 5:
                                self.stats['examples'].append({
                                    'roll_number': roll_number,
                                    'old_name': current_name,
                                    'new_name': new_name
                                })
                        else:
                            self.stats['skipped_students'] += 1
                            print(f"⚠️  No changes made for {roll_number}")
                
                except Exception as e:
                    self.stats['errors'] += 1
                    print(f"❌ Error updating student {roll_number}: {e}")
            
        except Exception as e:
            print(f"❌ Error during conversion: {e}")
            self.stats['errors'] += 1
    
    def print_summary(self):
        """Print conversion summary"""
        print("\n" + "=" * 80)
        print("📊 CONVERSION SUMMARY")
        print("=" * 80)
        print(f"Total students processed: {self.stats['total_students']}")
        print(f"Successfully updated: {self.stats['updated_students']}")
        print(f"Skipped (already uppercase/empty): {self.stats['skipped_students']}")
        print(f"Errors encountered: {self.stats['errors']}")
        
        if self.stats['examples']:
            print(f"\n📝 Examples of changes made:")
            for example in self.stats['examples']:
                print(f"   {example['roll_number']}: '{example['old_name']}' → '{example['new_name']}'")
        
        print(f"\n⏰ Script completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
    
    def run(self, dry_run=True):
        """Main execution method"""
        print("Student Name Uppercase Converter")
        print("=" * 50)
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Connect to database
        if not self.connect_to_database():
            return False
        
        # Get student count
        if self.get_student_count() == 0:
            print("No students found. Exiting.")
            return False
        
        # Preview changes
        self.preview_changes(limit=5)
        
        # Ask for confirmation if not dry run
        if not dry_run:
            print("\n⚠️  WARNING: This will permanently update student names in the database!")
            confirmation = input("Are you sure you want to proceed? (yes/no): ").lower().strip()
            if confirmation != 'yes':
                print("Operation cancelled by user.")
                return False
        
        # Convert names
        self.convert_names_to_uppercase(dry_run=dry_run)
        
        # Print summary
        self.print_summary()
        
        return True

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert student names to uppercase in MongoDB')
    parser.add_argument('--live', action='store_true', 
                       help='Perform live update (default is dry run)')
    parser.add_argument('--preview-only', action='store_true',
                       help='Only preview changes without converting')
    
    args = parser.parse_args()
    
    # Create converter instance
    converter = StudentNameConverter()
    
    if args.preview_only:
        # Only preview mode
        if converter.connect_to_database():
            converter.get_student_count()
            converter.preview_changes(limit=10)
    else:
        # Run conversion (dry run by default, live if --live flag is used)
        converter.run(dry_run=not args.live)

if __name__ == "__main__":
    main()
