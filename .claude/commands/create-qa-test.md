# Create New QA Test - Test Case Creation Command

Create one or more new QA test cases based on the provided requirements: $ARGUMENTS

## Overview
This command will guide you through creating new QA test cases with proper folder structure, documentation, and tracking files. Each test case will be properly organized and ready for execution.

## QA Test Folder Structure Explained

### Directory Organization
```
qa-tests/
├── [category]/                     # Test category (auth, navigation, forms, etc.)
│   ├── latest_runs.csv                   # Master list of latest runs for each test in this category. Same nr of rows as nr of tests in this category
│   ├── [test-id]/                  # Individual test case folder
│   │   ├── test-case.txt          # Test instructions (STATIC - never changes)
│   │   ├── runs.csv               # All historical runs tracking
│   │   └── run-YYYYMMDD-HHMMSS/   # Timestamped run results (created during execution)
│   │       ├── server.log         # Django server logs from test run
│   │       ├── results.md         # Detailed results and analysis
│   │       └── screenshots/       # Screenshots captured during test
│   └── [next-test-id]/
└── [next-category]/
```

### File Purposes

#### 1. `[category]/latest_runs.csv`
**Purpose:** Master tracking file for latest run of each test in a category
**Format:**
```csv
test_id,test_name,description,last_run,overall_status,total_runs,pass_count,fail_count
auth-001,School Manager Login,Passwordless email verification for school manager,20250703-110500,FAIL,1,0,1
auth-002,Invalid Email Test,Test login with non-existent email,,,0,0,0
```

#### 2. `[test-id]/test-case.txt`
**Purpose:** Complete test instructions that never change
**Contains:**
- Test overview (ID, name, purpose)
- Context and prerequisites
- Detailed step-by-step instructions
- Expected outcomes for each step
- Pass/fail criteria
- **NO actual results** (those go in run folders)

#### 3. `[test-id]/runs.csv`
**Purpose:** Historical tracking of all runs for this specific test
**Format:**
```csv
run_id,timestamp,overall_result,steps_passed,steps_failed,browser,environment,notes
run-20250703-110500,2025-07-03T11:05:00Z,FAIL,6,1,Playwright Chrome,macOS development,Dashboard route missing
```

#### 4. `run-YYYYMMDD-HHMMSS/` (Created during test execution)
**Purpose:** Contains all artifacts from a specific test run
- `server.log` - Backend server logs
- `results.md` - Detailed test results and analysis
- `screenshots/` - All screenshots from the test run

#### 5. Development Server Logs (Project Root)
**Purpose:** Live development server logs accessible during testing
- `logs/backend.log` - Django development server logs (use: make logs)
- `logs/frontend.log` - Expo development server logs (use: make logs)

## Test ID Naming Convention

### Format: `[category]-[number]`
- **Category:** 3-4 letter abbreviation (auth, nav, form, dash)
- **Number:** 3-digit zero-padded number (001, 002, 003)
- **Examples:** auth-001, auth-002, nav-001, form-001, dash-001

### Category Guidelines
- **auth** - Authentication and authorization tests
- **nav** - Navigation and routing tests
- **form** - Form submission and validation tests
- **dash** - Dashboard and UI component tests
- **api** - API endpoint tests
- **perf** - Performance and load tests

## Step-by-Step Test Creation Process

### Step 1: Analyze Test Requirements
Based on the provided requirements: "$ARGUMENTS"

1. **Identify Test Category:**
   - What part of the application is being tested?
   - Does the category already exist in qa-tests/?
   - If new category, what should it be called?

2. **Determine Test Scope:**
   - Single test case or multiple test cases?
   - What user roles are involved?
   - What data is needed?

3. **Define Test Objectives:**
   - What is the primary goal of each test?
   - What constitutes success vs failure?
   - What edge cases need coverage?

### Step 2: Create Directory Structure

#### A. Create Category Directory (if new)
```bash
# Create new category directory
mkdir -p qa-tests/[category]

# Create category index file
cat > qa-tests/[category]/latest_runs.csv << EOF
test_id,test_name,description,last_run,overall_status,total_runs,pass_count,fail_count
EOF
```

#### B. Create Test Case Directory
```bash
# Determine next test ID
# Check existing tests: ls qa-tests/[category]/
# Use next sequential number
ls qa-tests/[category]/
mkdir -p qa-tests/[category]/[test-id]

# Create runs tracking file
cat > qa-tests/[category]/[test-id]/runs.csv << EOF
run_id,timestamp,overall_result,steps_passed,steps_failed,browser,environment,notes
EOF
```

### Step 3: Create Test Case Documentation

