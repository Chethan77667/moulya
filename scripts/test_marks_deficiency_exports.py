from collections import namedtuple
import os, sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from app import create_app
from services.reporting_service import ReportingService
from services.excel_export_service import ExcelExportService
from io import BytesIO
import openpyxl


def build_sample_data():
    Course = namedtuple('Course', ['name'])
    Subject = namedtuple('Subject', ['name', 'code', 'course'])
    Student = namedtuple('Student', ['name', 'roll_number'])

    subj = Subject(name='Design and analysis of algorithm Theory', code='BCACACN501', course=Course(name='III BCA B'))
    students = [
        {
            'student': Student(name='Alice', roll_number='BCA23001'),
            'overall_percentage': 58.0,
            'marks_summary': {
                'internal1': {'obtained': 18, 'max': 40},
                'internal2': {'obtained': 0, 'max': 0},
                'assignment': {'obtained': 9, 'max': 10},
                'project': {'obtained': None, 'max': None},
            }
        },
        {
            'student': Student(name='Bob', roll_number='BCA23002'),
            'overall_percentage': 45,
            'marks_summary': {
                'internal1': {'obtained': 20, 'max': 40},
                'internal2': {'obtained': 25, 'max': 40},
                'assignment': {'obtained': 0, 'max': 0},
                'project': {'obtained': None, 'max': None},
            }
        },
    ]
    deficiency_data = [{'subject': subj, 'deficient_students': students}]
    return deficiency_data


def headers_from_excel_bytes(xlsx_bytes: bytes):
    wb = openpyxl.load_workbook(filename=BytesIO(xlsx_bytes))
    ws = wb.active
    # Find the last styled header row by searching for the first row that matches our header labels
    # We know they start with 'Student' and 'Roll Number'
    headers = None
    for row in ws.iter_rows(min_row=1, max_row=20):
        values = [c.value for c in row if c.value is not None]
        if values[:2] == ['Student', 'Roll Number']:
            headers = values
    return headers


def main():
    app = create_app()
    with app.app_context():
        data = build_sample_data()
        threshold = 60
        # PDF
        pdf_bytes = ReportingService.generate_marks_deficiency_pdf(threshold, data, lecturer_name='Test Lecturer')
        assert pdf_bytes and len(pdf_bytes) > 1000, 'PDF generation failed or too small'
        with open('test_marks_deficiency.pdf', 'wb') as f:
            f.write(pdf_bytes)
        # Excel
        xlsx_bytes = ExcelExportService.export_marks_deficiency(threshold, data, lecturer_name='Test Lecturer')
        assert xlsx_bytes and len(xlsx_bytes) > 1000, 'Excel generation failed or too small'
        with open('test_marks_deficiency.xlsx', 'wb') as f:
            f.write(xlsx_bytes)
        headers = headers_from_excel_bytes(xlsx_bytes)
        print('Detected headers:', headers)


if __name__ == '__main__':
    main()


