# Permissions Testing Guide

## Overview

This guide explains the comprehensive permissions testing setup created for the Aprende Comigo platform. The setup includes complex test data with multi-role users and comprehensive QA test cases to verify permissions, access control, and role-based functionality.

## Test Data Architecture

### Schools Created
- **Test School**: Primary school (ID: 1)
- **Test School 2**: Secondary school (ID: 2)
- **Test School 3**: Learning school (ID: 3)

### Main Test User: `test.manager@example.com`

This user has a unique multi-role setup across all three schools:
- **Test School**: `school_owner` (full management access)
- **Test School 2**: `teacher` (limited admin access)
- **Test School 3**: `student` (minimal learning access)

This creates a complex permissions scenario perfect for testing cross-school access control and role switching.

### Supporting Test Users

| Email | School | Role | Purpose |
|-------|--------|------|---------|
| `school2.admin@example.com` | Test School 2 | school_owner | Test isolated school management |
| `school3.owner@example.com` | Test School 3 | school_owner | Test isolated school management |
| `additional.teacher@example.com` | Test School | teacher | Test teacher permissions |
| `additional.student@example.com` | Test School | student | Test student permissions |
| `student2@testschool.com` | Test School 2 | student | Test cross-school student isolation |
| `teacher2@testschool.com` | Test School 3 | teacher | Test cross-school teacher isolation |

## Setting Up Test Data

### Management Command

The test data can be set up using the Django management command:

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source ../.venv/bin/activate

# Create test data (clean existing first)
python manage.py setup_permissions_test_data --clean

# Just preview what would be created (dry run)
python manage.py setup_permissions_test_data --dry-run

# Add new test data without cleaning existing
python manage.py setup_permissions_test_data
```

### Command Options

- `--clean`: Removes existing test data before creating new data
- `--dry-run`: Shows what would be created without actually creating it

### Verification

After running the command, you should see:
- 3 schools created
- 7 users created with appropriate roles
- Teacher profiles for users with teacher roles
- Student profiles for users with student roles
- All email verification flags set to true (for testing)

## QA Test Cases

Four comprehensive test cases have been created in the `qa-tests/perm/` directory:

### PERM-001: Multi-Role User Authentication
- **Purpose**: Verify multi-role user can authenticate and see appropriate dashboard
- **Focus**: Complex authentication with role detection
- **User**: `test.manager@example.com`

### PERM-002: Cross-School Access Control
- **Purpose**: Verify users cannot access unauthorized school data
- **Focus**: Access boundaries between schools
- **Users**: Various users with limited school access

### PERM-003: Role-Based Permissions Verification
- **Purpose**: Verify role permissions within authorized schools
- **Focus**: Owner vs Teacher vs Student capabilities
- **Users**: Multiple users with different roles in Test School

### PERM-004: School Context Switching
- **Purpose**: Verify context switching for multi-role users
- **Focus**: Interface adaptation based on current school/role
- **User**: `test.manager@example.com` (multi-role)

## Running the Tests

### Prerequisites

1. **Test Data Setup**:
   ```bash
   cd backend
   python manage.py setup_permissions_test_data --clean
   ```

2. **Start Servers**:
   ```bash
   # Backend (Terminal 1)
   cd backend
   python manage.py runserver 8000

   # Frontend (Terminal 2)
   cd frontend-ui
   npm run web:dev
   ```

3. **Verify Servers**:
   - Backend: http://localhost:8000/api/
   - Frontend: http://localhost:8081

### Test Execution

Each test case is in its own directory:
- `qa-tests/perm/perm-001/test-case.txt`
- `qa-tests/perm/perm-002/test-case.txt`
- `qa-tests/perm/perm-003/test-case.txt`
- `qa-tests/perm/perm-004/test-case.txt`

Follow the detailed step-by-step instructions in each test case file.

## Key Testing Scenarios

### 1. Multi-Role Authentication
- Login as `test.manager@example.com`
- Verify dashboard shows multiple school memberships
- Check role-specific navigation and features

### 2. Access Control Boundaries
- Test with `school2.admin@example.com` (only Test School 2 access)
- Verify cannot see Test School or Test School 3 data
- Test API access control with curl commands

### 3. Role Permission Verification
- Test owner capabilities (full access)
- Test teacher capabilities (limited admin)
- Test student capabilities (minimal access)
- Verify boundaries are enforced

### 4. Context Switching (Multi-Role User)
- Switch between Test School (owner), Test School 2 (teacher), Test School 3 (student)
- Verify interface adapts to each role
- Check data access changes appropriately

## Expected Permissions Matrix

### School Owner (`school_owner`)
- ✅ View all school data and members
- ✅ Manage school settings and configuration
- ✅ Create any type of user invitation
- ✅ Manage all user roles and memberships
- ✅ Access financial/billing information

### Teacher (`teacher`)
- ✅ View students and other teachers
- ✅ Manage assigned students (limited)
- ✅ Access teaching materials and classes
- ❌ Cannot access school settings
- ❌ Cannot create teacher/admin invitations
- ❌ Cannot access financial information

### Student (`student`)
- ✅ View own profile and information
- ✅ Access assigned learning materials
- ✅ View teachers (limited information)
- ❌ Cannot view other students' private data
- ❌ Cannot access any administrative functions
- ❌ Cannot create any invitations

## Common Issues and Troubleshooting

### Authentication Issues
- Ensure test users have `email_verified=True`
- Check Django logs for verification codes during testing
- In development, verification codes are logged to console

### Permission Issues
- Verify school memberships are active (`is_active=True`)
- Check user has correct role for the school being tested
- Confirm API permissions match expected behavior

### Data Issues
- Run setup command with `--clean` to reset data
- Verify educational system exists (Portugal system)
- Check that teacher/student profiles are created appropriately

### Frontend Issues
- Ensure both backend and frontend servers are running
- Check browser console for JavaScript errors
- Verify API endpoints are accessible

## API Testing Examples

### Get User Token
```bash
# Login via API to get auth token
curl -X POST -H "Content-Type: application/json" \
  -d '{"email":"test.manager@example.com","code":"123456"}' \
  http://localhost:8000/api/auth/verify-code/
