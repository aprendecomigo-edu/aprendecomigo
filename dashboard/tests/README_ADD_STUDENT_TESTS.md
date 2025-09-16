# Add Student Integration Test Suite

This directory contains comprehensive integration tests for the Add Student functionality in the Django application. These tests are designed to catch critical bugs in the form submission flow that complement the existing tests in `test_people_view.py`.

## Test Overview

The Add Student functionality supports three different account types:

1. **STUDENT_GUARDIAN**: Both student and guardian have separate user accounts
2. **GUARDIAN_ONLY**: Only guardian has an account, student info is stored as profile without user account
3. **ADULT_STUDENT**: Adult student manages their own account with full permissions

## Test Files

### 1. `test_add_student_integration.py`
Main integration tests covering:
- **HTMX Form Submission Flows**: Complete HTMX request/response cycles
- **Field Validation Edge Cases**: Age validation, email formats, date handling
- **Data Integrity**: Database constraints, transaction rollbacks
- **Multi-tenant Behavior**: School isolation, cross-school access
- **Security**: XSS prevention, SQL injection, CSRF protection
- **Error Handling**: Permission failures, missing systems, concurrent submissions
- **Business Logic**: Age requirements, account type consistency

### 2. `test_htmx_response_validation.py`
HTMX-specific response validation:
- **Response Headers**: HX-Trigger, HX-Target validation
- **Success Responses**: Proper HTML fragment structure
- **Error Responses**: Validation error display
- **Partial Rendering**: Modal vs inline form handling
- **Form Interactions**: Reset behavior, concurrent submissions

### 3. `test_model_constraints_integration.py`
Model and database constraint testing:
- **StudentProfile Constraints**: Account type validation rules
- **GuardianStudentRelationship**: Relationship constraints
- **Database Integrity**: Unique constraints, foreign keys
- **Form Constraint Integration**: How forms handle constraint violations
- **Model Validation**: Clean method enforcement

### 4. `test_add_student_runner.py`
Test suite organization and runner utilities:
- **Test Categorization**: Organize tests by functionality
- **Selective Running**: Run specific test categories
- **Quick Test Suite**: Critical tests for CI/CD
- **Test Discovery**: Find and categorize all tests

## Running Tests

### Run All Add Student Tests
```bash
python manage.py test dashboard.tests.test_add_student_integration dashboard.tests.test_htmx_response_validation dashboard.tests.test_model_constraints_integration
```

### Run Specific Test Categories

#### HTMX Tests Only
```bash
python manage.py test dashboard.tests.test_add_student_integration.HTMXAddStudentIntegrationTests
python manage.py test dashboard.tests.test_htmx_response_validation
```

#### Validation Tests Only
```bash
python manage.py test dashboard.tests.test_add_student_integration.FieldValidationEdgeCaseTests
python manage.py test dashboard.tests.test_add_student_integration.BusinessLogicValidationTests
```

#### Database/Constraint Tests Only
```bash
python manage.py test dashboard.tests.test_model_constraints_integration
python manage.py test dashboard.tests.test_add_student_integration.DataIntegrityConstraintTests
```

#### Security Tests Only
```bash
python manage.py test dashboard.tests.test_add_student_integration.FormSecurityTests
python manage.py test dashboard.tests.test_add_student_integration.MultiTenantBehaviorTests
```

### Run Tests with Coverage
```bash
coverage run --source='.' manage.py test dashboard.tests.test_add_student_integration
coverage report
coverage html
```

### Run Tests in Parallel (faster for large suites)
```bash
python manage.py test --parallel dashboard.tests.test_add_student_integration
```

## Test Categories Explained

### HTMX Integration Tests
These tests ensure the HTMX form submission flow works correctly:

- **Headers**: Verify HX-Trigger, HX-Target headers are set correctly
- **Responses**: Ensure responses are HTML partials, not full pages
- **Success Flow**: Form submission → database changes → HTMX response → list refresh
- **Error Flow**: Validation errors → error partial → no list refresh
- **Behavior Differences**: HTMX vs regular requests

**Why Important**: HTMX responses must be properly formatted or the frontend will break silently.

### Field Validation Tests
Test edge cases that could cause silent failures:

- **Age Validation**: Adult students must be 18+ (business rule)
- **Email Formats**: Unicode, special characters, malformed emails
- **Date Edge Cases**: Future dates, leap years, invalid formats
- **Name Handling**: Unicode, very long names, empty names
- **School Year Validation**: Valid years for educational system

**Why Important**: Invalid data could be saved without proper validation, causing downstream issues.

### Database Constraint Tests
Ensure database-level integrity:

- **Unique Constraints**: Email uniqueness, profile uniqueness
- **Foreign Keys**: Proper cascade behavior
- **Model Validation**: Account type consistency rules
- **Transaction Rollback**: Failures don't leave partial data

**Why Important**: Database constraints are the last line of defense against data corruption.

### Multi-tenant Tests
Verify school isolation and access control:

- **School Isolation**: Admins can only access their schools
- **Cross-school Guardians**: Guardians can have students in multiple schools
- **Superuser Access**: Superusers can access all schools

**Why Important**: Multi-tenant bugs could expose data across organizations.

### Security Tests
Prevent common web vulnerabilities:

- **XSS Prevention**: Form inputs are properly sanitized
- **SQL Injection**: Parameterized queries prevent injection
- **CSRF Protection**: Forms require valid CSRF tokens

**Why Important**: Security vulnerabilities could compromise user data.

## Key Test Patterns

### 1. HTMX Response Testing Pattern
```python
def test_htmx_response(self):
    response = self.client.post(
        self.url,
        form_data,
        HTTP_HX_REQUEST="true",  # HTMX header
        HTTP_HX_TARGET="#target-element",
    )

    # Check response is HTMX-compatible
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.get("HX-Trigger"), "refreshStudents")

    # Check response is HTML partial
    content = response.content.decode()
    self.assertNotIn("<html>", content)
    self.assertIn("success", content.lower())
```

### 2. Transaction Rollback Testing Pattern
```python
def test_transaction_rollback(self):
    with patch("service.method", side_effect=Exception("Test error")):
        response = self.client.post(self.url, form_data)

    # Verify no data was saved due to rollback
    self.assertFalse(User.objects.filter(email="test@test.com").exists())
```

### 3. Model Constraint Testing Pattern
```python
def test_model_constraint(self):
    with self.assertRaises(ValidationError) as context:
        invalid_model.full_clean()

    self.assertIn("constraint violation message", str(context.exception))
```

## Critical Test Cases

These tests catch the most common bugs:

### 1. Age Validation for Adult Students
```python
def test_adult_student_age_validation(self):
    # Ensures minors cannot be created as adult students
```

### 2. HTMX Response Headers
```python
def test_successful_submission_has_refresh_trigger(self):
    # Ensures frontend receives proper signals to refresh the list
```

### 3. Account Type Consistency
```python
def test_adult_student_cannot_have_guardian(self):
    # Ensures business rules are enforced at model level
```

### 4. Transaction Rollback
```python
def test_database_transaction_rollback_on_error(self):
    # Ensures partial data isn't saved when errors occur
```

### 5. Multi-tenant Isolation
```python
def test_admin_can_only_add_students_to_their_schools(self):
    # Ensures school isolation is maintained
```

## Edge Cases Covered

### Data Edge Cases
- **Unicode names**: José María García-López
- **Empty required fields**: Missing names, emails, dates
- **Invalid dates**: Future birth dates, leap years
- **Long inputs**: 150+ character names
- **Special characters**: Apostrophes, hyphens in names

### Business Logic Edge Cases
- **Minor adult students**: 16-year-old trying to be adult student
- **Duplicate emails**: Same email across different account types
- **Missing educational systems**: No default system available
- **Concurrent submissions**: Race conditions in user creation

### Technical Edge Cases
- **HTMX vs regular requests**: Different response handling
- **Transaction failures**: Permission service failures
- **Constraint violations**: Database integrity errors
- **Missing dependencies**: Educational systems, schools

## Test Data Patterns

### Valid Test Data Generators
```python
def _get_valid_student_guardian_data(self):
    return {
        "action": "add_student",
        "account_type": "separate",
        "student_name": "Test Student",
        "student_email": "test.student@school.com",
        "student_birth_date": "2008-01-15",
        "guardian_name": "Test Guardian",
        "guardian_email": "guardian@family.com",
        # ... additional fields
    }
```

