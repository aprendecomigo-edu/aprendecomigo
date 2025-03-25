# School Management Platform Implementation Plan (Feature-Driven Approach)

## Blueprint Overview

This document outlines a feature-driven implementation plan for building a School Management Platform. Rather than building all models and views upfront, this approach focuses on delivering core functionality first: calendar management for admins and financial reporting based on scheduling data. Each phase builds incrementally on working features.

## Feature-Driven Development Phases

### Phase 1: Core Calendar Management
- Set up project foundation and authentication
- Implement basic user and calendar models
- Create admin calendar management interface
- Enable basic scheduling functionality

### Phase 2: Financial Reporting
- Implement financial models for calendar data
- Create basic financial calculations
- Build admin financial dashboard
- Enable simple reporting

### Phase 3: User Role Expansion
- Expand user roles and permissions
- Implement teacher and student views
- Create role-specific dashboards
- Add notification system

### Phase 4: Advanced Features
- Implement homework management
- Add internationalization
- Enhance UI/UX
- Prepare for deployment

## Detailed Implementation Steps

Let's break these phases into smaller, focused implementation steps that deliver working functionality at each stage:

## Phase 1: Core Calendar Management - Implementation Steps

### Step 1: Project Setup and Authentication
- Initialize Django project with minimal structure
- Set up basic database configuration
- Implement custom User model with admin role
- Create authentication system with login/logout

### Step 2: Calendar Models and Google Integration
- Implement minimal Subject and ClassType models
- Create ClassSession model for scheduling
- Set up Google Calendar API integration
- Build basic sync mechanism

### Step 3: Admin Calendar Interface
- Create admin dashboard template
- Implement calendar view component
- Build class scheduling interface
- Add basic CRUD operations for classes

### Step 4: Enhanced Scheduling Features
- Implement recurring class functionality
- Add conflict detection
- Create calendar filtering options
- Build notification mechanism for changes

## Phase 2: Financial Reporting - Implementation Steps

### Step 5: Financial Foundation Models
- Implement TeacherProfile with compensation rates
- Create StudentProfile with basic payment info
- Build minimal payment tracking models
- Set up relationships with calendar data

### Step 6: Financial Calculations
- Implement teacher hours calculation from calendar
- Create student payment calculation logic
- Build basic reporting functions
- Add financial data validation

### Step 7: Financial Dashboard
- Create financial overview dashboard
- Implement teacher compensation reports
- Build student payment tracking interface
- Add export functionality for reports

### Step 8: Enhanced Financial Features
- Implement payment recording system
- Create financial notifications
- Add detailed financial analytics
- Build batch operations for admin

## Phase 3: User Role Expansion - Implementation Steps

### Step 9: Expanded User Roles
- Enhance user model with additional roles
- Implement role-based permissions system
- Create profile management for all roles
- Build user management interface

### Step 10: Teacher and Student Interfaces
- Create teacher dashboard
- Implement student schedule view
- Build parent dashboard for child monitoring
- Add role-specific calendar views

### Step 11: Communication System
- Implement notification preferences
- Create messaging system between users
- Build announcement functionality
- Add email notifications

### Step 12: Profile and Settings
- Create user profile management
- Implement account settings
- Build preference configuration
- Add privacy controls

## Phase 4: Advanced Features - Implementation Steps

### Step 13: Homework Management
- Implement assignment models
- Create submission system
- Build file upload functionality
- Add feedback mechanism

### Step 14: Internationalization and Polish
- Set up language configuration
- Implement UI translations
- Enhance mobile responsiveness
- Prepare for deployment

## Implementation Prompts

Below are the implementation prompts for a code-generation LLM to build each step, focusing on incremental feature delivery:

### Prompt 1: Project Setup and Authentication

```
Create a new Django project for a School Management Platform with a focus on calendar management. Initialize the project with:
0. Setup virtualenv that uses the latest version of python3 with the latest version of Django
1. Create a new Django project named "aprendecomigo"
2. Configure settings.py with:
   - PostgreSQL database configuration
   - Basic timezone and language settings
   - Static file configurations
3. Create a minimal project structure with these initial apps:
   - accounts: For user management
   - scheduling: For calendar functionality
4. Implement a custom User model in accounts/models.py:
   - Email as the primary identifier 
   - Fields: name, phone_number, is_admin (boolean)
5. Create basic authentication views:
   - Login page with email/password
   - Logout functionality
   - Password reset
6. Create simple templates for authentication:
   - Base template with navigation
   - Login/logout pages
   - Password reset pages
7. Set up a requirements.txt with essential dependencies:
   - Django
   - psycopg2-binary
   - python-dotenv
   - Pillow
   - google-auth, google-api-python-client (for Calendar API)

Provide the complete project structure, models, views, templates, and configurations for this initial setup.
```

