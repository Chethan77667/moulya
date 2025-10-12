"""
Reset attendance data for a specific month (all subjects, all lecturers).

This script deletes:
  - Daily records in AttendanceRecord for the month
  - Per-student monthly counts in MonthlyStudentAttendance for the month
  - Per-subject monthly summaries in MonthlyAttendanceSummary for the month

Usage (interactive):
  python scripts/reset_month_attendance.py

Usage (non-interactive):
  python scripts/reset_month_attendance.py --month 3 --year 2025 --yes
  python scripts/reset_month_attendance.py --month 3 --year 2025 --dry-run
"""

import sys
import os
import calendar
import argparse
from datetime import datetime

# Ensure project root is on sys.path when running as a script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from database import db
from models.attendance import AttendanceRecord, MonthlyStudentAttendance, MonthlyAttendanceSummary


def prompt_month_year(cli_month: int | None, cli_year: int | None, auto_yes: bool, dry_run: bool):
    now = datetime.now()
    # Prefer CLI inputs if provided
    if cli_month is not None:
        month = int(cli_month)
        if month < 1 or month > 12:
            raise SystemExit("--month must be between 1 and 12")
    else:
        while True:
            try:
                month_input = input("Enter month number to reset (1-12): ").strip()
                month = int(month_input)
                if 1 <= month <= 12:
                    break
                print("Invalid month. Please enter a number between 1 and 12.")
            except EOFError:
                raise SystemExit("No input available. Re-run with --month and --year.")
            except Exception:
                print("Invalid month. Please enter a number between 1 and 12.")

    if cli_year is not None:
        year = int(cli_year)
    else:
        year_default = now.year
        try:
            year_text = input(f"Enter year (default {year_default}): ").strip()
        except EOFError:
            raise SystemExit("No input available. Re-run with --month and --year.")
        year = int(year_text) if year_text else year_default

    month_name = calendar.month_name[month]
    if not dry_run:
        print(f"You are about to RESET attendance data for {month_name} {year}.")
    if not auto_yes and not dry_run:
        try:
            confirm = input("Type 'RESET' to confirm: ").strip()
        except EOFError:
            raise SystemExit("No input available. Re-run with --yes for non-interactive usage.")
        if confirm != 'RESET':
            print("Cancelled. No changes made.")
            sys.exit(0)

    return month, year


def reset_month(month: int, year: int, dry_run: bool = False):
    # Count records for visibility
    ar_q = (AttendanceRecord.query
        .filter(db.extract('month', AttendanceRecord.date) == month,
                db.extract('year', AttendanceRecord.date) == year))
    msa_q = MonthlyStudentAttendance.query.filter_by(month=month, year=year)
    mas_q = MonthlyAttendanceSummary.query.filter_by(month=month, year=year)

    ar_count = ar_q.count()
    msa_count = msa_q.count()
    mas_count = mas_q.count()

    if dry_run:
        deleted_ar = 0
        deleted_msa = 0
        deleted_mas = 0
    else:
        # Delete in an order that avoids any potential dependencies
        deleted_ar = ar_q.delete(synchronize_session=False)
        deleted_msa = msa_q.delete(synchronize_session=False)
        deleted_mas = mas_q.delete(synchronize_session=False)
        db.session.commit()

    return deleted_ar, deleted_msa, deleted_mas, ar_count, msa_count, mas_count


def main():
    parser = argparse.ArgumentParser(description="Reset monthly attendance data")
    parser.add_argument("--month", type=int, help="Month number (1-12)")
    parser.add_argument("--year", type=int, help="Year (e.g., 2025)")
    parser.add_argument("--yes", action="store_true", help="Do not prompt for confirmation")
    parser.add_argument("--dry-run", action="store_true", help="Show counts; do not delete")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        month, year = prompt_month_year(args.month, args.year, args.yes, args.dry_run)
        month_name = calendar.month_name[month]
        deleted_ar, deleted_msa, deleted_mas, ar_count, msa_count, mas_count = reset_month(month, year, dry_run=args.dry_run)

        print("\nDRY RUN" if args.dry_run else "\nReset complete.")
        print(f"Month: {month_name} {year}")
        print(f"AttendanceRecord: {deleted_ar}/{ar_count} deleted")
        print(f"MonthlyStudentAttendance: {deleted_msa}/{msa_count} deleted")
        print(f"MonthlyAttendanceSummary: {deleted_mas}/{mas_count} deleted")
        print("\nNote: Reports in admin/lecturer views compute from these tables, so the change is immediate.")


if __name__ == '__main__':
    main()


