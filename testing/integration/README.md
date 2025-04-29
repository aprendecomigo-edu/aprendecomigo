# Aprende Conmigo Integration Tests

This directory contains integration tests and E2E tests for the Aprende Conmigo application.

## Directory Structure

- `api-tests/`: API integration tests (using axios)
  - `auth-flow.test.js`: Basic authentication flow tests
- `e2e/`: End-to-end tests for the mobile app (using Detox)
  - `login.test.js`: Login flow E2E tests
  - `registration-email.test.js`: Email registration flow E2E tests
  - `registration-phone.test.js`: Phone registration flow E2E tests
  - `verification-code.test.js`: Verification code validation E2E tests
  - `secondary-contact.test.js`: Secondary contact verification E2E tests
  - `primary-contact-change.test.js`: Primary contact change E2E tests
  - `role-permissions.test.js`: Role-based permissions E2E tests

## Authentication Flow Tests

The following E2E tests cover the complete user authentication flow:

1. **Email Registration**
   - Validates registration form
   - Mocks email verification code delivery
   - Tests verification code validation
   - Validates successful registration and login

2. **Phone Registration**
   - Tests phone number validation
   - Mocks SMS verification code delivery
   - Handles international phone formats
   - Tests rate limiting for SMS delivery

3. **Verification Code Validation**
   - Tests code format validation
   - Handles expired codes
   - Implements rate limiting
   - Tests time-based expiration

4. **Secondary Contact Verification**
   - Tests adding secondary email and phone contacts
   - Verifies both contacts are properly marked as verified
   - Tests session timeout during verification
   - Ensures unverified contacts can't be used for authentication

5. **Changing Primary Contact**
   - Tests changing primary contact method (email to phone, etc.)
   - Requires password re-authentication
   - Verifies login with new primary contact works
   - Ensures old primary contact no longer works for login

6. **Role-Based Permissions**
   - Tests different UI elements for different user roles
   - Verifies proper HTTP status codes (401/403) for permission errors
   - Tests permission boundaries for each role
   - Ensures proper access control for sensitive actions

## Running the Tests

To run all E2E tests:

```bash
cd testing
npm run e2e:build:ios && npm run e2e:test:ios
# or
npm run e2e:build:android && npm run e2e:test:android
```

To run a specific test:

```bash
cd testing
npx detox test -c ios.sim.debug e2e/registration-email.test.js
```

## Development Notes

### Test Element IDs

These tests rely on specific `testID` props being set in the React Native components. Make sure these IDs are consistent with what's expected in the tests. Key IDs include:

- `login-screen`, `registration-screen`, `verification-screen`
- `email-input`, `phone-input`, `password-input`
- `verification-code-input`, `verify-button`, `resend-code-button`
- Various role-specific elements like `admin-panel-button`, `classes-button`, etc.

### Mocking Strategy

The tests use axios-mock-adapter to mock API responses. This approach allows us to:

- Test without sending real emails/SMS
- Simulate different server responses
- Control time-based operations
- Test error conditions systematically

### Potential Issues

1. **Deep Linking**: Tests rely on deep linking for authenticated state. Ensure your app handles deeplinks properly.
2. **Timeouts**: Some tests have explicit timeouts. You may need to adjust these based on your device/emulator performance.
3. **Element Selection**: If tests fail with "element not found", check that the testIDs match between your components and tests.

### Next Steps

- Add API integration tests to complement these E2E tests
- Implement test reporting with screenshots on failure
- Add performance benchmarks for critical flows
