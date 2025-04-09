# School Management Platform Implementation Plan (Feature-Driven Approach)

## Blueprint Overview

This document outlines a feature-driven implementation plan for building a School Management Platform, focusing on the financial and operational aspects using Django REST Framework and React Native. The plan prioritizes delivering core functionality: reading calendar data from Google Calendar and performing financial calculations/reporting based on this data, while enabling cross-platform deployment for web, iOS, and Android.

## Feature-Driven Development Phases

### Phase 1: API Foundation & Authentication
- Set up Django REST Framework project
- Implement JWT-based authentication
- Create core data models
- Build API endpoints for essential functionality

### Phase 2: React Native Foundation & Calendar Integration
- Set up React Native project with web support
- Implement authentication flows
- Create Google Calendar integration
- Build cross-platform UI components

### Phase 3: Financial Operations
- Implement financial API endpoints
- Create mobile-friendly financial UI
- Build reporting system
- Enable payment tracking

### Phase 4: User Role Expansion & Advanced Features
- Expand user roles and permissions
- Add mobile-specific features (notifications, offline support)
- Implement homework management
- Prepare for app store deployment

## Detailed Implementation Steps

Let's break these phases into smaller, focused implementation steps that deliver working functionality at each stage:

## Phase 1: API Foundation & Authentication - Implementation Steps

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

## Phase 2: React Native Foundation & Calendar Integration - Implementation Steps

### Step 5: React Native Setup
- Set up React Native project with web support
- Implement authentication flows
- Create Google Calendar integration
- Build cross-platform UI components

### Step 6: Calendar Models and Google Integration
- Implement minimal Subject and ClassType models
- Create ClassSession model for storing calendar data
- Set up Google Calendar API read-only integration
- Build a parsing mechanism to extract:
  - Student name from event title
  - Teacher name from location field
  - Price code from description field
  - Duration from start/end times
  - Absence status from "FALTOU" marking

### Step 7: Financial Foundation Models
- Create TeacherProfile with compensation rates
- Implement StudentProfile with payment info
- Build PaymentPlan model
- Create StudentPayment model
- Implement TeacherCompensation model

### Step 8: Admin Calendar Interface
- Create admin dashboard template
- Implement calendar view component
- Build class scheduling interface
- Add basic CRUD operations for classes

## Phase 3: Financial Operations - Implementation Steps

### Step 9: Financial Calculations
- Implement teacher hours calculation from calendar
- Create student payment calculation logic
- Build basic reporting functions
- Add financial data validation

### Step 10: Financial Dashboard
- Create financial overview dashboard
- Implement teacher compensation reports
- Build student payment tracking interface
- Add export functionality for reports

### Step 11: Payment Management
- Implement payment recording system
- Create payment history tracking
- Build invoice generation
- Add payment status monitoring

### Step 12: Enhanced Financial Features
- Implement financial notifications
- Add detailed financial analytics
- Build batch operations for admin
- Create financial health indicators

## Phase 4: User Role Expansion & Advanced Features - Implementation Steps

### Step 13: Expanded User Roles
- Enhance user model with additional roles
- Implement role-based permissions system
- Create profile management for all roles
- Build user management interface

### Step 14: Teacher and Student Interfaces
- Create teacher dashboard
- Implement student schedule view
- Build parent dashboard for child monitoring
- Add role-specific calendar views

### Step 15: Communication System
- Implement notification preferences
- Create messaging system between users
- Build announcement functionality
- Add email notifications

### Step 16: Profile and Settings
- Create user profile management
- Implement account settings
- Build preference configuration
- Add privacy controls

### Step 17: Homework Management
- Implement assignment models
- Create submission system
- Build file upload functionality
- Add feedback mechanism

### Step 18: Internationalization and Polish
- Set up language configuration
- Implement UI translations
- Enhance mobile responsiveness
- Prepare for deployment

## Implementation Prompts

Below are the implementation prompts for a code-generation LLM to build each step, focusing on incremental feature delivery:

### Prompt 1: Project Setup and API Foundation

```
Create a new Django project for a School Management Platform with a focus on API development:

0. Setup virtualenv that uses the latest version of python3 with the latest version of Django
1. Create a new Django project named "aprendecomigo"
2. Configure settings.py with:
   - PostgreSQL database configuration
   - DRF and JWT settings
   - CORS configuration for React Native
   - Static file configurations
3. Create a minimal project structure with these initial apps:
   - accounts: For user management
   - scheduling: For calendar functionality
   - financials: For financial tracking
   - api: For API endpoints and serializers
4. Implement a custom User model in accounts/models.py:
   - Email as the primary identifier
   - Fields: name, phone_number, is_admin (boolean)
5. Create JWT authentication:
   - Token-based authentication setup
   - Token refresh mechanism
   - Password reset via email
6. Set up basic API endpoints:
   - User authentication endpoints
   - User profile endpoints
   - Basic health check endpoints
7. Set up a requirements.txt with essential dependencies:
   - Django
   - djangorestframework
   - djangorestframework-simplejwt
   - django-cors-headers
   - psycopg2-binary
   - python-dotenv
   - Pillow
   - google-auth, google-api-python-client (for Calendar API)

Provide the complete project structure, models, serializers, views, and configurations for this initial setup.
```

