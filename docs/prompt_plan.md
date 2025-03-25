# School Management Platform Implementation Plan

## Blueprint Overview

This document outlines the step-by-step implementation plan for building a School Management Platform as specified in the requirements. The plan breaks down the development into small, manageable chunks that build upon each other, ensuring steady progress without overwhelming complexity.

## Development Phases

### Phase 1: Project Setup and Foundation
- Initialize Django project and configure settings
- Set up database and authentication system
- Create basic user models and authentication
- Implement basic UI structure and navigation

### Phase 2: Core Data Models and Admin Interface
- Implement all data models
- Set up Django admin interface
- Create basic views and forms
- Implement role-based permissions

### Phase 3: Calendar and Scheduling
- Implement Google Calendar integration
- Build class scheduling interface
- Create calendar views for different user roles
- Add notification system for schedule changes

### Phase 4: Financial Management
- Build teacher compensation tracking
- Implement student payment system
- Create financial dashboards for admins
- Add reporting functionality

### Phase 5: Learning Materials and Homework
- Implement file uploads for assignments
- Create homework submission system
- Build feedback mechanisms
- Add progress tracking

### Phase 6: Final Integration and Polish
- Implement internationalization
- Enhance UI/UX
- Add final integrations
- Perform testing and optimization

## Implementation Steps (Broken Down)

Let's break these phases into more granular implementation steps:

## Detailed Implementation Steps

### Step 1: Project Initialization
- Create Django project
- Configure database settings
- Set up basic project structure
- Initialize Git repository

### Step 2: Authentication Foundation
- Configure Django authentication system
- Set up Google OAuth integration
- Create custom user model
- Implement login/logout flow

### Step 3: User Role Models
- Create profile models (Teacher, Student, Parent)
- Implement role-based permissions
- Build user registration process
- Set up admin user management

### Step 4: Core Data Models
- Implement Subject model
- Create ClassType model
- Build ClassSession model
- Set up relationships between models

### Step 5: Basic Frontend Structure
- Create base templates
- Implement responsive layout
- Set up navigation structure
- Create role-specific dashboards

### Step 6: Calendar Integration Basics
- Set up Google Calendar API connection
- Implement basic calendar display
- Create event creation/editing interface
- Build synchronization mechanism

### Step 7: Class Scheduling System
- Create class scheduling forms
- Build recurring class functionality
- Implement availability checking
- Add student-class assignment

### Step 8: Financial Models
- Implement PaymentPlan model
- Create StudentPayment model
- Build TeacherCompensation model
- Set up financial calculations

### Step 9: Payment Tracking Interface
- Create payment tracking dashboard
- Implement payment recording system
- Build payment reports
- Add financial overview for admins

### Step 10: Teacher Compensation System
- Implement hours tracking
- Create compensation calculation
- Build payment processing
- Add reporting for teachers

### Step 11: Homework Management
- Create HomeworkAssignment model
- Implement HomeworkSubmission model
- Build file upload functionality
- Create assignment interfaces

### Step 12: Internationalization
- Set up language configuration
- Implement text translation
- Create language switching interface
- Test multilingual functionality

### Step 13: Testing and Optimization
- Write unit tests
- Perform integration testing
- Optimize database queries
- Improve UI/UX

### Step 14: Deployment Preparation
- Configure production settings
- Set up deployment scripts
- Prepare documentation
- Final testing

## Implementation Prompts

Below are the implementation prompts for a code-generation LLM to build each step of the School Management Platform:

### Prompt 1: Project Initialization

```
Create a new Django project for a School Management Platform. Initialize the project with the following:

1. Create a new Django project named "aprendecomigo"
2. Configure settings.py with:
   - PostgreSQL database configuration
   - Timezone and language settings
   - Static and media file configurations
3. Create a basic project structure with the following apps:
   - accounts: For user management
   - scheduling: For calendar and class scheduling
   - financials: For payment and compensation tracking
   - learning: For homework and learning materials
4. Set up a requirements.txt file with necessary dependencies:
   - Django
   - Django REST framework
   - psycopg2 or mysqlclient (depending on database choice)
   - python-dotenv (for environment variable management)
   - Pillow (for image handling)
   - django-allauth (for OAuth)

Provide the complete project structure and configuration files.
```

### Prompt 2: Custom User Model and Authentication

```
Building on the initial project setup, implement a custom user model and authentication system:

1. Create a custom User model in the accounts app that extends Django's AbstractUser with:
   - email as the primary identifier instead of username
   - Additional fields: phone_number, profile_picture, role (choices: admin, teacher, student, parent)
   
2. Set up Django Allauth for Google OAuth integration:
   - Configure settings for Google authentication
   - Create templates for login/signup pages
   - Implement social account connection
   
3. Create basic authentication views:
   - Login page with Google OAuth option
   - Logout functionality
   - Password reset flow
   
4. Implement middleware for role-based access checking

Provide the models, views, templates, and configuration needed for this authentication system.
```

