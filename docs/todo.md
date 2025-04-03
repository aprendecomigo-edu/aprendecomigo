# School Management Platform - Implementation Checklist

## Phase 1: Calendar Data Extraction & Financial Foundation

### Step 1: Project Setup and Authentication
- [x] Create Django project "aprendecomigo"
- [x] Configure PostgreSQL database connection
- [x] Set up timezone and language settings
- [x] Configure static and media file paths
- [x] Create accounts app
- [ ] Create scheduling app
- [ ] Create financials app
- [x] Implement custom User model
  - [x] Use email as primary identifier
  - [x] Add name, phone_number, is_admin fields
- [x] Create authentication views
  - [x] Login view and template
  - [x] Logout functionality
  - [x] Password reset flow
- [x] Build authentication templates
  - [x] Base template with navigation
  - [x] Login form
  - [x] Password reset forms
- [x] Set up requirements.txt
  - [x] Django
  - [x] PostgreSQL adapter
  - [x] python-dotenv
  - [x] Pillow
  - [x] Google API client libraries
  - [x] django-allauth
- [x] Write initial migration files
- [x] Test user creation and authentication

### Step 2: Calendar Models and Google Integration (READ-ONLY)
- [ ] Create scheduling app
  - [ ] Set up app configuration
  - [ ] Create models.py, views.py, urls.py structure
- [ ] Create Subject model
  - [ ] Add name and description fields
- [ ] Create ClassType model
  - [ ] Add name, group_class, default_duration fields
  - [ ] Add hourly_rate field (for pricing)
- [ ] Create ClassSession model
  - [ ] Add title field (will store student name)
  - [ ] Add start/end time, status fields
  - [ ] Add attended field (False if "FALTOU")
  - [ ] Set up ForeignKey to teacher (extracted from location)
  - [ ] Set up ManyToMany to students (extracted from title)
  - [ ] Add ForeignKeys to Subject and ClassType
  - [ ] Add google_calendar_id field
- [ ] Configure Django admin for models
  - [ ] Register models with admin site
  - [ ] Customize admin displays
- [ ] Set up Google OAuth2 authentication (READ-ONLY)
  - [ ] Create Google API credentials
  - [ ] Implement OAuth flow for admin account
  - [ ] Store and manage credentials
  - [ ] Handle token refresh
- [ ] Implement Google Calendar reading functionality
  - [ ] Fetch events from admin's calendars (online/in-person)
  - [ ] Parse event data:
    - [ ] Extract student name from title
    - [ ] Extract teacher name from location 
    - [ ] Extract price code from description
    - [ ] Check for "FALTOU" in title
  - [ ] Convert parsed data to ClassSession objects
  - [ ] Handle periodic synchronization
- [ ] Create management command for testing the parser
- [ ] Test Google Calendar integration

### Step 3: Financial Foundation Models
- [ ] Create financials app
  - [ ] Run startapp command
  - [ ] Add to INSTALLED_APPS
  - [ ] Setup models.py, admin.py, views.py structure
- [ ] Create PaymentPlan model
  - [ ] Add name, description fields
  - [ ] Add plan_type field with choices
  - [ ] Add rate field for monthly plans
  - [ ] Add hours_included, expiration_period for package plans
  - [ ] Add class_type ForeignKey to scheduling.ClassType
- [ ] Create StudentPayment model
  - [ ] Add student ForeignKey to CustomUser
  - [ ] Add payment_plan ForeignKey
  - [ ] Add amount_paid, payment_date fields
  - [ ] Add period_start, period_end fields for monthly plans
  - [ ] Add hours_purchased, hours_used for package plans
  - [ ] Add notes and status fields
- [ ] Create TeacherCompensation model
  - [ ] Add teacher ForeignKey
  - [ ] Add period_start, period_end fields
  - [ ] Add class_sessions ManyToManyField to ClassSession
  - [ ] Add hours_taught field
  - [ ] Add amount_owed, amount_paid fields
  - [ ] Add payment_date, notes, status fields
