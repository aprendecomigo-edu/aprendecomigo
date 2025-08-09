import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';

import { SignIn } from '@/components/auth/SignIn';
import { renderWithProviders, createMockRouter, createMockToast, AUTH_TEST_DATA } from '../../utils/auth-test-utils';

// Mock the auth API
const mockRequestEmailCode = jest.fn();
jest.mock('@/api/authApi', () => ({
  requestEmailCode: mockRequestEmailCode,
}));

// Mock router
const mockRouter = createMockRouter();
jest.mock('@unitools/router', () => ({
  __esModule: true,
  default: () => mockRouter,
}));

// Mock toast
const mockToast = createMockToast();
jest.mock('@/components/ui/toast', () => ({
  useToast: () => mockToast,
}));

// Mock Keyboard
jest.mock('react-native', () => ({
  ...jest.requireActual('react-native'),
  Keyboard: {
    dismiss: jest.fn(),
  },
}));

describe('SignIn Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockRequestEmailCode.mockClear();
    mockRouter._mocks.push.mockClear();
    mockRouter._mocks.back.mockClear();
    mockToast._mocks.showToast.mockClear();
  });

  describe('Basic Rendering', () => {
    it('should render main elements correctly', () => {
      const { getByText, getByPlaceholderText } = renderWithProviders(<SignIn />);
      
      // Check main heading
      expect(getByText('Login')).toBeTruthy();
      
      // Check brand name
      expect(getByText('Aprende Comigo')).toBeTruthy();
      
      // Check email input
      expect(getByPlaceholderText('your_email@example.com')).toBeTruthy();
      
      // Check send code button
      expect(getByText('Send Login Code')).toBeTruthy();
    });

    it('should render signup link', () => {
      const { getByText } = renderWithProviders(<SignIn />);
      
      expect(getByText("Don't have an account?")).toBeTruthy();
      expect(getByText('Sign up')).toBeTruthy();
    });
  });

  describe('Form Validation', () => {
    it('should show validation error for empty email', async () => {
      const { getByText, queryByText } = renderWithProviders(<SignIn />);
      
      const sendCodeButton = getByText('Send Login Code');
      
      // Submit without entering email
      fireEvent.press(sendCodeButton);
      
      await waitFor(() => {
        expect(queryByText('Email is required')).toBeTruthy();
      });
    });

    it('should show validation error for invalid email format', async () => {
      const { getByPlaceholderText, getByText, queryByText } = renderWithProviders(<SignIn />);
      
      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');
      
      // Enter invalid email formats
      for (const invalidEmail of AUTH_TEST_DATA.invalidEmails) {
        fireEvent.changeText(emailInput, invalidEmail);
        fireEvent.press(sendCodeButton);
        
        await waitFor(() => {
          expect(queryByText('Please enter a valid email address')).toBeTruthy();
        });
      }
    });

    it('should accept valid email formats', async () => {
      const { getByPlaceholderText, getByText, queryByText } = renderWithProviders(<SignIn />);
      
      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');
      
      // Mock successful API response
      mockRequestEmailCode.mockResolvedValue({ success: true });
      
      // Test valid email formats
      for (const validEmail of AUTH_TEST_DATA.validEmails) {
        fireEvent.changeText(emailInput, validEmail);
        
        await act(async () => {
          fireEvent.press(sendCodeButton);
        });
        
        // Should not show validation errors
        expect(queryByText('Please enter a valid email address')).toBeFalsy();
        expect(queryByText('Email is required')).toBeFalsy();
      }
    });
  });

  describe('User Interactions', () => {
    it('should handle email input changes', () => {
      const { getByPlaceholderText } = renderWithProviders(<SignIn />);
      
      const emailInput = getByPlaceholderText('your_email@example.com');
      
      fireEvent.changeText(emailInput, 'test@example.com');
      
      expect(emailInput.props.value).toBe('test@example.com');
    });

    it('should submit form when send code button is pressed', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<SignIn />);
      
      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');
      
      fireEvent.changeText(emailInput, 'test@example.com');
      
      await act(async () => {
        fireEvent.press(sendCodeButton);
      });
      
      expect(mockRequestEmailCode).toHaveBeenCalledWith({ email: 'test@example.com' });
    });

    it('should navigate to verify code page on successful submission', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<SignIn />);
      
      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');
      
      fireEvent.changeText(emailInput, 'test@example.com');
      
      await act(async () => {
        fireEvent.press(sendCodeButton);
      });
      
      await waitFor(() => {
        expect(mockRouter._mocks.push).toHaveBeenCalledWith('/auth/verify-code?email=test%40example.com');
      });
    });

    it('should show success toast on successful submission', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<SignIn />);
      
      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');
      
      fireEvent.changeText(emailInput, 'test@example.com');
      
      await act(async () => {
        fireEvent.press(sendCodeButton);
      });
      
      await waitFor(() => {
        expect(mockToast._mocks.showToast).toHaveBeenCalledWith('success', 'Verification code sent to your email!');
      });
    });
  });

  describe('Loading States', () => {
    it('should show loading state during submission', async () => {
      // Create a delayed promise to test loading state
      let resolvePromise: (value: any) => void;
      const delayedPromise = new Promise(resolve => {
        resolvePromise = resolve;
      });
      mockRequestEmailCode.mockReturnValue(delayedPromise);
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<SignIn />);
      
      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');
      
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.press(sendCodeButton);
      
      // Should show loading state
      await waitFor(() => {
        expect(getByText('Sending Code...')).toBeTruthy();
      });
      
      // Resolve the promise
      await act(async () => {
        resolvePromise!({ success: true });
      });
      
      // Should return to normal state
      await waitFor(() => {
        expect(getByText('Send Login Code')).toBeTruthy();
      });
    });

    it('should disable button during submission', async () => {
      // Create a delayed promise
      let resolvePromise: (value: any) => void;
      const delayedPromise = new Promise(resolve => {
        resolvePromise = resolve;
      });
      mockRequestEmailCode.mockReturnValue(delayedPromise);
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<SignIn />);
      
      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');
      
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.press(sendCodeButton);
      
      // Button should be disabled during loading
      await waitFor(() => {
        expect(sendCodeButton.props.accessibilityState?.disabled).toBe(true);
      });
      
      // Resolve the promise
      await act(async () => {
        resolvePromise!({ success: true });
      });
    });
  });

  describe('Error Handling', () => {
    it('should show error toast on API failure', async () => {
      mockRequestEmailCode.mockRejectedValue(new Error('Network error'));
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<SignIn />);
      
      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');
      
      fireEvent.changeText(emailInput, 'test@example.com');
      
      await act(async () => {
        fireEvent.press(sendCodeButton);
      });
      
      await waitFor(() => {
        expect(mockToast._mocks.showToast).toHaveBeenCalledWith('error', 'Failed to send verification code. Please try again.');
      });
    });

    it('should reset loading state after error', async () => {
      mockRequestEmailCode.mockRejectedValue(new Error('Network error'));
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<SignIn />);
      
      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');
      
      fireEvent.changeText(emailInput, 'test@example.com');
      
      await act(async () => {
        fireEvent.press(sendCodeButton);
      });
      
      // Should show error message and return to normal state
      await waitFor(() => {
        expect(getByText('Send Login Code')).toBeTruthy();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle rapid successive submissions gracefully', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<SignIn />);
      
      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');
      
      fireEvent.changeText(emailInput, 'test@example.com');
      
      // Rapid clicking
      await act(async () => {
        fireEvent.press(sendCodeButton);
        fireEvent.press(sendCodeButton);
        fireEvent.press(sendCodeButton);
      });
      
      // Should only make one API call
      await waitFor(() => {
        expect(mockRequestEmailCode).toHaveBeenCalledTimes(1);
      });
    });

    it('should trim whitespace from email input', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<SignIn />);
      
      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');
      
      fireEvent.changeText(emailInput, '  test@example.com  ');
      
      await act(async () => {
        fireEvent.press(sendCodeButton);
      });
      
      expect(mockRequestEmailCode).toHaveBeenCalledWith({ email: 'test@example.com' });
    });

    it('should handle special characters in email', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<SignIn />);
      
      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');
      
      const specialEmail = 'user+test@sub.domain.com';
      fireEvent.changeText(emailInput, specialEmail);
      
      await act(async () => {
        fireEvent.press(sendCodeButton);
      });
      
      expect(mockRequestEmailCode).toHaveBeenCalledWith({ email: specialEmail });
    });
  });

  describe('Accessibility', () => {
    it('should have proper accessibility labels', () => {
      const { getByText, getByPlaceholderText } = renderWithProviders(<SignIn />);
      
      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');
      
      // Check that elements are accessible
      expect(emailInput).toBeTruthy();
      expect(sendCodeButton).toBeTruthy();
    });

    it('should support keyboard navigation', () => {
      const { getByPlaceholderText } = renderWithProviders(<SignIn />);
      
      const emailInput = getByPlaceholderText('your_email@example.com');
      
      // Check keyboard properties
      expect(emailInput.props.returnKeyType).toBe('done');
      expect(emailInput.props.keyboardType).toBe('email-address');
    });
  });
});
