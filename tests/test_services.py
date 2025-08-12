"""
Unit tests for service classes
"""

import unittest
from datetime import date
from app import create_app
from database import db
from services.auth_service import AuthService
from services.management_service import ManagementService
from services.lecturer_service import LecturerService
from models.user import Management, Lecturer
from models.academic import Course, Subject
from models.student import Student

class TestServices(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with self.app.app_context():
            db.create_all()
            
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_auth_service_management_auth(self):
        """Test management authentication"""
        # Create management user
        mgmt = Management(username='admin')
        mgmt.set_password('password123')
        db.session.add(mgmt)
        db.session.commit()
        
        # Test successful authentication
        success, user, message = AuthService.authenticate_management('admin', 'password123')
        self.assertTrue(success)
        self.assertEqual(user.username, 'admin')
        
        # Test failed authentication
        success, user, message = AuthService.authenticate_management('admin', 'wrongpassword')
        self.assertFalse(success)
        self.assertIsNone(user)
    
    def test_auth_service_lecturer_auth(self):
        """Test lecturer authentication"""
        # Create lecturer
        lecturer = Lecturer(lecturer_id='LEC001', name='John Doe', username='john')
        lecturer.set_password('password123')
        db.session.add(lecturer)
        db.session.commit()
        
        # Test successful authentication
        success, user, message = AuthService.authenticate_lecturer('john', 'password123')
        self.assertTrue(success)
        self.assertEqual(user.username, 'john')
        
        # Test failed authentication
        success, user, message = AuthService.authenticate_lecturer('john', 'wrongpassword')
        self.assertFalse(success)
        self.assertIsNone(user)
    
    def test_auth_service_credential_generation(self):
        """Test credential generation"""
        success, username, password, message = AuthService.generate_lecturer_credentials('John Doe', 'LEC001')
        
        self.assertTrue(success)
        self.assertEqual(username, 'john_lec001')
        self.assertEqual(len(password), 8)
    
    def test_management_service_add_lecturer(self):
        """Test adding lecturer through management service"""
        lecturer_data = {
            'lecturer_id': 'LEC001',
            'name': 'John Doe',
            'email': 'john@example.com'
        }
        
        success, message = ManagementService.add_lecturer(lecturer_data)
        self.assertTrue(success)
        
        # Verify lecturer was created
        lecturer = Lecturer.query.filter_by(lecturer_id='LEC001').first()
        self.assertIsNotNone(lecturer)
        self.assertEqual(lecturer.name, 'John Doe')
    
    def test_management_service_add_student(self):
        """Test adding student through management service"""
        # Create course first
        course = Course(name='Computer Science', code='CS')
        db.session.add(course)
        db.session.commit()
        
        student_data = {
            'roll_number': 'CS001',
            'name': 'Alice Johnson',
            'course_id': course.id,
            'academic_year': 1
        }
        
        success, message = ManagementService.add_student(student_data)
        self.assertTrue(success)
        
        # Verify student was created
        student = Student.query.filter_by(roll_number='CS001').first()
        self.assertIsNotNone(student)
        self.assertEqual(student.name, 'Alice Johnson')
    
    def test_management_service_create_course(self):
        """Test creating course through management service"""
        course_data = {
            'name': 'Computer Science',
            'code': 'CS',
            'duration_years': 3,
            'total_semesters': 6
        }
        
        success, message = ManagementService.create_course(course_data)
        self.assertTrue(success)
        
        # Verify course was created
        course = Course.query.filter_by(code='CS').first()
        self.assertIsNotNone(course)
        self.assertEqual(course.name, 'Computer Science')
    
    def test_lecturer_service_dashboard_stats(self):
        """Test lecturer dashboard statistics"""
        # Create lecturer
        lecturer = Lecturer(lecturer_id='LEC001', name='John Doe', username='john')
        lecturer.set_password('password')
        db.session.add(lecturer)
        db.session.commit()
        
        stats = LecturerService.get_lecturer_dashboard_stats(lecturer.id)
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_subjects', stats)
        self.assertIn('total_students', stats)

if __name__ == '__main__':
    unittest.main()