- [ ] Implement Django admin for models
  - [ ] Register models with admin site
  - [ ] Create custom ModelAdmin classes
  - [ ] Add appropriate filters and fields
- [ ] Create financial service classes
  - [ ] StudentPaymentService for calculations
  - [ ] TeacherCompensationService for calculations
  - [ ] Financial utility functions
- [ ] Test financial models and calculations

### Step 4: Calendar Data Display
- [ ] Create admin dashboard view
  - [ ] Display synced class sessions in table format
  - [ ] Show last sync time and status
  - [ ] Add filter functionality for viewing classes
  - [ ] Implement manual sync controls
- [ ] Implement basic forms for filtering
  - [ ] DateRangeFilterForm
  - [ ] TeacherFilterForm
  - [ ] SubjectFilterForm
- [ ] Build templates
  - [ ] Admin dashboard template with class session table
  - [ ] Calendar filters partial template
  - [ ] Sync status and controls
- [ ] Configure URL patterns
- [ ] Add minimal JavaScript for filter functionality
  - [ ] Date range selection
  - [ ] Filter application
  - [ ] Sync trigger buttons

## Phase 2: Financial Operations

### Step 5: Financial Calculations
- [ ] Create TeacherCompensationService
  - [ ] Implement hours calculation method
  - [ ] Implement compensation amount method
  - [ ] Add monthly report generation
- [ ] Create StudentPaymentService
  - [ ] Implement attendance calculation
  - [ ] Create payment due calculation
  - [ ] Add payment report generation
- [ ] Add utility functions
  - [ ] Class duration calculation
  - [ ] Hours by class type calculation
  - [ ] Summary statistics generation
- [ ] Write unit tests for calculation methods
- [ ] Implement data validation
  - [ ] Edge case handling
  - [ ] Financial data validation
  - [ ] Logging for calculations
- [ ] Test financial calculations

### Step 6: Financial Dashboard
- [ ] Create dashboard views
  - [ ] Financial overview view
  - [ ] Teacher compensation view
  - [ ] Student payment view
  - [ ] Report generation view
- [ ] Build dashboard templates
  - [ ] Financial overview template
  - [ ] Teacher compensation template
  - [ ] Student payment template
  - [ ] Report generation template
- [ ] Implement financial forms
  - [ ] Teacher compensation form
  - [ ] Student payment form
  - [ ] Report filter form
- [ ] Add data visualization
  - [ ] Monthly revenue chart
  - [ ] Teacher compensation summary
  - [ ] Student payment status
  - [ ] Attendance statistics
- [ ] Create export functionality
  - [ ] CSV export
  - [ ] PDF generation
  - [ ] Data filtering options
- [ ] Test financial dashboard

### Step 7: Payment Management
- [ ] Create PaymentTransaction model
  - [ ] Add detailed transaction fields
- [ ] Build payment recording system
  - [ ] Create payment form
  - [ ] Add receipt generation
  - [ ] Implement payment history view
- [ ] Implement financial notifications
  - [ ] Add pending payment notifications
  - [ ] Create unpaid invoice reminders
  - [ ] Set up email notifications
  - [ ] Add payment confirmations
- [ ] Build financial analytics
  - [ ] Revenue projections
  - [ ] Teacher earnings analysis
  - [ ] Student payment patterns
  - [ ] Financial health indicators
- [ ] Add batch operations
  - [ ] Bulk payment recording
  - [ ] Mass email for invoices
  - [ ] Batch report generation
  - [ ] Import/export functionality
- [ ] Test enhanced financial features

### Step 8: Enhanced Financial Features
- [ ] Create notification system
  - [ ] Payment due notifications
  - [ ] Overdue payment alerts
  - [ ] Payment confirmation emails
  - [ ] Financial report notifications
- [ ] Implement analytics
  - [ ] Revenue projections
  - [ ] Teacher earnings analysis
  - [ ] Student payment patterns
  - [ ] Financial health indicators
