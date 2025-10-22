# Student Portal Integration with Main Moulya Database

## Overview

The Student Portal has been redesigned to match the lecturer portal design and integrated with the main Moulya College Management System database. Students can now view their enrolled subjects as individual cards with attendance and marks information.

## Key Features

### 1. Dashboard Design
- **Lecturer-style Layout**: Matches the lecturer portal design with clean navigation and card-based layout
- **Subject Cards**: Each enrolled subject (Kannada, English, etc.) gets its own individual card
- **Real-time Data**: Fetches live data from the main Moulya admin database

### 2. Subject Cards
Each subject card displays:
- Subject name and code
- Year and semester information
- Course name
- Attendance percentage (color-coded: green ≥75%, yellow ≥60%, red <60%)
- Marks summary (Internal 1, Internal 2, Assignment, Project)
- Quick action buttons for Attendance and Marks

### 3. Data Integration
- **Main Database**: Connects to the main Moulya SQLite database
- **Student Authentication**: Uses MongoDB for login credentials
- **Real-time Sync**: Fetches current enrollment, attendance, and marks data

## Files Modified/Created

### New Files
- `services/student_service.py` - Service to fetch data from main database
- `test_integration.py` - Test script to verify integration
- `INTEGRATION_README.md` - This documentation

### Modified Files
- `app.py` - Updated routes to fetch data from main database
- `templates/dashboard.html` - Complete redesign to match lecturer portal

## Database Structure

The integration uses two databases:

1. **MongoDB** (Student Portal): Stores login credentials
   - Collection: `login_credentials`
   - Fields: `roll_number`, `date_of_birth`, `migrated_at`, `source_database`

2. **SQLite** (Main Moulya): Stores academic data
   - Tables: `student`, `subject`, `course`, `student_enrollment`, `attendance_record`, `student_marks`

## How It Works

1. **Student Login**: Student authenticates using roll number and date of birth (MongoDB)
2. **Data Fetching**: System fetches student data from main Moulya database using roll number
3. **Subject Cards**: Creates individual cards for each enrolled subject
4. **Real-time Updates**: Data is fetched fresh on each page load

## Testing

Run the integration test:

```bash
cd AA_Student_Portal
python test_integration.py
```

## Running the Student Portal

```bash
cd AA_Student_Portal
python app.py
```

The portal will be available at `http://localhost:5000`

## Features by Page

### Dashboard
- Overview statistics (enrolled subjects count, overall attendance)
- Individual subject cards with attendance and marks
- Recent activity feed

### Subject Cards
- **Kannada Subject**: Individual card with attendance and marks
- **English Subject**: Individual card with attendance and marks
- **Other Subjects**: Each enrolled subject gets its own card

### Navigation
- Mobile-responsive header
- Profile and logout options
- Clean, modern design matching lecturer portal

## Error Handling

The system gracefully handles:
- Database connection failures
- Missing student data
- Empty enrollment records
- Network timeouts

If the main database is unavailable, the portal will still work with basic functionality and show appropriate warning messages.

## Future Enhancements

- Add more detailed subject information
- Implement assignment tracking
- Add grade calculation features
- Include semester-wise progress tracking
