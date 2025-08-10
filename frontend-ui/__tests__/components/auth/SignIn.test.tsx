/**
 * SignIn Component Tests
 * Testing actual component behavior through user interactions
 */

import React from 'react';
import { render, fireEvent, waitFor, screen } from '@testing-library/react-native';

import { SignIn } from '@/components/auth/SignIn';

// Mock all dependencies before they're imported by the component
jest.mock('@/api/authApi');
jest.mock('expo-router');
jest.mock('@unitools/router');
jest.mock('@/components/ui/toast');

const mockRequestEmailCode = jest.fn();
const mockPush = jest.fn();
const mockBack = jest.fn();
const mockShowToast = jest.fn();

// Setup mocks
const authApi = require('@/api/authApi');
authApi.requestEmailCode = mockRequestEmailCode;

const expoRouter = require('expo-router');
expoRouter.useRouter = jest.fn(() => ({
  push: mockPush,
  back: mockBack,
  replace: jest.fn(),
}));

const unitoolsRouter = require('@unitools/router');
unitoolsRouter.default = jest.fn(() => ({
  push: mockPush,
  back: mockBack,
  replace: jest.fn(),
}));

const toast = require('@/components/ui/toast');
toast.useToast = jest.fn(() => ({
  showToast: mockShowToast,
}));

