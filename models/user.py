"""
User models for Moulya College Management System
Management and Lecturer user models
"""

from database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Management(db.Model):
    """Management user model for administrative access"""
    __tablename__ = 'management'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<Management {self.username}>'

class Lecturer(db.Model):
    """Lecturer user model"""
    __tablename__ = 'lecturer'
    
    id = db.Column(db.Integer, primary_key=True)
    lecturer_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(120), nullable=False)
    password_encrypted = db.Column(db.Text, nullable=True)  # Encrypted password for management access
    email = db.Column(db.String(120), unique=True, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    subject_assignments = db.relationship('SubjectAssignment', backref='lecturer', lazy='dynamic')
    attendance_records = db.relationship('AttendanceRecord', backref='lecturer', lazy='dynamic')
    monthly_summaries = db.relationship('MonthlyAttendanceSummary', backref='lecturer', lazy='dynamic')
    student_marks = db.relationship('StudentMarks', backref='lecturer', lazy='dynamic')
    
    def set_password(self, password):
        """Set password hash and encrypted password for management access"""
        from utils.encryption import password_encryptor
        self.password_hash = generate_password_hash(password)
        self.password_encrypted = password_encryptor.encrypt_password(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def get_assigned_subjects(self):
        """Get all subjects assigned to this lecturer"""
        return [assignment.subject for assignment in self.subject_assignments]
    
    def is_assigned_to_subject(self, subject_id):
        """Check if lecturer is assigned to a specific subject"""
        return self.subject_assignments.filter_by(subject_id=subject_id).first() is not None
    
    def get_decrypted_password(self):
        """Get decrypted password for management access"""
        from utils.encryption import password_encryptor
        if self.password_encrypted:
            return password_encryptor.decrypt_password(self.password_encrypted)
        return None
    
    @staticmethod
    def generate_username(name, lecturer_id):
        """Generate username from name and lecturer ID in BBHC format"""
        # Take first name and add BBHC format
        first_name = name.split()[0].lower()
        return f"bbhc_{first_name}_{lecturer_id.lower()}"
    
    @staticmethod
    def generate_password():
        """Generate a random password for new lecturers"""
        import random
        import string
        
        # Generate 8-character password with letters and numbers
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(8))
    
    def to_dict(self):
        """Convert lecturer to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'lecturer_id': self.lecturer_id,
            'name': self.name,
            'username': self.username,
            'course_id': self.course_id,
            'course_name': self.course.name if self.course else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<Lecturer {self.lecturer_id}: {self.name}>'