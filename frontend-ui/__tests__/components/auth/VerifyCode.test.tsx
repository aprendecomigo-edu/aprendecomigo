import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';

import { VerifyCode } from '@/components/auth/Verif      const { getByPlaceholderText, getByText, queryByText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('Enter the verification code');de';
import { renderWithProviders, createMockRouter, createMockToast, AUTH_TEST_DATA } from '../../utils/auth-test-utils';

// Mock the auth API
const mockVerifyEmailCode = jest.fn();
const mockRequestEmailCode = jest.fn();
jest.mock('@/api/authApi', () => ({
  verifyEmailCode: mockVerifyEmailCode,
  requestEmailCode: mockRequestEmailCode,
}));

// Mock useAuth hook
const mockSetToken = jest.fn();
const mockSetUser = jest.fn();
jest.mock('@/api/auth', () => ({
  useAuth: () => ({
    setToken: mockSetToken,
    setUser: mockSetUser,
  }),
}));

// Mock onboarding API
const mockCheckOnboardingStatus = jest.fn();
jest.mock('@/api/onboardingApi', () => ({
  onboardingApi: {
    checkOnboardingStatus: mockCheckOnboardingStatus,
  },
}));

// Mock router
const mockRouter = createMockRouter();
jest.mock('@unitools/router', () => ({
  __esModule: true,
  default: () => mockRouter,
}));