### Prompt 3: User Profile Models

```
Continuing from the custom user model, implement the profile models for different user roles:

1. Create the following models in the accounts app:
   - TeacherProfile: linked to User (one-to-one), with fields for specialties, hourly_rate, bio, qualifications
   - StudentProfile: linked to User (one-to-one), with fields for grade_level, date_of_birth, notes
   - ParentProfile: linked to User (one-to-one), with a ManyToMany relationship to StudentProfile for children
   
2. Implement Django admin interfaces for these models

3. Create signals to automatically create the appropriate profile when a user is created or their role changes

4. Implement views and forms for users to complete their profiles after registration

5. Add permission decorators to restrict access based on user roles

Provide the complete models, admin configurations, signals, views, and templates needed.
```

### Prompt 4: Core Data Models

```
Implement the core data models needed for the School Management Platform:

1. Create the Subject model with fields:
   - name, description, grade_level_range
   
2. Create the ClassType model with fields:
   - name, group_class (boolean), default_duration, description
   
3. Create the ClassSession model with fields:
   - title, start_time, end_time, status
   - ForeignKey to User for teacher
   - ManyToMany to User for students
   - ForeignKey to Subject
   - ForeignKey to ClassType
   - google_calendar_id
   - price_override (optional)
   
4. Implement Django admin interfaces for these models

5. Create serializers if using Django REST framework

6. Add model methods for common operations (e.g., calculating session duration, checking conflicts)

Provide the complete models, admin configurations, and any additional utility methods needed.
```

### Prompt 5: Basic Frontend Structure

```
Create the basic frontend structure for the School Management Platform:

1. Create a base template with:
   - Responsive layout using CSS framework (Bootstrap or Tailwind)
   - Navigation bar that adapts based on user role
   - Sidebar for main navigation
   - Footer with basic info
   
2. Implement role-specific dashboard templates:
   - Admin dashboard with overview of system
   - Teacher dashboard focused on schedule and students
   - Student dashboard showing classes and homework
   - Parent dashboard with access to children's information
   
3. Set up static files:
   - CSS for styling
   - JS for basic interactions
   - Images and icons
   
4. Create template tags for common UI elements

5. Implement basic views to render these templates

Provide the complete templates, static files, template tags, and views needed.
```

### Prompt 6: Google Calendar Integration

```
Implement Google Calendar integration for the School Management Platform:

1. Set up Google Calendar API connection:
   - Configure OAuth2 for server-side applications
   - Create utility functions for API interactions
   - Implement token storage and refresh
   
2. Create a calendar display component:
   - Week view
   - Day view
   - Month overview
   - Color-coding for different class types
   
3. Implement calendar event synchronization:
   - Create Google Calendar events from ClassSessions
   - Update ClassSessions when Google Calendar events change
   - Handle recurring events
   
4. Add user calendar settings:
   - Timezone preferences
   - Display preferences
   - Notification settings
   
5. Create views and templates for the calendar interface

Provide the complete integration code, utility functions, views, and templates.
```

### Prompt 7: Class Scheduling System

```
Build the class scheduling system for the School Management Platform:

1. Create forms for class scheduling:
   - ClassSession creation form with teacher, students, subject, time selection
   - Recurring class setup form
   - Class modification and cancellation forms
   
2. Implement scheduling logic:
   - Availability checking for teachers and students
   - Conflict detection
   - Recurring class generation
   - Schedule modification rules
   
3. Create views for different scheduling operations:
   - Schedule class view
   - Modify class view
   - Cancel class view
   - View schedule by teacher/student/subject
   
4. Implement permissions checking to ensure only authorized users can schedule classes

5. Create templates for the scheduling interface

Provide the complete forms, logic, views, and templates for the scheduling system.
```

### Prompt 8: Financial Models and Logic

```
Implement the financial models and logic for the School Management Platform:

1. Create the PaymentPlan model with fields:
   - name, description, plan_type
   - rate (for monthly plans)
   - hours_included (for package plans)
   - expiration_period (for package plans)
   
2. Create the StudentPayment model with fields:
   - ForeignKey to User for student
   - ForeignKey to PaymentPlan
   - amount_paid, payment_date
   - period_start, period_end (for monthly plans)
   - hours_purchased, hours_used (for package plans)
   - notes
   
3. Create the TeacherCompensation model with fields:
   - ForeignKey to User for teacher
   - period_start, period_end
   - hours_taught
   - amount_owed, amount_paid
   - payment_date
   - notes
   
4. Implement financial calculation methods:
   - Calculate student remaining hours/credit
   - Calculate teacher compensation based on classes taught
   - Track payment status and history
   
5. Add model methods for common financial operations

Provide the complete models, calculation methods, and any utility functions needed.
```

### Prompt 9: Financial Management Interface

