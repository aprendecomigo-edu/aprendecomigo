# Aprende Comigo Project Roadmap

This document outlines the planned features, tasks, and priorities for the Aprende Comigo platform development, organized by app and priority.

## Accounts App

The accounts app handles user management, authentication, and authorization for different user types across the platform.

### User Management

#### High Priority
- **Completed**
  - Basic user model with email-based authentication
  - User type system (manager, teacher, student, parent)
  - Student and Teacher profile models with specific fields
  - Username generation from email

- **In Progress**
  - Parent profile implementation and linking to student accounts
  - Educational functionary role implementation

- **Planned**
  - Admin dashboard for user management
  - User search and filtering functionality
  - Bulk user creation/import capability
  - User profile completion status tracking
  - User deactivation/archiving process
  - Student registration by parents
  - Teacher-student relationship management
  - School/organization structure for multi-tenant support

### Authentication

#### High Priority
- **Completed**
  - Passwordless authentication with TOTP codes
  - Email verification system
  - Knox token-based authentication
  - Rate limiting for auth endpoints

- **In Progress**
  - Session timeout and token refresh mechanisms

- **Planned**
  - Social login integration (Google, etc.)
  - Optional password-based authentication as fallback
  - Multi-factor authentication options
  - Authentication audit logging
  - Device tracking and management
  - Account recovery processes
  - Remember device functionality

### Authorization & Permissions

#### High Priority
- **In Progress**
  - Role-based permission system implementation
  - Permission definitions for each user type

- **Planned**
  - Granular permissions for data access
  - Parent access to student information
  - Teacher access to assigned students
  - Admin permission delegation
  - Permission groups and custom roles
  - Object-level permissions
  - API-based permission management

### Onboarding & User Experience

#### Medium Priority
- **In Progress**
  - Student onboarding flow

- **Planned**
  - Guided user onboarding by user type
  - Teacher profile setup wizard
  - Parent-student connection process
  - User profile image handling
  - Email notification preferences
  - Student discipline/subject preferences
  - Teacher specialty and availability setup
  - User dashboard customization
  - Account verification enhancements
  - Welcome email sequences

### Security & Compliance

#### High Priority
- **Completed**
  - Basic security features (rate limiting, secure tokens)
  - TOTP-based passwordless authentication
  - Email and IP-based rate limiting
  - Failed attempt tracking

- **In Progress**
  - Fix identified security vulnerabilities
  - Enhance permission controls
  - Expand security test coverage

- **Planned**
  - Field-level encryption for sensitive data
  - Token refresh mechanism implementation
  - Security audit logging
  - GDPR compliance features
  - Data retention policies
  - Personal data export functionality
  - Access attempt monitoring
  - Suspicious activity detection
  - Data minimization implementation

#### Security Action Items (Prioritized)
1. **High Risk**:
   - Replace default secret key in EmailVerificationCode model
   - Implement proper secret key rotation

2. **Medium Risk**:
   - Enhance permission checks for user-related views
   - Add object-level permissions for all ViewSets
   - Design and implement parent-student relationship permissions
   - Implement sensitive data encryption

3. **Low Risk**:
   - Add token refresh mechanism
   - Improve exception handling for auth-related operations
   - Implement constant-time comparison for verification codes
   - Add session timeout handling on frontend
   - Create data cleanup schedules for expired verification codes

### Technical Improvements

#### Medium Priority
- **Planned**
  - Comprehensive test coverage for auth flows
  - Authentication service refactoring
  - Performance optimization for user queries
  - Cached user permissions
  - API documentation for auth endpoints
  - User model indexing optimization
  - Scalable user storage architecture

## Next Actions for Accounts App

1. Complete parent profile model and link to student accounts
2. Finalize educational functionary role implementation
3. ✅ Implement comprehensive role-based permission system
4. Develop user onboarding flows for all user types
5. Add teacher-student relationship management
6. Implement session management and token refresh
7. Develop admin dashboard for user management
8. ✅ Add comprehensive test coverage for authentication flows
9. Implement field-level encryption for sensitive data (blocked by Django compatibility issue)
