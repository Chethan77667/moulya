"""
Change the assigned faculty for a subject using faculty ID, course code, and subject code.

Safety:
- Does NOT delete any data.
- Only updates/creates SubjectAssignment rows and toggles is_active flags.
- Shows a dry-run summary first, then requires typing APPLY to commit.

Usage:
  python scripts/change_subject_faculty.py --faculty-id <LECTURER_ID> --course-code <COURSE_CODE> --subject-code <SUBJECT_CODE> [--year 2025]

Example:
  python scripts/change_subject_faculty.py --faculty-id LECT123 --course-code BCOM --subject-code BCMKALS302 --year 2025
"""

import argparse
import os
import sys
from datetime import datetime

# Ensure project root is importable when running from scripts/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from database import db
from models.academic import Subject, Course
from models.assignments import SubjectAssignment
from models.user import Lecturer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Change subject's assigned faculty (safe, confirmation required)")
    parser.add_argument('--faculty-id', required=True, help='Lecturer ID (e.g., EMP123)')
    parser.add_argument('--course-code', required=True, help='Course code (e.g., BCOM, BCA)')
    parser.add_argument('--subject-code', required=True, help='Subject code (e.g., BCMKALS302)')
    parser.add_argument('--year', type=int, default=datetime.now().year, help='Academic year to apply (default: current year)')
    return parser.parse_args()


def summarize(subject: Subject, lecturer: Lecturer, year: int):
    print("\n=== DRY RUN SUMMARY ===")
    course_name = subject.course.name if subject.course else 'N/A'
    print(f"Subject: [{subject.code}] {subject.name}")
    print(f"Class:   {course_name}")
    print(f"Target Year: {year}")
    print(f"New Faculty: {lecturer.name} (lecturer_id={lecturer.lecturer_id})")

    existing = (SubjectAssignment.query
                .filter_by(subject_id=subject.id, academic_year=year)
                .order_by(SubjectAssignment.assigned_at.desc())
                .all())
    if not existing:
        print("Current Assignments (this year): none")
    else:
        print("Current Assignments (this year):")
        for a in existing:
            lec_name = a.lecturer.name if a.lecturer else 'Unknown'
            print(f"  - id={a.id} lecturer='{lec_name}' active={a.is_active} assigned_at={a.assigned_at}")

    print("\nPlanned Changes:")
    # If an assignment already exists for this lecturer+subject+year, we'll activate it.
    existing_target = SubjectAssignment.query.filter_by(
        lecturer_id=lecturer.id, subject_id=subject.id, academic_year=year
    ).first()
    if existing_target:
        print(f"  - Activate existing assignment id={existing_target.id} for {lecturer.name}")
    else:
        print("  - Create new assignment row for target lecturer")

    # All other assignments for this subject/year will be deactivated
    print("  - Deactivate any other assignments for this subject in the target year")


def apply_change(subject: Subject, lecturer: Lecturer, year: int):
    # 1) Ensure target assignment exists and is active
    assignment = SubjectAssignment.query.filter_by(
        lecturer_id=lecturer.id, subject_id=subject.id, academic_year=year
    ).first()
    if assignment:
        if not assignment.is_active:
            assignment.is_active = True
    else:
        assignment = SubjectAssignment(
            lecturer_id=lecturer.id,
            subject_id=subject.id,
            academic_year=year,
            assigned_at=datetime.utcnow(),
            is_active=True
        )
        db.session.add(assignment)

    # 2) Deactivate other assignments for this subject/year
    others = (SubjectAssignment.query
              .filter(SubjectAssignment.subject_id == subject.id,
                      SubjectAssignment.academic_year == year,
                      SubjectAssignment.id != assignment.id)
              .all())
    for a in others:
        if a.is_active:
            a.is_active = False


def main():
    args = parse_args()
    app = create_app()
    with app.app_context():
        # Locate entities
        course = Course.query.filter_by(code=args.course_code).first()
        if not course:
            print(f"ERROR: Course with code '{args.course_code}' not found.")
            return

        subject = Subject.query.filter_by(code=args.subject_code, course_id=course.id).first()
        if not subject:
            print(f"ERROR: Subject with code '{args.subject_code}' under course '{args.course_code}' not found.")
            return

        lecturer = Lecturer.query.filter_by(lecturer_id=args.faculty_id, is_active=True).first()
        if not lecturer:
            print(f"ERROR: Active Lecturer with lecturer_id '{args.faculty_id}' not found.")
            return

        summarize(subject, lecturer, args.year)

        # Confirmation prompt
        print("\nType 'APPLY' to commit changes, or press Enter to cancel.")
        confirmation = input('> ').strip()
        if confirmation != 'APPLY':
            print('Cancelled. No changes were made.')
            db.session.rollback()
            return

        # Apply inside a transaction
        try:
            apply_change(subject, lecturer, args.year)
            db.session.commit()
            print('Changes applied successfully.')

            # Post-commit verification summary
            # Re-fetch lecturer and list assigned subjects for current year
            current_year = datetime.now().year
            refreshed_lecturer = Lecturer.query.get(lecturer.id)
            assigned_subjects = refreshed_lecturer.get_assigned_subjects() if refreshed_lecturer else []
            names = [f"[{s.code}] {s.name}" for s in assigned_subjects]
            print("\nVerification (current year):")
            print(f"  Assigned subjects count: {len(assigned_subjects)}")
            if names:
                for n in names:
                    print(f"   - {n}")
            in_list = any(s.id == subject.id for s in assigned_subjects)
            print(f"\n  Contains target subject {subject.code}: {'YES' if in_list else 'NO'}")
        except Exception as e:
            db.session.rollback()
            print(f'ERROR: Failed to apply changes: {e}')


if __name__ == '__main__':
    main()


