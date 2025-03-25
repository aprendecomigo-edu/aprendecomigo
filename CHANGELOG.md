# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-03-25

### Added
- Initial project setup with Django 5.1.7
- Custom User model using email as identifier
  - Fields: email, name, phone_number, is_admin
  - Custom user manager for email-based authentication
- Authentication system
  - Login functionality using Django's built-in auth views
  - Logout functionality
  - Password reset flow with custom templates
- Base templates
  - Base template with navigation bar
  - Dashboard template
  - Login template in registration directory
  - Password reset templates
- Test coverage
  - User model tests
  - Authentication tests
  - Root URL behavior tests
  - UI tests using Selenium
- Project structure
  - accounts app for user management
  - Initial database migrations
  - Development settings configuration

### Changed
- Moved from custom login view to Django's built-in authentication views
- Reorganized templates to follow Django's convention
  - Authentication templates in templates/registration/
  - Dashboard template in templates root

### Fixed
- Template path issues by properly organizing templates
- Login redirect issues by configuring proper URL patterns 