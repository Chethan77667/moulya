"""
Integration tests for routes and workflows
"""

import unittest
from app import create_app
from database import db
from models.user import Management, Lecturer
from models.academic import Course

class TestRoutes(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        with self.app.app_context():
            db.create_all()
            
            # Create test management user
            mgmt = Management(username='admin')
            mgmt.set_password('admin123')
            db.session.add(mgmt)
            
            # Create test lecturer
            lecturer = Lecturer(lecturer_id='LEC001', name='John Doe', username='john')
            lecturer.set_password('password123')
            db.session.add(lecturer)
            
            db.session.commit()
            
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_landing_page(self):
        """Test landing page loads correctly"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Moulya College Management System', response.data)
    
    def test_management_login_success(self):
        """Test successful management login"""
        response = self.client.post('/management/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Management Dashboard', response.data)
    
    def test_management_login_failure(self):
        """Test failed management login"""
        response = self.client.post('/management/login', data={
            'username': 'admin',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)
    
    def test_lecturer_login_success(self):
        """Test successful lecturer login"""
        response = self.client.post('/lecturer/login', data={
            'username': 'john',
            'password': 'password123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Lecturer Portal', response.data)
    
    def test_lecturer_login_failure(self):
        """Test failed lecturer login"""
        response = self.client.post('/lecturer/login', data={
            'username': 'john',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)
    
    def test_management_dashboard_access_control(self):
        """Test management dashboard requires authentication"""
        response = self.client.get('/management/dashboard')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_lecturer_dashboard_access_control(self):
        """Test lecturer dashboard requires authentication"""
        response = self.client.get('/lecturer/dashboard')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_management_workflow(self):
        """Test complete management workflow"""
        # Login as management
        self.client.post('/management/login', data={
            'username': 'admin',
            'password': 'admin123'
        })
        
        # Access dashboard
        response = self.client.get('/management/dashboard')
        self.assertEqual(response.status_code, 200)
        
        # Access lecturers page
        response = self.client.get('/management/lecturers')
        self.assertEqual(response.status_code, 200)
        
        # Add a course
        response = self.client.post('/management/courses/add', data={
            'name': 'Computer Science',
            'code': 'CS',
            'duration_years': 3,
            'total_semesters': 6
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify course was created
        course = Course.query.filter_by(code='CS').first()
        self.assertIsNotNone(course)
    
    def test_lecturer_workflow(self):
        """Test complete lecturer workflow"""
        # Login as lecturer
        self.client.post('/lecturer/login', data={
            'username': 'john',
            'password': 'password123'
        })
        
        # Access dashboard
        response = self.client.get('/lecturer/dashboard')
        self.assertEqual(response.status_code, 200)
        
        # Access subjects page
        response = self.client.get('/lecturer/subjects')
        self.assertEqual(response.status_code, 200)
    
    def test_logout(self):
        """Test logout functionality"""
        # Login first
        self.client.post('/management/login', data={
            'username': 'admin',
            'password': 'admin123'
        })
        
        # Logout
        response = self.client.post('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Try to access protected page
        response = self.client.get('/management/dashboard')
        self.assertEqual(response.status_code, 302)  # Should redirect to login

if __name__ == '__main__':
    unittest.main()