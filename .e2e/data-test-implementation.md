# Data-Test Implementation Checklist

## Overview
This document tracks the implementation of `data-test` attributes across the Aprende Comigo platform. Check off items as they're implemented.

## Phase 1: Critical Path (MVP Testing)
*Goal: Enable basic E2E smoke tests*

### Registration Flow (`/signup/`)
- [x] **Tab Selection**
  - [x] `select-individual-tutor` - Individual tutor tab ✅
  - [x] `select-school-admin` - School admin tab ✅

- [x] **Core Form Inputs**
  - [x] `input-full-name` - User's full name ✅
  - [x] `input-email` - Email address ✅
  - [x] `input-school-name` - School name (admin only) ✅

- [x] **Critical Actions**
  - [x] `submit-registration` - Create account button ✅

- [x] **Success State**
  - [x] `success-registration` - Success message container ✅

### Dashboard (`/dashboard/`)
- [x] **Key Metric**
  - [x] `metric-teacher-count` - Teacher count with data-value ✅

- [ ] **Primary Navigation**
  - [ ] `navigate-dashboard` - Dashboard link
  - [ ] `navigate-settings` - Settings link

## Phase 2: Complete Registration Flow
*Goal: Test all registration scenarios*

### Registration Form - Extended
- [ ] **All Form Inputs**
  - [x] `input-phone` - Phone number ✅
  - [ ] `input-password` - Password field
  - [ ] `input-password-confirm` - Password confirmation
  - [ ] `input-school-address` - School address
  - [ ] `input-school-phone` - School phone

- [ ] **Validation States**
  - [ ] `error-validation` - Validation error container
  - [ ] `error-email-taken` - Email already exists error
  - [ ] `error-password-weak` - Weak password error

- [ ] **Loading States**
  - [ ] `loading-registration` - Form submission loading

### Email Verification
- [ ] `section-email-verification` - Verification prompt
- [ ] `input-verification-code` - Code input
- [ ] `submit-verification` - Verify button
- [ ] `resend-verification` - Resend code link

## Phase 3: Dashboard - Core Features
*Goal: Test main dashboard functionality*

### Dashboard Statistics
- [ ] **All Metrics** (with data-value attributes)
  - [ ] `metric-student-count` - Total students
  - [ ] `metric-session-count` - Active sessions
  - [ ] `metric-monthly-revenue` - Revenue with data-currency

### Task Management
- [ ] **Task Section**
  - [ ] `section-pending-tasks` - Tasks container
  - [ ] `list-tasks` - Task list
  - [ ] `item-task` - Individual task (with data-task-id, data-task-type)

- [ ] **Task Actions**
  - [ ] `complete-task` - Mark task complete
  - [ ] `dismiss-task` - Dismiss/skip task


## Phase 4: Teacher Management
*Goal: Test teacher CRUD operations*

### Teacher List (`/teachers/`)
- [ ] **List View**
  - [ ] `list-teachers` - Teacher list container
  - [ ] `item-teacher` - Teacher item (with data-teacher-id)
  - [ ] `empty-teachers` - Empty state

- [ ] **Actions**
  - [ ] `add-teacher` - Add teacher button
  - [ ] `search-teachers` - Search input
  - [ ] `filter-teacher-status` - Status filter dropdown

### Add Teacher Modal
- [ ] **Modal**
  - [ ] `modal-add-teacher` - Modal container (with data-modal-state)

- [ ] **Form Inputs**
  - [ ] `input-teacher-name` - Teacher name
  - [ ] `input-teacher-email` - Teacher email
  - [ ] `input-teacher-subjects` - Subjects taught

- [ ] **Actions**
  - [ ] `submit-teacher` - Save teacher
  - [ ] `cancel-add-teacher` - Cancel button

### Teacher Details
- [ ] `view-teacher` - View details link
- [ ] `edit-teacher` - Edit button
- [ ] `delete-teacher` - Delete button
- [ ] `modal-confirm-delete` - Delete confirmation

## Phase 5: Student Management
*Goal: Test student CRUD operations*

### Student List (`/students/`)
- [ ] **List View**
  - [ ] `list-students` - Student list container
  - [ ] `item-student` - Student item (with data-student-id)
  - [ ] `empty-students` - Empty state

- [ ] **Pagination (HTMX)**
  - [ ] `load-more-students` - Load more button
  - [ ] `container-students` - HTMX target container

### Add Student Flow
- [ ] `modal-add-student` - Modal container
- [ ] `input-student-name` - Student name
- [ ] `input-student-email` - Student email
- [ ] `input-student-grade` - Grade level
- [ ] `select-student-teacher` - Assign teacher
- [ ] `submit-student` - Save student

## Phase 6: Session Management
*Goal: Test tutoring session features*

### Session Creation
- [ ] `create-session` - Create session button
- [ ] `input-session-date` - Date picker
- [ ] `input-session-time` - Time picker
- [ ] `select-session-student` - Student selection
- [ ] `select-session-teacher` - Teacher selection
- [ ] `input-session-duration` - Duration
- [ ] `submit-session` - Create session

### Session List
- [ ] `list-sessions` - Sessions container
- [ ] `item-session` - Session item (with data-session-id, data-session-status)
- [ ] `filter-session-date` - Date filter
- [ ] `filter-session-status` - Status filter

## Phase 7: PWA Features
*Goal: Test Progressive Web App functionality*

### Offline Indicators
- [ ] `status-offline` - Offline indicator
- [ ] `status-online` - Online indicator
- [ ] `modal-offline-warning` - Offline warning modal

### Install Prompt
- [ ] `prompt-install-pwa` - Install app prompt
- [ ] `dismiss-install` - Dismiss install
- [ ] `accept-install` - Install app button

## Implementation Guidelines

### For Developers

1. **When adding new features:**
   - Check this list for required data-test attributes
   - Follow patterns in `data-test-conventions.md`
   - Add new items to this checklist if not present

2. **Testing priority:**
   - Phase 1 = Smoke tests (must have)
   - Phase 2-3 = Core functionality (should have)
   - Phase 4-7 = Complete coverage (nice to have)

3. **PR Checklist:**
   - [ ] Added data-test to new interactive elements
   - [ ] Used correct naming pattern
   - [ ] Updated this checklist if adding new features

### For QA Team

1. **Test Coverage Tracking:**
   - Each checked item should have corresponding E2E test
   - Report missing data-test attributes as bugs
   - Prioritize testing based on phase

2. **Test Writing Order:**
   - Write Phase 1 tests first (critical path)
   - Add Phase 2-3 tests for regression suite
   - Phases 4-7 for comprehensive coverage
