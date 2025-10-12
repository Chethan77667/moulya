"""
Student models for Moulya College Management System
Student and StudentEnrollment models
"""

from database import db
from datetime import datetime

class Student(db.Model):
    """Student model"""
    __tablename__ = 'student'
    
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    academic_year = db.Column(db.Integer, nullable=False)
    current_semester = db.Column(db.Integer, default=1)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(15), nullable=True)
    address = db.Column(db.Text, nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    admission_date = db.Column(db.Date, default=datetime.utcnow().date())
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    enrollments = db.relationship('StudentEnrollment', backref='student', lazy='dynamic')
    attendance_records = db.relationship('AttendanceRecord', backref='student', lazy='dynamic')
    marks = db.relationship('StudentMarks', backref='student', lazy='dynamic')
    
    def get_enrolled_subjects(self):
        """Get all subjects the student is enrolled in"""
        return [enrollment.subject for enrollment in self.enrollments.filter_by(is_active=True)]
    
    def get_current_subjects(self):
        """Get subjects for current semester"""
        return [enrollment.subject for enrollment in self.enrollments.filter_by(
            is_active=True
        ).join('subject').filter_by(
            year=self.academic_year,
            semester=self.current_semester
        )]
    
    def is_enrolled_in_subject(self, subject_id):
        """Check if student is enrolled in a specific subject"""
        return self.enrollments.filter_by(subject_id=subject_id, is_active=True).first() is not None
    
    def get_overall_attendance_percentage(self):
        """Get overall attendance percentage across all subjects"""
        total_classes = self.attendance_records.count()
        if total_classes == 0:
            return 0
        
        present_classes = self.attendance_records.filter_by(status='present').count()
        return round((present_classes / total_classes) * 100, 2)
    
    def get_subject_attendance_percentage(self, subject_id):
        """Get attendance percentage for a specific subject"""
        total_classes = self.attendance_records.filter_by(subject_id=subject_id).count()
        if total_classes == 0:
            return 0
        
        present_classes = self.attendance_records.filter_by(
            subject_id=subject_id, 
            status='present'
        ).count()
        
        return round((present_classes / total_classes) * 100, 2)
    
    def has_attendance_shortage(self, threshold=75):
        """Check if student has attendance shortage"""
        return self.get_overall_attendance_percentage() < threshold
    
    def get_subject_marks_summary(self, subject_id):
        """Get marks summary for a specific subject"""
        # Use direct query instead of relationship to avoid any issues
        from models.marks import StudentMarks
        marks = StudentMarks.query.filter_by(
            student_id=self.id,
            subject_id=subject_id
        ).all()
        
        summary = {
            'internal1': {'obtained': 0, 'max': 0},
            'internal2': {'obtained': 0, 'max': 0},
            'assignment': {'obtained': 0, 'max': 0},
            'project': {'obtained': 0, 'max': 0}
        }
        
        for mark in marks:
            if mark.assessment_type in summary:
                summary[mark.assessment_type]['obtained'] = mark.marks_obtained
                summary[mark.assessment_type]['max'] = mark.max_marks
        
        return summary
    
    def get_overall_marks_percentage(self):
        """Get overall marks percentage across all subjects"""
        marks = self.marks.all()
        if not marks:
            return 0
        
        total_obtained = sum(mark.marks_obtained for mark in marks)
        total_max = sum(mark.max_marks for mark in marks)
        
        if total_max == 0:
            return 0
        
        return round((total_obtained / total_max) * 100, 2)
    
    def promote_to_next_semester(self):
        """Promote student to next semester"""
        if self.current_semester < 6:  # Assuming 6 semesters max
            self.current_semester += 1
            if self.current_semester % 2 == 1:  # Odd semester means new year
                self.academic_year += 1
    
    def to_dict(self):
        """Convert student to dictionary"""
        return {
            'id': self.id,
            'roll_number': self.roll_number,
            'name': self.name,
            'course_id': self.course_id,
            'course_name': self.course.name if self.course else None,
            'academic_year': self.academic_year,
            'current_semester': self.current_semester,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'admission_date': self.admission_date.isoformat() if self.admission_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'overall_attendance': self.get_overall_attendance_percentage(),
            'overall_marks': self.get_overall_marks_percentage()
        }
    
    def __repr__(self):
        return f'<Student {self.roll_number}: {self.name}>'

class StudentEnrollment(db.Model):
    """Student enrollment in subjects"""
    __tablename__ = 'student_enrollment'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    academic_year = db.Column(db.Integer, nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Unique constraint to prevent duplicate enrollments
    __table_args__ = (db.UniqueConstraint('student_id', 'subject_id', name='unique_student_subject_enrollment'),)
    
    def unenroll(self):
        """Unenroll student from subject"""
        self.is_active = False
    
    def re_enroll(self):
        """Re-enroll student in subject"""
        self.is_active = True
    
    def to_dict(self):
        """Convert enrollment to dictionary"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'student_roll_number': self.student.roll_number if self.student else None,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'subject_code': self.subject.code if self.subject else None,
            'academic_year': self.academic_year,
            'enrolled_at': self.enrolled_at.isoformat() if self.enrolled_at else None,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<StudentEnrollment {self.student.roll_number if self.student else "Unknown"} -> {self.subject.code if self.subject else "Unknown"}>'