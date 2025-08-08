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
