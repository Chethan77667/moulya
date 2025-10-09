"""
Lecturer service for Moulya College Management System
Business logic for lecturer portal operations
"""

from models.user import Lecturer
from models.academic import Subject
from models.student import Student, StudentEnrollment
from models.assignments import SubjectAssignment
from models.attendance import AttendanceRecord, MonthlyAttendanceSummary, MonthlyStudentAttendance
from models.marks import StudentMarks
from database import db
from utils.db_helpers import safe_add_and_commit, safe_update_and_commit
from datetime import datetime, date
from sqlalchemy import extract, func
from sqlalchemy import and_, extract, func

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
            
            # Return students ordered by roll number ascending
            enrollments = StudentEnrollment.query\
                .filter_by(subject_id=subject_id, is_active=True)\
                .join(Student, Student.id == StudentEnrollment.student_id)\
                .order_by(Student.roll_number.asc())\
                .all()
            return [e.student for e in enrollments]
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
        """Generate attendance report for a subject using monthly summary tables.

        Totals are computed from MonthlyAttendanceSummary (sum of total_classes),
        and per-student presents from MonthlyStudentAttendance (sum of present_count).
        This aligns with the new monthly marking model that allows multiple classes per day.
        """
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
            
            # Order enrolled students by roll number (and name as tiebreaker) for reports
            enrollments_sorted = (StudentEnrollment.query
                .filter_by(subject_id=subject_id, is_active=True)
                .join(Student, Student.id == StudentEnrollment.student_id)
                .order_by(Student.roll_number.asc(), Student.name.asc())
                .all())
            enrolled_students = [e.student for e in enrollments_sorted]
            report_data = []
            
            # Compute subject total classes cumulatively (overall across all lecturers)
            total_classes_cumulative = (db.session.query(func.coalesce(func.sum(MonthlyAttendanceSummary.total_classes), 0))
                .filter(
                    MonthlyAttendanceSummary.subject_id == subject_id
                ).scalar() or 0)
            total_classes_cumulative = int(total_classes_cumulative)
            
            for student in enrolled_students:
                # Sum student's presents cumulatively across months (overall across all lecturers)
                present_cumulative = (db.session.query(func.coalesce(func.sum(MonthlyStudentAttendance.present_count), 0))
                    .filter(
                        MonthlyStudentAttendance.student_id == student.id,
                        MonthlyStudentAttendance.subject_id == subject_id
                    ).scalar() or 0)
                present_cumulative = int(present_cumulative)
                # Sum student's deputation cumulatively across months (overall across all lecturers)
                deputation_cumulative = (db.session.query(func.coalesce(func.sum(MonthlyStudentAttendance.deputation_count), 0))
                    .filter(
                        MonthlyStudentAttendance.student_id == student.id,
                        MonthlyStudentAttendance.subject_id == subject_id
                    ).scalar() or 0)
                deputation_cumulative = int(deputation_cumulative)
                
                total_classes = total_classes_cumulative
                present_with_deputation = present_cumulative + deputation_cumulative
                present_classes = min(present_with_deputation, total_classes) if total_classes > 0 else present_with_deputation
                absent_classes = max(total_classes - present_classes, 0)
                attendance_percentage = (present_classes / total_classes * 100) if total_classes > 0 else 0
                
                report_data.append({
                    'student': student,
                    'total_classes': total_classes,
                    'present_classes': present_classes,
                    'absent_classes': absent_classes,
                    'attendance_percentage': round(attendance_percentage, 1),
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
                # Compute overall strictly from what is displayed in marks_summary so UI columns
                # and the Overall % stay consistent (ignores assessments with no max set).
                try:
                    total_obtained = 0.0
                    total_max = 0.0
                    for key in ('internal1', 'internal2', 'assignment', 'project'):
                        entry = marks_summary.get(key) if isinstance(marks_summary, dict) else None
                        if not entry:
                            continue
                        obtained = entry.get('obtained') if isinstance(entry, dict) else None
                        max_marks = entry.get('max') if isinstance(entry, dict) else None
                        if max_marks not in (None, 0, 0.0):
                            total_max += float(max_marks)
                            total_obtained += float(obtained or 0)
                    overall_percentage = round((total_obtained / total_max) * 100, 2) if total_max > 0 else 0.0
                except Exception:
                    # Fallback to DB-based computation if summary parsing fails
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
            
            # Upsert per-student monthly attendance (supports multiple classes per day)
            total_records_created = 0
            for student_id, attended_cumulative in attendance_data.items():
                # Present count up to previous month (use MonthlyStudentAttendance sums)
                prev_present = (db.session.query(func.coalesce(func.sum(MonthlyStudentAttendance.present_count), 0))
                    .filter(
                        MonthlyStudentAttendance.student_id == student_id,
                        MonthlyStudentAttendance.subject_id == subject_id,
                        MonthlyStudentAttendance.lecturer_id == lecturer_id,
                        ((MonthlyStudentAttendance.year < year) |
                         ((MonthlyStudentAttendance.year == year) & (MonthlyStudentAttendance.month < month)))
                    ).scalar() or 0)
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

                # Upsert MonthlyStudentAttendance with cumulative present for this month
                msa = MonthlyStudentAttendance.get_or_create(student_id, subject_id, lecturer_id, month, year)
                msa.present_count = attended_classes
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
            
            # Order enrolled students by roll number (and name as tiebreaker)
            enrollments_sorted = (StudentEnrollment.query
                .filter_by(subject_id=subject_id, is_active=True)
                .join(Student, Student.id == StudentEnrollment.student_id)
                .order_by(Student.roll_number.asc(), Student.name.asc())
                .all())
            enrolled_students = [e.student for e in enrollments_sorted]
            monthly_data = []
            
            for student in enrolled_students:
                # Read per-student monthly present from MonthlyStudentAttendance
                msa = MonthlyStudentAttendance.query.filter_by(
                    student_id=student.id,
                    subject_id=subject_id,
                    lecturer_id=lecturer_id,
                    month=month,
                    year=year
                ).first()
                month_present = msa.present_count if msa else 0
                month_deputation = msa.deputation_count if msa else 0

                # Use the total classes for the month (delta) from summary
                total_classes = total_classes_from_db
                present_classes = month_present
                absent_classes = max(total_classes - present_classes, 0)
                attendance_percentage = (present_classes / total_classes * 100) if total_classes > 0 else 0
                
                monthly_data.append({
                    'student_id': student.id,
                    'student_name': student.name,
                    'roll_number': student.roll_number,
                    'total_classes': total_classes,
                    'present_classes': present_classes,
                    'absent_classes': absent_classes,
                    'attendance_percentage': attendance_percentage,
                    'deputation_count': month_deputation
                })
            
            return monthly_data
            
        except Exception as e:
            return []
    
    @staticmethod
    def get_deputation_data(subject_id, lecturer_id, year):
        """Get cumulative deputation data for all students in a subject for a year"""
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
            
            # Get cumulative total classes for the entire year (do not depend on lecturer filter for robustness)
            cumulative_total_classes = (db.session.query(func.coalesce(func.sum(MonthlyAttendanceSummary.total_classes), 0))
                .filter(
                    MonthlyAttendanceSummary.subject_id == subject_id,
                    MonthlyAttendanceSummary.year == year
                ).scalar() or 0)
            
            # Order enrolled students by roll number
            enrollments_sorted = (StudentEnrollment.query
                .filter_by(subject_id=subject_id, is_active=True)
                .join(Student, Student.id == StudentEnrollment.student_id)
                .order_by(Student.roll_number.asc(), Student.name.asc())
                .all())
            enrolled_students = [e.student for e in enrollments_sorted]
            deputation_data = []
            
            # First pass: sum filtered by lecturer
            per_student_deputation = {}
            for student in enrolled_students:
                # Get cumulative deputation count for the entire year
                cumulative_deputation = (db.session.query(func.coalesce(func.sum(MonthlyStudentAttendance.deputation_count), 0))
                    .filter(
                        MonthlyStudentAttendance.student_id == student.id,
                        MonthlyStudentAttendance.subject_id == subject_id,
                        MonthlyStudentAttendance.lecturer_id == lecturer_id,
                        MonthlyStudentAttendance.year == year
                    ).scalar() or 0)
                per_student_deputation[student.id] = int(cumulative_deputation)

            # If everything is zero (possible lecturer_id mismatch), try a safe fallback without lecturer filter
            if all((v == 0 for v in per_student_deputation.values())):
                try:
                    print(f"[Deputation][Report] All zeros with lecturer filter; applying fallback without lecturer filter for subject={subject_id}, year={year}")
                except Exception:
                    pass
                for student in enrolled_students:
                    cumulative_deputation = (db.session.query(func.coalesce(func.sum(MonthlyStudentAttendance.deputation_count), 0))
                        .filter(
                            MonthlyStudentAttendance.student_id == student.id,
                            MonthlyStudentAttendance.subject_id == subject_id,
                            MonthlyStudentAttendance.year == year
                        ).scalar() or 0)
                    per_student_deputation[student.id] = int(cumulative_deputation)

            for student in enrolled_students:
                # Debug log per-student computed deputation (post-fallback if any)
                try:
                    print(f"[Deputation][Report] subj={subject_id} year={year} student={student.id} -> deputation={per_student_deputation.get(student.id, 0)}")
                except Exception:
                    pass
                
                deputation_data.append({
                    'student_id': student.id,
                    'student_name': student.name,
                    'roll_number': student.roll_number,
                    'total_classes': cumulative_total_classes,
                    'deputation_count': per_student_deputation.get(student.id, 0)
                })
            
            return deputation_data
            
        except Exception as e:
            return []
    
    @staticmethod
    def get_cumulative_total_classes(subject_id, lecturer_id, year):
        """Get cumulative total classes for a subject for the entire year"""
        try:
            cumulative_total_classes = (db.session.query(func.coalesce(func.sum(MonthlyAttendanceSummary.total_classes), 0))
                .filter(
                    MonthlyAttendanceSummary.subject_id == subject_id,
                    MonthlyAttendanceSummary.lecturer_id == lecturer_id,
                    MonthlyAttendanceSummary.year == year
                ).scalar() or 0)
            return cumulative_total_classes
        except Exception as e:
            return 0
    
    @staticmethod
    def get_cumulative_present_count(student_id, subject_id, lecturer_id, year):
        """Get cumulative present count for a student for the entire year"""
        try:
            cumulative_present = (db.session.query(func.coalesce(func.sum(MonthlyStudentAttendance.present_count), 0))
                .filter(
                    MonthlyStudentAttendance.student_id == student_id,
                    MonthlyStudentAttendance.subject_id == subject_id,
                    MonthlyStudentAttendance.lecturer_id == lecturer_id,
                    MonthlyStudentAttendance.year == year
                ).scalar() or 0)
            return cumulative_present
        except Exception as e:
            return 0
    
    @staticmethod
    def record_deputation_attendance(subject_id, lecturer_id, month, year, deputation_data):
        """Record deputation attendance for students"""
        try:
            # Verify lecturer is assigned to this subject
            assignment = SubjectAssignment.query.filter_by(
                lecturer_id=lecturer_id,
                subject_id=subject_id,
                is_active=True
            ).first()
            
            if not assignment:
                return False, "Lecturer not assigned to this subject"
            
            # Record deputation for each student
            for student_id, deputation_count in deputation_data.items():
                # Get or create monthly student attendance record
                msa = MonthlyStudentAttendance.get_or_create(
                    student_id, subject_id, lecturer_id, month, year
                )
                
                # Update deputation count
                msa.deputation_count = deputation_count
                msa.updated_at = datetime.utcnow()
            
            # Commit changes
            db.session.commit()
            return True, "Deputation attendance recorded successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error recording deputation attendance: {str(e)}"