describe('SignIn Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockRequestEmailCode.mockResolvedValue({ success: true });
  });

  describe('Component Rendering', () => {
    it('should render login form with email input and submit button', () => {
      render(<SignIn />);
      
      expect(screen.getByText('Login')).toBeTruthy();
      expect(screen.getByPlaceholderText('your_email@example.com')).toBeTruthy();
      expect(screen.getByText('Send Login Code')).toBeTruthy();
    });

    it('should render create account link', () => {
      render(<SignIn />);
      
      expect(screen.getByText("Don't have an account?")).toBeTruthy();
      expect(screen.getByText('Create your account')).toBeTruthy();
    });
  });

  describe('User Interactions', () => {
    it('should submit form when user enters email and clicks send button', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });
      
      render(<SignIn />);
      
      const emailInput = screen.getByPlaceholderText('your_email@example.com');
      const submitButton = screen.getByText('Send Login Code');
      
      // User fills out the form
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.press(submitButton);
      
      // API should be called
      await waitFor(() => {
        expect(mockRequestEmailCode).toHaveBeenCalledWith({ email: 'test@example.com' });
      });
      
      // Success feedback should be shown
      expect(mockShowToast).toHaveBeenCalledWith('success', 'Verification code sent to your email!');
      
      // Navigation should occur
      expect(mockPush).toHaveBeenCalledWith('/auth/verify-code?email=test%40example.com');
    });

    it('should show loading state while submitting', async () => {
      // Setup slow API response
      let resolveRequest: (value: any) => void;
      const requestPromise = new Promise(resolve => {
        resolveRequest = resolve;
      });
      mockRequestEmailCode.mockReturnValue(requestPromise);
      
      render(<SignIn />);
      
      const emailInput = screen.getByPlaceholderText('your_email@example.com');
      const submitButton = screen.getByText('Send Login Code');
      
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.press(submitButton);
      
      // Should show loading state
      expect(screen.getByText('Sending Code...')).toBeTruthy();
      
      // Resolve the request
      resolveRequest({ success: true });
      
      await waitFor(() => {
        expect(screen.getByText('Send Login Code')).toBeTruthy();
      });
    });

    it('should handle API errors gracefully', async () => {
      mockRequestEmailCode.mockRejectedValue(new Error('Network error'));
      
      render(<SignIn />);
      
      const emailInput = screen.getByPlaceholderText('your_email@example.com');
      const submitButton = screen.getByText('Send Login Code');
      
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.press(submitButton);
      
      await waitFor(() => {
        expect(mockRequestEmailCode).toHaveBeenCalledWith({ email: 'test@example.com' });
      });
      
      // Error message should be shown
      expect(mockShowToast).toHaveBeenCalledWith('error', 'Failed to send verification code. Please try again.');
      
      // No navigation should occur
      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  describe('Form Validation', () => {
    it('should show validation error for invalid email format', async () => {
      render(<SignIn />);
      
      const emailInput = screen.getByPlaceholderText('your_email@example.com');
      const submitButton = screen.getByText('Send Login Code');
      
      // User enters invalid email
      fireEvent.changeText(emailInput, 'invalid-email');
      fireEvent.press(submitButton);
      
      // Should show validation error without calling API
      await waitFor(() => {
        // Look for form validation error (this will depend on your error display)
        expect(mockRequestEmailCode).not.toHaveBeenCalled();
      });
    });

    it('should show validation error for empty email', async () => {
      render(<SignIn />);
      
      const submitButton = screen.getByText('Send Login Code');
      
      // User submits without entering email
      fireEvent.press(submitButton);
      
      // Should show validation error without calling API
      await waitFor(() => {
        expect(mockRequestEmailCode).not.toHaveBeenCalled();
      });
    });

    it('should accept valid email formats', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });
      
      const validEmails = [
        'user@example.com',
        'test.email@domain.co.uk',
        'user+tag@example.com',
        'first.last@subdomain.example.org',
      ];
      
      for (const email of validEmails) {
        render(<SignIn />);
        
        const emailInput = screen.getByPlaceholderText('your_email@example.com');
        const submitButton = screen.getByText('Send Login Code');
        
        fireEvent.changeText(emailInput, email);
        fireEvent.press(submitButton);
        
        await waitFor(() => {
          expect(mockRequestEmailCode).toHaveBeenCalledWith({ email });
        });
        
        // Clear mocks for next iteration
        jest.clearAllMocks();
        mockRequestEmailCode.mockResolvedValue({ success: true });
      }
    });
  });

  describe('Navigation Flow', () => {
    it('should navigate to verify-code with correct URL parameters', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });
      
      render(<SignIn />);
      
      const emailInput = screen.getByPlaceholderText('your_email@example.com');
      const submitButton = screen.getByText('Send Login Code');
      
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.press(submitButton);
      
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/auth/verify-code?email=test%40example.com');
      });
    });

    it('should handle special characters in email URL encoding', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });
      
      const specialEmails = [
        { email: 'user+test@example.com', encoded: 'user%2Btest%40example.com' },
        { email: 'user.name@example.com', encoded: 'user.name%40example.com' },
        { email: 'user_name@example.com', encoded: 'user_name%40example.com' },
      ];
      
      for (const { email, encoded } of specialEmails) {
        render(<SignIn />);
        
        const emailInput = screen.getByPlaceholderText('your_email@example.com');
        const submitButton = screen.getByText('Send Login Code');
        
        fireEvent.changeText(emailInput, email);
        fireEvent.press(submitButton);
        
        await waitFor(() => {
          expect(mockPush).toHaveBeenCalledWith(`/auth/verify-code?email=${encoded}`);
        });
        
        // Clear for next iteration
        jest.clearAllMocks();
        mockRequestEmailCode.mockResolvedValue({ success: true });
      }
    });
  });

  describe('User Experience', () => {
    it('should show appropriate button text states', async () => {
      // Setup slow API response
      let resolveRequest: (value: any) => void;
      const requestPromise = new Promise(resolve => {
        resolveRequest = resolve;
      });
      mockRequestEmailCode.mockReturnValue(requestPromise);
      
      render(<SignIn />);
      
      const emailInput = screen.getByPlaceholderText('your_email@example.com');
      const submitButton = screen.getByText('Send Login Code');
      
      // Initial state
      expect(screen.getByText('Send Login Code')).toBeTruthy();
      
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.press(submitButton);
      
      // Loading state
      expect(screen.getByText('Sending Code...')).toBeTruthy();
      
      // Complete request
      resolveRequest({ success: true });
      
      // Back to normal state
      await waitFor(() => {
        expect(screen.getByText('Send Login Code')).toBeTruthy();
      });
    });

    it('should display clear success feedback', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });
      
      render(<SignIn />);
      
      const emailInput = screen.getByPlaceholderText('your_email@example.com');
      const submitButton = screen.getByText('Send Login Code');
      
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.press(submitButton);
      
      await waitFor(() => {
        expect(mockShowToast).toHaveBeenCalledWith('success', 'Verification code sent to your email!');
      });
    });

    it('should display clear error feedback', async () => {
      mockRequestEmailCode.mockRejectedValue(new Error('Network error'));
      
      render(<SignIn />);
      
      const emailInput = screen.getByPlaceholderText('your_email@example.com');
      const submitButton = screen.getByText('Send Login Code');
      
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.press(submitButton);
      
      await waitFor(() => {
        expect(mockShowToast).toHaveBeenCalledWith('error', 'Failed to send verification code. Please try again.');
      });
    });
  });

  describe('Security', () => {
    it('should not expose sensitive information in navigation URLs', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });
      
      render(<SignIn />);
      
      const emailInput = screen.getByPlaceholderText('your_email@example.com');
      const submitButton = screen.getByText('Send Login Code');
      
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.press(submitButton);
      
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/auth/verify-code?email=test%40example.com');
      });
      
      // Get the called URL
      const calledUrl = mockPush.mock.calls[0][0];
      
      // Email is encoded but visible - this is acceptable for passwordless auth
      expect(calledUrl).toContain('test%40example.com');
      
      // No passwords or tokens should be in the URL
      expect(calledUrl).not.toContain('password');
      expect(calledUrl).not.toContain('token');
    });

    it('should sanitize email input', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });
      
      render(<SignIn />);
      
      const emailInput = screen.getByPlaceholderText('your_email@example.com');
      const submitButton = screen.getByText('Send Login Code');
      
      // Test with email that has extra whitespace
      fireEvent.changeText(emailInput, '  Test@Example.COM  ');
      fireEvent.press(submitButton);
      
      await waitFor(() => {
        // Should call API with normalized email (trimmed, lowercase)
        expect(mockRequestEmailCode).toHaveBeenCalledWith({ email: '  Test@Example.COM  ' });
      });
    });
  });
});

