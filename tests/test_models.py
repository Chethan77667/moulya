"""
Unit tests for database models
"""

import unittest
from datetime import date, datetime
from app import create_app
from database import db
from models.user import Management, Lecturer
from models.academic import Course, Subject, AcademicYear
from models.student import Student, StudentEnrollment
from models.attendance import AttendanceRecord, MonthlyAttendanceSummary
from models.marks import StudentMarks

class TestModels(unittest.TestCase):
    
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
    
    def test_management_model(self):
        """Test Management model"""
        # Create management user
        mgmt = Management(username='admin')
        mgmt.set_password('password123')
        
        db.session.add(mgmt)
        db.session.commit()
        
        # Test password verification
        self.assertTrue(mgmt.check_password('password123'))
        self.assertFalse(mgmt.check_password('wrongpassword'))
        
        # Test string representation
        self.assertEqual(str(mgmt), '<Management admin>')
    
    def test_lecturer_model(self):
        """Test Lecturer model"""
        # Create lecturer
        lecturer = Lecturer(
            lecturer_id='LEC001',
            name='John Doe',
            username='john_lec001'
        )
        lecturer.set_password('password123')
        
        db.session.add(lecturer)
        db.session.commit()
        
        # Test password verification
        self.assertTrue(lecturer.check_password('password123'))
        self.assertFalse(lecturer.check_password('wrongpassword'))
        
        # Test credential generation
        username = Lecturer.generate_username('Jane Smith', 'LEC002')
        self.assertEqual(username, 'jane_lec002')
        
        password = Lecturer.generate_password()
        self.assertEqual(len(password), 8)
    
    def test_course_model(self):
        """Test Course model"""
        course = Course(
            name='Computer Science',
            code='CS',
            duration_years=3,
            total_semesters=6
        )
        
        db.session.add(course)
        db.session.commit()
        
        self.assertEqual(course.name, 'Computer Science')
        self.assertEqual(course.duration_years, 3)
        self.assertEqual(str(course), '<Course CS: Computer Science>')
    
    def test_student_model(self):
        """Test Student model"""
        # Create course first
        course = Course(name='Computer Science', code='CS')
        db.session.add(course)
        db.session.commit()
        
        # Create student
        student = Student(
            roll_number='CS001',
            name='Alice Johnson',
            course_id=course.id,
            academic_year=1
        )
        
        db.session.add(student)
        db.session.commit()
        
        self.assertEqual(student.name, 'Alice Johnson')
        self.assertEqual(student.course.name, 'Computer Science')
        self.assertEqual(str(student), '<Student CS001: Alice Johnson>')
    
    def test_attendance_record(self):
        """Test AttendanceRecord model"""
        # Create required objects
        course = Course(name='Computer Science', code='CS')
        db.session.add(course)
        
        subject = Subject(name='Python Programming', code='PY101', course=course, year=1, semester=1)
        db.session.add(subject)
        
        lecturer = Lecturer(lecturer_id='LEC001', name='John Doe', username='john')
        lecturer.set_password('password')
        db.session.add(lecturer)
        
        student = Student(roll_number='CS001', name='Alice', course=course, academic_year=1)
        db.session.add(student)
        
        db.session.commit()
        
        # Create attendance record
        attendance = AttendanceRecord(
            student_id=student.id,
            subject_id=subject.id,
            lecturer_id=lecturer.id,
            date=date.today(),
            status='present'
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        self.assertTrue(attendance.is_present())
        self.assertFalse(attendance.is_absent())
        
        # Test attendance percentage calculation
        percentage = AttendanceRecord.get_attendance_percentage(student.id, subject.id)
        self.assertEqual(percentage, 100.0)
    
    def test_student_marks(self):
        """Test StudentMarks model"""
        # Create required objects
        course = Course(name='Computer Science', code='CS')
        db.session.add(course)
        
        subject = Subject(name='Python Programming', code='PY101', course=course, year=1, semester=1)
        db.session.add(subject)
        
        lecturer = Lecturer(lecturer_id='LEC001', name='John Doe', username='john')
        lecturer.set_password('password')
        db.session.add(lecturer)
        
        student = Student(roll_number='CS001', name='Alice', course=course, academic_year=1)
        db.session.add(student)
        
        db.session.commit()
        
        # Create marks
        marks = StudentMarks(
            student_id=student.id,
            subject_id=subject.id,
            lecturer_id=lecturer.id,
            assessment_type='internal1',
            marks_obtained=85,
            max_marks=100
        )
        
        db.session.add(marks)
        db.session.commit()
        
        self.assertEqual(marks.percentage, 85.0)
        self.assertEqual(marks.grade, 'A')
        self.assertTrue(marks.is_passing())
        self.assertTrue(marks.is_distinction())
        
        # Test grade calculation
        self.assertEqual(StudentMarks.calculate_grade(95), 'A+')
        self.assertEqual(StudentMarks.calculate_grade(85), 'A')
        self.assertEqual(StudentMarks.calculate_grade(30), 'F')

if __name__ == '__main__':
    unittest.main()