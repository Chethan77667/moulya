"""
Student Authentication Service
==============================

This module handles student authentication using MongoDB.
Students login with roll_number as username and password as password.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from config.database import mongodb_config


class AuthService:
    """Main AuthService class for compatibility"""
    pass

class SessionManager:
    """SessionManager class for compatibility"""
    pass

class StudentAuthService:
    """Service for student authentication"""
    
    def __init__(self):
        """Initialize the authentication service"""
        self.collection = mongodb_config.get_collection()
    
    def authenticate_student(self, roll_number: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate student using roll number and date of birth
        
        Args:
            roll_number: Student's roll number
            password: Student's date of birth (as string)
            
        Returns:
            Dict containing student data if authentication successful, None otherwise
        """
        try:
            # Query MongoDB for student with matching roll_number and password
            query = {
                'roll_number': roll_number.upper().strip(),
                'password': password
            }
            
            student = self.collection.find_one(query)
            
            if student:
                # Remove MongoDB's _id field and return student data
                student_data = {
                    'roll_number': student.get('roll_number'),
                    'password': '***',
                    'migrated_at': student.get('migrated_at'),
                    'source_database': student.get('source_database')
                }
                return student_data
            
            return None
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    def get_student_by_roll_number(self, roll_number: str) -> Optional[Dict[str, Any]]:
        """
        Get student data by roll number only
        
        Args:
            roll_number: Student's roll number
            
        Returns:
            Dict containing student data if found, None otherwise
        """
        try:
            query = {'roll_number': roll_number.upper().strip()}
            student = self.collection.find_one(query)
            
            if student:
                return {
                    'roll_number': student.get('roll_number'),
                    'password': student.get('password'),
                    'migrated_at': student.get('migrated_at'),
                    'source_database': student.get('source_database')
                }
            
            return None
            
        except Exception as e:
            print(f"Error fetching student: {e}")
            return None
    
    def validate_roll_number_format(self, roll_number: str) -> bool:
        """
        Validate roll number format
        
        Args:
            roll_number: Student's roll number
            
        Returns:
            bool: True if format is valid, False otherwise
        """
        if not roll_number:
            return False
        
        # Basic validation - should be alphanumeric and reasonable length
        roll_number = roll_number.strip().upper()
        return len(roll_number) >= 3 and len(roll_number) <= 20 and roll_number.replace(' ', '').isalnum()
    
    def validate_date_of_birth(self, date_of_birth: str) -> bool:
        """
        Validate date of birth format
        
        Args:
            date_of_birth: Student's date of birth (as string)
            
        Returns:
            bool: True if format is valid, False otherwise
        """
        if not date_of_birth:
            return False
        
        # Basic validation - should be reasonable length
        date_of_birth = date_of_birth.strip()
        return len(date_of_birth) >= 4 and len(date_of_birth) <= 20
    
    def validate_password(self, password: str) -> bool:
        """Basic password validation for student portal."""
        if not password:
            return False
        password = password.strip()
        return len(password) >= 4

    def update_password(self, roll_number: str, current_password: str, new_password: str) -> bool:
        """Update the student's password in MongoDB after verifying current password."""
        try:
            query = {
                'roll_number': roll_number.upper().strip(),
                'password': current_password.strip()
            }
            student = self.collection.find_one(query)
            if not student:
                return False
            self.collection.update_one(
                {'roll_number': roll_number.upper().strip()},
                {'$set': {'password': new_password.strip(), 'updated_at': datetime.utcnow().isoformat()}},
                upsert=False
            )
            return True
        except Exception as e:
            print(f"Error updating password: {e}")
            return False


# Global authentication service instance
auth_service = StudentAuthService()
