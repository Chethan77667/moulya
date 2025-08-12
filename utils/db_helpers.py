"""
Database helper utilities for Moulya College Management System
"""

from database import db, DatabaseError, handle_db_error
from sqlalchemy.exc import IntegrityError
from flask import flash

@handle_db_error
def safe_add_and_commit(obj):
    """Safely add object to database with error handling"""
    try:
        db.session.add(obj)
        db.session.commit()
        return True, "Record added successfully"
    except IntegrityError as e:
        db.session.rollback()
        if 'UNIQUE constraint failed' in str(e):
            return False, "Record with this identifier already exists"
        return False, "Database constraint violation"
    except Exception as e:
        db.session.rollback()
        return False, f"Database error: {str(e)}"

@handle_db_error
def safe_delete_and_commit(obj):
    """Safely delete object from database with error handling"""
    try:
        db.session.delete(obj)
        db.session.commit()
        return True, "Record deleted successfully"
    except Exception as e:
        db.session.rollback()
        return False, f"Database error: {str(e)}"

@handle_db_error
def safe_update_and_commit():
    """Safely commit database changes with error handling"""
    try:
        db.session.commit()
        return True, "Records updated successfully"
    except IntegrityError as e:
        db.session.rollback()
        if 'UNIQUE constraint failed' in str(e):
            return False, "Duplicate entry found"
        return False, "Database constraint violation"
    except Exception as e:
        db.session.rollback()
        return False, f"Database error: {str(e)}"

def paginate_query(query, page=1, per_page=20):
    """Paginate query results"""
    try:
        return query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    except Exception as e:
        flash(f"Error loading data: {str(e)}", 'error')
        return None

def get_or_404(model, **kwargs):
    """Get object or return 404 error"""
    try:
        return model.query.filter_by(**kwargs).first_or_404()
    except Exception as e:
        flash(f"Record not found: {str(e)}", 'error')
        return None

def bulk_insert(objects):
    """Bulk insert objects with error handling"""
    try:
        db.session.bulk_save_objects(objects)
        db.session.commit()
        return True, f"Successfully inserted {len(objects)} records"
    except IntegrityError as e:
        db.session.rollback()
        return False, f"Bulk insert failed: {str(e)}"
    except Exception as e:
        db.session.rollback()
        return False, f"Database error: {str(e)}"