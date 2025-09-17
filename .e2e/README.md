# E2E Tests for Aprende Comigo

This directory contains End-to-End tests for the Aprende Comigo educational platform, focusing on critical user flows and business logic validation.

## Test Coverage

### Student Account Creation Tests
- **Student with Guardian** (`test_add_student_with_guardian.py`) - Tests creation of accounts where both student and guardian get separate login access
- **Guardian-Only Account** (`test_add_guardian_only_account.py`) - Tests creation where only guardian gets login access to manage young child
- **Adult Student** (`test_add_adult_student.py`) - Tests creation of independent adult student accounts

### Test Categories
- Authentication flows
- Multi-tenant functionality
- Form validation
- Business rule enforcement
- UI interaction patterns

## Prerequisites

1. **Install Dependencies**:
   ```bash
   cd /Users/anapmc/Code/aprendecomigo
   pip install pytest-playwright
   playwright install chromium
   ```

2. **Start Local Development Server**:
   ```bash
   python manage.py runserver
   ```

3. **Ensure Test Admin User Exists**:
   The tests require a superuser with credentials:
   - Email: test@admin.com
   - Password: testpass123

   Create it with:
   ```bash
   python manage.py shell -c "
   from accounts.models import CustomUser
   user = CustomUser.objects.create_superuser('test@admin.com', 'testpass123', name='Test Admin')
   print(f'Created superuser: {user.email}')
   "
   ```

## Running Tests

### Local Development Server
```bash
cd .e2e
pytest --env=local
```

### Staging Environment
```bash
cd .e2e
pytest --env=staging
```

### Specific Test Categories
```bash
# Run only student creation tests
pytest -m student_creation

# Run only authentication tests
pytest -m auth

# Run a specific test file
pytest tests/auth/test_add_student_with_guardian.py

# Run with browser visible (for debugging)
pytest --headed
```

### Test Options
- `--env=local|staging` - Environment to test against
- `--headed` - Show browser window during tests
- `--video=retain-on-failure` - Record video on test failures
- `--screenshot=only-on-failure` - Take screenshots on failures

## Test Data

Tests use generated test data with unique emails and phone numbers to avoid conflicts:
- Student emails: `student.{timestamp}.{random}@e2e.test`
- Guardian emails: `guardian.{timestamp}.{random}@e2e.test`
- Phone numbers: `+351 9{random_8_digits}`

## Test Structure

- `conftest.py` - Pytest configuration and fixtures
- `fixtures/` - Test data and utilities
- `utils/` - Base test classes and helpers
- `tests/auth/` - Authentication and user management tests

## Data Test Attributes

Tests use `data-test` attributes for reliable element selection:
- `data-test="add-student-button"` - Add Student button
- `data-test="account-type-separate"` - Student with Guardian radio button
- `data-test="student-name-input"` - Student name input field
- `data-test="submit-student-form"` - Form submit button

## Business Rules Tested

1. **Student with Guardian Account**:
   - Both student and guardian get separate accounts
   - Student can access classes, guardian handles payments
   - Both email addresses are required and must be unique

2. **Guardian-Only Account**:
   - Only guardian gets login account
   - Student profile created without login credentials
   - Guardian manages everything for the child

3. **Adult Student Account**:
   - Single account with full permissions
   - Student manages classes, payments, and profile
   - No guardian involvement required

## Debugging Tests

1. **Run with browser visible**: `pytest --headed`
2. **Check screenshots**: Test artifacts saved in `test-results/`
3. **Review test logs**: Use `-v` for verbose output
4. **Debug specific test**: `pytest tests/auth/test_add_student_with_guardian.py::TestAddStudentWithGuardian::test_successful_student_with_guardian_creation -v --headed`

## Test Maintenance

- Tests automatically clean up browser state between runs
- Test data uses timestamps to avoid conflicts
- Failed tests generate screenshots and videos for debugging
- Tests can run in parallel with `pytest -n auto` (if pytest-xdist installed)
