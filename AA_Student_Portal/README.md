# Student Portal - Flask Application

A modern, responsive student portal built with Flask for managing academic information, attendance, marks, and assignments.

## Features

- **Dashboard**: Overview of academic performance and recent activity
- **Attendance Tracking**: View attendance records and statistics
- **Marks Management**: Track academic performance and grades
- **Assignment Management**: View and submit assignments
- **Profile Management**: Student profile information
- **Responsive Design**: Mobile-friendly interface using Bootstrap 5

## Project Structure

```
AA_Student_Portal/
├── app.py                 # Main Flask application
├── run.py                 # Application runner
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Home page
│   ├── login.html        # Login page
│   ├── dashboard.html    # Student dashboard
│   ├── profile.html      # Student profile
│   ├── attendance.html   # Attendance records
│   ├── marks.html        # Academic marks
│   └── assignments.html  # Assignment management
└── static/               # Static files
    ├── css/
    │   └── style.css     # Custom styles
    └── js/
        └── main.js       # JavaScript functionality
```

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd AA_Student_Portal
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Start the Flask application:**
   ```bash
   python run.py
   ```
   Or alternatively:
   ```bash
   python app.py
   ```

2. **Access the application:**
   - Open your web browser
   - Navigate to `http://localhost:5001`

## Configuration

- **Port**: The application runs on port 5001 by default
- **Debug Mode**: Enabled by default for development
- **Secret Key**: Change the secret key in `app.py` for production use

## Technologies Used

- **Backend**: Flask (Python web framework)
- **Frontend**: HTML5, CSS3, JavaScript
- **UI Framework**: Bootstrap 5
- **Icons**: Font Awesome
- **Styling**: Custom CSS with modern design principles

## Features Overview

### Dashboard
- Academic performance summary
- Recent activity feed
- Upcoming events and deadlines
- Quick access to all modules

### Attendance
- Overall attendance percentage
- Subject-wise attendance breakdown
- Visual attendance statistics
- Attendance history

### Marks
- Current CGPA display
- Subject-wise performance
- Grade breakdown
- Academic progress tracking

### Assignments
- Pending assignments list
- Submission status tracking
- Due date monitoring
- Assignment history

### Profile
- Personal information display
- Academic details
- Contact information
- Profile management

## Development

### Adding New Features
1. Create new routes in `app.py`
2. Add corresponding templates in `templates/`
3. Update navigation in `base.html`
4. Add any required static files

### Customization
- Modify `static/css/style.css` for custom styling
- Update `static/js/main.js` for additional functionality
- Customize templates for specific requirements

## Production Deployment

1. **Set environment variables:**
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=your-secure-secret-key
   ```

2. **Disable debug mode:**
   ```python
   app.config['DEBUG'] = False
   ```

3. **Use a production WSGI server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5001 app:app
   ```

## License

This project is part of the Moulya College Management System.

## Support

For support and questions, please contact the development team.
