"""
Excel export service for Moulya College Management System
Handles Excel export for reports
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO
from datetime import datetime

class ExcelExportService:
    """Service for exporting reports to Excel"""
    
    @staticmethod
    def create_workbook():
        """Create a new workbook with default styling"""
        wb = openpyxl.Workbook()
        return wb
    
    @staticmethod
    def style_header_row(ws, row_num, columns):
        """Apply styling to header row"""
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        for col_num, header in enumerate(columns, 1):
            cell = ws.cell(row=row_num, column=col_num, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
    
    @staticmethod
    def auto_adjust_columns(ws):
        """Auto-adjust column widths"""
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    @staticmethod
    def export_student_report(report_data):
        """Export individual student report to Excel"""
        try:
            wb = ExcelExportService.create_workbook()
            
            # Student Info Sheet
            ws_info = wb.active
            ws_info.title = "Student Information"
            
            student = report_data['student']
            
            # Student details
            ws_info['A1'] = "STUDENT REPORT"
            ws_info['A1'].font = Font(bold=True, size=16)
            
            ws_info['A3'] = "Name:"
            ws_info['B3'] = student['name']
            ws_info['A4'] = "Roll Number:"
            ws_info['B4'] = student['roll_number']
            ws_info['A5'] = "Course:"
            ws_info['B5'] = student['course']
            ws_info['A6'] = "Academic Year:"
            ws_info['B6'] = student['academic_year']
            ws_info['A7'] = "Current Semester:"
            ws_info['B7'] = student['current_semester']
            
            # Marks Sheet
            ws_marks = wb.create_sheet("Marks Report")
            
            marks_headers = ['Subject', 'Subject Code', 'Assessment Type', 'Marks Obtained', 
                           'Max Marks', 'Percentage', 'Grade', 'Status']
            ExcelExportService.style_header_row(ws_marks, 1, marks_headers)
            
            row = 2
            for subject in report_data['subjects']:
                for mark in subject['marks']:
                    ws_marks.cell(row=row, column=1, value=subject['subject_name'])
                    ws_marks.cell(row=row, column=2, value=subject['subject_code'])
                    ws_marks.cell(row=row, column=3, value=mark['assessment_type'])
                    ws_marks.cell(row=row, column=4, value=mark['marks_obtained'])
                    ws_marks.cell(row=row, column=5, value=mark['max_marks'])
                    ws_marks.cell(row=row, column=6, value=mark['percentage'])
                    ws_marks.cell(row=row, column=7, value=mark['grade'])
                    ws_marks.cell(row=row, column=8, value=mark['performance_status'])
                    row += 1
            
            # Attendance Sheet
            ws_attendance = wb.create_sheet("Attendance Report")
            
            attendance_headers = ['Subject', 'Subject Code', 'Total Classes', 'Present', 
                                'Absent', 'Attendance %', 'Status']
            ExcelExportService.style_header_row(ws_attendance, 1, attendance_headers)
            
            row = 2
            for subject in report_data['subjects']:
                attendance = subject['attendance']
                ws_attendance.cell(row=row, column=1, value=subject['subject_name'])
                ws_attendance.cell(row=row, column=2, value=subject['subject_code'])
                ws_attendance.cell(row=row, column=3, value=attendance['total_classes'])
                ws_attendance.cell(row=row, column=4, value=attendance['present_classes'])
                ws_attendance.cell(row=row, column=5, value=attendance['absent_classes'])
                ws_attendance.cell(row=row, column=6, value=attendance['attendance_percentage'])
                
                status = "Good" if attendance['attendance_percentage'] >= 75 else "Poor" if attendance['attendance_percentage'] < 50 else "Average"
                ws_attendance.cell(row=row, column=7, value=status)
                row += 1
            
            # Auto-adjust columns
            ExcelExportService.auto_adjust_columns(ws_info)
            ExcelExportService.auto_adjust_columns(ws_marks)
            ExcelExportService.auto_adjust_columns(ws_attendance)
            
            return wb
            
        except Exception as e:
            print(f"Error exporting student report: {e}")
            return None
    
    @staticmethod
    def export_class_marks_report(report_data):
        """Export class marks report to Excel"""
        try:
            wb = ExcelExportService.create_workbook()
            ws = wb.active
            ws.title = "Class Marks Report"
            
            # Title and subject info
            subject = report_data['subject']
            ws['A1'] = f"CLASS MARKS REPORT - {subject['name']} ({subject['code']})"
            ws['A1'].font = Font(bold=True, size=16)
            
            ws['A2'] = f"Course: {subject['course']}"
            ws['A3'] = f"Year: {subject['year']}, Semester: {subject['semester']}"
            
            if report_data['assessment_type']:
                ws['A4'] = f"Assessment Type: {report_data['assessment_type']}"
            
            # Statistics
            stats = report_data['statistics']
            ws['A6'] = "CLASS STATISTICS"
            ws['A6'].font = Font(bold=True)
            
            ws['A7'] = f"Total Students: {stats['total_students']}"
            ws['A8'] = f"Class Average: {stats['class_average']}%"
            ws['A9'] = f"Highest Score: {stats['highest_score']}%"
            ws['A10'] = f"Lowest Score: {stats['lowest_score']}%"
            ws['A11'] = f"Passing Students: {stats['passing_students']}"
            ws['A12'] = f"Failing Students: {stats['failing_students']}"
            
            # Student marks table
            headers = ['Roll Number', 'Student Name', 'Assessment Type', 'Marks Obtained', 
                      'Max Marks', 'Percentage', 'Grade', 'Status']
            ExcelExportService.style_header_row(ws, 14, headers)
            
            row = 15
            for student_data in report_data['student_marks']:
                student = student_data['student']
                for mark in student_data['marks']:
                    ws.cell(row=row, column=1, value=student.roll_number)
                    ws.cell(row=row, column=2, value=student.name)
                    ws.cell(row=row, column=3, value=mark['assessment_type'])
                    ws.cell(row=row, column=4, value=mark['marks_obtained'])
                    ws.cell(row=row, column=5, value=mark['max_marks'])
                    ws.cell(row=row, column=6, value=mark['percentage'])
                    ws.cell(row=row, column=7, value=mark['grade'])
                    ws.cell(row=row, column=8, value=mark['performance_status'])
                    row += 1
            
            ExcelExportService.auto_adjust_columns(ws)
            return wb
            
        except Exception as e:
            print(f"Error exporting class marks report: {e}")
            return None
    
    @staticmethod
    def export_class_attendance_report(report_data):
        """Export class attendance report to Excel"""
        try:
            wb = ExcelExportService.create_workbook()
            ws = wb.active
            ws.title = "Class Attendance Report"
            
            # Title and subject info
            subject = report_data['subject']
            ws['A1'] = f"CLASS ATTENDANCE REPORT - {subject['name']} ({subject['code']})"
            ws['A1'].font = Font(bold=True, size=16)
            
            ws['A2'] = f"Course: {subject['course']}"
            ws['A3'] = f"Year: {subject['year']}, Semester: {subject['semester']}"
            ws['A4'] = f"Month: {report_data['month']}/{report_data['year']}"
            
            # Statistics
            stats = report_data['statistics']
            ws['A6'] = "CLASS STATISTICS"
            ws['A6'].font = Font(bold=True)
            
            ws['A7'] = f"Total Students: {stats['total_students']}"
            ws['A8'] = f"Total Classes Conducted: {stats['total_classes_conducted']}"
            ws['A9'] = f"Class Average Attendance: {stats['class_average_attendance']}%"
            ws['A10'] = f"Students with Good Attendance (≥75%): {stats['students_with_good_attendance']}"
            ws['A11'] = f"Students with Poor Attendance (<50%): {stats['students_with_poor_attendance']}"
            
            # Student attendance table
            headers = ['Roll Number', 'Student Name', 'Total Classes', 'Present', 
                      'Absent', 'Attendance %', 'Status']
            ExcelExportService.style_header_row(ws, 13, headers)
            
            row = 14
            for student in report_data['student_attendance']:
                ws.cell(row=row, column=1, value=student['roll_number'])
                ws.cell(row=row, column=2, value=student['student_name'])
                ws.cell(row=row, column=3, value=student['total_classes'])
                ws.cell(row=row, column=4, value=student['present_classes'])
                ws.cell(row=row, column=5, value=student['absent_classes'])
                ws.cell(row=row, column=6, value=student['attendance_percentage'])
                ws.cell(row=row, column=7, value=student['status'])
                row += 1
            
            ExcelExportService.auto_adjust_columns(ws)
            return wb
            
        except Exception as e:
            print(f"Error exporting class attendance report: {e}")
            return None
    
    @staticmethod
    def export_course_overview_report(report_data):
        """Export course overview report to Excel"""
        try:
            wb = ExcelExportService.create_workbook()
            ws = wb.active
            ws.title = "Course Overview"
            
            # Title and course info
            course = report_data['course']
            ws['A1'] = f"COURSE OVERVIEW REPORT - {course['name']} ({course['code']})"
            ws['A1'].font = Font(bold=True, size=16)
            
            ws['A2'] = f"Duration: {course['duration_years']} years ({course['total_semesters']} semesters)"
            ws['A3'] = f"Total Students: {report_data['total_students']}"
            ws['A4'] = f"Total Subjects: {report_data['total_subjects']}"
            
            # Subject-wise report
            headers = ['Subject Code', 'Subject Name', 'Year', 'Semester', 'Enrolled Students',
                      'Total Assessments', 'Average Marks %', 'Passing Rate %', 'Average Attendance %']
            ExcelExportService.style_header_row(ws, 6, headers)
            
            row = 7
            for subject in report_data['subjects']:
                ws.cell(row=row, column=1, value=subject['subject_code'])
                ws.cell(row=row, column=2, value=subject['subject_name'])
                ws.cell(row=row, column=3, value=subject['year'])
                ws.cell(row=row, column=4, value=subject['semester'])
                ws.cell(row=row, column=5, value=subject['enrolled_students'])
                ws.cell(row=row, column=6, value=subject['marks_statistics']['total_assessments'])
                ws.cell(row=row, column=7, value=subject['marks_statistics']['average_marks'])
                ws.cell(row=row, column=8, value=subject['marks_statistics']['passing_rate'])
                ws.cell(row=row, column=9, value=subject['attendance_statistics']['average_attendance'])
                row += 1
            
            ExcelExportService.auto_adjust_columns(ws)
            return wb
            
        except Exception as e:
            print(f"Error exporting course overview report: {e}")
            return None
    
    @staticmethod
    def workbook_to_bytes(workbook):
        """Convert workbook to bytes for download"""
        try:
            output = BytesIO()
            workbook.save(output)
            output.seek(0)
            return output.getvalue()
        except Exception as e:
            print(f"Error converting workbook to bytes: {e}")
            return None