### Invalid Test Data for Edge Cases
```python
invalid_emails = [
    "notanemail",
    "missing@",
    "@domain.com",
    "spaces @domain.com",
]
```

## Debugging Failed Tests

### 1. HTMX Response Issues
- Check response headers: `response.get("HX-Trigger")`
- Verify response is partial: `assertNotIn("<html>", content)`
- Check response size: should be small for partials

### 2. Validation Failures
- Check model `full_clean()` is called
- Verify business rules in model `clean()` methods
- Test both form-level and model-level validation

### 3. Database Constraint Issues
- Use `TransactionTestCase` for constraint testing
- Check foreign key relationships
- Verify unique constraints are enforced

### 4. Multi-tenant Issues
- Verify user has correct school memberships
- Check school filtering in views
- Test superuser access separately

## Extending the Test Suite

### Adding New Account Type Tests
1. Create test data generator in base test class
2. Add validation tests for new business rules
3. Add HTMX response tests for new form fields
4. Add constraint tests for new model relationships

### Adding New Validation Tests
1. Identify edge cases for new fields
2. Create both valid and invalid test data
3. Test both form validation and model validation
4. Test error message clarity

### Adding New Security Tests
1. Test new form fields for XSS vulnerabilities
2. Test new database queries for SQL injection
3. Test new permissions for authorization bypass
4. Test new CSRF token requirements

## Performance Considerations

### Fast Tests
- Use `TestCase` for tests that don't need transaction rollback
- Mock external services (PermissionService)
- Use minimal test data

### Slow Tests
- Use `TransactionTestCase` only when testing actual transactions
- Test real database constraints
- Test concurrent access scenarios

### Test Organization
- Group related tests in same class
- Use `setUpClass` for expensive setup shared across tests
- Use `setUp` for test-specific setup only

## Common Pitfalls

### 1. Not Testing HTMX Headers
```python
# Bad: Not checking HTMX response headers
response = self.client.post(url, data, HTTP_HX_REQUEST="true")
self.assertEqual(response.status_code, 200)

# Good: Verify HTMX headers
response = self.client.post(url, data, HTTP_HX_REQUEST="true")
self.assertEqual(response.get("HX-Trigger"), "refreshStudents")
```

### 2. Not Testing Transaction Rollback
```python
# Bad: Not verifying rollback behavior
with patch("service.method", side_effect=Exception()):
    response = self.client.post(url, data)

# Good: Verify no data was saved
with patch("service.method", side_effect=Exception()):
    response = self.client.post(url, data)
self.assertFalse(User.objects.filter(email="test@test.com").exists())
```

### 3. Not Testing Model Constraints
```python
# Bad: Only testing form validation
response = self.client.post(url, invalid_data)
self.assertContains(response, "error")

# Good: Also test model-level validation
with self.assertRaises(ValidationError):
    invalid_model.full_clean()
```

### 4. Not Testing Multi-tenant Isolation
```python
# Bad: Only testing happy path
response = self.client.post(url, data)
self.assertEqual(response.status_code, 200)

# Good: Test cross-school access
other_school_admin = User.objects.create_user(...)
self.client.force_login(other_school_admin)
response = self.client.post(url, data)
# Verify proper isolation
```

## Integration with CI/CD

### Quick Test Suite for Pull Requests
```python
class AddStudentQuickTestSuite(TestCase):
    def test_critical_functionality(self):
        # Run only the most critical tests for fast feedback
```

### Full Test Suite for Deployments
Run all test files before production deployment:
```bash
python manage.py test dashboard.tests.test_add_student_integration dashboard.tests.test_htmx_response_validation dashboard.tests.test_model_constraints_integration --parallel
```

### Coverage Requirements
Aim for >95% code coverage on Add Student functionality:
```bash
coverage run --source='dashboard.views' manage.py test dashboard.tests.test_add_student_*
coverage report --show-missing
```

This comprehensive test suite ensures that the Add Student functionality is robust, secure, and reliable across all supported use cases and edge conditions.
