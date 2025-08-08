/**
 * Authentication Testing Utilities
 * 
 * This file provides utilities and helpers specifically for testing authentication components.
 * It follows React Native Testing Library best practices for user-centric testing.
 */

import React from 'react';
import { render, RenderOptions } from '@testing-library/react-native';

// Mock providers for authentication tests
const MockAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <>{children}</>;
};

const MockToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <>{children}</>;
};

const MockSafeAreaProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <div className="safe-area-provider">{children}</div>;
};

/**
 * Custom render function that wraps components with necessary providers for auth testing
 */
export const renderWithProviders = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    return (
      <MockSafeAreaProvider>
        <MockToastProvider>
          <MockAuthProvider>
            {children}
          </MockAuthProvider>
        </MockToastProvider>
      </MockSafeAreaProvider>
    );
  };

  return render(ui, { wrapper: Wrapper, ...options });
};

/**
 * Utility to create mock authentication API responses
 */
export const createMockAuthApiResponse = (success: boolean, data?: any) => {
  if (success) {
    return Promise.resolve(data || { success: true });
  } else {
    return Promise.reject(new Error('Authentication failed'));
  }
};

/**
 * Utility to create mock router functions with call tracking
 */
export const createMockRouter = () => {
  const mockPush = jest.fn();
  const mockBack = jest.fn();
  const mockReplace = jest.fn();

  return {
    push: mockPush,
    back: mockBack,
    replace: mockReplace,
    // For testing purposes, return the mock functions for assertions
    _mocks: {
      push: mockPush,
      back: mockBack,
      replace: mockReplace,
    }
  };
};

/**
 * Utility to create mock toast functions
 */
export const createMockToast = () => {
  const mockShowToast = jest.fn();
  const mockClose = jest.fn();
  const mockCloseAll = jest.fn();

  return {
    showToast: mockShowToast,
    close: mockClose,
    closeAll: mockCloseAll,
    // For testing purposes, return the mock functions for assertions
    _mocks: {
      showToast: mockShowToast,
      close: mockClose,
      closeAll: mockCloseAll,
    }
  };
};

/**
 * Wait for async operations to complete in tests
 */
export const flushPromises = () => new Promise(resolve => setImmediate(resolve));

/**
 * Mock user factory for testing
 */
export const createMockAuthUser = (overrides: any = {}) => ({
  id: 1,
  email: 'user@example.com',
  name: 'Test User',
  role: 'student',
  isAuthenticated: true,
  hasCompletedOnboarding: false,
  createdAt: new Date().toISOString(),
  ...overrides,
});

/**
 * Mock token response factory
 */
export const createMockTokenResponse = (overrides: any = {}) => ({
  success: true,
  token: 'mock_jwt_token_' + Math.random(),
  refreshToken: 'mock_refresh_token_' + Math.random(),
  expiresAt: Date.now() + 3600000, // 1 hour from now
  user: createMockAuthUser(),
  ...overrides,
});

/**
 * Create auth test wrapper component
 */
export const createAuthTestWrapper = (component: React.ReactElement) => {
  const AuthTestWrapper = ({ children }: { children: React.ReactNode }) => (
    <MockSafeAreaProvider>
      <MockToastProvider>
        <MockAuthProvider>
          {children}
        </MockAuthProvider>
      </MockToastProvider>
    </MockSafeAreaProvider>
  );
  
  return React.cloneElement(component, { wrapper: AuthTestWrapper });
};

/**
 * Mock authenticated user scenario
 */
export const mockAuthenticatedUser = (user = createMockAuthUser()) => {
  // Mock auth context or state management
  return {
    user,
    isAuthenticated: true,
    token: 'valid_token',
  };
};

/**
 * Mock unauthenticated user scenario
 */
export const mockUnauthenticatedUser = () => {
  return {
    user: null,
    isAuthenticated: false,
    token: null,
  };
};

/**
 * Simulate token expiry scenario
 */
export const simulateTokenExpiry = () => {
  return {
    error: 'Token expired',
    status: 401,
    shouldRefresh: true,
  };
};

/**
 * Simulate session recovery
 */
export const simulateSessionRecovery = () => {
  return {
    success: true,
    user: createMockAuthUser(),
    token: createMockTokenResponse().token,
  };
};

/**
 * Common test data for authentication
 */
export const AUTH_TEST_DATA = {
  validEmails: [
    'user@example.com',
    'test.email@domain.co.uk',
    'user+tag@example-domain.com',
    'first.last@subdomain.example.org'
  ],
  invalidEmails: [
    'invalid-email',
    '@domain.com',
    'user@',
    'user space@domain.com',
    'user..double@domain.com'
  ],
  validCodes: [
    '123456',
    '000000',
    '999999'
  ],
  invalidCodes: [
    '12345',   // too short
    '1234567', // too long
    'abcdef',  // non-numeric
    '12 456',  // contains space
  ]
};

/**
 * Helper to test form validation
 */
export const testFormValidation = async (
  getByTestId: any,
  getByText: any,
  inputTestId: string,
  submitText: string,
  invalidValue: string,
  expectedErrorMessage: string
) => {
  const { fireEvent, waitFor } = require('@testing-library/react-native');
  
  const input = getByTestId(inputTestId);
  const submitButton = getByText(submitText);
  
  // Enter invalid value
  fireEvent.changeText(input, invalidValue);
  fireEvent.press(submitButton);
  
  // Wait for validation error to appear
  await waitFor(() => {
    expect(getByText(expectedErrorMessage)).toBeTruthy();
  });
};

/**
 * Helper to test loading states
 */
export const testLoadingState = async (
  getByText: any,
  submitText: string,
  loadingText: string,
  asyncAction: () => Promise<void>
) => {
  const { fireEvent, waitFor } = require('@testing-library/react-native');
  
  const submitButton = getByText(submitText);
  
  // Start async action
  fireEvent.press(submitButton);
  
  // Check loading state appears
  await waitFor(() => {
    expect(getByText(loadingText)).toBeTruthy();
  });
  
  // Wait for action to complete
  await asyncAction();
  
  // Check loading state disappears
  await waitFor(() => {
    expect(getByText(submitText)).toBeTruthy();
  });
};