### Prompt 2: Calendar Models and Google Integration

```
Building on the authentication system, implement core calendar models and Google Calendar integration:

1. Create these models in the scheduling app:
   - Subject: name, description
   - ClassType: name, group_class (boolean), default_duration
   - ClassSession: title, teacher (ForeignKey to User), students (ManyToMany to User), 
     subject (ForeignKey), class_type (ForeignKey), start_time, end_time, google_calendar_id
   
2. Implement Django admin interfaces for these models
   
3. Create Google Calendar authentication:
   - Implement OAuth2 flow for Google Calendar API
   - Store user credentials securely
   - Handle token refresh and management
   - Create permission screens for calendar access
   
4. Implement Google Calendar reading service:
   - Method to fetch events from user's Google Calendar
   - Convert Google Calendar events to ClassSession objects
   - Handle sync conflicts and updates
   - Schedule periodic syncing
   
5. Create a simple management command to test the Calendar API integration

Provide the complete models, admin configurations, authentication flow, and calendar reading service for the calendar functionality.
```

### Prompt 3: Admin Calendar Interface

```
Create an admin calendar interface by embedding Google Calendar:

1. Implement an admin dashboard view in scheduling/views.py:
   - Embed user's Google Calendar within the platform using iframes
   - Display read-only overview of scheduled classes from the database
   - Add filter options for viewing different calendar data
   - Include calendar sync status and controls
   
2. Create filter forms in scheduling/forms.py:
   - DateRangeFilterForm for viewing specific time periods
   - TeacherFilterForm for filtering calendar by teacher
   - SubjectFilterForm for filtering by subject
   
3. Build templates for the calendar interface:
   - admin_dashboard.html with embedded Google Calendar
   - calendar_filters.html for filtering options
   - sync_controls.html for manual sync triggers
   
4. Implement URL patterns in scheduling/urls.py for all views
   
5. Add minimal JavaScript functionality:
   - Filter application handling
   - Sync button functionality
   - Calendar loading indicators
   
6. Configure proper Google Calendar embedding with:
   - API key configuration
   - Proper iframe setup with customization options
   - Security considerations for embedded calendar

Provide the complete views, forms, templates, URL configurations, and JavaScript for the admin calendar interface with embedded Google Calendar.
```

### Prompt 4: Enhanced Scheduling Features

```
Enhance the scheduling system with features that complement Google Calendar:

1. Implement improved Google Calendar sync:
   - Add configuration for which calendars to sync
   - Create rules for determining class types from event properties
   - Implement recurring event handling
   - Add conflict detection for imported events
   
2. Build calendar data processing:
   - Create utility to extract teacher/student information from event details
   - Implement pattern matching for subject identification
   - Add data validation for imported events
   - Create logs and reports for sync issues
   
3. Add calendar filtering and display options:
   - Implement filter interface for embedded calendar
   - Create view methods for displaying calendar data in different formats
   - Build API endpoints to fetch calendar data for the UI
   
4. Build a notification system for calendar changes:
   - Create a Notification model to track calendar changes
   - Add notifications for newly created/modified/deleted events
   - Implement basic email notification for important changes

Provide the complete models, services, and integration components needed for these enhanced calendar features.
```

### Prompt 5: Financial Foundation Models

```
Implement the financial foundation models linked to the calendar system:

1. Enhance the User model or create profiles:
   - Add TeacherProfile model with fields: user (OneToOne), hourly_rate, bio
   - Add StudentProfile model with fields: user (OneToOne), payment_notes
   
2. Create financial models in a new financials app:
   - Create PaymentPlan model with fields: name, rate_type (hourly, package, monthly), rate, hours_included
   - Create StudentPayment model with fields: student (ForeignKey to User), amount, payment_date, notes
   - Create TeacherCompensation model with fields: teacher (ForeignKey to User), month, year, hours_taught, amount, paid (boolean)
   
3. Implement methods to calculate financial data:
   - Calculate teacher hours from ClassSession records
   - Calculate student payment amount based on classes attended
   - Track payment history
   
4. Create Django admin interfaces for all financial models
   
5. Implement signals to update financial records when ClassSessions change

Provide the complete financial models, calculation methods, admin configurations, and signals needed.
```