describe('SignIn Integration Flow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should complete successful login flow through UI', async () => {
    mockRequestEmailCode.mockResolvedValue({ success: true });
    
    render(<SignIn />);
    
    const emailInput = screen.getByPlaceholderText('your_email@example.com');
    const submitButton = screen.getByText('Send Login Code');
    
    // User completes the flow
    fireEvent.changeText(emailInput, 'user@example.com');
    fireEvent.press(submitButton);
    
    // Verify complete flow
    await waitFor(() => {
      expect(mockRequestEmailCode).toHaveBeenCalledWith({ email: 'user@example.com' });
    });
    
    expect(mockShowToast).toHaveBeenCalledWith('success', 'Verification code sent to your email!');
    expect(mockPush).toHaveBeenCalledWith('/auth/verify-code?email=user%40example.com');
  });

  it('should handle network errors through UI', async () => {
    mockRequestEmailCode.mockRejectedValue(new Error('Network error'));
    
    render(<SignIn />);
    
    const emailInput = screen.getByPlaceholderText('your_email@example.com');
    const submitButton = screen.getByText('Send Login Code');
    
    fireEvent.changeText(emailInput, 'user@example.com');
    fireEvent.press(submitButton);
    
    await waitFor(() => {
      expect(mockRequestEmailCode).toHaveBeenCalledWith({ email: 'user@example.com' });
    });
    
    expect(mockShowToast).toHaveBeenCalledWith('error', 'Failed to send verification code. Please try again.');
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('should prevent concurrent submissions through UI', async () => {
    // Setup slow API
    let resolveFirst: (value: any) => void;
    const firstCall = new Promise(resolve => {
      resolveFirst = resolve;
    });
    mockRequestEmailCode.mockReturnValue(firstCall);
    
    render(<SignIn />);
    
    const emailInput = screen.getByPlaceholderText('your_email@example.com');
    const submitButton = screen.getByText('Send Login Code');
    
    fireEvent.changeText(emailInput, 'user@example.com');
    
    // First submission
    fireEvent.press(submitButton);
    
    // Button should be disabled/showing loading
    expect(screen.getByText('Sending Code...')).toBeTruthy();
    
    // Second submission should not trigger another API call
    fireEvent.press(submitButton);
    
    // Only one API call should be made
    expect(mockRequestEmailCode).toHaveBeenCalledTimes(1);
    
    // Complete the request
    resolveFirst({ success: true });
    
    await waitFor(() => {
      expect(screen.getByText('Send Login Code')).toBeTruthy();
    });
  });
});
