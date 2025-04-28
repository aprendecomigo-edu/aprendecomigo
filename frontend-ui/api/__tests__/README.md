# Authentication Testing Strategy

This directory contains tests for the authentication flow in our React Native application. These tests ensure that:

1. The app redirects to the login screen when the user is not authenticated
2. The app redirects to the dashboard when the user is authenticated
3. The authentication flow works correctly on all supported platforms (iOS, Android, Web)

## Test Files

- **authentication-flow.test.tsx**: Tests the core authentication flow logic using React TestRenderer
- **platform-auth.test.tsx**: Tests platform-specific authentication behavior on iOS, Android, and Web

## Testing Approach

We've used React TestRenderer to directly test the authentication logic without requiring a full React Native environment. This approach avoids compatibility issues with testing libraries and provides a more reliable test suite.

Key patterns used:
- Mock Platform.OS to simulate different platforms
- Test components with refs to prevent infinite re-renders
- Proper component unmounting to prevent memory leaks
- Isolated tests for each authentication scenario

## Running Tests

```bash
# Run all authentication flow tests
npx jest api/__tests__/authentication-flow.test.tsx api/__tests__/platform-auth.test.tsx

# Run with detailed output
npx jest api/__tests__/authentication-flow.test.tsx api/__tests__/platform-auth.test.tsx --verbose
```

## Notes for Future Test Development

1. Use TestRenderer instead of react-testing-library for component testing to avoid compatibility issues
2. For platform-specific tests, set Platform.OS directly rather than using jest.spyOn
3. Always use useRef with a boolean flag to prevent multiple effect triggers in test components
4. Always unmount test components after assertions are complete
5. Create minimal test components that focus on the specific behavior being tested