### Prompt 6: Financial Calculations

```
Implement the core financial calculation logic based on calendar data:

1. Create financial service classes in financials/services.py:
   - TeacherCompensationService with methods:
     - calculate_hours_for_period(teacher, start_date, end_date)
     - calculate_compensation_amount(teacher, hours)
     - generate_monthly_report(teacher, month, year)
   
   - StudentPaymentService with methods:
     - calculate_attendance(student, start_date, end_date)
     - calculate_payment_due(student, attendance)
     - generate_payment_report(student, month, year)
   
2. Implement utility functions for common calculations:
   - Calculate duration of a class session
   - Calculate hours by class type
   - Generate summary statistics
   
3. Create unit tests for all calculation methods
   
4. Add data validation and error handling:
   - Handle edge cases (canceled classes, partial attendance)
   - Add validation for financial data
   - Implement logging for financial calculations

Provide the complete service classes, utility functions, tests, and validation logic for the financial calculations.
```

### Prompt 7: Financial Dashboard

```
Create a financial dashboard for admins to view and manage financial data:

1. Implement dashboard views in financials/views.py:
   - FinancialOverviewView with summary of all financial data
   - TeacherCompensationView for managing teacher payments
   - StudentPaymentView for tracking student payments
   - ReportGenerationView for creating custom reports
   
2. Create templates for financial dashboard:
   - financial_overview.html with summary cards and charts
   - teacher_compensation.html for teacher payment management
   - student_payment.html for student payment tracking
   - report_generation.html for custom reporting
   
3. Implement forms for financial management:
   - TeacherCompensationForm for recording teacher payments
   - StudentPaymentForm for recording student payments
   - ReportFilterForm for custom report generation
   
4. Add data visualization components:
   - Monthly revenue chart
   - Teacher compensation summary
   - Student payment status
   - Class attendance statistics
   
5. Create export functionality for reports:
   - CSV export for financial data
   - PDF generation for invoices/receipts
   - Data filtering options for exports

Provide the complete views, templates, forms, and export functionality for the financial dashboard.
```

### Prompt 8: Enhanced Financial Features

```
Enhance the financial system with more advanced features:

1. Implement a payment recording system:
   - Create PaymentTransaction model for detailed transaction tracking
   - Build form for recording payments with multiple payment methods
   - Add receipt generation functionality
   - Implement payment history view
   
2. Create financial notifications:
   - Add notifications for pending payments
   - Create reminders for unpaid invoices
   - Implement email notifications for financial updates
   - Add payment confirmation messages
   
3. Build financial analytics:
   - Create revenue projection charts
   - Implement teacher earnings analysis
   - Add student payment pattern analysis
   - Build financial health indicators
   
4. Implement batch operations for admins:
   - Bulk payment recording
   - Mass email generation for invoices
   - Batch report generation
   - Financial data import/export

Provide the complete models, views, forms, templates, and utility functions for these enhanced financial features.
```

### Prompt 9: Expanded User Roles

```
Enhance the user system with expanded roles and permissions:

1. Update the User model with role-based system:
   - Add role field with choices (admin, teacher, student, parent)
   - Implement role-specific permissions
   - Create middleware for role checking
   
2. Create profile models for all roles:
   - Complete TeacherProfile with additional fields: specialties, qualifications
   - Enhance StudentProfile with: grade_level, date_of_birth, emergency_contact
   - Add ParentProfile with ManyToMany relationship to StudentProfile for children
   
3. Implement user management views:
   - UserListView for admins to see all users
   - UserDetailView for viewing user profiles
   - UserCreateView and UserUpdateView for managing users
   - Role-specific registration views
   
4. Build templates for user management:
   - user_list.html for displaying all users
   - user_detail.html for showing user information
   - user_form.html for creating/editing users
   - role-specific profile forms
   
5. Implement permission decorators for controlling access

Provide the complete models, views, templates, and permission system for the expanded user roles.
```

### Prompt 10: Teacher and Student Interfaces

```
Create role-specific interfaces for teachers and students:

1. Implement teacher dashboard:
   - TeacherDashboardView showing upcoming classes
   - TeacherCalendarView for personal schedule
   - TeacherStudentsView listing assigned students
   - TeacherCompensationView showing earnings
   
2. Build student dashboard:
   - StudentDashboardView with upcoming classes
   - StudentCalendarView for personal schedule
   - StudentPaymentView showing payment status
   - StudentProgressView (placeholder for future)
   
3. Create parent dashboard:
   - ParentDashboardView showing children's activities
   - ParentCalendarView with all children's schedules
   - ParentPaymentView for managing payments
   - ParentStudentView for viewing child's progress
   
4. Implement role-specific navigation:
   - Custom navigation bar based on user role
   - Role-specific sidebar menus
   - Dashboard quick links by role
   - Restricted access controls

Provide the complete views, templates, and navigation components for these role-specific interfaces.
```

