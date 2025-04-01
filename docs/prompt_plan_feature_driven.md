# School Management Platform Implementation Plan (Feature-Driven Approach)

## Blueprint Overview

This document outlines a feature-driven implementation plan for building a School Management Platform, focusing on the financial and operational aspects. The plan prioritizes delivering core functionality: reading calendar data from Google Calendar and performing financial calculations/reporting based on this data. Each phase builds incrementally on working features.

## Feature-Driven Development Phases

### Phase 1: Calendar Data Extraction & Financial Foundation
- Set up project foundation and authentication
- Implement basic user and calendar models
- Create Google Calendar read-only integration
- Build financial tracking models

### Phase 2: Financial Operations
- Implement financial calculations based on calendar data
- Create admin financial dashboard
- Build reporting system
- Enable payment tracking

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

## Phase 1: Calendar Data Extraction & Financial Foundation - Implementation Steps

### Step 1: Project Setup and Authentication
- Initialize Django project with minimal structure
- Set up basic database configuration
- Implement custom User model with admin role
- Create authentication system with login/logout

### Step 2: Calendar Models and Google Integration
- Implement minimal Subject and ClassType models
- Create ClassSession model for storing calendar data
- Set up Google Calendar API read-only integration
- Build a parsing mechanism to extract:
  - Student name from event title
  - Teacher name from location field
  - Price code from description field
  - Duration from start/end times
  - Absence status from "FALTOU" marking

### Step 3: Financial Foundation Models
- Create TeacherProfile with compensation rates
- Implement StudentProfile with payment info
- Build PaymentPlan model
- Create StudentPayment model
- Implement TeacherCompensation model

### Step 4: Admin Calendar Interface
- Create admin dashboard template
- Implement calendar view component
- Build class scheduling interface
- Add basic CRUD operations for classes

## Phase 2: Financial Operations - Implementation Steps

### Step 5: Financial Calculations
- Implement teacher hours calculation from calendar
- Create student payment calculation logic
- Build basic reporting functions
- Add financial data validation

### Step 6: Financial Dashboard
- Create financial overview dashboard
- Implement teacher compensation reports
- Build student payment tracking interface
- Add export functionality for reports

### Step 7: Payment Management
- Implement payment recording system
- Create payment history tracking
- Build invoice generation
- Add payment status monitoring

### Step 8: Enhanced Financial Features
- Implement financial notifications
- Add detailed financial analytics
- Build batch operations for admin
- Create financial health indicators

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
Create a new Django project for a School Management Platform with a focus on calendar and financial management. Initialize the project with:
0. Setup virtualenv that uses the latest version of python3 with the latest version of Django
1. Create a new Django project named "aprendecomigo"
2. Configure settings.py with:
   - PostgreSQL database configuration
   - Basic timezone and language settings
   - Static file configurations
3. Create a minimal project structure with these initial apps:
   - accounts: For user management
   - scheduling: For calendar functionality
   - financials: For financial tracking
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
   - django-allauth (for Google OAuth)

Provide the complete project structure, models, views, templates, and configurations for this initial setup.
```

### Prompt 2: Calendar Models and Google Integration

```
Building on the authentication system, implement calendar models and Google Calendar read-only integration:

1. Create these models in the scheduling app:
   - Subject: name, description
   - ClassType: name, group_class (boolean), default_duration, hourly_rate
   - ClassSession: 
       - title (extracted from event title)
       - teacher (ForeignKey to User, extracted from event location)
       - students (ManyToMany to User, extracted from event title)
       - subject (ForeignKey)
       - class_type (ForeignKey, determined by price code in description)
       - start_time, end_time (from calendar event)
       - google_calendar_id
       - attended (boolean, false if title contains "FALTOU")

2. Implement Django admin interfaces for these models

3. Create Google Calendar authentication:
   - Implement OAuth2 flow for Google Calendar API (read-only access)
   - Store admin credentials securely
   - Handle token refresh and management

4. Implement Google Calendar reading service:
   - Method to fetch events from admin's Google Calendars (online/in-person)
   - Parse event data according to the specified format:
     * Extract student name from event title
     * Extract teacher name from location field
     * Extract price code from description
     * Extract attendance status from title ("FALTOU")
   - Convert parsed data to ClassSession objects
   - Handle periodic synchronization

5. Create a simple management command to test the Calendar API integration and parsing

Provide the complete models, admin configurations, authentication flow, and calendar reading service for this functionality.
```

### Prompt 3: Financial Foundation Models

```
Implement the core financial models and their relationships:

