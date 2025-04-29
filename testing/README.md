# Aprende Conmigo Testing Framework

This directory contains testing utilities, integration tests, and E2E tests for the Aprende Conmigo application.

## Testing Philosophy

Our testing approach follows best practices for each technology:

- **Django Backend**: Tests live within each Django app (`tests.py` or `tests/` directory)
- **React Native Frontend**: Tests are colocated with components in `__tests__` directories
- **Integration/E2E Tests**: Live in this central `/testing` directory

## Directory Structure

- `backend/`: Backend test utilities, fixtures, and helpers
- `frontend/`: Frontend test utilities, fixtures, and helpers
- `integration/`: Integration and E2E tests
  - `api-tests/`: API integration tests
  - `e2e/`: Detox E2E tests for mobile apps
    - `registration-email.test.js`: Email registration flow tests
    - `registration-phone.test.js`: Phone registration flow tests
    - `verification-code.test.js`: Verification code validation tests
    - `secondary-contact.test.js`: Secondary contact verification tests
    - `primary-contact-change.test.js`: Primary contact change tests
    - `role-permissions.test.js`: Role-based permissions tests
  - `web/`: Playwright web UI tests
    - `auth/`: Authentication tests for web
      - `password-reset.spec.js`: Password reset flow tests
- `scripts/`: Automation scripts for testing workflow

## Running Tests

### Django Backend Unit Tests

```bash
cd backend
python manage.py test

# Or with pytest
pytest
```

### React Native Unit Tests

```bash
cd frontend-ui
npm test

# Run with coverage
npm test --coverage
```

### API Integration Tests

```bash
cd testing
npm install
node integration/api-tests/auth-flow.test.js
```

### Mobile E2E Tests (Detox)

```bash
cd testing
npm install
npm run prepare:e2e  # Sets up the test environment

# Run all auth tests on iOS
npm run test:auth:ios

# Run all auth tests on Android
npm run test:auth:android

# Run a specific test file
cd frontend-ui
npx detox test -c ios.sim.debug e2e/basic.e2e.js
```

### Web E2E Tests (Playwright)

```bash
cd testing
npm install
npx playwright install  # Install browsers for Playwright

# Run all web tests
npm run test:web

# Run with UI mode for debugging
npm run test:web:ui

# Run specific password reset tests
npm run test:web:password-reset
```

## Authentication E2E Tests

Our authentication E2E tests cover seven key areas:

1. **Email Registration**: Tests the complete email-based registration flow, including validation, verification codes, and successful completion.

2. **Phone Registration**: Tests phone-based registration with international format validation, SMS verification, and handling of rate limiting.

3. **Verification Code Validation**: Tests code validation including format validation, expiration handling, and rate limiting.

4. **Secondary Contact Verification**: Tests the addition and verification of secondary contact methods.

5. **Primary Contact Change**: Tests changing the primary contact method, including re-authentication and proper update of authentication tokens.

6. **Role-Based Permissions**: Tests role-specific UI elements and proper permission boundaries between different user roles.

7. **Password Reset (Web)**: Tests the complete password reset flow, including requesting a reset, verifying the code, setting a new password, and validating password requirements.

## Dependency Management

This project uses npm for dependency management. To ensure the stability and security of dependencies:

```bash
# Update dependencies to their latest compatible versions
npm update

# Run security audit and fix issues
npm run audit:fix

# Clean install dependencies
npm ci  # Use instead of npm install in CI environments
```

Key dependency policies:
- Dependencies are pinned to specific major versions with ^ to allow minor updates
- All direct dependencies are listed in package.json
- Package overrides are used to fix transitive dependency issues
- Security audits are run automatically on CI builds

## Testing Best Practices

### Backend Tests

- Use the fixtures provided in `testing/backend/conftest.py`
- Test permission rules with different user types
- Use factories for generating test data
- Test both positive and negative cases

### Frontend Tests

- Use React Test Renderer for component testing
- Mock API calls and external dependencies
- Test component behavior, not implementation details
- Test important user workflows

### Integration Tests

- Focus on API contracts and authentication flows
- Test error cases and boundary conditions
- Verify the frontend and backend work together correctly

### E2E Tests

- Test critical user journeys
- Cover login, navigation, and core functionality
- Keep tests independent and isolated
- Clean up test data after tests run

## CI Integration

Tests are automatically run on GitHub Actions workflows when code is pushed to the repository.
