# Requirements Document

## Introduction

Moulya is a comprehensive college management system designed to streamline academic administration and lecturer operations. The system provides two distinct portals: a Management Portal for administrative tasks like managing lecturers, students, courses, and academic structure, and a Lecturer Portal for day-to-day teaching activities including attendance tracking, marks recording, and student reporting. Built with Flask backend, SQLite database, and a responsive black-and-white UI using Tailwind CSS, the system ensures efficient academic management while maintaining simplicity and usability.

## Requirements

### Requirement 1: Authentication System

**User Story:** As a system user, I want secure login functionality with role-based access, so that management and lecturers can access their respective portals safely.

#### Acceptance Criteria

1. WHEN a user accesses the system THEN the system SHALL present separate login options for Management and Lecturer roles
2. WHEN management credentials are entered THEN the system SHALL authenticate against management login and redirect to management portal
3. WHEN lecturer credentials are entered THEN the system SHALL authenticate against lecturer username/password and redirect to lecturer portal
4. WHEN invalid credentials are provided THEN the system SHALL display appropriate error messages and prevent access
5. WHEN a user is authenticated THEN the system SHALL maintain session state until logout or session expiry
6. WHEN a user attempts to access unauthorized areas THEN the system SHALL redirect to appropriate login page

### Requirement 2: Management Portal - Lecturer Management

**User Story:** As a management user, I want to add and manage lecturers individually or in bulk, so that I can efficiently maintain the teaching staff database.

#### Acceptance Criteria

1. WHEN management adds a lecturer individually THEN the system SHALL capture Lecturer ID, Name, and generate or accept manual username/password
2. WHEN management uploads bulk lecturer data THEN the system SHALL accept Excel or multiline text input and process multiple lecturer records
3. WHEN lecturer data is processed THEN the system SHALL validate unique Lecturer IDs and prevent duplicates
4. WHEN lecturer credentials are generated automatically THEN the system SHALL create secure username/password combinations
5. WHEN lecturer data is saved THEN the system SHALL store all information in the database and confirm successful creation
6. WHEN management views lecturers THEN the system SHALL display a list of all lecturers with their details

### Requirement 3: Management Portal - Student Management

**User Story:** As a management user, I want to add and manage students individually or in bulk, so that I can maintain accurate student enrollment records.

#### Acceptance Criteria

1. WHEN management adds a student individually THEN the system SHALL capture Roll Number, Name, and Course information
2. WHEN management uploads bulk student data THEN the system SHALL accept Excel or multiline text input and process multiple student records
3. WHEN student data is processed THEN the system SHALL validate unique Roll Numbers and prevent duplicates
4. WHEN student data is saved THEN the system SHALL store all information in the database and confirm successful creation
5. WHEN management views students THEN the system SHALL display a list of all students with their details and course information

### Requirement 4: Management Portal - Academic Structure Management

**User Story:** As a management user, I want to manage courses, subjects, academic years, and semesters, so that I can maintain the complete academic framework.

#### Acceptance Criteria

1. WHEN management creates a course THEN the system SHALL store 3-year course information with appropriate details
2. WHEN management adds subjects THEN the system SHALL map subjects to specific courses and semesters
3. WHEN management sets up academic years THEN the system SHALL handle 3-year duration with multiple semesters per year
4. WHEN management configures semesters THEN the system SHALL associate semesters with appropriate academic years and courses
5. WHEN academic structure is updated THEN the system SHALL maintain referential integrity across all related entities

### Requirement 5: Lecturer Portal - Subject and Student Management

**User Story:** As a lecturer, I want to view my assigned subjects and manage student enrollments, so that I can organize my teaching responsibilities effectively.

#### Acceptance Criteria

1. WHEN a lecturer logs in THEN the system SHALL display all subjects assigned to that lecturer
2. WHEN a lecturer selects a subject THEN the system SHALL show current student enrollments for that subject
3. WHEN a lecturer adds students to a subject THEN the system SHALL allow multiple student selection and enrollment
4. WHEN a lecturer removes students from a subject THEN the system SHALL allow multiple student deselection and unenrollment
5. WHEN student enrollments are modified THEN the system SHALL update the database and reflect changes immediately

