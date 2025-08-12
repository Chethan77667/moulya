#!/usr/bin/env python3
"""
Database initialization script for Moulya College Management System
Run this script to set up the database with initial data
"""

from app import create_app
from database import init_db, reset_database
import sys

def main():
    """Main function to initialize database"""
    app = create_app()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        print("WARNING: This will delete all existing data!")
        confirm = input("Are you sure you want to reset the database? (yes/no): ")
        if confirm.lower() == 'yes':
            reset_database(app)
        else:
            print("Database reset cancelled.")
    else:
        init_db(app)

if __name__ == '__main__':
    main()