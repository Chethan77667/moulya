"""
Fix script: Adjust September monthly attendance when entered before August.

Problem context:
- Some lecturers entered cumulative attendance for September first (till Sep),
  then later entered August (till Aug). September's stored monthly delta should
  be reduced by August's delta so that September reflects only its own month.

What this script does for a specific subject (course_code + subject_code, year):
- For each lecturer who has August/September data for the subject/year:
  - Compute new September monthly total_classes as (existing September delta - August delta), clamped to [0, ∞)
  - For each enrolled student, compute new September present_count as
    (existing September present delta - August present delta), clamped to [0, ∞)
  - Recalculate September MonthlyAttendanceSummary.average_attendance

Usage:
    python scripts/fix_attendance_cumulative_order.py

The script will prompt for:
- Course code (e.g., CSE)
- Subject code (e.g., CS301)
- Year (optional; default = current calendar year)
- Dry run confirmation before applying changes

Notes:
- Only September (9) and August (8) for the selected year are adjusted.
- Deputation counts are left unchanged.
"""

import sys
import os
from datetime import datetime

# Ensure project root is on sys.path so `app` and other modules can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from database import db

from models.academic import Subject, Course
from models.attendance import MonthlyAttendanceSummary, MonthlyStudentAttendance
from models.student import StudentEnrollment, Student
from models.assignments import SubjectAssignment
from sqlalchemy import func


def prompt_input(prompt_text, allow_empty=False):
    try:
        val = input(prompt_text).strip()
    except EOFError:
        val = ""
    if not allow_empty and not val:
        print("Input required. Exiting.")
        sys.exit(1)
    return val


def find_subject(course_code: str, subject_code: str):
    course = Course.query.filter(func.lower(Course.code) == course_code.lower()).first()
    if not course:
        print(f"Course not found for code: {course_code}")
        return None
    subject = Subject.query.filter(
        Subject.course_id == course.id,
        func.lower(Subject.code) == subject_code.lower()
    ).first()
    if not subject:
        print(f"Subject not found in course {course_code} with code: {subject_code}")
        return None
    return subject


def get_enrolled_students(subject_id: int):
    enrollments = (StudentEnrollment.query
        .filter_by(subject_id=subject_id, is_active=True)
        .join(Student, Student.id == StudentEnrollment.student_id)
        .order_by(Student.roll_number.asc(), Student.name.asc())
        .all())
    return [e.student for e in enrollments]


def adjust_for_lecturer(subject_id: int, lecturer_id: int, year: int, dry_run: bool):
    AUG, SEP = 8, 9

    aug_summary = MonthlyAttendanceSummary.query.filter_by(
        subject_id=subject_id, lecturer_id=lecturer_id, month=AUG, year=year
    ).first()
    sep_summary = MonthlyAttendanceSummary.query.filter_by(
        subject_id=subject_id, lecturer_id=lecturer_id, month=SEP, year=year
    ).first()

    if not sep_summary:
        return { 'lecturer_id': lecturer_id, 'changed': False, 'reason': 'No September summary' }
    if not aug_summary:
        return { 'lecturer_id': lecturer_id, 'changed': False, 'reason': 'No August summary' }

    aug_delta = int(aug_summary.total_classes or 0)
    sep_delta_old = int(sep_summary.total_classes or 0)
    sep_delta_new = max(sep_delta_old - aug_delta, 0)

    # Per-student adjustments
    students = get_enrolled_students(subject_id)
    changes = []

    for s in students:
        msa_aug = MonthlyStudentAttendance.query.filter_by(
            student_id=s.id, subject_id=subject_id, lecturer_id=lecturer_id, month=AUG, year=year
        ).first()
        msa_sep = MonthlyStudentAttendance.query.filter_by(
            student_id=s.id, subject_id=subject_id, lecturer_id=lecturer_id, month=SEP, year=year
        ).first()

        aug_present = int(msa_aug.present_count if msa_aug else 0)
        sep_present_old = int(msa_sep.present_count if msa_sep else 0)
        sep_present_new = max(sep_present_old - aug_present, 0)

        if msa_sep is None:
            # If there is no September per-student record but we have a September summary,
            # skip; nothing to adjust for this student.
            continue

        changes.append({
            'student_id': s.id,
            'roll_number': s.roll_number,
            'sep_present_old': sep_present_old,
            'sep_present_new': sep_present_new
        })

        if not dry_run:
            msa_sep.present_count = sep_present_new

    if not dry_run:
        sep_summary.total_classes = sep_delta_new
        # Recalculate average strictly from updated records
        sep_summary.calculate_average_attendance()

    return {
        'lecturer_id': lecturer_id,
        'changed': True,
        'aug_delta': aug_delta,
        'sep_delta_old': sep_delta_old,
        'sep_delta_new': sep_delta_new,
        'student_changes': changes
    }


