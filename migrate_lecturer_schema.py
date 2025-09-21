"""
Database migration script to remove course_id from lecturer table
Run this script to update the database schema after changing lecturer assignment from courses to subjects
"""

from database import db
from app import create_app

def migrate_lecturer_course_assignment():
    """Migrate lecturer assignments from courses to subjects"""

    app = create_app()

    with app.app_context():
        try:
            # Get database connection
            connection = db.engine.connect()

            # Check if course_id column exists
            result = connection.execute(db.text("PRAGMA table_info(lecturer)"))
            columns = [row[1] for row in result.fetchall()]

            if 'course_id' in columns:
                print("Removing course_id column from lecturer table...")

                # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
                # First, backup existing data
                print("Backing up existing lecturer data...")
                lecturers_data = connection.execute(db.text("""
                    SELECT id, lecturer_id, name, username, password_hash,
                           password_encrypted, email, created_at, last_login, is_active
                    FROM lecturer
                """)).fetchall()

                # Drop and recreate table without course_id
                print("Recreating lecturer table without course_id...")
                connection.execute(db.text("DROP TABLE lecturer"))

                # Recreate table (this will use the new model definition)
                db.create_all()

                # Restore data
                print("Restoring lecturer data...")
                for lecturer in lecturers_data:
                    connection.execute(db.text("""
                        INSERT INTO lecturer (id, lecturer_id, name, username, password_hash,
                                           password_encrypted, email, created_at, last_login, is_active)
                        VALUES (:id, :lecturer_id, :name, :username, :password_hash,
                               :password_encrypted, :email, :created_at, :last_login, :is_active)
                    """), {
                        'id': lecturer[0],
                        'lecturer_id': lecturer[1],
                        'name': lecturer[2],
                        'username': lecturer[3],
                        'password_hash': lecturer[4],
                        'password_encrypted': lecturer[5],
                        'email': lecturer[6],
                        'created_at': lecturer[7],
                        'last_login': lecturer[8],
                        'is_active': lecturer[9]
                    })

                print("Migration completed successfully!")
                print("Note: You may need to manually assign lecturers to subjects using the management interface.")

            else:
                print("course_id column not found - migration may already be applied.")

            connection.close()

        except Exception as e:
            print(f"Migration failed: {str(e)}")
            print("Please backup your database before running this script.")
            return False

    return True

if __name__ == "__main__":
    print("Starting database migration...")
    print("WARNING: This will modify your database structure.")
    print("Make sure to backup your database before proceeding.")
    print()

    confirm = input("Do you want to continue? (yes/no): ")
    if confirm.lower() == 'yes':
        if migrate_lecturer_course_assignment():
            print("Migration completed successfully!")
        else:
            print("Migration failed!")
    else:
        print("Migration cancelled.")