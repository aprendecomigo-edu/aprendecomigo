import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import React from 'react';

import { renderWithProviders, createMockRouter, createMockToast } from '../utils/auth-test-utils';

import { SignIn } from '@/components/auth/SignIn';
import { SignUp } from '@/components/auth/SignUp';
import { VerifyCode } from '@/components/auth/VerifyCode';

// Mock all auth APIs
const mockRequestEmailCode = jest.fn();
const mockVerifyEmailCode = jest.fn();
const mockCreateUser = jest.fn();

jest.mock('@/api/authApi', () => ({
  requestEmailCode: mockRequestEmailCode,
  verifyEmailCode: mockVerifyEmailCode,
  createUser: mockCreateUser,
}));

// Mock auth hooks
const mockSetToken = jest.fn();
const mockSetUser = jest.fn();
jest.mock('@/api/auth', () => ({
  useAuth: () => ({
    setToken: mockSetToken,
    setUser: mockSetUser,
  }),
  useUserProfile: () => ({
    profile: null,
    loading: false,
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

// Mock expo-router
const mockUseLocalSearchParams = jest.fn();
jest.mock('expo-router', () => ({
  useLocalSearchParams: mockUseLocalSearchParams,
}));

// Mock toast
const mockToast = createMockToast();
jest.mock('@/components/ui/toast', () => ({
  useToast: () => mockToast,
}));

// Mock React Native components
jest.mock('react-native', () => ({
  ...jest.requireActual('react-native'),
  Keyboard: {
    dismiss: jest.fn(),
  },
  ScrollView: ({ children, ...props }: any) => {
    const React = require('react');
    return React.createElement('div', { ...props, className: 'scroll-view' }, children);
  },
}));

describe('Authentication Flow Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockRequestEmailCode.mockClear();
    mockVerifyEmailCode.mockClear();
    mockCreateUser.mockClear();
    mockSetToken.mockClear();
    mockSetUser.mockClear();
    mockCheckOnboardingStatus.mockClear();
    mockRouter._mocks.push.mockClear();
    mockRouter._mocks.back.mockClear();
    mockToast._mocks.showToast.mockClear();

    // Default mocks
    mockUseLocalSearchParams.mockReturnValue({});
  });

  describe('Complete Sign In Flow', () => {
    it('should complete full sign in to dashboard flow', async () => {
      // Step 1: User enters email and requests code
      mockRequestEmailCode.mockResolvedValue({ success: true });

      const { getByPlaceholderText, getByText } = renderWithProviders(<SignIn />);

      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');

      fireEvent.changeText(emailInput, 'existing@example.com');

      await act(async () => {
        fireEvent.press(sendCodeButton);
      });

      // Verify API call and navigation
      await waitFor(() => {
        expect(mockRequestEmailCode).toHaveBeenCalledWith({ email: 'existing@example.com' });
        expect(mockRouter._mocks.push).toHaveBeenCalledWith(
          '/auth/verify-code?email=existing%40example.com'
        );
        expect(mockToast._mocks.showToast).toHaveBeenCalledWith(
          'success',
          'Verification code sent to your email!'
        );
      });

      // Step 2: User verifies code
      mockUseLocalSearchParams.mockReturnValue({
        contact: 'existing@example.com',
        contactType: 'email',
        email: 'existing@example.com',
      });

      mockVerifyEmailCode.mockResolvedValue({
        access_token: 'user-token-123',
        user: { id: 1, email: 'existing@example.com', name: 'Existing User' },
      });
      mockCheckOnboardingStatus.mockResolvedValue({ needsOnboarding: false });

      const { getByPlaceholderText: getCodeInput, getByText: getVerifyButton } =
        renderWithProviders(<VerifyCode />);

      const codeInput = getCodeInput('000000');
      const verifyButton = getVerifyButton('Verify Code');

      fireEvent.changeText(codeInput, '123456');

      await act(async () => {
        fireEvent.press(verifyButton);
      });

      // Verify authentication completion
      await waitFor(() => {
        expect(mockVerifyEmailCode).toHaveBeenCalledWith({
          contact: 'existing@example.com',
          contactType: 'email',
          code: '123456',
        });
        expect(mockSetToken).toHaveBeenCalledWith('user-token-123');
        expect(mockSetUser).toHaveBeenCalledWith({
          id: 1,
          email: 'existing@example.com',
          name: 'Existing User',
        });
        expect(mockRouter._mocks.push).toHaveBeenCalledWith('/(tabs)/dashboard');
      });
    });

    it('should handle sign in to onboarding flow for new users', async () => {
      // Step 1: Email submission
      mockRequestEmailCode.mockResolvedValue({ success: true });

      const { getByPlaceholderText, getByText } = renderWithProviders(<SignIn />);

      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');

      fireEvent.changeText(emailInput, 'newuser@example.com');

      await act(async () => {
        fireEvent.press(sendCodeButton);
      });

      // Step 2: Code verification for new user
      mockUseLocalSearchParams.mockReturnValue({
        contact: 'newuser@example.com',
        contactType: 'email',
        email: 'newuser@example.com',
      });

      mockVerifyEmailCode.mockResolvedValue({
        access_token: 'new-user-token-123',
        user: { id: 2, email: 'newuser@example.com', name: 'New User' },
      });
      mockCheckOnboardingStatus.mockResolvedValue({ needsOnboarding: true });

      const { getByPlaceholderText: getCodeInput, getByText: getVerifyButton } =
        renderWithProviders(<VerifyCode />);

      const codeInput = getCodeInput('000000');
      const verifyButton = getVerifyButton('Verify Code');

      fireEvent.changeText(codeInput, '654321');

      await act(async () => {
        fireEvent.press(verifyButton);
      });

      // Verify navigation to onboarding
      await waitFor(() => {
        expect(mockRouter._mocks.push).toHaveBeenCalledWith('/onboarding/welcome');
      });
    });
  });

  describe('Complete Sign Up Flow', () => {
    it('should complete full tutor registration flow', async () => {
      mockUseLocalSearchParams.mockReturnValue({
        userType: 'tutor',
      });

      mockCreateUser.mockResolvedValue({
        access_token: 'tutor-token-123',
        user: { id: 3, email: 'tutor@example.com', name: 'New Tutor', userType: 'tutor' },
      });

      const { getByPlaceholderText, getByText, getByLabelText } = renderWithProviders(<SignUp />);

      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const termsCheckbox = getByLabelText(/I agree to the Terms of Service/);
      const createButton = getByText('Create Account');

      fireEvent.changeText(nameInput, 'New Tutor');
      fireEvent.changeText(emailInput, 'tutor@example.com');
      fireEvent.press(termsCheckbox);

      await act(async () => {
        fireEvent.press(createButton);
      });

      await waitFor(() => {
        expect(mockCreateUser).toHaveBeenCalledWith({
          name: 'New Tutor',
          email: 'tutor@example.com',
          userType: 'tutor',
          schoolName: undefined,
          acceptedTerms: true,
        });
        expect(mockSetToken).toHaveBeenCalledWith('tutor-token-123');
        expect(mockSetUser).toHaveBeenCalledWith({
          id: 3,
          email: 'tutor@example.com',
          name: 'New Tutor',
          userType: 'tutor',
        });
        expect(mockRouter._mocks.push).toHaveBeenCalledWith('/onboarding/welcome');
      });
    });

    it('should complete full school registration flow', async () => {
      mockUseLocalSearchParams.mockReturnValue({
        userType: 'school',
      });

      mockCreateUser.mockResolvedValue({
        access_token: 'school-token-123',
        user: { id: 4, email: 'admin@school.com', name: 'School Admin', userType: 'school' },
      });

      const { getByPlaceholderText, getByText, getByLabelText } = renderWithProviders(<SignUp />);

      const schoolRadio = getByLabelText('School');
      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const termsCheckbox = getByLabelText(/I agree to the Terms of Service/);
      const createButton = getByText('Create Account');

      // Switch to school type
      fireEvent.press(schoolRadio);

      const schoolNameInput = getByPlaceholderText('Enter your school name');

      fireEvent.changeText(nameInput, 'School Admin');
      fireEvent.changeText(emailInput, 'admin@school.com');
      fireEvent.changeText(schoolNameInput, 'Test Academy');
      fireEvent.press(termsCheckbox);

      await act(async () => {
        fireEvent.press(createButton);
      });

      await waitFor(() => {
        expect(mockCreateUser).toHaveBeenCalledWith({
          name: 'School Admin',
          email: 'admin@school.com',
          userType: 'school',
          schoolName: 'Test Academy',
          acceptedTerms: true,
        });
        expect(mockSetToken).toHaveBeenCalledWith('school-token-123');
        expect(mockSetUser).toHaveBeenCalledWith({
          id: 4,
          email: 'admin@school.com',
          name: 'School Admin',
          userType: 'school',
        });
        expect(mockRouter._mocks.push).toHaveBeenCalledWith('/onboarding/welcome');
      });
    });
  });

  describe('Error Recovery Scenarios', () => {
    it('should handle network timeout during sign in', async () => {
      // Simulate network timeout
      mockRequestEmailCode.mockRejectedValue(new Error('Request timeout'));

      const { getByPlaceholderText, getByText } = renderWithProviders(<SignIn />);

      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');

      fireEvent.changeText(emailInput, 'user@example.com');

      await act(async () => {
        fireEvent.press(sendCodeButton);
      });

      await waitFor(() => {
        expect(mockToast._mocks.showToast).toHaveBeenCalledWith(
          'error',
          'Failed to send verification code. Please try again.'
        );
        // User should be able to retry
        expect(getByText('Send Login Code')).toBeTruthy();
      });
    });

    it('should handle invalid verification code with retry', async () => {
      mockUseLocalSearchParams.mockReturnValue({
        contact: 'user@example.com',
        contactType: 'email',
        email: 'user@example.com',
      });

      // First attempt fails
      mockVerifyEmailCode.mockRejectedValueOnce(new Error('Invalid code'));

      const { getByPlaceholderText, getByText } = renderWithProviders(<VerifyCode />);

      const codeInput = getByPlaceholderText('000000');
      const verifyButton = getByText('Verify Code');

      fireEvent.changeText(codeInput, '000000');

      await act(async () => {
        fireEvent.press(verifyButton);
      });

      await waitFor(() => {
        expect(mockToast._mocks.showToast).toHaveBeenCalledWith(
          'error',
          'Invalid verification code. Please try again.'
        );
      });

      // Second attempt succeeds
      mockVerifyEmailCode.mockResolvedValue({
        access_token: 'retry-token-123',
        user: { id: 5, email: 'user@example.com', name: 'Retry User' },
      });
      mockCheckOnboardingStatus.mockResolvedValue({ needsOnboarding: false });

      fireEvent.changeText(codeInput, '123456');

      await act(async () => {
        fireEvent.press(verifyButton);
      });

      await waitFor(() => {
        expect(mockSetToken).toHaveBeenCalledWith('retry-token-123');
        expect(mockRouter._mocks.push).toHaveBeenCalledWith('/(tabs)/dashboard');
      });
    });

    it('should handle registration failure with retry', async () => {
      mockUseLocalSearchParams.mockReturnValue({
        userType: 'tutor',
      });

      // First attempt fails
      mockCreateUser.mockRejectedValueOnce(new Error('Email already exists'));

      const { getByPlaceholderText, getByText, getByLabelText } = renderWithProviders(<SignUp />);

      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const termsCheckbox = getByLabelText(/I agree to the Terms of Service/);
      const createButton = getByText('Create Account');

      fireEvent.changeText(nameInput, 'Test User');
      fireEvent.changeText(emailInput, 'existing@example.com');
      fireEvent.press(termsCheckbox);

      await act(async () => {
        fireEvent.press(createButton);
      });

      await waitFor(() => {
        expect(mockToast._mocks.showToast).toHaveBeenCalledWith(
          'error',
          'Failed to create account. Please try again.'
        );
      });

      // User can try with different email
      mockCreateUser.mockResolvedValue({
        access_token: 'new-user-token',
        user: { id: 6, email: 'newuser@example.com', name: 'Test User' },
      });

      fireEvent.changeText(emailInput, 'newuser@example.com');

      await act(async () => {
        fireEvent.press(createButton);
      });

      await waitFor(() => {
        expect(mockSetToken).toHaveBeenCalledWith('new-user-token');
        expect(mockRouter._mocks.push).toHaveBeenCalledWith('/onboarding/welcome');
      });
    });
  });

  describe('Cross-Component State Management', () => {
    it('should maintain email context between SignIn and VerifyCode', async () => {
      // Sign in flow
      mockRequestEmailCode.mockResolvedValue({ success: true });

      const { getByPlaceholderText, getByText } = renderWithProviders(<SignIn />);

      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');

      const testEmail = 'context@example.com';
      fireEvent.changeText(emailInput, testEmail);

      await act(async () => {
        fireEvent.press(sendCodeButton);
      });

      // Verify navigation includes email parameter
      await waitFor(() => {
        expect(mockRouter._mocks.push).toHaveBeenCalledWith(
          '/auth/verify-code?email=context%40example.com'
        );
      });

      // VerifyCode should receive and display the email
      mockUseLocalSearchParams.mockReturnValue({
        contact: testEmail,
        contactType: 'email',
        email: testEmail,
      });

      const { getByText: getEmailText } = renderWithProviders(<VerifyCode />);

      expect(getEmailText(testEmail)).toBeTruthy();
    });

    it('should handle authentication state consistently across components', async () => {
      // Test that authentication state is properly set regardless of which component sets it
      const authData = {
        access_token: 'consistent-token',
        user: { id: 7, email: 'consistent@example.com', name: 'Consistent User' },
      };

      // From SignUp
      mockUseLocalSearchParams.mockReturnValue({ userType: 'tutor' });
      mockCreateUser.mockResolvedValue(authData);

      const { getByPlaceholderText, getByText, getByLabelText } = renderWithProviders(<SignUp />);

      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const termsCheckbox = getByLabelText(/I agree to the Terms of Service/);
      const createButton = getByText('Create Account');

      fireEvent.changeText(nameInput, 'Consistent User');
      fireEvent.changeText(emailInput, 'consistent@example.com');
      fireEvent.press(termsCheckbox);

      await act(async () => {
        fireEvent.press(createButton);
      });

      await waitFor(() => {
        expect(mockSetToken).toHaveBeenCalledWith('consistent-token');
        expect(mockSetUser).toHaveBeenCalledWith(authData.user);
      });

      // Reset mocks
      mockSetToken.mockClear();
      mockSetUser.mockClear();

      // From VerifyCode (should set same data structure)
      mockUseLocalSearchParams.mockReturnValue({
        contact: 'consistent@example.com',
        contactType: 'email',
        email: 'consistent@example.com',
      });

      mockVerifyEmailCode.mockResolvedValue(authData);
      mockCheckOnboardingStatus.mockResolvedValue({ needsOnboarding: false });

      const { getByPlaceholderText: getCodeInput, getByText: getVerifyButton } =
        renderWithProviders(<VerifyCode />);

      const codeInput = getCodeInput('000000');
      const verifyButton = getVerifyButton('Verify Code');

      fireEvent.changeText(codeInput, '123456');

      await act(async () => {
        fireEvent.press(verifyButton);
      });

      await waitFor(() => {
        expect(mockSetToken).toHaveBeenCalledWith('consistent-token');
        expect(mockSetUser).toHaveBeenCalledWith(authData.user);
      });
    });
  });

  describe('Performance and User Experience', () => {
    it('should handle rapid user interactions gracefully', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });

      const { getByPlaceholderText, getByText } = renderWithProviders(<SignIn />);

      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');

      fireEvent.changeText(emailInput, 'rapid@example.com');

      // Rapid clicking should be handled gracefully
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

    it('should maintain responsive UI during async operations', async () => {
      // Create a delayed promise to test UI responsiveness
      let resolvePromise: (value: any) => void;
      const delayedPromise = new Promise(resolve => {
        resolvePromise = resolve;
      });
      mockRequestEmailCode.mockReturnValue(delayedPromise);

      const { getByPlaceholderText, getByText } = renderWithProviders(<SignIn />);

      const emailInput = getByPlaceholderText('your_email@example.com');
      const sendCodeButton = getByText('Send Login Code');

      fireEvent.changeText(emailInput, 'responsive@example.com');
      fireEvent.press(sendCodeButton);

      // UI should show loading state
      await waitFor(() => {
        expect(getByText('Sending Code...')).toBeTruthy();
      });

      // User should be able to interact with other elements
      expect(emailInput).toBeTruthy(); // Input should still be there

      // Resolve the operation
      await act(async () => {
        resolvePromise!({ success: true });
      });

      // UI should return to normal state
      await waitFor(() => {
        expect(getByText('Send Login Code')).toBeTruthy();
      });
    });
  });
});
