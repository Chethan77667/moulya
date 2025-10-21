import pymongo
from pymongo import MongoClient
from flask import current_app
import os
from datetime import datetime
import pandas as pd
from io import BytesIO
import hashlib

class MongoDBService:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        try:
            # MongoDB connection string - update with your MongoDB details
            connection_string = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
            self.client = MongoClient(connection_string)
            self.db = self.client['moulya']
            print("Connected to MongoDB successfully")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
    
    def get_collection(self, collection_name):
        """Get a collection from the moulya database"""
        return self.db[collection_name]
    
    def add_student_credential(self, roll_number, name, password):
        """Add a new student credential to login_credentials collection"""
        try:
            collection = self.get_collection('login_credentials')
            
            # Check if roll number already exists
            existing = collection.find_one({'roll_number': roll_number})
            if existing:
                return {'success': False, 'message': 'Roll number already exists'}
            
            # Store password as plain text (as per existing data structure)
            # Create student document
            student_doc = {
                'roll_number': roll_number,
                'name': name,
                'username': roll_number.lower(),  # Use roll number as username
                'password': password,  # Store as plain text to match existing data
                'createdAt': datetime.now(),
                'updatedAt': datetime.now(),
                'status': 'active',
                'migrated_at': datetime.now().isoformat(),
                'source_database': 'web_interface'
            }
            
            result = collection.insert_one(student_doc)
            
            if result.inserted_id:
                return {'success': True, 'message': 'Student added successfully', 'id': str(result.inserted_id)}
            else:
                return {'success': False, 'message': 'Failed to add student'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error adding student: {str(e)}'}
    
    def bulk_upload_students(self, excel_data):
        """Bulk upload students from Excel data"""
        try:
            collection = self.get_collection('login_credentials')
            added_count = 0
            errors = []
            
            for index, row in excel_data.iterrows():
                try:
                    roll_number = str(row['Roll Number']).strip()
                    name = str(row['Name']).strip()
                    password = str(row['Password']).strip()
                    
                    # Validate required fields
                    if not roll_number or not name or not password:
                        errors.append(f"Row {index + 1}: Missing required fields")
                        continue
                    
                    # Check if roll number already exists
                    existing = collection.find_one({'roll_number': roll_number})
                    if existing:
                        errors.append(f"Row {index + 1}: Roll number {roll_number} already exists")
                        continue
                    
                    # Store password as plain text (as per existing data structure)
                    # Create student document
                    student_doc = {
                        'roll_number': roll_number,
                        'name': name,
                        'username': roll_number.lower(),
                        'password': password,  # Store as plain text to match existing data
                        'createdAt': datetime.now(),
                        'updatedAt': datetime.now(),
                        'status': 'active',
                        'migrated_at': datetime.now().isoformat(),
                        'source_database': 'bulk_upload'
                    }
                    
                    collection.insert_one(student_doc)
                    added_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return {
                'success': True, 
                'count': added_count, 
                'errors': errors,
                'message': f'Successfully added {added_count} students'
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error in bulk upload: {str(e)}'}
    
    def get_all_students(self):
        """Get all students from login_credentials collection"""
        try:
            collection = self.get_collection('login_credentials')
            students = list(collection.find({}))  # Include password for display
            
            # Convert ObjectId to string for JSON serialization
            for student in students:
                student['_id'] = str(student['_id'])
            
            return {'success': True, 'data': students}
            
        except Exception as e:
            return {'success': False, 'message': f'Error fetching students: {str(e)}'}
    
    def get_student_by_id(self, student_id):
        """Get a specific student by ID"""
        try:
            from bson import ObjectId
            collection = self.get_collection('login_credentials')
            student = collection.find_one({'_id': ObjectId(student_id)})
            
            if student:
                student['_id'] = str(student['_id'])
                return {'success': True, 'data': student}
            else:
                return {'success': False, 'message': 'Student not found'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error fetching student: {str(e)}'}
    
    def update_student(self, student_id, update_data):
        """Update student information"""
        try:
            from bson import ObjectId
            collection = self.get_collection('login_credentials')
            
            print(f"DEBUG: Updating student {student_id} with data: {update_data}")
            
            # Validate ObjectId format
            if not ObjectId.is_valid(student_id):
                print(f"DEBUG: Invalid ObjectId format: {student_id}")
                return {'success': False, 'message': 'Invalid student ID format'}
            
            # Store password as plain text (as per existing data structure)
            # Don't hash the password to match existing data
            
            update_data['updatedAt'] = datetime.now()
            
            result = collection.update_one(
                {'_id': ObjectId(student_id)},
                {'$set': update_data}
            )
            
            print(f"DEBUG: Update result - matched: {result.matched_count}, modified: {result.modified_count}")
            
            if result.modified_count > 0:
                return {'success': True, 'message': 'Student updated successfully'}
            else:
                return {'success': False, 'message': 'No changes made or student not found'}
                
        except Exception as e:
            print(f"DEBUG: Error in update_student: {e}")
            return {'success': False, 'message': f'Error updating student: {str(e)}'}
    
    def delete_student(self, student_id):
        """Delete a student"""
        try:
            from bson import ObjectId
            collection = self.get_collection('login_credentials')
            
            # Validate ObjectId format
            if not ObjectId.is_valid(student_id):
                return {'success': False, 'message': 'Invalid student ID format'}
            
            result = collection.delete_one({'_id': ObjectId(student_id)})
            
            if result.deleted_count > 0:
                return {'success': True, 'message': 'Student deleted successfully'}
            else:
                return {'success': False, 'message': 'Student not found'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error deleting student: {str(e)}'}
    
    def search_students(self, search_term):
        """Search students by roll number, name, or username"""
        try:
            collection = self.get_collection('login_credentials')
            
            # Create search query
            query = {
                '$or': [
                    {'roll_number': {'$regex': search_term, '$options': 'i'}},
                    {'name': {'$regex': search_term, '$options': 'i'}},
                    {'username': {'$regex': search_term, '$options': 'i'}}
                ]
            }
            
            students = list(collection.find(query))  # Include password for display
            
            # Convert ObjectId to string
            for student in students:
                student['_id'] = str(student['_id'])
            
            return {'success': True, 'data': students}
            
        except Exception as e:
            return {'success': False, 'message': f'Error searching students: {str(e)}'}
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

# Global instance
mongodb_service = MongoDBService()
