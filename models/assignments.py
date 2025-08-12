"""
Assignment models for Moulya College Management System
SubjectAssignment model for lecturer-subject relationships
"""

from database import db
from datetime import datetime

class SubjectAssignment(db.Model):
    """Subject assignment to lecturers"""
    __tablename__ = 'subject_assignment'
    
    id = db.Column(db.Integer, primary_key=True)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturer.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    academic_year = db.Column(db.Integer, nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Unique constraint to prevent duplicate assignments
    __table_args__ = (db.UniqueConstraint('lecturer_id', 'subject_id', 'academic_year', name='unique_lecturer_subject_year'),)
    
    def deactivate(self):
        """Deactivate assignment"""
        self.is_active = False
    
    def activate(self):
        """Activate assignment"""
        self.is_active = True
    
    def to_dict(self):
        """Convert assignment to dictionary"""
        return {
            'id': self.id,
            'lecturer_id': self.lecturer_id,
            'lecturer_name': self.lecturer.name if self.lecturer else None,
            'lecturer_code': self.lecturer.lecturer_id if self.lecturer else None,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'subject_code': self.subject.code if self.subject else None,
            'course_name': self.subject.course.name if self.subject and self.subject.course else None,
            'academic_year': self.academic_year,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        lecturer_name = self.lecturer.name if self.lecturer else "Unknown"
        subject_code = self.subject.code if self.subject else "Unknown"
        return f'<SubjectAssignment {lecturer_name} -> {subject_code}>'