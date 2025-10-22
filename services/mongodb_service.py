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
    
    def add_student_credential(self, roll_number, name, password, class_name=None):
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
            
            # Add class_name if provided
            if class_name and class_name.strip():
                student_doc['class_name'] = class_name.strip()
                # Auto-generate course_code from class_name
                course_code = class_name.strip().replace(' ', '_')
                student_doc['course_code'] = course_code
            
            result = collection.insert_one(student_doc)
            
            if result.inserted_id:
                return {'success': True, 'message': 'Student added successfully', 'id': str(result.inserted_id)}
            else:
                return {'success': False, 'message': 'Failed to add student'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error adding student: {str(e)}'}
    
    def reset_all_passwords(self, new_password: str):
        """Reset all student passwords to the provided value"""
        try:
            collection = self.get_collection('login_credentials')
            
            # Update all student passwords to provided value
            result = collection.update_many(
                {},  # Empty filter to match all documents
                {
                    '$set': {
                        'password': new_password,
                        'updatedAt': datetime.now()
                    }
                }
            )
            
            return {
                'success': True,
                'message': f'Successfully reset passwords for {result.modified_count} students',
                'modified_count': result.modified_count
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error resetting passwords: {str(e)}'}
    
    def bulk_upload_students(self, excel_data):
        """Bulk upload students from Excel data with update support"""
        try:
            collection = self.get_collection('login_credentials')
            
            added_count = 0
            updated_count = 0
            error_count = 0
            errors = []
            
            for index, row in excel_data.iterrows():
                try:
                    # Extract data from Excel row with proper column mapping
                    roll_number = str(row.get('Roll Number', '')).strip()
                    name = str(row.get('Student Name', '')).strip()
                    class_name = str(row.get('Class Name', '')).strip()
                    password = str(row.get('Password', '')).strip()
                    
                    # Validate required fields
                    if not roll_number or not name or not password:
                        error_count += 1
                        errors.append(f"Row {index + 1}: Missing required fields (Roll Number, Student Name, Password)")
                        continue
                    
                    # Validate password format (DD-MM-YYYY)
                    try:
                        from datetime import datetime
                        datetime.strptime(password, '%d-%m-%Y')
                    except ValueError:
                        error_count += 1
                        errors.append(f"Row {index + 1}: Invalid password format '{password}'. Use DD-MM-YYYY format")
                        continue
                    
                    # Check if student already exists
                    existing = collection.find_one({'roll_number': roll_number})
                    
                    # Prepare student document
                    student_doc = {
                        'roll_number': roll_number,
                        'name': name,
                        'username': roll_number.lower(),
                        'password': password,  # Store DOB as password
                        'updatedAt': datetime.now(),
                        'status': 'active',
                        'source_database': 'excel_upload'
                    }
                    
                    # Add class_name if provided
                    if class_name and class_name.strip():
                        student_doc['class_name'] = class_name.strip()
                        # Auto-generate course_code from class_name
                        course_code = class_name.strip().replace(' ', '_')
                        student_doc['course_code'] = course_code
                    
                    if existing:
                        # Check if there are actual changes
                        has_changes = False
                        changes = {}
                        
                        # Compare each field to see if there are changes
                        if existing.get('name') != student_doc['name']:
                            changes['name'] = student_doc['name']
                            has_changes = True
                        
                        if existing.get('password') != student_doc['password']:
                            changes['password'] = student_doc['password']
                            has_changes = True
                        
                        if existing.get('class_name') != student_doc.get('class_name'):
                            changes['class_name'] = student_doc.get('class_name')
                            has_changes = True
                        
                        if existing.get('course_code') != student_doc.get('course_code'):
                            changes['course_code'] = student_doc.get('course_code')
                            has_changes = True
                        
                        if has_changes:
                            # Only update if there are actual changes
                            changes['updatedAt'] = datetime.now()
                            result = collection.update_one(
                                {'roll_number': roll_number},
                                {'$set': changes}
                            )
                            if result.modified_count > 0:
                                updated_count += 1
                        else:
                            # No changes needed, but still count as processed
                            pass
                    else:
                        # Add new student
                        student_doc['createdAt'] = datetime.now()
                    collection.insert_one(student_doc)
                    added_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return {
                'success': True, 
                'added_count': added_count,
                'updated_count': updated_count,
                'error_count': error_count,
                'errors': errors,
                'message': f'Bulk upload completed. {added_count} students added, {updated_count} students updated, {error_count} errors.'
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
            
            # Debug: Check specific student
            debug_student = next((s for s in students if s.get('roll_number') == 'BBA23101'), None)
            if debug_student:
                print(f"DEBUG: Retrieved student BBA23101: class_name='{debug_student.get('class_name')}', course_code='{debug_student.get('course_code')}'")
            
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
            
            # Verify the update by fetching the updated document
            updated_doc = collection.find_one({'_id': ObjectId(student_id)})
            if updated_doc:
                print(f"DEBUG: Updated document after save: {updated_doc}")
                print(f"DEBUG: Class name in updated doc: {updated_doc.get('class_name', 'NOT_FOUND')}")
            
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
