"""
Utility script to refresh lecturer-subject assignments so reports show only
the currently assigned faculty per subject.

Behavior:
- For each subject, identify the most recent active assignment for the current
  academic year (if any). If none exists, fall back to the most recent active
  assignment across years; if none are active, fall back to the most recent
  assignment overall.
- Keep ONLY that single assignment record for the subject.
- Permanently delete all other SubjectAssignment rows for that subject to
  prevent them from appearing in reports that enumerate `subject.assignments`.

Run:
  python scripts/refresh_subject_faculty_assignments.py

Optional:
  Set DRY_RUN=1 to preview actions without making changes.
"""

import os
import sys
from datetime import datetime

# Ensure project root is importable when running from scripts/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from database import db
from models.academic import Subject
from models.assignments import SubjectAssignment


def choose_assignment_to_keep(assignments, current_year):
    """Choose a single assignment to keep for a subject.

    Preference order:
      1) Most recent active assignment for current_year
      2) Most recent active assignment (any year)
      3) Most recent assignment (any year, any status)
    """
    if not assignments:
        return None

    # 1) Active for current year
    current_year_active = [a for a in assignments if a.is_active and a.academic_year == current_year]
    if current_year_active:
        return sorted(current_year_active, key=lambda a: a.assigned_at or datetime.min, reverse=True)[0]

    # 2) Any active
    any_active = [a for a in assignments if a.is_active]
    if any_active:
        return sorted(any_active, key=lambda a: a.assigned_at or datetime.min, reverse=True)[0]

    # 3) Any assignment at all
    return sorted(assignments, key=lambda a: a.assigned_at or datetime.min, reverse=True)[0]


def refresh_assignments(dry_run: bool = False) -> None:
    now = datetime.now()
    current_year = now.year

    subjects = Subject.query.all()
    total_subjects = len(subjects)
    subjects_changed = 0
    total_deleted = 0

    for subject in subjects:
        # Load all assignments for this subject
        subject_assignments = (SubjectAssignment.query
                               .filter_by(subject_id=subject.id)
                               .order_by(SubjectAssignment.assigned_at.desc())
                               .all())

        if not subject_assignments:
            continue

        keep = choose_assignment_to_keep(subject_assignments, current_year)
        if not keep:
            continue

        to_delete = [a for a in subject_assignments if a.id != keep.id]
        if not to_delete:
            continue

        subjects_changed += 1

        keep_lecturer_name = getattr(keep.lecturer, 'name', 'Unknown')
        class_text = subject.course.name if getattr(subject, 'course', None) else 'N/A'
        print(f"Subject [{subject.code}] {subject.name} | Class: {class_text}: keeping lecturer '{keep_lecturer_name}' (id={keep.id}, year={keep.academic_year}, active={keep.is_active})")

        for a in to_delete:
            lec_name = getattr(a.lecturer, 'name', 'Unknown')
            print(f"  - Deleting extra assignment id={a.id} lecturer='{lec_name}' year={a.academic_year} active={a.is_active}")
            if not dry_run:
                db.session.delete(a)
        if not dry_run:
            db.session.commit()
        total_deleted += len(to_delete)

    print("\n=== Summary ===")
    print(f"Subjects scanned: {total_subjects}")
    print(f"Subjects updated: {subjects_changed}")
    print(f"Assignments deleted: {total_deleted}")
    if dry_run:
        print("(Dry Run) No changes were committed.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        dry_run_flag = os.getenv("DRY_RUN", "0") in ("1", "true", "True")
        refresh_assignments(dry_run=dry_run_flag)