- [ ] Add batch operations
  - [ ] Bulk payment recording
  - [ ] Mass email for invoices
  - [ ] Batch report generation
  - [ ] Import/export functionality
- [ ] Create financial reports
  - [ ] Monthly revenue reports
  - [ ] Teacher compensation reports
  - [ ] Student payment reports
  - [ ] Financial health reports
- [ ] Implement data visualization
  - [ ] Revenue charts
  - [ ] Payment trend graphs
  - [ ] Teacher earnings charts
  - [ ] Student payment status charts
- [ ] Test enhanced financial features

## Phase 3: User Role Expansion

### Step 9: Expanded User Roles
- [ ] Update User model
  - [ ] Add role field with choices
  - [ ] Implement role-specific permissions
  - [ ] Create role checking middleware
- [ ] Enhance profile models
  - [ ] Add specialties, qualifications to TeacherProfile
  - [ ] Add grade_level, DOB to StudentProfile
  - [ ] Create ParentProfile with children relationship
- [ ] Implement user management views
  - [ ] UserListView
  - [ ] UserDetailView
  - [ ] UserCreateView and UserUpdateView
  - [ ] Role-specific registration
- [ ] Build user management templates
  - [ ] User list template
  - [ ] User detail template
  - [ ] User form templates
  - [ ] Role-specific profile forms
- [ ] Add permission decorators
- [ ] Test user role system

### Step 10: Teacher and Student Interfaces
- [ ] Create teacher dashboard
  - [ ] Upcoming classes display
  - [ ] Personal calendar view
  - [ ] Student list view
  - [ ] Compensation view
- [ ] Build student dashboard
  - [ ] Upcoming classes display
  - [ ] Personal calendar view
  - [ ] Payment status view
  - [ ] Progress view placeholder
- [ ] Implement parent dashboard
  - [ ] Children activities view
  - [ ] Children schedules view
  - [ ] Payment management view
  - [ ] Child progress view
- [ ] Add role-specific navigation
  - [ ] Role-based navigation bar
  - [ ] Role-specific sidebar
  - [ ] Dashboard quick links
  - [ ] Access controls
- [ ] Test role-specific interfaces

## Phase 4: Advanced Features

### Step 11: Homework Management
- [ ] Create homework models
  - [ ] Assignment model
  - [ ] Submission model
  - [ ] Feedback model
- [ ] Implement file handling
  - [ ] File upload functionality
  - [ ] File type validation
  - [ ] Secure storage
- [ ] Build assignment views
  - [ ] Assignment creation
  - [ ] Assignment listing
  - [ ] Submission handling
  - [ ] Feedback system
- [ ] Create notification system
  - [ ] New assignment alerts
  - [ ] Due date reminders
  - [ ] Submission confirmations
  - [ ] Feedback notifications
- [ ] Test homework system

### Step 12: Internationalization and Polish
- [ ] Set up language configuration
  - [ ] Configure i18n settings
  - [ ] Set up middleware
  - [ ] Configure URL patterns
- [ ] Create translation files
  - [ ] Extract strings
  - [ ] Provide Portuguese translations
  - [ ] Implement translation tags
- [ ] Build language switching
  - [ ] Language selector
  - [ ] Preference storage
  - [ ] URL handling
- [ ] Polish the UI
  - [ ] Enhance responsive design
  - [ ] Add loading indicators
  - [ ] Implement animations
  - [ ] Ensure accessibility
- [ ] Prepare for deployment
  - [ ] Configure production settings
  - [ ] Optimize static files
  - [ ] Set up error logging
  - [ ] Create documentation

## Final Validation
- [ ] Verify all features work together
- [ ] Check user flows for all roles
- [ ] Ensure data consistency across system
- [ ] Test system with real-world scenarios
- [ ] Validate all integrations (Google Calendar, etc.)
- [ ] Check language translations
- [ ] Verify responsive design on all devices
- [ ] Final security review
- [ ] Performance optimization review
- [ ] Documentation completeness check