#### Template for test-case.txt
```
QA Test Case: [Test Name]

Test ID: [TEST-ID]
Test Name: [Descriptive Test Name]
Purpose: [What this test verifies]
Expected Result: [What should happen when test passes]

=== CONTEXT (Pre-test Requirements) ===

System Information:
- Project: Aprende Comigo - Educational platform
- Architecture: Django REST backend + React Native frontend
- [Additional relevant system info]

Required Environment Setup:
1. Project Location: /Users/anapmc/Code/aprendecomigo/
2. Python Virtual Environment: .venv/ in project root
3. Environment Variables: (automatically set by make dev)
   - DJANGO_ENV=development
   - EXPO_PUBLIC_ENV=development

Test Data:
- [List all required test data]
- [User accounts, emails, etc.]
- [Any database state requirements]

=== DETAILED STEP-BY-STEP INSTRUCTIONS ===

Step 1: [Step Name]
[Detailed instructions]
Commands (if any):
  [bash commands]

Expected: [What should happen]
Screenshot: [screenshot_name.png] (if applicable)

Step 2: [Next Step]
[Continue for all steps...]

=== PASS/FAIL CRITERIA ===

PASS: [Conditions for overall test success]
FAIL: [Conditions for overall test failure]

Individual Step Criteria:
- Step 1: PASS if [condition], FAIL if [condition]
- Step 2: PASS if [condition], FAIL if [condition]
[Continue for all steps...]

Overall Result: PASS only if ALL steps pass, FAIL if ANY step fails
```

### Step 4: Update Category runs

Add the new test to the category's latest_runs.csv (replace previous run if applicable):
```csv
[test-id],[Test Name],[Description],,[status],0,0,0
```

## Example: AUTH-001 Test Case

### Directory Structure
```
qa-tests/auth/auth-001/
├── test-case.txt       # Complete test instructions
└── runs.csv           # Empty initially, populated after runs
```

### test-case.txt Content (Abbreviated)
```
QA Test Case: School Manager Login Authentication

Test ID: AUTH-001
Test Name: School Manager Login Authentication Flow
Purpose: Verify that a school manager can successfully authenticate using passwordless email verification
Expected Result: User successfully logs in and reaches the dashboard

=== CONTEXT ===
Test Data:
- Test Email: anapmc.carvalho@gmail.com
- User Role: school_owner

=== STEPS ===
Step 1: Environment Setup
Commands:
  make dev
  [additional setup commands]

Step 2: Navigate to Application
1. Open browser to http://localhost:8081
2. Verify login page loads
Screenshot: 01_signin_page_loaded.png
Debug: Use 'make logs' to view server logs if issues occur

[Additional steps...]

=== PASS/FAIL CRITERIA ===
PASS: All steps complete AND user reaches functional dashboard
FAIL: Any step fails OR dashboard doesn't work
```

## Test Creation Guidelines

### 1. Test Independence
- Each test should be self-contained
- Don't rely on state from previous tests
- Include all necessary setup in test instructions

### 2. Clear Instructions
- Write instructions for someone who doesn't know the project
- Include all commands and expected outcomes
- Specify exact text to enter, buttons to click

### 3. Comprehensive Coverage
- Test happy path (expected successful flow)
- Test error conditions (invalid input, timeouts)
- Test edge cases (boundary conditions)

### 4. Screenshot Strategy
- Capture screenshots at key decision points
- Name screenshots descriptively with step numbers
- Document when each screenshot should be taken

### 5. Data Requirements
- Specify all required test data upfront
- Include database state requirements
- Document any test user accounts needed

## Common Test Patterns

### Authentication Tests
- Login flows (valid/invalid credentials)
- Registration processes
- Password reset flows
- Session management

### Navigation Tests
- Page routing and navigation
- Menu functionality
- Back/forward button behavior
- Deep linking

### Form Tests
- Form validation (client and server side)
- Required field handling
- Input format validation
- Submission success/failure

### Dashboard/UI Tests
- Component rendering
- User role-based content
- Interactive elements
- Responsive design

## Test Data Management

### User Accounts
- Document which test users are needed
- Specify required roles and permissions
- Include email addresses and any special setup

### Database State
- Describe required data setup
- Include any specific records needed
- Document cleanup requirements

## Integration with Existing Tests

### When Adding to Existing Category
1. Check existing test IDs to avoid conflicts
2. Use next sequential number
3. Update category index.csv
4. Follow existing naming patterns

### When Creating New Category
1. Choose clear, short category name
2. Create new index.csv
3. Document category purpose
4. Consider how it relates to other categories

## Validation Checklist

Before finalizing a new test case:

- [ ] Test ID follows naming convention
- [ ] Directory structure is correct
- [ ] test-case.txt is complete and clear
- [ ] All required test data is documented
- [ ] Pass/fail criteria are specific
- [ ] Screenshot points are identified
- [ ] Category index.csv is updated
- [ ] Instructions are self-contained

  === UX/BEHAVIORAL REQUIREMENTS ===
  - Button only visible when action is actually available
  - Modal closes automatically after successful submission
  - Clear success/error feedback provided
  - Loading states prevent double-submission

## Example Usage

Create a test for invalid login:
```
/project:create-qa-test Create a test that verifies login fails gracefully when user enters an email that doesn't exist in the database. Should show appropriate error message and not crash.
```

Create multiple navigation tests:
```
/project:create-qa-test Create tests for the main navigation: 1) Test that all menu items are clickable and lead to correct pages, 2) Test breadcrumb navigation works correctly, 3) Test that back button works from any page.
```

This framework ensures consistent, maintainable, and comprehensive test case creation that integrates seamlessly with the existing QA structure.
