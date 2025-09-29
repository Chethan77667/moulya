"""
Lecturer service for Moulya College Management System
Business logic for lecturer portal operations
"""

from models.user import Lecturer
from models.academic import Subject
from models.student import Student, StudentEnrollment
from models.assignments import SubjectAssignment
from models.attendance import AttendanceRecord, MonthlyAttendanceSummary
from models.marks import StudentMarks
from database import db
from utils.db_helpers import safe_add_and_commit, safe_update_and_commit
from datetime import datetime, date
from sqlalchemy import extract, func
from sqlalchemy import and_, extract

class LecturerService:
    """Lecturer service class"""
    
    @staticmethod
    def get_lecturer_dashboard_stats(lecturer_id):
        """Get dashboard statistics for lecturer"""
        try:
            lecturer = Lecturer.query.get(lecturer_id)
            if not lecturer:
                return {}
            
            # Get assigned subjects
            assigned_subjects = lecturer.get_assigned_subjects()
            
            # Calculate total students across all subjects
            total_students = 0
            for subject in assigned_subjects:
                total_students += subject.get_enrolled_students_count()
            
            # Get recent attendance records
            recent_attendance = AttendanceRecord.query.filter_by(
                lecturer_id=lecturer_id
            ).order_by(AttendanceRecord.created_at.desc()).limit(5).all()
            
            stats = {
                'total_subjects': len(assigned_subjects),
                'total_students': total_students,
                'assigned_subjects': assigned_subjects,
                'recent_attendance': recent_attendance
            }
            
            return stats
        except Exception as e:
            return {}
    
    @staticmethod
    def get_assigned_subjects(lecturer_id):
        """Get all subjects assigned to lecturer"""
        try:
            lecturer = Lecturer.query.get(lecturer_id)
            if not lecturer:
                return []
            
            return lecturer.get_assigned_subjects()
        except Exception as e:
            return []
    
    @staticmethod
    def get_subject_students(subject_id, lecturer_id):
        """Get students enrolled in a subject"""
        try:
            # Verify lecturer is assigned to this subject
            assignment = SubjectAssignment.query.filter_by(
                lecturer_id=lecturer_id,
                subject_id=subject_id,
                is_active=True
            ).first()
            
            if not assignment:
                return []
            
            subject = Subject.query.get(subject_id)
            if not subject:
                return []
            
            return subject.get_enrolled_students()
        except Exception as e:
            return []
    
    @staticmethod
    def enroll_students(subject_id, student_ids, lecturer_id):
        """Enroll multiple students in a subject"""
        try:
            # Verify lecturer is assigned to this subject
            assignment = SubjectAssignment.query.filter_by(
                lecturer_id=lecturer_id,
                subject_id=subject_id,
                is_active=True
            ).first()
            
            if not assignment:
                return False, "You are not assigned to this subject"
            
            enrolled_count = 0
            errors = []
            
            for student_id in student_ids:
                try:
                    # Check if already enrolled
                    existing = StudentEnrollment.query.filter_by(
                        student_id=student_id,
                        subject_id=subject_id
                    ).first()
                    
                    if existing:
                        if not existing.is_active:
                            existing.re_enroll()
                            enrolled_count += 1
                    else:
                        enrollment = StudentEnrollment(
                            student_id=student_id,
                            subject_id=subject_id,
                            academic_year=datetime.now().year
                        )
                        db.session.add(enrollment)
                        enrolled_count += 1
                        
                except Exception as e:
                    errors.append(f"Error enrolling student {student_id}: {str(e)}")
            
            if enrolled_count > 0:
                success, message = safe_update_and_commit()
                if success:
                    return True, f"Successfully enrolled {enrolled_count} students"
                else:
                    return False, message
            else:
                return False, "No students were enrolled"
                
        except Exception as e:
            return False, f"Error enrolling students: {str(e)}"
    
    @staticmethod
    def unenroll_students(subject_id, student_ids, lecturer_id):
        """Unenroll multiple students from a subject"""
        try:
            # Verify lecturer is assigned to this subject
            assignment = SubjectAssignment.query.filter_by(
                lecturer_id=lecturer_id,
                subject_id=subject_id,
                is_active=True
            ).first()
            
            if not assignment:
                return False, "You are not assigned to this subject"
            
            unenrolled_count = 0
            
            for student_id in student_ids:
                enrollment = StudentEnrollment.query.filter_by(
                    student_id=student_id,
                    subject_id=subject_id,
                    is_active=True
                ).first()
                
                if enrollment:
                    enrollment.unenroll()
                    unenrolled_count += 1
            
            if unenrolled_count > 0:
                success, message = safe_update_and_commit()
                if success:
                    return True, f"Successfully unenrolled {unenrolled_count} students"
                else:
                    return False, message
            else:
                return False, "No students were unenrolled"
                
        except Exception as e:
            return False, f"Error unenrolling students: {str(e)}"
    
    @staticmethod
    def record_daily_attendance(subject_id, lecturer_id, attendance_data, attendance_date=None):
        """Record daily attendance for students"""
        try:
            # Verify lecturer is assigned to this subject
            assignment = SubjectAssignment.query.filter_by(
                lecturer_id=lecturer_id,
                subject_id=subject_id,
                is_active=True
            ).first()
            
            if not assignment:
                return False, "You are not assigned to this subject"
            
            if not attendance_date:
                attendance_date = date.today()
            
            recorded_count = 0
            updated_count = 0
            
            for student_id, status in attendance_data.items():
                try:
                    # Check if attendance already exists for this date
                    existing = AttendanceRecord.query.filter_by(
                        student_id=student_id,
                        subject_id=subject_id,
                        date=attendance_date
                    ).first()
                    
                    if existing:
                        existing.status = status
                        existing.updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        attendance = AttendanceRecord(
                            student_id=student_id,
                            subject_id=subject_id,
                            lecturer_id=lecturer_id,
                            date=attendance_date,
                            status=status
                        )
                        db.session.add(attendance)
                        recorded_count += 1
                        
                except Exception as e:
                    continue
            
            success, message = safe_update_and_commit()
            if success:
                total_processed = recorded_count + updated_count
                return True, f"Attendance recorded for {total_processed} students"
            else:
                return False, message
                
        except Exception as e:
            return False, f"Error recording attendance: {str(e)}"
    
    @staticmethod
    def record_monthly_summary(subject_id, lecturer_id, month, year, total_classes):
        """Record monthly attendance summary"""
        try:
            # Verify lecturer is assigned to this subject
            assignment = SubjectAssignment.query.filter_by(
                lecturer_id=lecturer_id,
                subject_id=subject_id,
                is_active=True
            ).first()
            
            if not assignment:
                return False, "You are not assigned to this subject"
            
            # Get or create monthly summary
            summary = MonthlyAttendanceSummary.get_or_create(
                subject_id, lecturer_id, month, year, total_classes
            )
            
            success, message = safe_update_and_commit()
            if success:
                return True, f"Monthly summary updated for {month}/{year}"
            else:
                return False, message
                
        except Exception as e:
            return False, f"Error recording monthly summary: {str(e)}"
    
    @staticmethod
    def add_marks(subject_id, lecturer_id, marks_data):
        """Add marks for students"""
        try:
            # Verify lecturer is assigned to this subject
            assignment = SubjectAssignment.query.filter_by(
                lecturer_id=lecturer_id,
                subject_id=subject_id,
                is_active=True
            ).first()
            
            if not assignment:
                return False, "You are not assigned to this subject"
            
            added_count = 0
            updated_count = 0
            
            for data in marks_data:
                try:
                    student_id = data['student_id']
                    assessment_type = data['assessment_type']
                    marks_obtained = float(data['marks_obtained'])
                    max_marks = float(data['max_marks'])
                    
                    # Validate marks
                    if marks_obtained > max_marks:
                        continue
                    
                    # Check if marks already exist
                    existing = StudentMarks.query.filter_by(
                        student_id=student_id,
                        subject_id=subject_id,
                        assessment_type=assessment_type
                    ).first()
                    
                    if existing:
                        existing.update_marks(marks_obtained, max_marks)
                        updated_count += 1
                    else:
                        marks = StudentMarks(
                            student_id=student_id,
                            subject_id=subject_id,
                            lecturer_id=lecturer_id,
                            assessment_type=assessment_type,
                            marks_obtained=marks_obtained,
                            max_marks=max_marks,
                            assessment_date=data.get('assessment_date')
                        )
                        db.session.add(marks)
                        added_count += 1
                        
                except Exception as e:
                    continue
            
            success, message = safe_update_and_commit()
            if success:
                total_processed = added_count + updated_count
                return True, f"Marks updated for {total_processed} entries"
            else:
                return False, message
                
        except Exception as e:
            return False, f"Error adding marks: {str(e)}"
    
    @staticmethod
    def generate_attendance_report(subject_id, lecturer_id):
        """Generate attendance report for a subject"""
        try:
            # Verify lecturer is assigned to this subject
            assignment = SubjectAssignment.query.filter_by(
                lecturer_id=lecturer_id,
                subject_id=subject_id,
                is_active=True
            ).first()
            
            if not assignment:
                return None, "You are not assigned to this subject"
            
            subject = Subject.query.get(subject_id)
            if not subject:
                return None, "Subject not found"
            
            enrolled_students = subject.get_enrolled_students()
            report_data = []
            
            for student in enrolled_students:
                attendance_percentage = subject.get_attendance_percentage(student.id)
                total_classes = AttendanceRecord.query.filter_by(
                    student_id=student.id,
                    subject_id=subject_id
                ).count()
                
                present_classes = AttendanceRecord.query.filter_by(
                    student_id=student.id,
                    subject_id=subject_id,
                    status='present'
                ).count()
                
                report_data.append({
                    'student': student,
                    'total_classes': total_classes,
                    'present_classes': present_classes,
                    'absent_classes': total_classes - present_classes,
                    'attendance_percentage': attendance_percentage,
                    'has_shortage': attendance_percentage < 75
                })
            
            return report_data, "Report generated successfully"
            
        except Exception as e:
            return None, f"Error generating report: {str(e)}"
    
    @staticmethod
    def generate_marks_report(subject_id, lecturer_id):
        """Generate marks report for a subject"""
        try:
            # Verify lecturer is assigned to this subject
            assignment = SubjectAssignment.query.filter_by(
                lecturer_id=lecturer_id,
                subject_id=subject_id,
                is_active=True
            ).first()
            
            if not assignment:
                return None, "You are not assigned to this subject"
            
            subject = Subject.query.get(subject_id)
            if not subject:
                return None, "Subject not found"
            
            enrolled_students = subject.get_enrolled_students()
            report_data = []
            
            for student in enrolled_students:
                marks_summary = student.get_subject_marks_summary(subject_id)
                overall_percentage = StudentMarks.get_student_overall_percentage(student.id, subject_id)
                
                report_data.append({
                    'student': student,
                    'marks_summary': marks_summary,
                    'overall_percentage': overall_percentage,
                    'has_deficiency': overall_percentage < 50
                })
            
            return report_data, "Report generated successfully"
            
        except Exception as e:
            return None, f"Error generating report: {str(e)}"
    
    @staticmethod
    def record_monthly_attendance(subject_id, lecturer_id, month, year, total_classes, attendance_data):
        """Record monthly attendance for all students at once"""
        try:
            # Verify lecturer is assigned to this subject
            assignment = SubjectAssignment.query.filter_by(
                lecturer_id=lecturer_id,
                subject_id=subject_id,
                is_active=True
            ).first()
            
            if not assignment:
                return False, "You are not assigned to this subject"
            
            # Compute monthly delta from cumulative inputs
            from datetime import date as date_class
            import calendar

            # Previous month/year
            prev_year = year
            prev_month = month - 1
            if prev_month == 0:
                prev_month = 12
                prev_year -= 1

            # Sum prior months' total_classes to get cumulative through previous month
            prior_total_classes = db.session.query(func.coalesce(func.sum(MonthlyAttendanceSummary.total_classes), 0)).filter(
                MonthlyAttendanceSummary.subject_id == subject_id,
                MonthlyAttendanceSummary.lecturer_id == lecturer_id,
                ( (MonthlyAttendanceSummary.year < year) | ((MonthlyAttendanceSummary.year == year) & (MonthlyAttendanceSummary.month < month)) )
            ).scalar() or 0

            # Validate cumulative total must be at least prior cumulative (non-decreasing)
            if total_classes < prior_total_classes:
                return False, (
                    f"Total classes till {month} ({total_classes}) cannot be less than previous cumulative ({prior_total_classes})."
                )

            # Calculate delta classes for this month
            month_total_classes = total_classes - prior_total_classes

            # Create or update monthly summary using monthly delta
            summary = MonthlyAttendanceSummary.get_or_create(
                subject_id, lecturer_id, month, year, month_total_classes
            )

            # Ensure daily records reflect the month's delta exactly:
            # remove any existing records in this month beyond the new total (e.g., when total reduced)
            # This keeps the unique class days equal to month_total_classes for reporting.
            def _cleanup_days_beyond_delta():
                try:
                    # Delete records where day index in month exceeds month_total_classes
                    extra_recs = AttendanceRecord.query.filter(
                        AttendanceRecord.subject_id == subject_id,
                        AttendanceRecord.lecturer_id == lecturer_id,
                        extract('month', AttendanceRecord.date) == month,
                        extract('year', AttendanceRecord.date) == year,
                        func.extract('day', AttendanceRecord.date) > month_total_classes
                    ).all()
                    for rec in extra_recs:
                        db.session.delete(rec)
                    db.session.flush()
                except Exception:
                    # Best-effort cleanup; continue even if none
                    pass

            _cleanup_days_beyond_delta()

            # Preload existing month records mapped by student for selective updates
            existing_records_by_student = {}
            existing_q = AttendanceRecord.query.filter(
                AttendanceRecord.subject_id == subject_id,
                AttendanceRecord.lecturer_id == lecturer_id,
                extract('month', AttendanceRecord.date) == month,
                extract('year', AttendanceRecord.date) == year
            )
            for rec in existing_q.all():
                existing_records_by_student.setdefault(rec.student_id, []).append(rec)
            
            # Create attendance records based on monthly delta
            days_in_month = calendar.monthrange(year, month)[1]
            
            total_records_created = 0
            
            for student_id, attended_cumulative in attendance_data.items():
                # Present count up to previous month
                prev_end = date_class(prev_year, prev_month, calendar.monthrange(prev_year, prev_month)[1]) if prior_total_classes > 0 else None
                prev_present = 0
                if prev_end:
                    prev_present = AttendanceRecord.query.filter(
                        AttendanceRecord.student_id == student_id,
                        AttendanceRecord.subject_id == subject_id,
                        AttendanceRecord.lecturer_id == lecturer_id,
                        AttendanceRecord.date <= prev_end,
                        AttendanceRecord.status == 'present'
                    ).count()
                # Already recorded present in the current month (before this submission)
                existing_month_present = AttendanceRecord.query.filter(
                    AttendanceRecord.student_id == student_id,
                    AttendanceRecord.subject_id == subject_id,
                    AttendanceRecord.lecturer_id == lecturer_id,
                    extract('month', AttendanceRecord.date) == month,
                    extract('year', AttendanceRecord.date) == year,
                    AttendanceRecord.status == 'present'
                ).count()
                # Monthly delta for student derived from cumulative without hard validation
                # Normalize bad values and clamp within [0, month_total_classes]
                if attended_cumulative is None:
                    attended_cumulative = 0
                # Hard validation: cumulative for this month must be at least the
                # sum of all previous months for this student, and cannot exceed
                # the total classes entered for the selected month.
                if attended_cumulative < prev_present:
                    student = Student.query.get(student_id)
                    student_label = f"{student.name} ({student.roll_number})" if student else str(student_id)
                    return False, (
                        f"Cumulative for {student_label} is too low. "
                        f"Minimum is {prev_present}."
                    )
                if attended_cumulative > total_classes:
                    student = Student.query.get(student_id)
                    student_label = f"{student.name} ({student.roll_number})" if student else str(student_id)
                    return False, (
                        f"Cumulative for {student_label} exceeds total classes. "
                        f"Maximum is {total_classes}."
                    )

                attended_classes = attended_cumulative - prev_present
                if attended_classes < 0:
                    attended_classes = 0
                if attended_classes > month_total_classes:
                    attended_classes = month_total_classes
                absent_classes = max(month_total_classes - attended_classes, 0)
                
                # Create attendance records for each day of the month
                # We'll distribute present/absent days across the month
                present_days = []
                absent_days = []
                
                # Simple distribution: mark first 'attended_classes' days as present
                for day in range(1, month_total_classes + 1):
                    if day <= attended_classes:
                        present_days.append(day)
                    else:
                        absent_days.append(day)
                
                # Replace existing month records for this student, then insert
                if student_id in existing_records_by_student:
                    for rec in existing_records_by_student[student_id]:
                        db.session.delete(rec)
                    db.session.flush()

                # Create attendance records
                for day in present_days:
                    if day <= days_in_month:
                        attendance_date = date_class(year, month, day)
                        record = AttendanceRecord(
                            student_id=student_id,
                            subject_id=subject_id,
                            lecturer_id=lecturer_id,
                            date=attendance_date,
                            status='present'
                        )
                        db.session.add(record)
                        total_records_created += 1
                
                for day in absent_days:
                    if day <= days_in_month:
                        attendance_date = date_class(year, month, day)
                        record = AttendanceRecord(
                            student_id=student_id,
                            subject_id=subject_id,
                            lecturer_id=lecturer_id,
                            date=attendance_date,
                            status='absent'
                        )
                        db.session.add(record)
                        total_records_created += 1
            
            # Update the monthly summary
            summary.calculate_average_attendance()
            
            success, message = safe_update_and_commit()
            if success:
                return True, f"Monthly attendance recorded for {len(attendance_data)} students ({total_records_created} records created)"
            else:
                return False, message
                
        except Exception as e:
            return False, f"Error recording monthly attendance: {str(e)}"
    
    @staticmethod
    def get_monthly_attendance_data(subject_id, lecturer_id, month, year):
        """Get monthly attendance data for all students in a subject"""
        try:
            # Verify lecturer is assigned to this subject
            assignment = SubjectAssignment.query.filter_by(
                lecturer_id=lecturer_id,
                subject_id=subject_id,
                is_active=True
            ).first()
            
            if not assignment:
                return []
            
            subject = Subject.query.get(subject_id)
            if not subject:
                return []
            
            # Get the monthly summary to get the actual total classes from database
            monthly_summary = MonthlyAttendanceSummary.query.filter_by(
                subject_id=subject_id,
                lecturer_id=lecturer_id,
                month=month,
                year=year
            ).first()
            
            # If no monthly summary exists, return empty data
            if not monthly_summary:
                return []
            
            # Get the actual total classes from the monthly summary
            total_classes_from_db = monthly_summary.total_classes
            
            enrolled_students = subject.get_enrolled_students()
            monthly_data = []
            
            for student in enrolled_students:
                # Get attendance records for the specific month
                attendance_records = AttendanceRecord.query.filter(
                    AttendanceRecord.student_id == student.id,
                    AttendanceRecord.subject_id == subject_id,
                    extract('month', AttendanceRecord.date) == month,
                    extract('year', AttendanceRecord.date) == year
                ).all()
                
                # Use the total classes from the monthly summary (database value)
                total_classes = total_classes_from_db
                present_classes = len([r for r in attendance_records if r.status == 'present'])
                absent_classes = total_classes - present_classes
                attendance_percentage = (present_classes / total_classes * 100) if total_classes > 0 else 0
                
                monthly_data.append({
                    'student_id': student.id,
                    'student_name': student.name,
                    'roll_number': student.roll_number,
                    'total_classes': total_classes,
                    'present_classes': present_classes,
                    'absent_classes': absent_classes,
                    'attendance_percentage': attendance_percentage
                })
            
            return monthly_data
            
        except Exception as e:
            return []