```

### Test School Access
```bash
# Test school owner access (should see all members)
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/schools/1/members/

# Test unauthorized access (should get 403/404)
curl -H "Authorization: Token SCHOOL2_ADMIN_TOKEN" \
  http://localhost:8000/api/schools/1/members/
```

### Test Permission Boundaries
```bash
# Test creating invitation (owner should succeed, others fail)
curl -X POST -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"school":1,"email":"test@example.com","role":"student"}' \
  http://localhost:8000/api/invitations/
```

## Cleanup

### Remove Test Data
```bash
cd backend
python manage.py setup_permissions_test_data --clean
# (Run without creating new data)
```

### Stop Servers
```bash
# Kill backend server
pkill -f "python manage.py runserver"

# Kill frontend server
pkill -f "npm run web:dev"
```

## Next Steps

### Extending the Tests
1. Add more complex role combinations
2. Test inactive memberships and reactivation
3. Add tests for invitation flows
4. Test profile management across roles

### Automation
1. Consider creating Playwright automation for these tests
2. Add API-only test versions
3. Create performance tests with the multi-role data

### Integration
1. Include these tests in CI/CD pipeline
2. Create database fixtures for faster test setup
3. Add monitoring for permission boundary violations

## File Structure

```
qa-tests/perm/
├── latest_runs.csv              # Master tracking file
├── perm-001/                    # Multi-role authentication
│   ├── test-case.txt
│   └── runs.csv
├── perm-002/                    # Cross-school access control
│   ├── test-case.txt
│   └── runs.csv
├── perm-003/                    # Role-based permissions
│   ├── test-case.txt
│   └── runs.csv
└── perm-004/                    # School context switching
    ├── test-case.txt
    └── runs.csv

backend/accounts/management/commands/
└── setup_permissions_test_data.py  # Test data creation command
```

This comprehensive testing setup provides robust verification of the platform's permissions and access control systems.
