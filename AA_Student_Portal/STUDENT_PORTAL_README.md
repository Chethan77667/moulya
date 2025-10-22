# Student Portal - Moulya College

A modern, secure student portal for Moulya College that allows students to access their academic information using roll number and date of birth authentication.

## Features

- **Secure Authentication**: Login using roll number and date of birth
- **MongoDB Integration**: Student credentials stored in MongoDB
- **Premium UI Design**: Modern, responsive design with Tailwind CSS
- **Session Management**: Secure session handling
- **Dashboard**: Comprehensive student dashboard with quick stats
- **Navigation**: Easy access to profile, attendance, marks, and assignments

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: MongoDB
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Authentication**: Custom MongoDB-based authentication

## File Structure

```
AA_Student_Portal/
├── app.py                          # Main Flask application
├── run.py                          # Application runner
├── requirements.txt                # Python dependencies
├── config/
│   ├── __init__.py
│   └── database.py                 # MongoDB configuration
├── services/
│   ├── __init__.py
│   └── auth_service.py             # Authentication service
├── templates/
│   ├── base.html                   # Base template
│   ├── index.html                  # Home page
│   ├── login.html                  # Student login page
│   ├── dashboard.html              # Student dashboard
│   ├── profile.html                # Student profile
│   ├── attendance.html             # Attendance view
│   ├── marks.html                  # Marks view
│   └── assignments.html            # Assignments view
└── static/
    ├── css/
    │   └── style.css               # Custom styles
    └── js/
        └── main.js                 # JavaScript functionality
```

## Installation & Setup

### Prerequisites

1. **Python 3.7+**
2. **MongoDB** (local or cloud)
3. **Student data migrated** to MongoDB (use the migration script)

### Installation Steps

1. **Install Dependencies**:
   ```bash
   cd AA_Student_Portal
   pip install -r requirements.txt
   ```

2. **Configure MongoDB**:
   - Ensure MongoDB is running
   - Update connection string in `config/database.py` if needed
   - Default: `mongodb://localhost:27017/`

3. **Run the Application**:
   ```bash
   python run.py
   ```

4. **Access the Portal**:
   - Open browser and go to `http://localhost:5000`

## Authentication System

### Student Login Process

1. **Username**: Student's roll number (e.g., BCA25001)
2. **Password**: Student's date of birth (e.g., 123456 or DD-MM-YYYY)
3. **Validation**: Credentials checked against MongoDB collection
4. **Session**: Successful login creates secure session

### MongoDB Collection Structure

```json
{
  "_id": "BCA25001",
  "roll_number": "BCA25001",
  "date_of_birth": 123456,
  "migrated_at": "2025-10-19T14:04:53.736207",
  "source_database": "sqlite_moulya_college"
}
```

## Usage

### For Students

1. **Access Portal**: Go to the student portal homepage
2. **Login**: Enter roll number and date of birth
3. **Dashboard**: View academic overview and quick stats
4. **Navigation**: Access different sections:
   - Profile: Personal information
   - Attendance: Attendance records
   - Marks: Academic performance
   - Assignments: Assignment details

### For Administrators

1. **Data Migration**: Use the migration script to transfer student data
2. **MongoDB Management**: Manage student credentials in MongoDB
3. **User Support**: Help students with login issues

## Security Features

- **Input Validation**: All inputs are validated and sanitized
- **Session Security**: Secure session management
- **Error Handling**: Comprehensive error handling
- **Authentication**: MongoDB-based authentication
- **CSRF Protection**: Built-in CSRF protection

## Configuration

### Environment Variables

Create a `.env` file (optional):
```env
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=moulya
MONGODB_COLLECTION=login_credentials
SECRET_KEY=your-secret-key-here
```

### MongoDB Configuration

Update `config/database.py` for custom MongoDB settings:
```python
mongodb_uri = "mongodb://username:password@host:port/"
database_name = "your_database"
collection_name = "your_collection"
```

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**:
   - Ensure MongoDB is running
   - Check connection string
   - Verify network connectivity

2. **Login Not Working**:
   - Verify student data is migrated to MongoDB
   - Check roll number and date of birth format
   - Ensure MongoDB collection exists

3. **Session Issues**:
   - Clear browser cookies
   - Restart the application
   - Check secret key configuration

### Support

For technical support:
- Check MongoDB logs
- Verify application logs
- Contact system administrator

## Development

### Adding New Features

1. **New Routes**: Add to `app.py`
2. **New Services**: Add to `services/` directory
3. **New Templates**: Add to `templates/` directory
4. **New Styles**: Add to `static/css/`

### Database Schema Changes

1. Update MongoDB collection structure
2. Update authentication service
3. Update migration script
4. Test with sample data

## License

© 2025 Moulya College. All rights reserved.

## Contact

For questions or support, contact the administration office.