### Prompt 11: Communication System

```
Implement a communication system for users:

1. Create notification models:
   - Notification model with fields: user, message, read_status, created_at, notification_type
   - NotificationPreference model for user settings
   
2. Build messaging functionality:
   - Message model with fields: sender, recipient, subject, content, read_status, sent_at
   - Conversation model for tracking message threads
   - Attachment model for message files
   
3. Implement announcement system:
   - Announcement model for admin broadcasts
   - AnnouncementRecipient for tracking views
   - Template for different announcement types
   
4. Create communication views:
   - NotificationListView for viewing all notifications
   - MessageComposeView for creating messages
   - MessageInboxView and MessageDetailView
   - AnnouncementCreateView for admins
   
5. Add email notification integration:
   - Email sending service
   - Email templates for different notification types
   - Email preference settings

Provide the complete models, views, templates, and services for the communication system.
```

### Prompt 12: Profile and Settings

```
Create user profile management and settings functionality:

1. Implement profile management views:
   - ProfileView for viewing own profile
   - ProfileEditView for updating profile information
   - PasswordChangeView for security
   - ProfilePictureUploadView for avatar management
   
2. Build account settings:
   - AccountSettingsView with tabs for different settings
   - NotificationSettingsView for communication preferences
   - PrivacySettingsView for controlling data sharing
   - CalendarSyncSettingsView for Google Calendar options
   
3. Implement preference configuration:
   - UserPreference model for storing preferences
   - Form for updating preferences
   - Apply preferences across the platform
   
4. Create templates for profile and settings:
   - profile.html for displaying profile
   - profile_edit.html for updating information
   - settings/* templates for different settings pages
   - partials for common settings components

Provide the complete views, models, forms, and templates for the profile and settings functionality.
```

### Prompt 13: Homework Management

```
Implement a basic homework management system:

1. Create homework models in a new learning app:
   - Assignment model with fields: title, description, teacher, class_session, due_date, file_attachment
   - Submission model with fields: assignment, student, submission_date, file_attachment, notes
   - Feedback model for teacher responses
   
2. Implement file handling:
   - File upload functionality for assignments and submissions
   - File type validation
   - Secure file storage configuration
   
3. Build assignment views:
   - AssignmentCreateView for teachers
   - AssignmentListView filtered by role
   - AssignmentDetailView with submission capability
   - SubmissionGradeView for teachers
   
4. Create submission interface:
   - SubmissionCreateView for students
   - SubmissionListView for teachers
   - FeedbackCreateView for teachers
   - SubmissionDetailView with feedback display
   
5. Implement notification integration:
   - Notifications for new assignments
   - Due date reminders
   - Submission confirmations
   - Feedback notifications

Provide the complete models, views, forms, templates, and file handling functionality for the homework system.
```

### Prompt 14: Internationalization and Polish

```
Implement internationalization and final polish:

1. Configure Django internationalization:
   - Update settings.py for i18n support
   - Set up middleware for language detection
   - Configure URL patterns for language prefixes
   
2. Create translation files:
   - Extract strings using makemessages
   - Provide initial translations for Portuguese
   - Implement translation tags in templates
   - Use gettext in Python code
   
3. Build language switching:
   - Create language selector component
   - Implement view for changing language
   - Store language preference
   - Add language to user profile
   
4. Polish the UI:
   - Enhance responsive design
   - Implement loading indicators
   - Add animations for interactions
   - Ensure accessibility compliance
   
5. Prepare for deployment:
   - Configure production settings
   - Optimize static files
   - Set up error logging
   - Create deployment documentation

Provide the complete internationalization configuration, language switching functionality, UI enhancements, and deployment preparations.
```

## Conclusion

This implementation plan takes a feature-driven approach, focusing first on the core calendar management and financial reporting functionality. Each step builds incrementally on previous work, ensuring that you have working features at each stage rather than building all models and views upfront.

The first two phases deliver the core functionality described in your requirements: admins managing calendars and generating financial reports. Later phases expand on this foundation to add more advanced features and support for additional user roles.

This approach allows for earlier feedback and testing of the most critical features, while still maintaining a structured path to the complete platform. 