// Mock expo-router for useLocalSearchParams
const mockUseLocalSearchParams = jest.fn();
jest.mock('expo-router', () => ({
  useLocalSearchParams: mockUseLocalSearchParams,
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

describe('VerifyCode Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockVerifyEmailCode.mockClear();
    mockRequestEmailCode.mockClear();
    mockSetToken.mockClear();
    mockSetUser.mockClear();
    mockCheckOnboardingStatus.mockClear();
    mockRouter._mocks.push.mockClear();
    mockRouter._mocks.back.mockClear();
    mockToast._mocks.showToast.mockClear();
    
    // Default mock for search params
    mockUseLocalSearchParams.mockReturnValue({
      contact: 'test@example.com',
      contactType: 'email',
      email: 'test@example.com',
      nextRoute: null,
    });
  });

  describe('Basic Rendering', () => {
    it('should render main elements correctly', () => {
      const { getByText, getByPlaceholderText } = renderWithProviders(<VerifyCode />);
      
      // Check main heading
      expect(getByText('Verify Your Email')).toBeTruthy();
      
      // Check instruction text
      expect(getByText(/We sent a 6-digit code to/)).toBeTruthy();
      expect(getByText('test@example.com')).toBeTruthy();
      
      // Check code input
      expect(getByPlaceholderText('000000')).toBeTruthy();
      
      // Check verify button
      expect(getByText('Verify Code')).toBeTruthy();
      
      // Check resend option
      expect(getByText(/Didn't receive the code/)).toBeTruthy();
    });

    it('should display email from search params', () => {
      mockUseLocalSearchParams.mockReturnValue({
        contact: 'user@domain.com',
        contactType: 'email',
        email: 'user@domain.com',
        nextRoute: null,
      });
      
      const { getByText } = renderWithProviders(<VerifyCode />);
      
      expect(getByText('user@domain.com')).toBeTruthy();
    });

    it('should handle missing email in search params', () => {
      mockUseLocalSearchParams.mockReturnValue({
        contact: '',
        contactType: 'email',
        email: '',
        nextRoute: null,
      });
      
      const { getByText } = renderWithProviders(<VerifyCode />);
      
      // Should still render the form
      expect(getByText('Verify Your Email')).toBeTruthy();
      expect(getByText('Verify Code')).toBeTruthy();
    });
  });

  describe('Form Validation', () => {
    it('should show validation error for empty code', async () => {
      const { getByText, queryByText } = renderWithProviders(<VerifyCode />);
      
      const verifyButton = getByText('Verify Code');
      
      // Submit without entering code
      fireEvent.press(verifyButton);
      
      await waitFor(() => {
        expect(queryByText('Verification code is required')).toBeTruthy();
      });
    });

    it('should show validation error for short code', async () => {
      const { getByPlaceholderText, getByText, queryByText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('Enter the verification code');
      const verifyButton = getByText('Verify Code');
      
      // Enter short code
      fireEvent.changeText(codeInput, '123');
      fireEvent.press(verifyButton);
      
      await waitFor(() => {
        expect(queryByText('Code must be 6 digits')).toBeTruthy();
      });
    });

    it('should validate invalid code formats', async () => {
      const { getByPlaceholderText, getByText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('000000');
      const verifyButton = getByText('Verify Code');
      
      for (const invalidCode of AUTH_TEST_DATA.invalidCodes) {
        fireEvent.changeText(codeInput, invalidCode);
        fireEvent.press(verifyButton);
        
        await waitFor(() => {
          // Form should not submit with invalid code
          expect(mockVerifyEmailCode).not.toHaveBeenCalled();
        });
        
        mockVerifyEmailCode.mockClear();
      }
    });

    it('should accept valid code formats', async () => {
      const { getByPlaceholderText, getByText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('000000');
      const verifyButton = getByText('Verify Code');
      
      // Mock successful API response
      mockVerifyEmailCode.mockResolvedValue({
        access_token: 'fake-token',
        user: { id: 1, email: 'test@example.com' },
      });
      mockCheckOnboardingStatus.mockResolvedValue({ needsOnboarding: false });
      
      for (const validCode of AUTH_TEST_DATA.validCodes) {
        fireEvent.changeText(codeInput, validCode);
        
        await act(async () => {
          fireEvent.press(verifyButton);
        });
        
        await waitFor(() => {
          expect(mockVerifyEmailCode).toHaveBeenCalledWith({
            contact: 'test@example.com',
            contactType: 'email',
            code: validCode,
          });
        });
        
        mockVerifyEmailCode.mockClear();
      }
    });
  });

  describe('User Interactions', () => {
    it('should handle valid code submission', async () => {
      mockVerifyEmailCode.mockResolvedValue({
        access_token: 'fake-token',
        user: { id: 1, email: 'test@example.com' },
      });
      mockCheckOnboardingStatus.mockResolvedValue({ needsOnboarding: false });
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('000000');
      const verifyButton = getByText('Verify Code');
      
      fireEvent.changeText(codeInput, '123456');
      
      await act(async () => {
        fireEvent.press(verifyButton);
      });
      
      await waitFor(() => {
        expect(mockVerifyEmailCode).toHaveBeenCalledWith({
          contact: 'test@example.com',
          contactType: 'email',
          code: '123456',
        });
      });
    });

    it('should set auth token and user on successful verification', async () => {
      const mockAuthResponse = {
        access_token: 'fake-token',
        user: { id: 1, email: 'test@example.com', name: 'Test User' },
      };
      
      mockVerifyEmailCode.mockResolvedValue(mockAuthResponse);
      mockCheckOnboardingStatus.mockResolvedValue({ needsOnboarding: false });
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('000000');
      const verifyButton = getByText('Verify Code');
      
      fireEvent.changeText(codeInput, '123456');
      
      await act(async () => {
        fireEvent.press(verifyButton);
      });
      
      await waitFor(() => {
        expect(mockSetToken).toHaveBeenCalledWith('fake-token');
        expect(mockSetUser).toHaveBeenCalledWith(mockAuthResponse.user);
      });
    });

    it('should navigate to dashboard after successful verification', async () => {
      mockVerifyEmailCode.mockResolvedValue({
        access_token: 'fake-token',
        user: { id: 1, email: 'test@example.com' },
      });
      mockCheckOnboardingStatus.mockResolvedValue({ needsOnboarding: false });
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('000000');
      const verifyButton = getByText('Verify Code');
      
      fireEvent.changeText(codeInput, '123456');
      
      await act(async () => {
        fireEvent.press(verifyButton);
      });
      
      await waitFor(() => {
        expect(mockRouter._mocks.push).toHaveBeenCalledWith('/(tabs)/dashboard');
      });
    });

    it('should navigate to onboarding if user needs onboarding', async () => {
      mockVerifyEmailCode.mockResolvedValue({
        access_token: 'fake-token',
        user: { id: 1, email: 'test@example.com' },
      });
      mockCheckOnboardingStatus.mockResolvedValue({ needsOnboarding: true });
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('000000');
      const verifyButton = getByText('Verify Code');
      
      fireEvent.changeText(codeInput, '123456');
      
      await act(async () => {
        fireEvent.press(verifyButton);
      });
      
      await waitFor(() => {
        expect(mockRouter._mocks.push).toHaveBeenCalledWith('/onboarding/welcome');
      });
    });

    it('should navigate to nextRoute if provided', async () => {
      mockUseLocalSearchParams.mockReturnValue({
        contact: 'test@example.com',
        contactType: 'email',
        email: 'test@example.com',
        nextRoute: '/custom-route',
      });
      
      mockVerifyEmailCode.mockResolvedValue({
        access_token: 'fake-token',
        user: { id: 1, email: 'test@example.com' },
      });
      mockCheckOnboardingStatus.mockResolvedValue({ needsOnboarding: false });
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('000000');
      const verifyButton = getByText('Verify Code');
      
      fireEvent.changeText(codeInput, '123456');
      
      await act(async () => {
        fireEvent.press(verifyButton);
      });
      
      await waitFor(() => {
        expect(mockRouter._mocks.push).toHaveBeenCalledWith('/custom-route');
      });
    });
  });

  describe('Resend Code Functionality', () => {
    it('should resend code when resend button is clicked', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });
      
      const { getByText } = renderWithProviders(<VerifyCode />);
      
      const resendButton = getByText('Resend Code');
      
      await act(async () => {
        fireEvent.press(resendButton);
      });
      
      await waitFor(() => {
        expect(mockRequestEmailCode).toHaveBeenCalledWith({ email: 'test@example.com' });
      });
    });

    it('should show success toast when code is resent', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });
      
      const { getByText } = renderWithProviders(<VerifyCode />);
      
      const resendButton = getByText('Resend Code');
      
      await act(async () => {
        fireEvent.press(resendButton);
      });
      
      await waitFor(() => {
        expect(mockToast._mocks.showToast).toHaveBeenCalledWith('success', 'Verification code sent!');
      });
    });

    it('should show error toast when resend fails', async () => {
      mockRequestEmailCode.mockRejectedValue(new Error('Network error'));
      
      const { getByText } = renderWithProviders(<VerifyCode />);
      
      const resendButton = getByText('Resend Code');
      
      await act(async () => {
        fireEvent.press(resendButton);
      });
      
      await waitFor(() => {
        expect(mockToast._mocks.showToast).toHaveBeenCalledWith('error', 'Failed to resend code. Please try again.');
      });
    });

    it('should implement resend cooldown', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });
      
      const { getByText } = renderWithProviders(<VerifyCode />);
      
      const resendButton = getByText('Resend Code');
      
      // First resend
      await act(async () => {
        fireEvent.press(resendButton);
      });
      
      // Should disable the button temporarily
      await waitFor(() => {
        const disabledButton = getByText(/Resend in/);
        expect(disabledButton).toBeTruthy();
      });
    });
  });

  describe('Loading States', () => {
    it('should show loading state during verification', async () => {
      // Create a delayed promise
      let resolvePromise: (value: any) => void;
      const delayedPromise = new Promise(resolve => {
        resolvePromise = resolve;
      });
      mockVerifyEmailCode.mockReturnValue(delayedPromise);
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('000000');
      const verifyButton = getByText('Verify Code');
      
      fireEvent.changeText(codeInput, '123456');
      fireEvent.press(verifyButton);
      
      // Check loading state appears
      await waitFor(() => {
        expect(getByText('Verifying...')).toBeTruthy();
      });
      
      // Resolve the promise
      await act(async () => {
        resolvePromise!({
          access_token: 'fake-token',
          user: { id: 1, email: 'test@example.com' },
        });
      });
    });

    it('should disable button during verification', async () => {
      // Create a delayed promise
      let resolvePromise: (value: any) => void;
      const delayedPromise = new Promise(resolve => {
        resolvePromise = resolve;
      });
      mockVerifyEmailCode.mockReturnValue(delayedPromise);
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('000000');
      const verifyButton = getByText('Verify Code');
      
      fireEvent.changeText(codeInput, '123456');
      fireEvent.press(verifyButton);
      
      // Check button becomes disabled
      await waitFor(() => {
        const loadingButton = getByText('Verifying...');
        expect(loadingButton.props.disabled).toBe(true);
      });
      
      // Resolve the promise
      await act(async () => {
        resolvePromise!({
          access_token: 'fake-token',
          user: { id: 1, email: 'test@example.com' },
        });
      });
    });
  });

  describe('Error Handling', () => {
    it('should show error toast for invalid code', async () => {
      mockVerifyEmailCode.mockRejectedValue(new Error('Invalid verification code'));
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('000000');
      const verifyButton = getByText('Verify Code');
      
      fireEvent.changeText(codeInput, '123456');
      
      await act(async () => {
        fireEvent.press(verifyButton);
      });
      
      await waitFor(() => {
        expect(mockToast._mocks.showToast).toHaveBeenCalledWith('error', 'Invalid verification code. Please try again.');
      });
    });

    it('should show error toast for expired code', async () => {
      mockVerifyEmailCode.mockRejectedValue(new Error('Code expired'));
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('000000');
      const verifyButton = getByText('Verify Code');
      
      fireEvent.changeText(codeInput, '123456');
      
      await act(async () => {
        fireEvent.press(verifyButton);
      });
      
      await waitFor(() => {
        expect(mockToast._mocks.showToast).toHaveBeenCalledWith('error', 'Invalid verification code. Please try again.');
      });
    });

    it('should reset loading state after error', async () => {
      mockVerifyEmailCode.mockRejectedValue(new Error('Network error'));
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('000000');
      const verifyButton = getByText('Verify Code');
      
      fireEvent.changeText(codeInput, '123456');
      
      await act(async () => {
        fireEvent.press(verifyButton);
      });
      
      await waitFor(() => {
        expect(getByText('Verify Code')).toBeTruthy();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle rapid successive verification attempts', async () => {
      mockVerifyEmailCode.mockResolvedValue({
        access_token: 'fake-token',
        user: { id: 1, email: 'test@example.com' },
      });
      mockCheckOnboardingStatus.mockResolvedValue({ needsOnboarding: false });
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('000000');
      const verifyButton = getByText('Verify Code');
      
      fireEvent.changeText(codeInput, '123456');
      
      // Click button multiple times rapidly
      await act(async () => {
        fireEvent.press(verifyButton);
        fireEvent.press(verifyButton);
        fireEvent.press(verifyButton);
      });
      
      // Should only be called once due to loading state
      await waitFor(() => {
        expect(mockVerifyEmailCode).toHaveBeenCalledTimes(1);
      });
    });

    it('should handle verification with different contact types', async () => {
      mockUseLocalSearchParams.mockReturnValue({
        contact: '+1234567890',
        contactType: 'phone',
        email: '',
        nextRoute: null,
      });
      
      mockVerifyEmailCode.mockResolvedValue({
        access_token: 'fake-token',
        user: { id: 1, phone: '+1234567890' },
      });
      mockCheckOnboardingStatus.mockResolvedValue({ needsOnboarding: false });
      
      const { getByPlaceholderText, getByText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('000000');
      const verifyButton = getByText('Verify Code');
      
      fireEvent.changeText(codeInput, '123456');
      
      await act(async () => {
        fireEvent.press(verifyButton);
      });
      
      await waitFor(() => {
        expect(mockVerifyEmailCode).toHaveBeenCalledWith({
          contact: '+1234567890',
          contactType: 'phone',
          code: '123456',
        });
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper accessibility labels', () => {
      const { getByText, getByPlaceholderText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('000000');
      const verifyButton = getByText('Verify Code');
      
      // Check that elements are accessible
      expect(codeInput).toBeTruthy();
      expect(verifyButton).toBeTruthy();
    });

    it('should support keyboard navigation', () => {
      const { getByPlaceholderText } = renderWithProviders(<VerifyCode />);
      
      const codeInput = getByPlaceholderText('000000');
      
      // Check keyboard properties
      expect(codeInput.props.keyboardType).toBe('numeric');
      expect(codeInput.props.maxLength).toBe(6);
    });
  });
});