### Requirement 6: Lecturer Portal - Attendance Management

**User Story:** As a lecturer, I want to record daily and monthly attendance for my subjects, so that I can track student participation accurately.

#### Acceptance Criteria

1. WHEN a lecturer records daily attendance THEN the system SHALL allow marking present/absent for each enrolled student
2. WHEN daily attendance is submitted THEN the system SHALL save attendance records with date and subject information
3. WHEN a lecturer records monthly attendance summary THEN the system SHALL capture total number of classes conducted in that month
4. WHEN monthly summary is saved THEN the system SHALL calculate attendance percentages based on daily records and total classes
5. WHEN attendance data is viewed THEN the system SHALL display both daily records and monthly summaries with calculated statistics

### Requirement 7: Lecturer Portal - Marks Management

**User Story:** As a lecturer, I want to record marks for different assessment categories, so that I can maintain comprehensive student evaluation records.

#### Acceptance Criteria

1. WHEN a lecturer adds marks for Internal 1 THEN the system SHALL record marks against maximum marks for that category
2. WHEN a lecturer adds marks for Internal 2 THEN the system SHALL record marks against maximum marks for that category
3. WHEN a lecturer adds marks for Assignments THEN the system SHALL record marks against maximum marks for that category
4. WHEN a lecturer adds marks for Projects THEN the system SHALL record marks against maximum marks for that category
5. WHEN maximum marks are set for each category THEN the system SHALL validate entered marks do not exceed maximum limits
6. WHEN marks are saved THEN the system SHALL store all assessment data with student and subject associations

### Requirement 8: Lecturer Portal - Student Reports

**User Story:** As a lecturer, I want to generate comprehensive reports showing student attendance and marks, so that I can identify students needing attention and provide academic guidance.

#### Acceptance Criteria

1. WHEN a lecturer generates attendance reports THEN the system SHALL show attendance shortages for each student with percentage calculations
2. WHEN a lecturer views marks overview THEN the system SHALL display all assessment categories with marks and deficiencies
3. WHEN reports are generated THEN the system SHALL highlight students with attendance below acceptable thresholds
4. WHEN marks deficiencies are shown THEN the system SHALL identify students with poor performance in specific assessment categories
5. WHEN reports are displayed THEN the system SHALL provide clear visual indicators for students requiring intervention

### Requirement 9: User Interface and Experience

**User Story:** As any system user, I want a clean, responsive, and intuitive interface, so that I can efficiently perform my tasks across different devices.

#### Acceptance Criteria

1. WHEN the system loads on any device THEN the interface SHALL be fully responsive and functional on desktop and mobile screens
2. WHEN users interact with the interface THEN the system SHALL use only black, white, and grayscale colors as per design requirements
3. WHEN users navigate between sections THEN the system SHALL provide clear navigation paths and maintain consistent layout
4. WHEN forms are submitted THEN the system SHALL provide immediate feedback and validation messages
5. WHEN errors occur THEN the system SHALL display user-friendly error messages with guidance for resolution
6. WHEN bulk operations are performed THEN the system SHALL provide clear instructions and feedback on processing status for Excel uploads

### Requirement 10: Data Integrity and Validation

**User Story:** As a system administrator, I want robust data validation and error handling, so that the system maintains data integrity and provides reliable operation.

#### Acceptance Criteria

1. WHEN duplicate Lecturer IDs are entered THEN the system SHALL prevent creation and display appropriate error messages
2. WHEN duplicate Roll Numbers are entered THEN the system SHALL prevent creation and display appropriate error messages
3. WHEN invalid data formats are submitted THEN the system SHALL validate input and provide specific error guidance
4. WHEN database operations fail THEN the system SHALL handle errors gracefully and maintain system stability
5. WHEN bulk data is processed THEN the system SHALL validate each record and report any failures with specific details