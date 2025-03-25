# School Management Platform Specification

## 1. Project Overview

### 1.1 Purpose
A digital platform for specialized training and tutoring centers to manage teachers, students, and parents. The system will streamline administrative tasks, class scheduling, financial tracking, and communication between all stakeholders.

### 1.2 Target Users
- Specialized training/tutoring centers
- Teachers and tutors
- Students (primary school through adult)
- Parents/guardians

### 1.3 Core Problems Addressed
- Centralized management of multiple calendars and schedules
- Automated financial tracking for teachers and students
- Integrated communication and homework management
- Reduction of manual processes and errors

## 2. Core Features & Requirements

### 2.1 Authentication & Authorization
- Google OAuth integration for login
- Role-based access control (admin, teacher, student, parent)

### 2.2 Calendar & Scheduling
- Integration with Google Calendar
- Embedded calendar view within the platform
- Class scheduling with details including:
  - Student name(s)
  - Teacher name
  - Class type/code (for pricing reference)
  - Start/end times
  - Subject information

### 2.3 Financial Management
- Track teacher hours and calculate compensation
- Track student payments and remaining class hours
- Support multiple payment models:
  - Monthly subscriptions
  - Pay-per-class
  - Package deals
  - Different rates based on class types/subjects

### 2.4 Learning Materials & Homework
- File upload capability
- Assignment creation with due dates
- Teacher feedback functionality

### 2.5 Internationalization
- Multi-language support (initially Portuguese and Spanish)
- Translatable text strings throughout the application

## 3. User Roles & Permissions

### 3.1 Admin Staff
- Access to all teacher and student information
- View and manage all calendars
- Financial oversight for the entire system
- User management capabilities
- May also be a teacher with extended permissions

### 3.2 Teachers
- View and manage their own calendar
- Access their list of assigned students
- Post homework/notes to their students
- View their own financial information (earnings)
- Communicate with students

### 3.3 Students
- View their own calendar and scheduled classes
- Access homework assignments
- Submit questions to teachers
- View their own learning materials

### 3.4 Parents
- Extended permissions to access their children's student portals
- View financial information related to their children
- Payment management

## 4. Technology Stack

### 4.1 Backend
- Django framework
  - Django REST framework for API endpoints
  - Django's built-in admin panel
  - Authentication system with Google OAuth integration
  - ORM for database interactions
  - Internationalization support

### 4.2 Frontend
- Vue.js or Django templates with HTMX
- Mobile-responsive design
- Minimalist UI approach for the MVP

### 4.3 Database
- PostgreSQL or MySQL (compatible with PythonAnywhere)

### 4.4 External Service Integrations
- Google OAuth for authentication
- Google Calendar API for scheduling
- (Optional) Google Drive API for file storage
- (Optional) Google Meet or Zoom for virtual sessions

## 5. Data Models

### 5.1 User (extends Django's built-in User model)
- Email, first_name, last_name, phone, profile_picture
- Role (admin, teacher, student, parent)
- Google OAuth credentials

### 5.2 Profile Models
- **TeacherProfile**
  - Related to User (one-to-one)
  - Specialties, hourly_rate, bio, qualifications

- **StudentProfile**
  - Related to User (one-to-one)
  - Grade_level, date_of_birth, notes

- **ParentProfile**
  - Related to User (one-to-one)
  - Children (ManyToMany to StudentProfile)

### 5.3 Subject
- Name, description, grade_level_range

### 5.4 ClassType
- Name (e.g., "Apoio ao estudo", "Individual tutoring")
- Group_class (boolean)
- Default_duration (minutes)
- Description

### 5.5 ClassSession
- Title, start_time, end_time, status
- Teacher (ForeignKey to User)
- Students (ManyToMany to User)
- Subject (ForeignKey to Subject)
- Class_type (ForeignKey to ClassType)
- Google_calendar_id
- Price_override (optional)

### 5.6 PaymentPlan
- Name, description, plan_type
- Rate (for monthly)
- Hours_included (for package)
- Expiration_period (for package)

### 5.7 StudentPayment
- Student (ForeignKey to User)
- Payment_plan (ForeignKey to PaymentPlan)
- Amount_paid, payment_date
- Period_start, period_end (for monthly)
- Hours_purchased, hours_used (for package)
- Notes

### 5.8 TeacherCompensation
- Teacher (ForeignKey to User)
- Period_start, period_end
- Hours_taught
- Amount_owed, amount_paid
- Payment_date
- Notes

### 5.9 HomeworkAssignment
- Title, description, due_date
- Teacher (ForeignKey to User)
- Students (ManyToMany to User)
- File_attachments
- Date_created

### 5.10 HomeworkSubmission
- Assignment (ForeignKey to HomeworkAssignment)
- Student (ForeignKey to User)
- Submission_date
- File_attachments
- Feedback, notes

## 6. Security & Compliance

### 6.1 GDPR Compliance
- Privacy policy documentation
- Data processing agreements
- User consent management
- Data export functionality
- Right to be forgotten implementation

### 6.2 Data Protection
- Encryption of sensitive information in the database
- Masked personal information (names, addresses)
- Secure authentication processes
- Regular security audits
- Data backup procedures

## 7. UI/UX Requirements

### 7.1 Design Approach
- Minimalist design for the MVP
- Focus on functionality over aesthetics initially
- Intuitive navigation

### 7.2 Responsive Design
- Mobile-friendly interface
- Accessible on various devices (desktop, tablet, smartphone)
- Responsive calendar views

### 7.3 User Flows
- Simplified onboarding process
- Streamlined calendar management
- Easy access to financial information
- Straightforward homework submission

## 8. Deployment

### 8.1 Hosting Platform
- PythonAnywhere for initial deployment
- MySQL database (provided by PythonAnywhere)

### 8.2 Environment Setup
- Development, staging, and production environments
- Environment variable management
- Database configuration

## 9. Testing Requirements

### 9.1 Unit Testing
- Test coverage for core functionality
- Django test framework implementation

### 9.2 End-to-End Testing
- Critical user flows testing
- Integration test suite

### 9.3 Browser Compatibility
- Testing across major browsers
- Mobile device testing

## 10. Development Phases

### 10.1 Phase 1 (MVP)
- Admin functionality for viewing/changing teacher calendars
- Financial tracking system for:
  - Student payments and remaining hours
  - Teacher compensation tracking
  - Financial overview for administrators

### 10.2 Future Phases (Post-MVP)
- Advanced reporting and analytics
- Notification system
- Enhanced homework management
- Additional integration options
- Mobile applications

## 11. Future Considerations

### 11.1 Features for Later Implementation
- Notification system for classes, homework, and payments
- Reporting dashboards and analytics
- Invoice generation
- Advanced student progress tracking
- Parent-teacher communication portal
- Virtual classroom integration