def compute_report_preview(subject_id: int, lecturer_id: int, year: int, result_snapshot: dict):
    """Produce a preview similar to the attendance report page, showing BEFORE vs AFTER
    cumulative totals and percentages for a few students, based on dry-run changes.

    - Uses current DB as BEFORE.
    - Applies virtual Sep adjustments from result_snapshot to compute AFTER (without writing).
    """
    from models.attendance import MonthlyAttendanceSummary as MAS, MonthlyStudentAttendance as MSA

    # BEFORE cumulative totals (year, per-lecturer)
    total_classes_before = int((db.session.query(func.coalesce(func.sum(MAS.total_classes), 0))
        .filter(MAS.subject_id == subject_id, MAS.lecturer_id == lecturer_id, MAS.year == year)
        .scalar() or 0))

    # AFTER cumulative totals adjust only September by delta change
    sep_old = int(result_snapshot.get('sep_delta_old') or 0)
    sep_new = int(result_snapshot.get('sep_delta_new') or 0)
    total_classes_after = total_classes_before - sep_old + sep_new

    # Build per-student BEFORE and AFTER present counts
    students = get_enrolled_students(subject_id)
    rows = []
    # Map student -> current year cumulative present
    for s in students:
        present_before = int((db.session.query(func.coalesce(func.sum(MSA.present_count), 0))
            .filter(MSA.student_id == s.id, MSA.subject_id == subject_id, MSA.lecturer_id == lecturer_id, MSA.year == year)
            .scalar() or 0))
        deputation_before = int((db.session.query(func.coalesce(func.sum(MSA.deputation_count), 0))
            .filter(MSA.student_id == s.id, MSA.subject_id == subject_id, MSA.lecturer_id == lecturer_id, MSA.year == year)
            .scalar() or 0))

        # September component before and after
        sep_msa = MSA.query.filter_by(student_id=s.id, subject_id=subject_id, lecturer_id=lecturer_id, month=9, year=year).first()
        sep_present_old = int(sep_msa.present_count) if sep_msa else 0

        # Find corresponding change (if any) for this student in the result snapshot
        after_sep_present = sep_present_old
        for ch in (result_snapshot.get('student_changes') or []):
            if ch['student_id'] == s.id:
                after_sep_present = int(ch['sep_present_new'])
                break

        present_after = present_before - sep_present_old + after_sep_present

        # Include deputation in report-style percentages to match UI
        present_before_with_dep = present_before + deputation_before
        present_after_with_dep = present_after + deputation_before

        pct_before = (present_before_with_dep / total_classes_before * 100) if total_classes_before > 0 else 0.0
        pct_after = (present_after_with_dep / total_classes_after * 100) if total_classes_after > 0 else 0.0

        rows.append({
            'roll': s.roll_number,
            'name': s.name,
            'present_before': present_before_with_dep,
            'present_after': present_after_with_dep,
            'total_before': total_classes_before,
            'total_after': total_classes_after,
            'pct_before': round(pct_before, 2),
            'pct_after': round(pct_after, 2)
        })

    return {
        'total_before': total_classes_before,
        'total_after': total_classes_after,
        'students': rows
    }


def compute_report_preview_combined(subject_id: int, year: int, result_snapshot_by_lect: dict):
    """Combined preview across all lecturers for the subject/year (matches management/report pages).
    Applies September adjustments from each lecturer's snapshot when available.
    """
    from models.attendance import MonthlyAttendanceSummary as MAS, MonthlyStudentAttendance as MSA

    # BEFORE cumulative totals across all lecturers
    total_classes_before = int((db.session.query(func.coalesce(func.sum(MAS.total_classes), 0))
        .filter(MAS.subject_id == subject_id, MAS.year == year)
        .scalar() or 0))

    # AFTER totals: replace Sep totals per lecturer if provided
    total_classes_after = total_classes_before
    # For each lecturer snapshot, adjust total by (sep_new - sep_old)
    for res in result_snapshot_by_lect.values():
        if res.get('changed'):
            total_classes_after += int(res.get('sep_delta_new', 0)) - int(res.get('sep_delta_old', 0))

    students = get_enrolled_students(subject_id)
    rows = []

    # For each student, sum presents and deputations across lecturers; apply Sep deltas per lecturer
    for s in students:
        # BEFORE cumulative presents across all lecturers
        present_before = int((db.session.query(func.coalesce(func.sum(MSA.present_count), 0))
            .filter(MSA.student_id == s.id, MSA.subject_id == subject_id, MSA.year == year)
            .scalar() or 0))
        deputation_before = int((db.session.query(func.coalesce(func.sum(MSA.deputation_count), 0))
            .filter(MSA.student_id == s.id, MSA.subject_id == subject_id, MSA.year == year)
            .scalar() or 0))

        # Adjustment: for each lecturer snapshot, adjust Sep present for this student
        sep_present_delta = 0
        for lid, res in result_snapshot_by_lect.items():
            if not res.get('changed'):
                continue
            # Current Sep present for this lecturer
            msa_sep = MSA.query.filter_by(student_id=s.id, subject_id=subject_id, lecturer_id=lid, month=9, year=year).first()
            sep_old = int(msa_sep.present_count) if msa_sep else 0
            sep_new = sep_old
            for ch in (res.get('student_changes') or []):
                if ch['student_id'] == s.id:
                    sep_new = int(ch['sep_present_new'])
                    break
            sep_present_delta += (sep_new - sep_old)

        present_after = present_before + sep_present_delta
        present_before_with_dep = present_before + deputation_before
        present_after_with_dep = present_after + deputation_before

        pct_before = (present_before_with_dep / total_classes_before * 100) if total_classes_before > 0 else 0.0
        pct_after = (present_after_with_dep / total_classes_after * 100) if total_classes_after > 0 else 0.0

        rows.append({
            'roll': s.roll_number,
            'name': s.name,
            'present_before': present_before_with_dep,
            'present_after': present_after_with_dep,
            'total_before': total_classes_before,
            'total_after': total_classes_after,
            'pct_before': round(pct_before, 2),
            'pct_after': round(pct_after, 2)
        })

    return {
        'total_before': total_classes_before,
        'total_after': total_classes_after,
        'students': rows
    }