### Prompt 2: React Native Foundation

```
Set up a React Native project with web support for the School Management Platform:

1. Create a new React Native project with Expo:
   - Initialize with TypeScript template
   - Configure for web support
   - Set up directory structure for cross-platform development

2. Implement the basic UI components:
   - Design system with platform-specific styling
   - Navigation structure (bottom tabs for mobile, sidebar for web)
   - Authentication screens (login, signup, password reset)
   - Dashboard layout

3. Create authentication services:
   - JWT token management
   - Secure storage for credentials
   - Google OAuth integration
   - API client setup

4. Set up state management:
   - User authentication state
   - API request/response handling
   - Error handling
   - Loading states

5. Implement responsive layouts:
   - Mobile-first design
   - Web adaptations
   - Platform-specific UI adjustments

Provide the complete React Native project structure, key components, authentication services, and navigation setup.
```

### Prompt 3: Calendar Models and API Endpoints

```
Implement calendar models and API endpoints for the School Management Platform:

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

2. Create serializers for these models:
   - SubjectSerializer
   - ClassTypeSerializer
   - ClassSessionSerializer with nested teacher and students

3. Create API viewsets and endpoints:
   - Subject API endpoints (list, retrieve)
   - ClassType API endpoints (list, retrieve)
   - ClassSession API endpoints (list, retrieve, filter)
   - Endpoints for calendar data synchronization

4. Implement Google Calendar integration:
   - OAuth2 flow for Google Calendar API (read-only access)
   - Store admin credentials securely
   - Handle token refresh and management
   - Implement calendar sync API endpoint

5. Create React Native calendar components:
   - Calendar view for different platforms
   - Class session details view
   - Schedule view for teachers and students

Provide the complete models, serializers, viewsets, URL patterns, and calendar integration services.
```

### Prompt 4: Financial Models and API Endpoints

```
Implement financial models and API endpoints for the School Management Platform:

1. Create these models in the financials app:
   - PaymentPlan:
     * name, description
     * plan_type (monthly/package)
     * rate, hours_included, expiration_period
     * class_type (ForeignKey, optional)

   - StudentPayment:
     * student (ForeignKey to User)
     * payment_plan (ForeignKey to PaymentPlan)
     * amount_paid, payment_date
     * period fields for monthly plans
     * hours fields for package plans
     * status (pending, completed, cancelled)

   - TeacherCompensation:
     * teacher (ForeignKey to User)
     * period_start, period_end
     * class_sessions (ManyToManyField)
     * hours_taught, amount_owed, amount_paid
     * payment_date, status

2. Create serializers for these models:
   - PaymentPlanSerializer
   - StudentPaymentSerializer
   - TeacherCompensationSerializer
   - Financial summary serializers

3. Create API viewsets and endpoints:
   - PaymentPlan API endpoints
   - StudentPayment API endpoints
   - TeacherCompensation API endpoints
   - Financial reporting endpoints

4. Implement financial calculation services:
   - Payment management
   - Hours calculation
   - Compensation calculation
   - Reporting services

5. Create React Native financial components:
   - Financial dashboard
   - Payment management screens
   - Teacher compensation view
   - Student payment tracking

Provide the complete models, serializers, viewsets, URL patterns, and financial services.
```

### Prompt 5: User Roles and Permissions

```
Implement user roles and permissions for the School Management Platform:

1. Enhance the User model with roles:
   - Add role field with choices (admin, teacher, student, parent)
   - Create profile models for each role
   - Add permissions based on roles

2. Create role-based API permissions:
   - Custom permission classes
   - Role-based viewset mixins
   - Object-level permissions for user data

3. Implement API endpoints for role management:
   - User role assignment
   - Profile management
   - Role-based data access

4. Create React Native role-specific components:
   - Admin dashboard
   - Teacher dashboard
   - Student dashboard
   - Parent dashboard

5. Implement role-based navigation:
   - Different navigation options based on user role
   - Role-specific screens and actions
   - Permission-based UI elements

Provide the complete user role models, permissions, viewsets, and role-based components.
```

### Prompt 6: Advanced Features and Mobile-Specific Functionality

```
Implement advanced features and mobile-specific functionality:

1. Create homework assignment system:
   - Homework models and serializers
   - File upload API endpoints
   - Submission tracking and grading

2. Implement mobile notifications:
   - Push notification service
   - Notification preferences
   - Event-based notifications

3. Add offline capabilities:
   - Local data storage
   - Synchronization on reconnection
   - Conflict resolution

4. Implement deep linking:
   - App URL schemes
   - Universal links/app links
   - Navigation from notifications

5. Prepare for app store deployment:
   - iOS app configuration
   - Android app configuration
   - App store assets
   - Deployment scripts

Provide the complete homework system, notification service, offline capabilities, and app configuration.
```

## Conclusion

This implementation plan takes a feature-driven approach, focusing first on the core calendar management and financial reporting functionality. Each step builds incrementally on previous work, ensuring that you have working features at each stage rather than building all models and views upfront.

The first two phases deliver the core functionality described in your requirements: admins managing calendars and generating financial reports. Later phases expand on this foundation to add more advanced features and support for additional user roles.

This approach allows for earlier feedback and testing of the most critical features, while still maintaining a structured path to the complete platform.
