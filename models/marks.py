"""
Marks models for Moulya College Management System
StudentMarks model for assessment tracking
"""

from database import db
from datetime import datetime

class StudentMarks(db.Model):
    """Student marks for different assessment types"""
    __tablename__ = 'student_marks'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturer.id'), nullable=False)
    assessment_type = db.Column(db.String(20), nullable=False)  # 'internal1', 'internal2', 'assignment', 'project'
    marks_obtained = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    percentage = db.Column(db.Float, nullable=False, default=0.0)
    grade = db.Column(db.String(2), nullable=True)
    remarks = db.Column(db.String(200), nullable=True)
    assessment_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint to prevent duplicate marks for same student, subject, assessment type
    __table_args__ = (db.UniqueConstraint('student_id', 'subject_id', 'assessment_type', name='unique_student_subject_assessment'),)
    
    def __init__(self, **kwargs):
        super(StudentMarks, self).__init__(**kwargs)
        self.calculate_percentage_and_grade()
    
    def calculate_percentage_and_grade(self):
        """Calculate percentage and grade based on marks"""
        if self.max_marks > 0:
            self.percentage = (self.marks_obtained / self.max_marks) * 100
            self.grade = self.calculate_grade(self.percentage)
        else:
            self.percentage = 0.0
            self.grade = 'F'
    
    @staticmethod
    def calculate_grade(percentage):
        """Calculate grade based on percentage"""
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B+'
        elif percentage >= 60:
            return 'B'
        elif percentage >= 50:
            return 'C+'
        elif percentage >= 40:
            return 'C'
        elif percentage >= 35:
            return 'D'
        else:
            return 'F'
    
    def is_passing(self, passing_percentage=35):
        """Check if marks are passing"""
        return self.percentage >= passing_percentage
    
    def is_distinction(self, distinction_percentage=75):
        """Check if marks are distinction level"""
        return self.percentage >= distinction_percentage
    
    def update_marks(self, marks_obtained, max_marks):
        """Update marks and recalculate percentage and grade"""
        self.marks_obtained = marks_obtained
        self.max_marks = max_marks
        self.calculate_percentage_and_grade()
        self.updated_at = datetime.utcnow()
    
    @staticmethod
    def get_student_subject_marks(student_id, subject_id):
        """Get all marks for a student in a specific subject"""
        return StudentMarks.query.filter_by(
            student_id=student_id,
            subject_id=subject_id
        ).all()
    
    @staticmethod
    def get_assessment_type_marks(subject_id, assessment_type):
        """Get all marks for a specific assessment type in a subject"""
        return StudentMarks.query.filter_by(
            subject_id=subject_id,
            assessment_type=assessment_type
        ).all()
    
    @staticmethod
    def get_student_overall_percentage(student_id, subject_id):
        """Calculate overall percentage for a student in a subject"""
        marks = StudentMarks.get_student_subject_marks(student_id, subject_id)
        
        if not marks:
            return 0.0
        
        total_obtained = sum(mark.marks_obtained for mark in marks)
        total_max = sum(mark.max_marks for mark in marks)
        
        if total_max == 0:
            return 0.0
        
        return (total_obtained / total_max) * 100
    
    @staticmethod
    def get_class_average(subject_id, assessment_type):
        """Get class average for a specific assessment type"""
        marks = StudentMarks.get_assessment_type_marks(subject_id, assessment_type)
        
        if not marks:
            return 0.0
        
        total_percentage = sum(mark.percentage for mark in marks)
        return round(total_percentage / len(marks), 2)
    
    @staticmethod
    def get_failing_students(subject_id, assessment_type, passing_percentage=35):
        """Get students who are failing in a specific assessment"""
        return StudentMarks.query.filter(
            StudentMarks.subject_id == subject_id,
            StudentMarks.assessment_type == assessment_type,
            StudentMarks.percentage < passing_percentage
        ).all()
    
    @staticmethod
    def get_top_performers(subject_id, assessment_type, limit=10):
        """Get top performing students in a specific assessment"""
        return StudentMarks.query.filter_by(
            subject_id=subject_id,
            assessment_type=assessment_type
        ).order_by(StudentMarks.percentage.desc()).limit(limit).all()
    
    def get_performance_status(self):
        """Get performance status based on percentage"""
        if self.percentage >= 90:
            return 'Excellent'
        elif self.percentage >= 75:
            return 'Very Good'
        elif self.percentage >= 60:
            return 'Good'
        elif self.percentage >= 50:
            return 'Average'
        elif self.percentage >= 35:
            return 'Below Average'
        else:
            return 'Poor'
    
    def to_dict(self):
        """Convert marks to dictionary"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'student_roll_number': self.student.roll_number if self.student else None,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'subject_code': self.subject.code if self.subject else None,
            'lecturer_id': self.lecturer_id,
            'lecturer_name': self.lecturer.name if self.lecturer else None,
            'assessment_type': self.assessment_type,
            'marks_obtained': self.marks_obtained,
            'max_marks': self.max_marks,
            'percentage': self.percentage,
            'grade': self.grade,
            'remarks': self.remarks,
            'assessment_date': self.assessment_date.isoformat() if self.assessment_date else None,
            'performance_status': self.get_performance_status(),
            'is_passing': self.is_passing(),
            'is_distinction': self.is_distinction(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        student_roll = self.student.roll_number if self.student else "Unknown"
        subject_code = self.subject.code if self.subject else "Unknown"
        return f'<StudentMarks {student_roll} - {subject_code} - {self.assessment_type}: {self.marks_obtained}/{self.max_marks}>'