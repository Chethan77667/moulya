#!/usr/bin/env python3
"""
Probe monthly attendance retrieval using the same logic as lecturer reports.
Run:
  python debug_monthly_attendance_probe.py --roll BCA25001 --subject 80
"""
import argparse
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join('..', 'instance', 'moulya_college.db')

def fetch_student_id(conn, roll):
    cur = conn.execute('SELECT id, name FROM student WHERE roll_number = ?', (roll.upper().strip(),))
    row = cur.fetchone()
    return (row[0], row[1]) if row else (None, None)

def fetch_enrollment_subjects(conn, student_id):
    cur = conn.execute('''
        SELECT s.id, s.name, s.code
        FROM subject s
        JOIN student_enrollment se ON s.id = se.subject_id
        WHERE se.student_id = ? AND se.is_active = 1
    ''', (student_id,))
    return cur.fetchall()

def fetch_monthly_for_subject(conn, student_id, subject_id):
    cur = conn.execute('''
        SELECT msa.month, msa.year,
               COALESCE(SUM(msa.present_count), 0) AS present,
               COALESCE(SUM(msa.deputation_count), 0) AS deputation,
               COALESCE(SUM(mas.total_classes), 0) AS total
        FROM monthly_student_attendance msa
        JOIN monthly_attendance_summary mas
          ON mas.subject_id = msa.subject_id
         AND mas.month = msa.month
         AND mas.year = msa.year
        WHERE msa.student_id = ? AND msa.subject_id = ?
        GROUP BY msa.year, msa.month
        ORDER BY msa.year DESC, msa.month DESC
    ''', (student_id, subject_id))
    return cur.fetchall()

def fetch_monthly_overall(conn, student_id):
    cur = conn.execute('''
        SELECT msa.month, msa.year,
               COALESCE(SUM(msa.present_count), 0) AS present,
               COALESCE(SUM(msa.deputation_count), 0) AS deputation,
               COALESCE(SUM(mas.total_classes), 0) AS total
        FROM monthly_student_attendance msa
        JOIN monthly_attendance_summary mas
          ON mas.subject_id = msa.subject_id
         AND mas.month = msa.month
         AND mas.year = msa.year
        WHERE msa.student_id = ?
        GROUP BY msa.year, msa.month
        ORDER BY msa.year DESC, msa.month DESC
    ''', (student_id,))
    return cur.fetchall()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--roll', required=True, help='Student roll number')
    ap.add_argument('--subject', type=int, help='Subject id (optional)')
    args = ap.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"DB not found: {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)

    student_id, student_name = fetch_student_id(conn, args.roll)
    if not student_id:
        print(f"Student not found for roll {args.roll}")
        return 1

    print(f"Student: {student_name} ({args.roll}) id={student_id}")

    if args.subject:
        print(f"\n=== Monthly (Subject {args.subject}) ===")
        rows = fetch_monthly_for_subject(conn, student_id, args.subject)
    else:
        print(f"\n=== Monthly (All Subjects) ===")
        rows = fetch_monthly_overall(conn, student_id)

    total_all = 0
    present_all = 0
    deput_all = 0

    for month, year, present, deputation, total in rows:
        present_with_deputation = (present or 0) + (deputation or 0)
        pct = (present_with_deputation / total * 100) if total else 0
        label = datetime(int(year), int(month), 1).strftime('%B %Y')
        print(f"  - {label}: present={present} deputation={deputation} total={total} => {present_with_deputation}/{total} ({pct:.2f}%)")
        total_all += total or 0
        present_all += present or 0
        deput_all += deputation or 0

    print("\n=== Overall ===")
    present_with_deputation_all = present_all + deput_all
    pct_all = (present_with_deputation_all / total_all * 100) if total_all else 0
    print(f"Total={total_all} Present={present_all} Deputation={deput_all} => {present_with_deputation_all}/{total_all} ({pct_all:.2f}%)")

    # Show enrollment subjects for quick validation
    subs = fetch_enrollment_subjects(conn, student_id)
    if subs:
        print("\nEnrolled Subjects:")
        for sid, sname, scode in subs:
            print(f"  - {sid}: {sname} ({scode})")

    conn.close()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