def main():
    app = create_app()
    with app.app_context():
        print("\n=== Attendance Cumulative Order Fix (Aug->Sep) ===\n")
        course_code = prompt_input("Enter Course Code (e.g., CSE): ")
        subject_code = prompt_input("Enter Subject Code (e.g., CS301): ")
        year_str = prompt_input("Enter Year (default: current year): ", allow_empty=True)
        try:
            year = int(year_str) if year_str else datetime.now().year
        except Exception:
            print("Invalid year. Exiting.")
            return

        subject = find_subject(course_code, subject_code)
        if not subject:
            return

        # Identify lecturers who have Aug/Sep data on this subject/year
        lecturer_ids = set()
        for m in (8, 9):
            rows = MonthlyAttendanceSummary.query.with_entities(MonthlyAttendanceSummary.lecturer_id).filter_by(
                subject_id=subject.id, month=m, year=year
            ).all()
            for (lid,) in rows:
                if lid:
                    lecturer_ids.add(int(lid))

        if not lecturer_ids:
            print("No August/September summaries found for this subject/year. Nothing to do.")
            return

        print(f"Found lecturers with Aug/Sep data: {sorted(lecturer_ids)}")
        dry = prompt_input("Perform a dry run first? (y/N): ", allow_empty=True)
        dry_run = (dry.lower() == 'y')

        all_results = []
        for lid in lecturer_ids:
            result = adjust_for_lecturer(subject.id, lid, year, dry_run)
            all_results.append(result)

        # Print summary
        print("\n--- Proposed Changes ---" if dry_run else "\n--- Changes Applied ---")
        for res in all_results:
            if not res.get('changed'):
                print(f"Lecturer {res.get('lecturer_id')}: Skipped ({res.get('reason')})")
                continue
            print(f"Lecturer {res['lecturer_id']}: Sep total {res['sep_delta_old']} -> {res['sep_delta_new']} (Aug was {res['aug_delta']})")
            if res.get('student_changes'):
                sample = res['student_changes'][:5]
                for ch in sample:
                    print(f"  Student {ch['roll_number']}: Sep present {ch['sep_present_old']} -> {ch['sep_present_new']}")
                if len(res['student_changes']) > 5:
                    print(f"  ... and {len(res['student_changes']) - 5} more")

        # Report-style preview (BEFORE vs AFTER) for the first lecturer found
        print("\n=== Attendance Report Preview (BEFORE vs AFTER) ===")
        # Per-lecturer preview (first lecturer with changes)
        for res in all_results:
            if res.get('changed'):
                preview = compute_report_preview(subject.id, res['lecturer_id'], year, res)
                print(f"Per-lecturer (Lecturer {res['lecturer_id']}) totals: {preview['total_before']} -> {preview['total_after']}")
                for row in preview['students'][:10]:
                    print(f"  {row['roll']}: {row['present_before']}/{row['total_before']} ({row['pct_before']}%) -> "
                          f"{row['present_after']}/{row['total_after']} ({row['pct_after']}%)")
                break
        # Combined preview across all lecturers
        res_by_lect = {res['lecturer_id']: res for res in all_results if res.get('changed')}
        if res_by_lect:
            combined = compute_report_preview_combined(subject.id, year, res_by_lect)
            print(f"Combined totals (all lecturers): {combined['total_before']} -> {combined['total_after']}")
            for row in combined['students'][:10]:
                print(f"  {row['roll']}: {row['present_before']}/{row['total_before']} ({row['pct_before']}%) -> "
                      f"{row['present_after']}/{row['total_after']} ({row['pct_after']}%)")

        if dry_run:
            confirm = prompt_input("Apply these changes? (type APPLY to confirm): ", allow_empty=True)
            if confirm == 'APPLY':
                # Run real adjustments
                all_results = []
                for lid in lecturer_ids:
                    res2 = adjust_for_lecturer(subject.id, lid, year, dry_run=False)
                    all_results.append(res2)
                try:
                    db.session.commit()
                    print("Changes committed.")
                except Exception as e:
                    db.session.rollback()
                    print(f"Commit failed: {e}")
            else:
                print("No changes applied.")
                return
        else:
            try:
                db.session.commit()
                print("Changes committed.")
            except Exception as e:
                db.session.rollback()
                print(f"Commit failed: {e}")


if __name__ == '__main__':
    main()


