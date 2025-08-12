# Moulya College Management System

A comprehensive college management system built with Flask, SQLite, and Tailwind CSS. The system provides separate portals for management and lecturers to handle academic administration efficiently.

## Features

### Management Portal
- **Lecturer Management**: Add lecturers individually or via Excel bulk upload
- **Student Management**: Add students individually or via Excel bulk upload  
- **Course Management**: Create and manage 3-year academic courses
- **Subject Management**: Create subjects mapped to courses and semesters
- **Academic Year Management**: Set up academic years and semesters

### Lecturer Portal
- **Subject Management**: View assigned subjects and manage student enrollments
- **Attendance Management**: Record daily attendance and monthly summaries
- **Marks Management**: Record marks for Internal 1, Internal 2, Assignments, and Projects
- **Reporting**: Generate attendance shortage and marks deficiency reports

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, Tailwind CSS (black and white theme)
- **File Processing**: openpyxl for Excel file handling
- **Authentication**: Session-based with password hashing

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone or download the project files**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   python init_db.py
   ```

4. **Create sample data (optional)**
   ```bash
   python sample_data.py
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open your web browser and go to `http://localhost:5000`

## Default Login Credentials

### Management Portal
- **Username**: admin
- **Password**: admin123

### Lecturer Portal (if sample data is loaded)
- **Username**: john_lec001, **Password**: password123
- **Username**: sarah_lec002, **Password**: password123
- **Username**: michael_lec003, **Password**: password123
- **Username**: emily_lec004, **Password**: password123

## Usage Guide

### Management Portal

1. **Login** as management user
2. **Add Courses** before adding students or subjects
3. **Add Lecturers** individually or via Excel upload
4. **Add Students** individually or via Excel upload
5. **Create Subjects** and map them to courses/semesters
6. **Assign Subjects** to lecturers (done through subject assignments)

### Lecturer Portal

1. **Login** with lecturer credentials
2. **View Assigned Subjects** on the dashboard
3. **Manage Students** - add/remove students from subjects
4. **Record Attendance** - daily attendance and monthly summaries
5. **Enter Marks** - for different assessment categories
6. **Generate Reports** - attendance shortage and marks deficiency

## Excel Upload Format

### Lecturers Excel Format
| Column A | Column B | Column C | Column D | Column E |
|----------|----------|----------|----------|----------|
| Lecturer ID | Full Name | Email | Phone | Department |
| LEC001 | John Doe | john@college.edu | 1234567890 | Computer Science |

### Students Excel Format
| Column A | Column B | Column C | Column D | Column E | Column F |
|----------|----------|----------|----------|----------|----------|
| Roll Number | Full Name | Course Code | Academic Year | Email | Phone |
| CS001 | Alice Johnson | CSE | 1 | alice@student.edu | 9876543210 |

## Testing

Run the test suite:
```bash
python run_tests.py
```

## Project Structure

```
moulya/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── database.py           # Database configuration
├── init_db.py            # Database initialization script
├── sample_data.py        # Sample data generator
├── run_tests.py          # Test runner
├── requirements.txt      # Python dependencies
├── models/               # Database models
├── routes/               # Route handlers
├── services/             # Business logic
├── utils/                # Utility functions
├── templates/            # HTML templates
├── static/               # CSS and JavaScript files
└── tests/                # Test files
```

## Database Schema

The system uses SQLite with the following main entities:
- **Management**: Administrative users
- **Lecturer**: Teaching staff with login credentials
- **Course**: Academic programs (3-year duration)
- **Subject**: Course subjects mapped to semesters
- **Student**: Enrolled students with course information
- **AttendanceRecord**: Daily attendance tracking
- **StudentMarks**: Assessment marks for different categories
- **SubjectAssignment**: Lecturer-subject assignments

## Security Features

- Password hashing using Werkzeug
- Session-based authentication
- Role-based access control
- CSRF protection
- Input validation and sanitization
- SQL injection prevention through SQLAlchemy ORM

## Responsive Design

The application features a responsive black-and-white design that works on:
- Desktop computers
- Tablets
- Mobile phones

## Troubleshooting

### Common Issues

1. **Database errors**: Delete `moulya_college.db` and run `python init_db.py` again
2. **Import errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
3. **Port conflicts**: Change the port in `app.py` if 5000 is already in use

### Getting Help

1. Check the error messages in the terminal
2. Verify all dependencies are installed
3. Ensure Python 3.8+ is being used
4. Check file permissions for database creation

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Maintain the black-and-white UI theme
4. Update documentation for new features

## License

This project is created for educational purposes. Feel free to use and modify as needed.

## Support

For technical support or questions about the system, please refer to the code comments and documentation within the source files.