1. Create these models in the financials app:
   - TeacherProfile: OneToOne to User, hourly_rate, bio
   - StudentProfile: OneToOne to User, payment_notes
   - PaymentPlan: name, plan_type, rate, hours_included, expiration_period
   - StudentPayment: student (FK), payment_plan (FK), amount_paid, payment_date,
     period_start, period_end, hours_purchased, hours_used
   - TeacherCompensation: teacher (FK), period_start, period_end, hours_taught,
     amount_owed, amount_paid, payment_date

2. Implement Django admin interfaces for these models

3. Create signals for ClassSession changes:
   - Update TeacherCompensation when classes are completed
   - Update StudentPayment hours_used when classes are completed
   - Handle payment plan expiration

4. Add utility methods:
   - Calculate remaining hours for students
   - Calculate teacher compensation
   - Validate payment plans

5. Create basic financial reports:
   - Student payment status
   - Teacher compensation summary
   - Payment plan usage

Provide the complete models, admin configurations, signals, and utility methods for the financial functionality.
```

### Prompt 4: Admin Calendar Interface

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

### Prompt 5: Financial Calculations

```
Implement the core financial calculation logic:

1. Create financial calculation services:
   - TeacherCompensationService:
     * Calculate hours from ClassSessions
     * Compute compensation based on hourly rate
     * Generate monthly reports
   - StudentPaymentService:
     * Track hours used from ClassSessions
     * Calculate remaining hours
     * Generate payment status reports

2. Implement calculation methods:
   - Class duration calculation
   - Hours by class type calculation
   - Payment plan validation
   - Compensation computation

3. Add data validation:
   - Edge case handling
   - Financial data validation
   - Logging for calculations

4. Create management commands:
   - Calculate teacher compensation
   - Update student payment status
   - Generate financial reports

5. Add utility functions:
   - Date range calculations
   - Payment plan validation
   - Financial data formatting

Provide the complete services, calculation methods, validation logic, and management commands for financial calculations.
```

### Prompt 6: Financial Dashboard

```
Create the admin financial dashboard:

1. Implement dashboard views in financials/views.py:
   - Financial overview dashboard
   - Teacher compensation view
   - Student payment view
   - Report generation view

2. Build dashboard templates:
   - Financial overview template
   - Teacher compensation template
   - Student payment template
   - Report generation template

3. Implement financial forms:
   - Teacher compensation form
   - Student payment form
   - Report filter form

4. Add data visualization:
   - Monthly revenue chart
   - Teacher compensation summary
   - Student payment status
   - Attendance statistics

5. Create export functionality:
   - CSV export
   - PDF generation
   - Data filtering options

6. Add JavaScript functionality:
   - Chart rendering
   - Filter application
   - Export handling
   - Real-time updates

Provide the complete views, templates, forms, and JavaScript for the financial dashboard.
```

### Prompt 7: Payment Management

```
Implement the payment management system:

1. Create payment models:
   - PaymentTransaction
   - PaymentReceipt
   - PaymentHistory

2. Implement payment views:
   - Payment recording form
   - Payment history view
   - Receipt generation
   - Payment status tracking

3. Build payment templates:
   - Payment form template
   - Payment history template
   - Receipt template
   - Status view template

4. Add payment functionality:
   - Payment recording
   - Receipt generation
   - Status updates
   - History tracking

5. Implement export features:
   - Payment report generation
   - Receipt PDF generation
   - Transaction history export

6. Add validation and security:
   - Payment validation
   - Receipt verification
   - Access control
   - Audit logging

Provide the complete models, views, templates, and functionality for payment management.
```

### Prompt 8: Enhanced Financial Features

```
Implement advanced financial features:

1. Create notification system:
   - Payment due notifications
   - Overdue payment alerts
   - Payment confirmation emails
   - Financial report notifications

2. Implement analytics:
   - Revenue projections
   - Teacher earnings analysis
   - Student payment patterns
   - Financial health indicators

3. Add batch operations:
   - Bulk payment recording
   - Mass email for invoices
   - Batch report generation
   - Import/export functionality

4. Create financial reports:
   - Monthly revenue reports
   - Teacher compensation reports
   - Student payment reports
   - Financial health reports

5. Implement data visualization:
   - Revenue charts
   - Payment trend graphs
   - Teacher earnings charts
   - Student payment status charts

Provide the complete notification system, analytics, batch operations, and reporting functionality.
```

## Conclusion

This implementation plan takes a feature-driven approach, focusing first on the core calendar management and financial reporting functionality. Each step builds incrementally on previous work, ensuring that you have working features at each stage rather than building all models and views upfront.

The first two phases deliver the core functionality described in your requirements: admins managing calendars and generating financial reports. Later phases expand on this foundation to add more advanced features and support for additional user roles.

This approach allows for earlier feedback and testing of the most critical features, while still maintaining a structured path to the complete platform.