```
Create the financial management interface for the School Management Platform:

1. Implement student payment views:
   - Payment recording form
   - Payment history view
   - Remaining credit/hours display
   - Payment plan selection interface
   
2. Create teacher compensation views:
   - Hours taught tracking
   - Compensation calculation display
   - Payment history
   - Compensation reports
   
3. Build admin financial dashboard:
   - Overview of all financial transactions
   - Revenue tracking
   - Teacher payment tracking
   - Financial reports generation
   
4. Implement financial notifications:
   - Low balance alerts for students
   - Payment due notifications
   - Payment received confirmations
   
5. Create templates for all financial interfaces

Provide the complete views, forms, templates, and notification logic for the financial management system.
```

### Prompt 10: Homework Management System

```
Implement the homework management system for the School Management Platform:

1. Create the HomeworkAssignment model with fields:
   - title, description, due_date
   - ForeignKey to User for teacher
   - ManyToMany to User for students
   - file_attachments
   - date_created
   
2. Create the HomeworkSubmission model with fields:
   - ForeignKey to HomeworkAssignment
   - ForeignKey to User for student
   - submission_date
   - file_attachments
   - feedback, notes
   
3. Implement file upload functionality:
   - Secure file storage
   - File type validation
   - Size limitations
   
4. Create homework interfaces:
   - Assignment creation for teachers
   - Assignment viewing for students
   - Submission interface
   - Feedback system for teachers
   
5. Implement notification system for homework deadlines and feedback

Provide the complete models, file handling logic, views, and templates for the homework system.
```

### Prompt 11: Internationalization

```
Implement internationalization for the School Management Platform:

1. Configure Django's internationalization settings:
   - Set up language settings in settings.py
   - Configure middleware and context processors
   - Set up URL patterns for language prefixes
   
2. Create translation files:
   - Extract strings from templates and Python code
   - Create initial translation files for Portuguese and Spanish
   - Implement translation process
   
3. Create a language switching interface:
   - Add language selector in the UI
   - Store user language preference
   - Apply language selection across the site
   
4. Ensure all user-facing text is translatable:
   - Use translation tags in templates
   - Use gettext functions in Python code
   - Handle dynamic content translation
   
5. Test multilingual functionality across all interfaces

Provide the complete internationalization configuration, translation files, and language switching interface.
```

### Prompt 12: Testing and Optimization

```
Implement testing and optimization for the School Management Platform:

1. Create unit tests for all critical components:
   - User authentication and permissions
   - Class scheduling logic
   - Financial calculations
   - Homework submission system
   
2. Implement integration tests for key workflows:
   - Complete class scheduling process
   - Payment recording and tracking
   - User registration and profile completion
   
3. Optimize database queries:
   - Add select_related and prefetch_related where appropriate
   - Analyze and optimize slow queries
   - Implement caching for frequent operations
   
4. Improve UI/UX:
   - Enhance form validation and feedback
   - Optimize page load times
   - Improve responsive design
   - Add loading indicators for async operations
   
5. Perform security checks and enhancements

Provide the complete test suite, optimization changes, and UI/UX improvements.
```

### Prompt 13: Deployment Preparation

```
Prepare the School Management Platform for deployment:

1. Configure production settings:
   - Security settings (SECRET_KEY, ALLOWED_HOSTS, etc.)
   - Static file serving configuration
   - Database settings for production
   - Logging configuration
   
2. Create deployment scripts:
   - Database migration commands
   - Static file collection
   - Environment setup
   
3. Prepare documentation:
   - Installation guide
   - User manual for different roles
   - Administration guide
   
4. Implement final checks:
   - Security audit
   - Performance testing
   - Cross-browser compatibility testing
   
5. Set up backup and monitoring systems

Provide the complete production settings, deployment scripts, documentation, and final check implementation.
```

### Prompt 14: Final Integration and Polishing

```
Complete the final integration and polishing of the School Management Platform:

1. Ensure all components are properly connected:
   - Calendar events link to financial tracking
   - User profiles connect to all relevant data
   - Notifications integrate with all subsystems
   
2. Implement any missing features:
   - Dashboard widgets and summaries
   - Export functionality for reports
   - Batch operations for admins
   
3. Add final UI polishing:
   - Consistent styling across all pages
   - Enhanced mobile responsiveness
   - Accessibility improvements
   
4. Create seed data and demo mode:
   - Sample users of all roles
   - Demo classes and assignments
   - Example financial data
   
5. Perform final testing and bug fixing

Provide the integrated components, missing features, UI improvements, seed data, and bug fixes.
```

## Conclusion

This implementation plan provides a structured approach to building the School Management Platform. Each prompt builds upon the previous ones, ensuring that all components are properly integrated. The steps are small enough to be manageable but substantial enough to make meaningful progress.

By following this plan, developers can systematically implement the platform with a focus on best practices and incremental development. 