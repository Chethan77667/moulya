"""
Reporting service for Moulya College Management System
Handles marks and attendance reports for management
"""

from models.student import Student
from models.academic import Course, Subject
from models.marks import StudentMarks
from models.attendance import AttendanceRecord, MonthlyAttendanceSummary
from models.user import Lecturer
from database import db
from datetime import datetime, date
from sqlalchemy import func, and_, or_

class ReportingService:
    """Service for generating reports"""
    
    @staticmethod
    def get_student_detailed_report(student_id):
        """Get detailed report for a specific student"""
        try:
            student = Student.query.get(student_id)
            if not student:
                return None
            
            # Get all subjects the student is enrolled in
            subjects = Subject.query.join('enrollments').filter_by(
                student_id=student_id,
                is_active=True
            ).all()
            
            report = {
                'student': {
                    'id': student.id,
                    'name': student.name,
                    'roll_number': student.roll_number,
                    'course': student.course.name if student.course else None,
                    'academic_year': student.academic_year,
                    'current_semester': student.current_semester
                },
                'subjects': []
            }
            
            for subject in subjects:
                # Get marks for this subject
                marks = StudentMarks.query.filter_by(
                    student_id=student_id,
                    subject_id=subject.id
                ).all()
                
                # Get attendance for this subject
                attendance_records = AttendanceRecord.query.filter_by(
                    student_id=student_id,
                    subject_id=subject.id
                ).all()
                
                total_classes = len(attendance_records)
                present_classes = len([r for r in attendance_records if r.status == 'present'])
                attendance_percentage = round((present_classes / total_classes) * 100, 2) if total_classes > 0 else 0
                
                # Calculate overall marks percentage
                overall_percentage = StudentMarks.get_student_overall_percentage(student_id, subject.id)
                
                subject_data = {
                    'subject_id': subject.id,
                    'subject_name': subject.name,
                    'subject_code': subject.code,
                    'year': subject.year,
                    'semester': subject.semester,
                    'marks': [mark.to_dict() for mark in marks],
                    'overall_marks_percentage': overall_percentage,
                    'attendance': {
                        'total_classes': total_classes,
                        'present_classes': present_classes,
                        'absent_classes': total_classes - present_classes,
                        'attendance_percentage': attendance_percentage
                    }
                }
                
                report['subjects'].append(subject_data)
            
            return report
            
        except Exception as e:
            print(f"Error generating student report: {e}")
            return None
    
    @staticmethod
    def get_class_marks_report(subject_id, assessment_type=None):
        """Get marks report for entire class in a subject"""
        try:
            subject = Subject.query.get(subject_id)
            if not subject:
                return None
            
            query = StudentMarks.query.filter_by(subject_id=subject_id)
            if assessment_type:
                query = query.filter_by(assessment_type=assessment_type)
            
            marks = query.all()
            
            # Group marks by student
            student_marks = {}
            for mark in marks:
                student_id = mark.student_id
                if student_id not in student_marks:
                    student_marks[student_id] = {
                        'student': mark.student,
                        'marks': []
                    }
                student_marks[student_id]['marks'].append(mark.to_dict())
            
            # Calculate statistics
            all_percentages = [mark.percentage for mark in marks]
            statistics = {
                'total_students': len(student_marks),
                'total_assessments': len(marks),
                'class_average': round(sum(all_percentages) / len(all_percentages), 2) if all_percentages else 0,
                'highest_score': max(all_percentages) if all_percentages else 0,
                'lowest_score': min(all_percentages) if all_percentages else 0,
                'passing_students': len([p for p in all_percentages if p >= 35]),
                'failing_students': len([p for p in all_percentages if p < 35])
            }
            
            report = {
                'subject': {
                    'id': subject.id,
                    'name': subject.name,
                    'code': subject.code,
                    'course': subject.course.name if subject.course else None,
                    'year': subject.year,
                    'semester': subject.semester
                },
                'assessment_type': assessment_type,
                'statistics': statistics,
                'student_marks': list(student_marks.values())
            }
            
            return report
            
        except Exception as e:
            print(f"Error generating class marks report: {e}")
            return None
    
    @staticmethod
    def get_class_attendance_report(subject_id, month=None, year=None):
        """Get attendance report for entire class in a subject"""
        try:
            subject = Subject.query.get(subject_id)
            if not subject:
                return None
            
            # Default to current month/year if not specified
            if not month:
                month = datetime.now().month
            if not year:
                year = datetime.now().year
            
            # Get all students enrolled in this subject
            students = Student.query.join('enrollments').filter_by(
                subject_id=subject_id,
                is_active=True
            ).all()
            
            student_attendance = []
            total_classes_conducted = 0
            
            for student in students:
                attendance_records = AttendanceRecord.query.filter(
                    AttendanceRecord.student_id == student.id,
                    AttendanceRecord.subject_id == subject_id,
                    db.extract('month', AttendanceRecord.date) == month,
                    db.extract('year', AttendanceRecord.date) == year
                ).all()
                
                total_classes = len(attendance_records)
                present_classes = len([r for r in attendance_records if r.status == 'present'])
                attendance_percentage = round((present_classes / total_classes) * 100, 2) if total_classes > 0 else 0
                
                if total_classes > total_classes_conducted:
                    total_classes_conducted = total_classes
                
                student_data = {
                    'student_id': student.id,
                    'student_name': student.name,
                    'roll_number': student.roll_number,
                    'total_classes': total_classes,
                    'present_classes': present_classes,
                    'absent_classes': total_classes - present_classes,
                    'attendance_percentage': attendance_percentage,
                    'status': 'Good' if attendance_percentage >= 75 else 'Poor' if attendance_percentage < 50 else 'Average'
                }
                
                student_attendance.append(student_data)
            
            # Calculate class statistics
            all_percentages = [s['attendance_percentage'] for s in student_attendance if s['total_classes'] > 0]
            statistics = {
                'total_students': len(students),
                'total_classes_conducted': total_classes_conducted,
                'class_average_attendance': round(sum(all_percentages) / len(all_percentages), 2) if all_percentages else 0,
                'students_with_good_attendance': len([s for s in student_attendance if s['attendance_percentage'] >= 75]),
                'students_with_poor_attendance': len([s for s in student_attendance if s['attendance_percentage'] < 50])
            }
            
            report = {
                'subject': {
                    'id': subject.id,
                    'name': subject.name,
                    'code': subject.code,
                    'course': subject.course.name if subject.course else None,
                    'year': subject.year,
                    'semester': subject.semester
                },
                'month': month,
                'year': year,
                'statistics': statistics,
                'student_attendance': student_attendance
            }
            
            return report
            
        except Exception as e:
            print(f"Error generating class attendance report: {e}")
            return None
    
    @staticmethod
    def get_course_overview_report(course_id):
        """Get overview report for entire course"""
        try:
            course = Course.query.get(course_id)
            if not course:
                return None
            
            # Get all subjects in this course
            subjects = Subject.query.filter_by(course_id=course_id, is_active=True).all()
            
            # Get all students in this course
            students = Student.query.filter_by(course_id=course_id, is_active=True).all()
            
            subject_reports = []
            for subject in subjects:
                # Get marks statistics
                marks = StudentMarks.query.filter_by(subject_id=subject.id).all()
                marks_percentages = [mark.percentage for mark in marks]
                
                # Get attendance statistics
                attendance_records = AttendanceRecord.query.filter_by(subject_id=subject.id).all()
                total_records = len(attendance_records)
                present_records = len([r for r in attendance_records if r.status == 'present'])
                
                subject_data = {
                    'subject_id': subject.id,
                    'subject_name': subject.name,
                    'subject_code': subject.code,
                    'year': subject.year,
                    'semester': subject.semester,
                    'enrolled_students': subject.get_enrolled_students_count(),
                    'marks_statistics': {
                        'total_assessments': len(marks),
                        'average_marks': round(sum(marks_percentages) / len(marks_percentages), 2) if marks_percentages else 0,
                        'passing_rate': round((len([p for p in marks_percentages if p >= 35]) / len(marks_percentages)) * 100, 2) if marks_percentages else 0
                    },
                    'attendance_statistics': {
                        'total_classes': total_records,
                        'average_attendance': round((present_records / total_records) * 100, 2) if total_records > 0 else 0
                    }
                }
                
                subject_reports.append(subject_data)
            
            report = {
                'course': {
                    'id': course.id,
                    'name': course.name,
                    'code': course.code,
                    'duration_years': course.duration_years,
                    'total_semesters': course.total_semesters
                },
                'total_students': len(students),
                'total_subjects': len(subjects),
                'subjects': subject_reports
            }
            
            return report
            
        except Exception as e:
            print(f"Error generating course overview report: {e}")
            return None
    
    @staticmethod
    def get_subjects_for_reporting():
        """Get all subjects available for reporting"""
        try:
            subjects = Subject.query.filter_by(is_active=True).all()
            return [{
                'id': subject.id,
                'name': subject.name,
                'code': subject.code,
                'course_name': subject.course.name if subject.course else None,
                'year': subject.year,
                'semester': subject.semester,
                'enrolled_students_count': subject.get_enrolled_students_count()
            } for subject in subjects]
        except Exception as e:
            print(f"Error getting subjects for reporting: {e}")
            return []
    
    @staticmethod
    def get_courses_for_reporting():
        """Get all courses available for reporting"""
        try:
            courses = Course.query.filter_by(is_active=True).all()
            return [{
                'id': course.id,
                'name': course.name,
                'code': course.code,
                'total_students': course.get_active_students_count(),
                'total_subjects': course.subjects.filter_by(is_active=True).count()
            } for course in courses]
        except Exception as e:
            print(f"Error getting courses for reporting: {e}")
            return []
    
    @staticmethod
    def get_students_for_reporting(course_id=None):
        """Get all students available for reporting, optionally filtered by course"""
        try:
            query = Student.query.filter_by(is_active=True)
            if course_id:
                query = query.filter_by(course_id=course_id)
            
            students = query.all()
            return [{
                'id': student.id,
                'name': student.name,
                'roll_number': student.roll_number,
                'course_name': student.course.name if student.course else None,
                'course_id': student.course_id,
                'academic_year': student.academic_year,
                'current_semester': student.current_semester
            } for student in students]
        except Exception as e:
            print(f"Error getting students for reporting: {e}")
            return []