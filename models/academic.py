"""
Academic structure models for Moulya College Management System
Course, Subject, and AcademicYear models
"""

from database import db
from datetime import datetime

class Course(db.Model):
    """Course model for academic programs"""
    __tablename__ = 'course'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    duration_years = db.Column(db.Integer, default=3, nullable=False)
    total_semesters = db.Column(db.Integer, default=6, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    students = db.relationship('Student', backref='course', lazy='dynamic')
    subjects = db.relationship('Subject', backref='course', lazy='dynamic')
    lecturers = db.relationship('Lecturer', backref='course', lazy='dynamic')
    
    def get_subjects_by_year_semester(self, year, semester):
        """Get subjects for a specific year and semester"""
        return self.subjects.filter_by(year=year, semester=semester).all()
    
    def get_total_subjects(self):
        """Get total number of subjects in the course"""
        return self.subjects.count()
    
    def get_active_students_count(self):
        """Get count of active students in this course"""
        return self.students.filter_by(is_active=True).count()
    
    def to_dict(self):
        """Convert course to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'duration_years': self.duration_years,
            'total_semesters': self.total_semesters,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'total_subjects': self.get_total_subjects(),
            'active_students': self.get_active_students_count()
        }
    
    def __repr__(self):
        return f'<Course {self.code}: {self.name}>'

class Subject(db.Model):
    """Subject model for course subjects"""
    __tablename__ = 'subject'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    credits = db.Column(db.Integer, default=3)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    assignments = db.relationship('SubjectAssignment', backref='subject', lazy='dynamic')
    enrollments = db.relationship('StudentEnrollment', backref='subject', lazy='dynamic')
    attendance_records = db.relationship('AttendanceRecord', backref='subject', lazy='dynamic')
    monthly_summaries = db.relationship('MonthlyAttendanceSummary', backref='subject', lazy='dynamic')
    student_marks = db.relationship('StudentMarks', backref='subject', lazy='dynamic')
    
    # Unique constraint for subject code within a course
    __table_args__ = (db.UniqueConstraint('code', 'course_id', name='unique_subject_code_per_course'),)
    
    def get_assigned_lecturers(self):
        """Get all lecturers assigned to this subject"""
        return [assignment.lecturer for assignment in self.assignments]
    
    def get_enrolled_students(self):
        """Get all students enrolled in this subject"""
        return [enrollment.student for enrollment in self.enrollments.filter_by(is_active=True)]
    
    def get_enrolled_students_count(self):
        """Get count of enrolled students"""
        return self.enrollments.filter_by(is_active=True).count()
    
    def is_student_enrolled(self, student_id):
        """Check if a student is enrolled in this subject"""
        return self.enrollments.filter_by(student_id=student_id, is_active=True).first() is not None
    
    def get_attendance_percentage(self, student_id):
        """Get attendance percentage for a specific student"""
        total_classes = self.attendance_records.filter_by(student_id=student_id).count()
        if total_classes == 0:
            return 0
        
        present_classes = self.attendance_records.filter_by(
            student_id=student_id, 
            status='present'
        ).count()
        
        return round((present_classes / total_classes) * 100, 2)
    
    def to_dict(self):
        """Convert subject to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'course_id': self.course_id,
            'course_name': self.course.name if self.course else None,
            'semester': self.semester,
            'year': self.year,
            'credits': self.credits,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'enrolled_students': self.get_enrolled_students_count()
        }
    
    def __repr__(self):
        return f'<Subject {self.code}: {self.name}>'

class AcademicYear(db.Model):
    """Academic year model for managing academic sessions"""
    __tablename__ = 'academic_year'
    
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False, unique=True, index=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_current = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_semester_dates(self, semester):
        """Get start and end dates for a specific semester"""
        # Simple calculation - divide academic year into semesters
        from datetime import timedelta
        
        total_days = (self.end_date - self.start_date).days
        semester_days = total_days // 2
        
        if semester == 1:
            return self.start_date, self.start_date + timedelta(days=semester_days)
        else:
            mid_date = self.start_date + timedelta(days=semester_days)
            return mid_date, self.end_date
    
    @staticmethod
    def get_current_academic_year():
        """Get the current academic year"""
        return AcademicYear.query.filter_by(is_current=True).first()
    
    def to_dict(self):
        """Convert academic year to dictionary"""
        return {
            'id': self.id,
            'year': self.year,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_current': self.is_current,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<AcademicYear {self.year}>'