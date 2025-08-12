"""
Lecturer portal routes for Moulya College Management System
Handles all lecturer functionality
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from routes.auth import login_required
from services.lecturer_service import LecturerService
from models.academic import Subject
from models.student import Student
from models.attendance import AttendanceRecord, MonthlyAttendanceSummary
from datetime import datetime, date

lecturer_bp = Blueprint('lecturer', __name__)

@lecturer_bp.route('/dashboard')
@login_required('lecturer')
def dashboard():
    """Lecturer dashboard with overview statistics"""
    try:
        lecturer_id = session.get('user_id')
        stats = LecturerService.get_lecturer_dashboard_stats(lecturer_id)
        return render_template('lecturer/dashboard.html', stats=stats)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('lecturer/dashboard.html', stats={})

@lecturer_bp.route('/subjects')
@login_required('lecturer')
def subjects():
    """View assigned subjects"""
    try:
        lecturer_id = session.get('user_id')
        subjects_list = LecturerService.get_assigned_subjects(lecturer_id)
        return render_template('lecturer/subjects.html', subjects=subjects_list)
    except Exception as e:
        flash(f'Error loading subjects: {str(e)}', 'error')
        return render_template('lecturer/subjects.html', subjects=[])

@lecturer_bp.route('/subjects/<int:subject_id>/students')
@login_required('lecturer')
def subject_students(subject_id):
    """View students enrolled in a subject"""
    try:
        lecturer_id = session.get('user_id')
        students = LecturerService.get_subject_students(subject_id, lecturer_id)
        subject = Subject.query.get_or_404(subject_id)
        
        # Get all students for enrollment
        all_students = Student.query.filter_by(is_active=True).all()
        
        return render_template('lecturer/subject_students.html', 
                             subject=subject, 
                             students=students,
                             all_students=all_students)
    except Exception as e:
        flash(f'Error loading students: {str(e)}', 'error')
        return redirect(url_for('lecturer.subjects'))

@lecturer_bp.route('/subjects/<int:subject_id>/students/add', methods=['POST'])
@login_required('lecturer')
def add_students_to_subject(subject_id):
    """Add students to subject"""
    try:
        lecturer_id = session.get('user_id')
        student_ids = request.form.getlist('student_ids')
        
        if not student_ids:
            flash('No students selected', 'error')
            return redirect(url_for('lecturer.subject_students', subject_id=subject_id))
        
        success, message = LecturerService.enroll_students(subject_id, student_ids, lecturer_id)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
            
    except Exception as e:
        flash(f'Error adding students: {str(e)}', 'error')
    
    return redirect(url_for('lecturer.subject_students', subject_id=subject_id))

@lecturer_bp.route('/subjects/<int:subject_id>/students/remove', methods=['POST'])
@login_required('lecturer')
def remove_students_from_subject(subject_id):
    """Remove students from subject"""
    try:
        lecturer_id = session.get('user_id')
        student_ids = request.form.getlist('student_ids')
        
        if not student_ids:
            flash('No students selected', 'error')
            return redirect(url_for('lecturer.subject_students', subject_id=subject_id))
        
        success, message = LecturerService.unenroll_students(subject_id, student_ids, lecturer_id)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
            
    except Exception as e:
        flash(f'Error removing students: {str(e)}', 'error')
    
    return redirect(url_for('lecturer.subject_students', subject_id=subject_id))

@lecturer_bp.route('/subjects/<int:subject_id>/attendance')
@login_required('lecturer')
def attendance_management(subject_id):
    """Attendance management for a subject"""
    try:
        lecturer_id = session.get('user_id')
        students = LecturerService.get_subject_students(subject_id, lecturer_id)
        subject = Subject.query.get_or_404(subject_id)
        
        # Get selected date from query params
        selected_date = request.args.get('date')
        if selected_date:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        else:
            selected_date = date.today()
        
        # Get existing attendance for the date
        from models.attendance import AttendanceRecord, MonthlyAttendanceSummary
        existing_attendance = {}
        for student in students:
            record = AttendanceRecord.query.filter_by(
                student_id=student.id,
                subject_id=subject_id,
                date=selected_date
            ).first()
            if record:
                existing_attendance[student.id] = record.status
        
        # Get monthly summary for current month
        monthly_summary = MonthlyAttendanceSummary.query.filter_by(
            subject_id=subject_id,
            lecturer_id=lecturer_id,
            month=selected_date.month,
            year=selected_date.year
        ).first()
        
        # Get monthly attendance data if requested
        monthly_attendance_data = None
        view_month = request.args.get('view_month', selected_date.month, type=int)
        view_year = request.args.get('view_year', selected_date.year, type=int)
        
        if request.args.get('view') == 'monthly' or request.args.get('view_month') or request.args.get('view_year'):
            monthly_attendance_data = LecturerService.get_monthly_attendance_data(
                subject_id, lecturer_id, view_month, view_year
            )
        
        return render_template('lecturer/attendance.html', 
                             subject=subject, 
                             students=students,
                             selected_date=selected_date,
                             existing_attendance=existing_attendance,
                             monthly_summary=monthly_summary,
                             monthly_attendance_data=monthly_attendance_data)
    except Exception as e:
        flash(f'Error loading attendance: {str(e)}', 'error')
        return redirect(url_for('lecturer.subjects'))

@lecturer_bp.route('/subjects/<int:subject_id>/attendance/daily', methods=['POST'])
@login_required('lecturer')
def record_daily_attendance(subject_id):
    """Record daily attendance"""
    try:
        lecturer_id = session.get('user_id')
        attendance_date_str = request.form.get('attendance_date')
        
        if not attendance_date_str:
            flash('Attendance date is required', 'error')
            return redirect(url_for('lecturer.attendance_management', subject_id=subject_id))
        
        attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()
        
        # Build attendance data - exclude system fields
        attendance_data = {}
        
        for key, value in request.form.items():
            # Only process attendance fields that are not system fields
            if key.startswith('attendance_') and key != 'attendance_date' and value:
                try:
                    student_id_str = key.replace('attendance_', '')
                    # Make sure it's a valid integer (student ID)
                    if student_id_str.isdigit():
                        student_id = int(student_id_str)
                        if value in ['present', 'absent']:  # Validate attendance status
                            attendance_data[student_id] = value
                except (ValueError, TypeError):
                    continue
        
        if not attendance_data:
            flash('No attendance data provided', 'error')
            return redirect(url_for('lecturer.attendance_management', subject_id=subject_id))
        
        success, message = LecturerService.record_daily_attendance(
            subject_id, lecturer_id, attendance_data, attendance_date
        )
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
            
    except ValueError as ve:
        flash(f'Invalid date format: {str(ve)}', 'error')
    except Exception as e:
        flash(f'Error recording attendance: {str(e)}', 'error')
    
    return redirect(url_for('lecturer.attendance_management', subject_id=subject_id, date=attendance_date_str))

@lecturer_bp.route('/subjects/<int:subject_id>/attendance/monthly', methods=['POST'])
@login_required('lecturer')
def record_monthly_attendance(subject_id):
    """Record monthly attendance for all students"""
    try:
        lecturer_id = session.get('user_id')
        month = int(request.form.get('month'))
        year = int(request.form.get('year'))
        total_classes = int(request.form.get('total_classes'))
        
        # Build attendance data from form
        attendance_data = {}
        for key, value in request.form.items():
            if key.startswith('attended_') and value:
                try:
                    student_id_str = key.replace('attended_', '')
                    student_id = int(student_id_str)
                    attended_classes = int(value)
                    if attended_classes <= total_classes:
                        attendance_data[student_id] = attended_classes
                except ValueError:
                    continue
        
        if not attendance_data:
            flash('No attendance data provided', 'error')
            return redirect(url_for('lecturer.attendance_management', subject_id=subject_id))
        
        success, message = LecturerService.record_monthly_attendance(
            subject_id, lecturer_id, month, year, total_classes, attendance_data
        )
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
            
    except Exception as e:
        flash(f'Error recording monthly attendance: {str(e)}', 'error')
    
    return redirect(url_for('lecturer.attendance_management', subject_id=subject_id))

@lecturer_bp.route('/subjects/<int:subject_id>/attendance/summary', methods=['POST'])
@login_required('lecturer')
def record_monthly_summary(subject_id):
    """Record monthly attendance summary"""
    try:
        lecturer_id = session.get('user_id')
        month = int(request.form.get('month'))
        year = int(request.form.get('year'))
        total_classes = int(request.form.get('total_classes'))
        
        success, message = LecturerService.record_monthly_summary(
            subject_id, lecturer_id, month, year, total_classes
        )
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
            
    except Exception as e:
        flash(f'Error recording monthly summary: {str(e)}', 'error')
    
    return redirect(url_for('lecturer.attendance_management', subject_id=subject_id))

@lecturer_bp.route('/subjects/<int:subject_id>/marks')
@login_required('lecturer')
def marks_management(subject_id):
    """Marks management for a subject"""
    try:
        lecturer_id = session.get('user_id')
        students = LecturerService.get_subject_students(subject_id, lecturer_id)
        subject = Subject.query.get_or_404(subject_id)
        
        # Get existing marks for students
        from models.marks import StudentMarks
        existing_marks = {}
        for student in students:
            marks = StudentMarks.query.filter_by(
                student_id=student.id,
                subject_id=subject_id
            ).all()
            existing_marks[student.id] = {mark.assessment_type: mark for mark in marks}
        
        return render_template('lecturer/marks.html', 
                             subject=subject, 
                             students=students,
                             existing_marks=existing_marks)
    except Exception as e:
        flash(f'Error loading marks: {str(e)}', 'error')
        return redirect(url_for('lecturer.subjects'))

@lecturer_bp.route('/subjects/<int:subject_id>/marks/add', methods=['POST'])
@login_required('lecturer')
def add_marks(subject_id):
    """Add marks for students"""
    try:
        lecturer_id = session.get('user_id')
        assessment_type = request.form.get('assessment_type')
        max_marks = float(request.form.get('max_marks'))
        
        # Build marks data
        marks_data = []
        for key, value in request.form.items():
            if key.startswith('marks_'):
                student_id = int(key.replace('marks_', ''))
                if value:  # Only process if marks are provided
                    marks_data.append({
                        'student_id': student_id,
                        'assessment_type': assessment_type,
                        'marks_obtained': float(value),
                        'max_marks': max_marks,
                        'assessment_date': date.today()
                    })
        
        if marks_data:
            success, message = LecturerService.add_marks(subject_id, lecturer_id, marks_data)
            
            if success:
                flash(message, 'success')
            else:
                flash(message, 'error')
        else:
            flash('No marks data provided', 'error')
            
    except Exception as e:
        flash(f'Error adding marks: {str(e)}', 'error')
    
    return redirect(url_for('lecturer.marks_management', subject_id=subject_id))

@lecturer_bp.route('/subjects/<int:subject_id>/reports')
@login_required('lecturer')
def subject_reports(subject_id):
    """View reports for a subject"""
    try:
        lecturer_id = session.get('user_id')
        subject = Subject.query.get_or_404(subject_id)
        
        # Generate attendance report
        attendance_report, att_message = LecturerService.generate_attendance_report(subject_id, lecturer_id)
        
        # Generate marks report
        marks_report, marks_message = LecturerService.generate_marks_report(subject_id, lecturer_id)
        
        return render_template('lecturer/reports.html', 
                             subject=subject,
                             attendance_report=attendance_report,
                             marks_report=marks_report)
    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'error')
        return redirect(url_for('lecturer.subjects'))

@lecturer_bp.route('/reports/attendance-shortage')
@login_required('lecturer')
def attendance_shortage_report():
    """Overall attendance shortage report"""
    try:
        lecturer_id = session.get('user_id')
        subjects = LecturerService.get_assigned_subjects(lecturer_id)
        
        shortage_data = []
        for subject in subjects:
            report, message = LecturerService.generate_attendance_report(subject.id, lecturer_id)
            if report:
                shortage_students = [r for r in report if r['has_shortage']]
                if shortage_students:
                    shortage_data.append({
                        'subject': subject,
                        'shortage_students': shortage_students
                    })
        
        return render_template('lecturer/attendance_shortage.html', shortage_data=shortage_data)
    except Exception as e:
        flash(f'Error loading attendance shortage report: {str(e)}', 'error')
        return render_template('lecturer/attendance_shortage.html', shortage_data=[])

@lecturer_bp.route('/reports/marks-deficiency')
@login_required('lecturer')
def marks_deficiency_report():
    """Overall marks deficiency report"""
    try:
        lecturer_id = session.get('user_id')
        subjects = LecturerService.get_assigned_subjects(lecturer_id)
        
        deficiency_data = []
        for subject in subjects:
            report, message = LecturerService.generate_marks_report(subject.id, lecturer_id)
            if report:
                deficient_students = [r for r in report if r['has_deficiency']]
                if deficient_students:
                    deficiency_data.append({
                        'subject': subject,
                        'deficient_students': deficient_students
                    })
        
        return render_template('lecturer/marks_deficiency.html', deficiency_data=deficiency_data)
    except Exception as e:
        flash(f'Error loading marks deficiency report: {str(e)}', 'error')
        return render_template('lecturer/marks_deficiency.html', deficiency_data=[])