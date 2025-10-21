#!/usr/bin/env python3
"""
SQLite to MongoDB Migration Script - Roll Number, Name and Password
=================================================================

This script reads roll_number, name and password from the SQLite database
and transfers them to MongoDB. The password is stored as a STRING to
match the portal's authentication logic.

Database Details:
- Source: SQLite database at instance/moulya_college.db
- Target: MongoDB database 'moulya' with collection 'login_credentials'
- Fields: roll_number, name and password (123456)

Requirements:
- pymongo
- sqlite3 (built-in)

Usage:
    python sqlite_to_mongodb_rollno_dob_only.py

Author: Generated for Moulya College System
Date: 2025
"""

import sqlite3
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, DuplicateKeyError
    from pymongo import UpdateOne
except ImportError:
    print("Error: pymongo is not installed. Please install it using:")
    print("pip install pymongo")
    sys.exit(1)


class RollNoDOBMigrator:
    """Handles migration of roll_number, name and password from SQLite to MongoDB"""
    
    def __init__(self, sqlite_path: str, mongodb_uri: str = "mongodb://localhost:27017/"):
        """
        Initialize the migrator
        
        Args:
            sqlite_path: Path to the SQLite database file
            mongodb_uri: MongoDB connection URI
        """
        self.sqlite_path = sqlite_path
        self.mongodb_uri = mongodb_uri
        self.mongo_client = None
        self.mongo_db = None
        self.collection = None
        
    def connect_to_mongodb(self) -> bool:
        """
        Connect to MongoDB
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            print(f"Connecting to MongoDB at {self.mongodb_uri}...")
            self.mongo_client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.mongo_client.admin.command('ping')
            print("✓ MongoDB connection successful")
            
            # Get database and collection
            self.mongo_db = self.mongo_client['moulya']
            self.collection = self.mongo_db['login_credentials']
            
            return True
            
        except ConnectionFailure as e:
            print(f"✗ Failed to connect to MongoDB: {e}")
            print("Please ensure MongoDB is running and accessible")
            return False
        except Exception as e:
            print(f"✗ Unexpected error connecting to MongoDB: {e}")
            return False
    
    def read_rollno_dob_data(self) -> List[Dict]:
        """
        Read roll_number, name and password from SQLite database.
        Ensures password is coerced to a STRING for consistent auth.
        
        Returns:
            List[Dict]: List of student records with roll_number, name and password
        """
        if not os.path.exists(self.sqlite_path):
            print(f"✗ SQLite database not found at: {self.sqlite_path}")
            return []
        
        try:
            print(f"Reading roll_number and name from SQLite database: {self.sqlite_path}")
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            # Query to get roll_number and name from student table
            query = """
            SELECT 
                roll_number,
                name
            FROM student 
            WHERE is_active = 1
            ORDER BY roll_number
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            print(f"✓ Raw SQLite query returned {len(rows)} rows")
            
            # Convert to list of dictionaries with roll_number, name and default password
            students = []
            for i, row in enumerate(rows):
                try:
                    roll_number = str(row[0]).strip() if row[0] else f"EMPTY_{i}"
                    name = str(row[1]).strip() if row[1] else f"UNKNOWN_{i}"
                    
                    # Always set password to default '123456' (string)
                    password_str = "123456"
                    student_data = {
                        'roll_number': roll_number,  # Use roll_number to match existing collection
                        'name': name,
                        'username': roll_number.lower(),
                        'password': password_str,
                        'status': 'active',
                        'createdAt': datetime.now(),
                        'updatedAt': datetime.now(),
                        'migrated_at': datetime.now().isoformat(),
                        'source_database': 'sqlite_moulya_college'
                    }
                    students.append(student_data)
                    
                    # Show first few records for debugging
                    if i < 3:
                        print(f"  Sample record {i+1}: {roll_number} - {name}")
                        
                except Exception as e:
                    print(f"✗ Error processing row {i}: {e}")
                    continue
            
            conn.close()
            print(f"✓ Successfully processed {len(students)} student records (roll_number, name and password)")
            return students
            
        except sqlite3.Error as e:
            print(f"✗ SQLite error: {e}")
            return []
        except Exception as e:
            print(f"✗ Unexpected error reading SQLite data: {e}")
            return []
    
    def clear_existing_data(self) -> bool:
        """
        Clear existing data from MongoDB collection and drop indexes
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print("Clearing existing data from MongoDB collection...")
            
            # Drop all indexes first
            try:
                indexes = self.collection.list_indexes()
                for index in indexes:
                    if index['name'] != '_id_':  # Don't drop the default _id index
                        print(f"Dropping index: {index['name']}")
                        self.collection.drop_index(index['name'])
            except Exception as e:
                print(f"⚠ Index dropping warning: {e}")
            
            # Clear all data
            result = self.collection.delete_many({})
            print(f"✓ Deleted {result.deleted_count} existing records")
            return True
        except Exception as e:
            print(f"✗ Error clearing existing data: {e}")
            return False
    
    def migrate_to_mongodb(self, students: List[Dict]) -> bool:
        """
        Migrate student data to MongoDB
        
        Args:
            students: List of student records to migrate
            
        Returns:
            bool: True if migration successful, False otherwise
        """
        if not students:
            print("No student data to migrate")
            return False
        
        try:
            print(f"Migrating {len(students)} records to MongoDB...")
            
            # Create index on roll_number for better performance
            try:
                self.collection.create_index("roll_number", unique=True)
                print("✓ Created unique index on roll_number")
            except Exception as e:
                print(f"⚠ Index creation warning: {e}")
            
            # Use bulk operations for better performance
            inserted_count = 0
            updated_count = 0
            error_count = 0
            
            # Process in batches for better performance
            batch_size = 1000
            for i in range(0, len(students), batch_size):
                batch = students[i:i + batch_size]
                print(f"Processing batch {i//batch_size + 1}/{(len(students)-1)//batch_size + 1} ({len(batch)} records)")
                
                # Prepare bulk operations
                bulk_operations = []
                
                for student in batch:
                    try:
                        # Remove _id if it exists to let MongoDB generate it
                        if '_id' in student:
                            del student['_id']
                        
                        # Use upsert operation (insert if not exists, update if exists)
                        bulk_operations.append(UpdateOne(
                            {'roll_number': student['roll_number']},
                            {'$set': student},
                            upsert=True
                        ))
                        
                    except Exception as e:
                        error_count += 1
                        print(f"✗ Error preparing roll_number {student.get('roll_number', 'UNKNOWN')}: {e}")
                        continue
                
                # Execute bulk operations
                if bulk_operations:
                    try:
                        result = self.collection.bulk_write(bulk_operations)
                        inserted_count += result.upserted_count
                        updated_count += result.modified_count
                        print(f"  Batch result: {result.upserted_count} inserted, {result.modified_count} updated")
                    except Exception as e:
                        print(f"✗ Bulk operation error: {e}")
                        # Fallback to individual operations
                        for student in batch:
                            try:
                                if '_id' in student:
                                    del student['_id']
                                result = self.collection.replace_one(
                                    {'roll_number': student['roll_number']},
                                    student,
                                    upsert=True
                                )
                                if result.upserted_id:
                                    inserted_count += 1
                                elif result.modified_count > 0:
                                    updated_count += 1
                            except Exception as e2:
                                error_count += 1
                                print(f"✗ Individual operation error for {student.get('roll_number', 'UNKNOWN')}: {e2}")
            
            print(f"✓ Migration completed!")
            print(f"  - Records inserted: {inserted_count}")
            print(f"  - Records updated: {updated_count}")
            print(f"  - Errors encountered: {error_count}")
            print(f"  - Total records in MongoDB: {self.collection.count_documents({})}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error during migration: {e}")
            return False
    
    def verify_migration(self) -> bool:
        """
        Verify the migration by comparing record counts
        
        Returns:
            bool: True if verification successful, False otherwise
        """
        try:
            # Count records in SQLite
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM student WHERE is_active = 1")
            sqlite_count = cursor.fetchone()[0]
            conn.close()
            
            # Count records in MongoDB
            mongo_count = self.collection.count_documents({})
            
            print(f"\n=== MIGRATION VERIFICATION ===")
            print(f"SQLite active students: {sqlite_count}")
            print(f"MongoDB records: {mongo_count}")
            
            if sqlite_count == mongo_count:
                print("✓ Record counts match - migration successful!")
                return True
            else:
                print("⚠ Record counts don't match - please check migration")
                return False
                
        except Exception as e:
            print(f"✗ Error during verification: {e}")
            return False
    
    def show_sample_data(self, limit: int = 5):
        """
        Show sample data from MongoDB collection
        
        Args:
            limit: Number of sample records to show
        """
        try:
            print(f"\n=== SAMPLE DATA FROM MONGODB (ROLL NUMBER, NAME & PASSWORD) ===")
            sample_docs = list(self.collection.find().limit(limit))
            
            for i, doc in enumerate(sample_docs, 1):
                print(f"\nRecord {i}:")
                print(f"  Roll Number: {doc.get('roll_number', 'N/A')}")
                print(f"  Name: {doc.get('name', 'N/A')}")
                print(f"  Username: {doc.get('username', 'N/A')}")
                print(f"  Password: {doc.get('password', 'N/A')}")
                print(f"  Status: {doc.get('status', 'N/A')}")
                print(f"  Migrated At: {doc.get('migrated_at', 'N/A')}")
                
        except Exception as e:
            print(f"✗ Error showing sample data: {e}")
    
    def close_connections(self):
        """Close database connections"""
        if self.mongo_client:
            self.mongo_client.close()
            print("✓ MongoDB connection closed")


def main():
    """Main function to run the migration"""
    print("=" * 70)
    print("SQLite to MongoDB Migration Script - ROLL NUMBER, NAME & PASSWORD")
    print("Moulya College Student Data Migration (Complete Fields)")
    print("=" * 70)
    
    # Configuration
    sqlite_path = "instance/moulya_college.db"
    mongodb_uri = "mongodb://localhost:27017/"  # Change this if MongoDB is on different host/port
    
    # Initialize migrator
    migrator = RollNoDOBMigrator(sqlite_path, mongodb_uri)
    
    try:
        # Step 1: Connect to MongoDB
        if not migrator.connect_to_mongodb():
            return False
        
        # Step 2: Clear existing data
        if not migrator.clear_existing_data():
            return False
        
        # Step 3: Read data from SQLite (roll_number, name and password as STRING)
        students = migrator.read_rollno_dob_data()
        if not students:
            print("No data to migrate. Exiting.")
            return False
        
        # Debug: Check for potential issues
        print(f"\n=== DATA VALIDATION ===")
        print(f"Total students to migrate: {len(students)}")
        
        # Check for empty roll numbers
        empty_rolls = [s for s in students if not s.get('rollNumber') or s.get('rollNumber').startswith('EMPTY_')]
        if empty_rolls:
            print(f"⚠ Found {len(empty_rolls)} students with empty roll numbers")
        
        # Check for empty names
        empty_names = [s for s in students if not s.get('name') or s.get('name').startswith('UNKNOWN_')]
        if empty_names:
            print(f"⚠ Found {len(empty_names)} students with empty names")
        
        # Show sample data
        print(f"\nFirst 3 records:")
        for i, student in enumerate(students[:3]):
            print(f"  {i+1}. Roll: {student.get('rollNumber')} | Name: {student.get('name')}")
        
        print(f"Last 3 records:")
        for i, student in enumerate(students[-3:]):
            print(f"  {len(students)-2+i}. Roll: {student.get('rollNumber')} | Name: {student.get('name')}")
        
        # Step 4: Migrate to MongoDB
        if not migrator.migrate_to_mongodb(students):
            return False
        
        # Step 5: Verify migration
        migrator.verify_migration()
        
        # Step 6: Show sample data
        migrator.show_sample_data()
        
        print("\n" + "=" * 70)
        print("Migration completed successfully!")
        print("Roll number, name and password fields migrated.")
        print("=" * 70)
        
        return True
        
    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False
    finally:
        migrator.close_connections()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
