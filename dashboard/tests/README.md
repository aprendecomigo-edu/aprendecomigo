# Dashboard Tests

## PeopleView Test Suite

This directory contains comprehensive tests for the refactored PeopleView in `dashboard/views.py`, which handles creating different types of users for the school management system.

### Test Coverage

The test suite covers all three account type scenarios:

1. **STUDENT_GUARDIAN** - Both student and guardian have accounts, guardian handles finances
2. **ADULT_STUDENT** - Student manages everything themselves  
3. **GUARDIAN_ONLY** - Student has no account, guardian manages everything

### Test Classes

- `PeopleViewTestCase` - Base test case with common setup
- `PeopleViewGetRequestsTests` - Tests for GET requests and template rendering
- `PeopleViewStudentGuardianTests` - Tests for STUDENT_GUARDIAN account type creation
- `PeopleViewAdultStudentTests` - Tests for ADULT_STUDENT account type creation  
- `PeopleViewGuardianOnlyTests` - Tests for GUARDIAN_ONLY account type creation
- `PeopleViewErrorHandlingTests` - Tests for error handling and edge cases
- `PeopleViewAuthorizationTests` - Tests for authentication and authorization
- `PeopleViewAddTeacherTests` - Tests for teacher addition functionality
- `PeopleViewPartialRenderingTests` - Tests for HTMX partial template rendering
- `PeopleViewIntegrationTests` - Integration tests for complete workflows

### Key Features Tested

#### HTTP Request/Response Handling
- Authentication requirements for GET/POST requests
- Correct HTTP status codes
- Template rendering and context data
- Form submission handling

#### Account Type Creation
- User and profile creation for all three scenarios
- School membership assignment
- Guardian-student relationships
- Permission service integration
- Transaction handling and rollback on errors

#### Form Validation
- Required field validation
- Invalid account type handling
- Checkbox field processing
- Date and email validation

#### Authorization
- School membership-based access control
- Superuser privileges
- Cross-school data isolation

#### Error Handling
- Database transaction rollback
- PermissionService exception handling
- Invalid form data
- Missing school memberships

#### Mocking and Dependencies
- PermissionService.setup_permissions_for_student() calls
- External service dependencies
- Database transaction management

### Running Tests

```bash
# Run all PeopleView tests
python manage.py test dashboard.tests.test_people_view

# Run specific test class
python manage.py test dashboard.tests.test_people_view.PeopleViewAdultStudentTests

# Run with verbose output
python manage.py test dashboard.tests.test_people_view --verbosity=2
```

### Test Results Summary

As of the latest run:
- ✅ GET request tests pass
- ✅ Adult student creation works correctly
- ✅ Authentication and authorization tests pass
- ✅ Error handling tests pass
- ✅ Form validation tests pass
- ⚠️ Student-Guardian and Guardian-Only scenarios have issues in the actual view implementation

### Known Issues

Some tests reveal potential issues in the PeopleView implementation:
1. Student-Guardian creation may not be working as expected
2. Guardian-Only creation may have form processing issues
3. Some edge cases in user/profile creation need investigation

These failing tests provide valuable feedback for debugging the actual view implementation.

### Integration with Existing Tests

These view tests complement the existing permission system tests in:
- `accounts/tests/test_permission_system.py` (34 tests for permission logic)
- `accounts/tests/test_models.py` (model-level validation)

The view tests focus specifically on HTTP request/response handling while the permission tests focus on business logic.