/**
 * TDD Integration Tests for New Authentication Architecture
 *
 * These tests will INITIALLY FAIL until the new architecture is implemented.
 * Tests the complete authentication flow with the new separated architecture.
 */

import { NavigationContainer } from '@react-navigation/native';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import React from 'react';

// These components don't exist yet - tests will fail until implemented
import { SignIn } from '@/components/auth/SignIn';
import { SignInForm } from '@/components/auth/SignInForm';
import { SignUp } from '@/components/auth/SignUp';
import { SignUpForm } from '@/components/auth/SignUpForm';
import { VerifyCode } from '@/components/auth/VerifyCode';
import { VerifyCodeForm } from '@/components/auth/VerifyCodeForm';
import { useSignInLogic } from '@/hooks/auth/useSignInLogic';
import { useSignUpLogic } from '@/hooks/auth/useSignUpLogic';
import { useVerifyCodeLogic } from '@/hooks/auth/useVerifyCodeLogic';
import { AuthDependencyProvider } from '@/providers/AuthDependencyProvider';

// Mock navigation
jest.mock('@react-navigation/native');
jest.mock('expo-router');

describe('Authentication New Architecture - Integration Tests', () => {
  const createMockDependencies = () => ({
    authApi: {
      requestEmailCode: jest.fn(),
      createUser: jest.fn(),
      verifyEmailCode: jest.fn(),
    },
    onboardingApi: {
      getNavigationPreferences: jest.fn(),
      getOnboardingProgress: jest.fn(),
    },
    authContext: {
      checkAuthStatus: jest.fn(),
      setUserProfile: jest.fn(),
      userProfile: null,
    },
    router: {
      push: jest.fn(),
      back: jest.fn(),
      replace: jest.fn(),
    },
    toast: {
      showToast: jest.fn(),
    },
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Complete Sign-In Flow with New Architecture', () => {
    it('should complete sign-in flow using separated components and hooks', async () => {
      const mockDeps = createMockDependencies();

      // Set up mock responses
      mockDeps.authApi.requestEmailCode.mockResolvedValue({ success: true });
      mockDeps.authApi.verifyEmailCode.mockResolvedValue({
        user: {
          id: 1,
          email: 'signin@test.com',
          name: 'Sign In User',
          is_admin: false,
          user_type: 'student',
          primary_role: 'student',
          first_login_completed: true,
        },
        is_new_user: false,
        access_token: 'signin-token',
        refresh_token: 'signin-refresh',
      });

      // Test SignIn component with new architecture
      const { getByPlaceholderText, getByText } = render(
        <AuthDependencyProvider dependencies={mockDeps}>
          <SignIn />
        </AuthDependencyProvider>,
      );

      // Verify UI elements are rendered
      expect(getByText('Login')).toBeTruthy();
      expect(getByPlaceholderText('your_email@example.com')).toBeTruthy();
      expect(getByText('Send Login Code')).toBeTruthy();

      // User enters email and submits
      const emailInput = getByPlaceholderText('your_email@example.com');
      const submitButton = getByText('Send Login Code');

      fireEvent.changeText(emailInput, 'signin@test.com');
      fireEvent.press(submitButton);

      // Verify business logic was executed
      await waitFor(() => {
        expect(mockDeps.authApi.requestEmailCode).toHaveBeenCalledWith({
          email: 'signin@test.com',
        });
        expect(mockDeps.toast.showToast).toHaveBeenCalledWith(
          'success',
          'Verification code sent to your email!',
        );
        expect(mockDeps.router.push).toHaveBeenCalledWith(
          '/auth/verify-code?email=signin%40test.com',
        );
      });
    });

    it('should handle sign-in errors with separated error handling', async () => {
      const mockDeps = createMockDependencies();

      // Set up error response
      const networkError = new Error('Network connection failed');
      mockDeps.authApi.requestEmailCode.mockRejectedValue(networkError);

      const { getByPlaceholderText, getByText } = render(
        <AuthDependencyProvider dependencies={mockDeps}>
          <SignIn />
        </AuthDependencyProvider>,
      );

      // User enters email and submits
      const emailInput = getByPlaceholderText('your_email@example.com');
      const submitButton = getByText('Send Login Code');

      fireEvent.changeText(emailInput, 'error@test.com');
      fireEvent.press(submitButton);

      // Verify error handling
      await waitFor(() => {
        expect(mockDeps.authApi.requestEmailCode).toHaveBeenCalledWith({
          email: 'error@test.com',
        });
        expect(mockDeps.toast.showToast).toHaveBeenCalledWith(
          'error',
          'Failed to send verification code. Please try again.',
        );
        expect(mockDeps.router.push).not.toHaveBeenCalled();
      });
    });
  });

  describe('Complete Sign-Up Flow with New Architecture', () => {
    it('should complete tutor registration with separated architecture', async () => {
      const mockDeps = createMockDependencies();

      // Set up mock responses
      mockDeps.authApi.createUser.mockResolvedValue({ success: true });
      mockDeps.authContext.userProfile = {
        name: 'Test Tutor',
        email: 'tutor@example.com',
        phone_number: '+1234567890',
      };

      const { getByText, getByPlaceholderText, getByLabelText } = render(
        <AuthDependencyProvider dependencies={mockDeps}>
          <SignUp />
        </AuthDependencyProvider>,
      );

      // Verify UI elements for tutor type
      expect(getByText('Set Up Your Tutoring Practice')).toBeTruthy();
      expect(getByText('Individual Tutor')).toBeTruthy();

      // Fill out the tutor registration form
      fireEvent.changeText(getByPlaceholderText('Enter your full name'), 'Test Tutor');
      fireEvent.changeText(getByPlaceholderText('Enter your email address'), 'tutor@example.com');
      fireEvent.changeText(getByPlaceholderText('Enter your phone number'), '+1234567890');
      fireEvent.press(getByLabelText('Email'));

      // Submit registration
      const createButton = getByText('Create Account');
      fireEvent.press(createButton);

      // Verify business logic execution
      await waitFor(() => {
        expect(mockDeps.authApi.createUser).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Test Tutor',
            email: 'tutor@example.com',
            phone_number: '+1234567890',
            primary_contact: 'email',
            user_type: 'tutor',
            school: expect.objectContaining({
              name: "Test Tutor's Tutoring Practice",
            }),
          }),
        );
        expect(mockDeps.authContext.checkAuthStatus).toHaveBeenCalled();
        expect(mockDeps.toast.showToast).toHaveBeenCalledWith(
          'success',
          'Registration successful! Please verify your email.',
        );
      });
    });

    it('should complete school registration with different flow', async () => {
      const mockDeps = createMockDependencies();
      mockDeps.authApi.createUser.mockResolvedValue({ success: true });

      const { getByText, getByPlaceholderText, getByLabelText } = render(
        <AuthDependencyProvider dependencies={mockDeps}>
          <SignUp />
        </AuthDependencyProvider>,
      );

      // Switch to school type
      const schoolTab = getByText('School');
      fireEvent.press(schoolTab);

      // Verify UI changes for school type
      expect(getByText('Register Your School')).toBeTruthy();
      expect(getByText('School Information')).toBeTruthy();

      // Fill out school registration form
      fireEvent.changeText(getByPlaceholderText('Enter your full name'), 'School Admin');
      fireEvent.changeText(getByPlaceholderText('Enter your email address'), 'admin@school.edu');
      fireEvent.changeText(getByPlaceholderText('Enter your phone number'), '+0987654321');
      fireEvent.changeText(getByPlaceholderText('Enter your school name'), 'Test University');
      fireEvent.changeText(getByPlaceholderText('Enter your school address'), '123 Education St');
      fireEvent.changeText(getByPlaceholderText('https://example.com'), 'https://test.edu');
      fireEvent.press(getByLabelText('Phone'));

      // Submit registration
      const createButton = getByText('Create Account');
      fireEvent.press(createButton);

      // Verify different business logic for school
      await waitFor(() => {
        expect(mockDeps.authApi.createUser).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'School Admin',
            email: 'admin@school.edu',
            phone_number: '+0987654321',
            primary_contact: 'phone',
            user_type: 'school',
            school: expect.objectContaining({
              name: 'Test University',
              address: '123 Education St',
              website: 'https://test.edu',
            }),
          }),
        );
        // School flow doesn't include tutor-specific next route
        expect(mockDeps.router.replace).toHaveBeenCalledWith(
          expect.stringContaining('/auth/verify-code'),
        );
        expect(mockDeps.router.replace).toHaveBeenCalledWith(
          expect.not.stringContaining('nextRoute'),
        );
      });
    });

    it('should handle registration validation errors', async () => {
      const mockDeps = createMockDependencies();

      const { getByText } = render(
        <AuthDependencyProvider dependencies={mockDeps}>
          <SignUp />
        </AuthDependencyProvider>,
      );

      // Try to submit empty form
      const createButton = getByText('Create Account');
      fireEvent.press(createButton);

      // Verify validation errors are shown
      await waitFor(() => {
        expect(getByText('Name is required')).toBeTruthy();
        expect(getByText('Email is required')).toBeTruthy();
        expect(getByText('Phone number is required')).toBeTruthy();
        expect(getByText('Please select a primary contact method')).toBeTruthy();
      });

      // API should not be called with invalid data
      expect(mockDeps.authApi.createUser).not.toHaveBeenCalled();
    });
  });

  describe('Complete Verification Flow with New Architecture', () => {
    it('should complete verification with onboarding redirect', async () => {
      const mockDeps = createMockDependencies();

      // Set up admin user requiring onboarding
      const adminUser = {
        id: 1,
        email: 'admin@test.com',
        name: 'Test Admin',
        is_admin: true,
        user_type: 'school_admin',
        primary_role: 'school_admin',
        first_login_completed: false,
      };

      mockDeps.authApi.verifyEmailCode.mockResolvedValue({
        user: adminUser,
        is_new_user: true,
        access_token: 'admin-token',
        refresh_token: 'admin-refresh',
      });

      mockDeps.onboardingApi.getNavigationPreferences.mockResolvedValue({
        show_onboarding: true,
      });

      mockDeps.onboardingApi.getOnboardingProgress.mockResolvedValue({
        completion_percentage: 0,
      });

      const { getByPlaceholderText, getByText } = render(
        <AuthDependencyProvider dependencies={mockDeps}>
          <VerifyCode />
        </AuthDependencyProvider>,
      );

      // Verify UI elements
      expect(getByText('Verify Code')).toBeTruthy();
      expect(getByPlaceholderText('Enter the verification code')).toBeTruthy();

      // Enter verification code
      const codeInput = getByPlaceholderText('Enter the verification code');
      const verifyButton = getByText('Verify Code');

      fireEvent.changeText(codeInput, '123456');
      fireEvent.press(verifyButton);

      // Verify complete flow execution
      await waitFor(() => {
        expect(mockDeps.authApi.verifyEmailCode).toHaveBeenCalledWith({
          email: expect.any(String),
          code: '123456',
        });
        expect(mockDeps.authContext.setUserProfile).toHaveBeenCalledWith(adminUser);
        expect(mockDeps.authContext.checkAuthStatus).toHaveBeenCalled();
        expect(mockDeps.onboardingApi.getNavigationPreferences).toHaveBeenCalled();
        expect(mockDeps.onboardingApi.getOnboardingProgress).toHaveBeenCalled();
        expect(mockDeps.router.replace).toHaveBeenCalledWith('/onboarding/welcome');
        expect(mockDeps.toast.showToast).toHaveBeenCalledWith(
          'success',
          'Verification successful!',
        );
      });
    });

    it('should complete verification with direct dashboard redirect', async () => {
      const mockDeps = createMockDependencies();

      // Set up regular user (not requiring onboarding)
      const regularUser = {
        id: 1,
        email: 'user@test.com',
        name: 'Regular User',
        is_admin: false,
        user_type: 'student',
        primary_role: 'student',
        first_login_completed: true,
      };

      mockDeps.authApi.verifyEmailCode.mockResolvedValue({
        user: regularUser,
        is_new_user: false,
        access_token: 'user-token',
        refresh_token: 'user-refresh',
      });

      const { getByPlaceholderText, getByText } = render(
        <AuthDependencyProvider dependencies={mockDeps}>
          <VerifyCode />
        </AuthDependencyProvider>,
      );

      // Enter verification code
      const codeInput = getByPlaceholderText('Enter the verification code');
      const verifyButton = getByText('Verify Code');

      fireEvent.changeText(codeInput, '654321');
      fireEvent.press(verifyButton);

      // Verify direct redirect to dashboard
      await waitFor(() => {
        expect(mockDeps.authApi.verifyEmailCode).toHaveBeenCalledWith({
          email: expect.any(String),
          code: '654321',
        });
        expect(mockDeps.authContext.setUserProfile).toHaveBeenCalledWith(regularUser);
        expect(mockDeps.router.replace).toHaveBeenCalledWith('/');
        expect(mockDeps.toast.showToast).toHaveBeenCalledWith(
          'success',
          'Verification successful!',
        );
      });
    });

    it('should handle verification failures with error recovery', async () => {
      const mockDeps = createMockDependencies();

      // Set up verification failure
      mockDeps.authApi.verifyEmailCode.mockRejectedValue({
        response: {
          status: 400,
          data: { error: 'Invalid verification code' },
        },
      });

      const { getByPlaceholderText, getByText } = render(
        <AuthDependencyProvider dependencies={mockDeps}>
          <VerifyCode />
        </AuthDependencyProvider>,
      );

      // Enter invalid verification code
      const codeInput = getByPlaceholderText('Enter the verification code');
      const verifyButton = getByText('Verify Code');

      fireEvent.changeText(codeInput, 'invalid');
      fireEvent.press(verifyButton);

      // Verify error handling
      await waitFor(() => {
        expect(mockDeps.authApi.verifyEmailCode).toHaveBeenCalledWith({
          email: expect.any(String),
          code: 'invalid',
        });
        expect(mockDeps.toast.showToast).toHaveBeenCalledWith('error', 'Invalid verification code');
        expect(mockDeps.router.replace).not.toHaveBeenCalled();
        expect(mockDeps.authContext.setUserProfile).not.toHaveBeenCalled();
      });
    });

    it('should handle code resending with proper feedback', async () => {
      const mockDeps = createMockDependencies();

      mockDeps.authApi.requestEmailCode.mockResolvedValue({ success: true });

      const { getByText } = render(
        <AuthDependencyProvider dependencies={mockDeps}>
          <VerifyCode />
        </AuthDependencyProvider>,
      );

      // Click resend button
      const resendButton = getByText('Try Again');
      fireEvent.press(resendButton);

      // Verify resend logic
      await waitFor(() => {
        expect(mockDeps.authApi.requestEmailCode).toHaveBeenCalledWith({
          email: expect.any(String),
        });
        expect(mockDeps.toast.showToast).toHaveBeenCalledWith(
          'success',
          'New verification code sent to your email!',
        );
      });
    });
  });

  describe('Architecture Separation Verification', () => {
    it('should demonstrate clear separation between UI and business logic', async () => {
      const mockDeps = createMockDependencies();
      mockDeps.authApi.requestEmailCode.mockResolvedValue({ success: true });

      // Create a custom SignIn component that uses the separated architecture
      const TestSignIn = () => {
        const signInLogic = useSignInLogic(mockDeps);

        return (
          <SignInForm
            isRequesting={signInLogic.isRequesting}
            error={signInLogic.error}
            onSubmitEmail={signInLogic.submitEmail}
            onKeyPress={signInLogic.handleKeyPress}
            onBackPress={() => mockDeps.router.back()}
          />
        );
      };

      const { getByPlaceholderText, getByText } = render(
        <AuthDependencyProvider dependencies={mockDeps}>
          <TestSignIn />
        </AuthDependencyProvider>,
      );

      // Interact with pure UI component
      const emailInput = getByPlaceholderText('your_email@example.com');
      const submitButton = getByText('Send Login Code');

      fireEvent.changeText(emailInput, 'separation@test.com');
      fireEvent.press(submitButton);

      // Verify business logic was executed
      await waitFor(() => {
        expect(mockDeps.authApi.requestEmailCode).toHaveBeenCalledWith({
          email: 'separation@test.com',
        });
      });
    });

    it('should allow independent testing of UI components', () => {
      // Test pure UI component in isolation
      const mockProps = {
        isRequesting: false,
        error: null,
        onSubmitEmail: jest.fn(),
        onKeyPress: jest.fn(),
        onBackPress: jest.fn(),
      };

      const { getByPlaceholderText, getByText } = render(<SignInForm {...mockProps} />);

      // Interact with UI
      const emailInput = getByPlaceholderText('your_email@example.com');
      const submitButton = getByText('Send Login Code');

      fireEvent.changeText(emailInput, 'ui@test.com');
      fireEvent.press(submitButton);

      // Only UI callbacks should be called, no business logic
      expect(mockProps.onSubmitEmail).toHaveBeenCalledWith('ui@test.com');
    });

    it('should allow independent testing of business logic hooks', async () => {
      const mockDeps = createMockDependencies();
      mockDeps.authApi.requestEmailCode.mockResolvedValue({ success: true });

      // Test business logic hook in isolation
      const { result } = renderHook(() => useSignInLogic(mockDeps));

      await act(async () => {
        await result.current.submitEmail('logic@test.com');
      });

      // Only business logic should be executed
      expect(mockDeps.authApi.requestEmailCode).toHaveBeenCalledWith({
        email: 'logic@test.com',
      });
      expect(mockDeps.toast.showToast).toHaveBeenCalledWith(
        'success',
        'Verification code sent to your email!',
      );
      expect(mockDeps.router.push).toHaveBeenCalledWith('/auth/verify-code?email=logic%40test.com');
    });
  });

  describe('Cross-Component Integration', () => {
    it('should maintain state consistency across component transitions', async () => {
      const mockDeps = createMockDependencies();

      // Set up successful flow
      mockDeps.authApi.requestEmailCode.mockResolvedValue({ success: true });
      mockDeps.authApi.verifyEmailCode.mockResolvedValue({
        user: {
          id: 1,
          email: 'flow@test.com',
          name: 'Flow User',
          is_admin: false,
          user_type: 'student',
        },
        is_new_user: false,
        access_token: 'flow-token',
      });

      // Start with SignIn
      const { getByPlaceholderText, getByText, rerender } = render(
        <AuthDependencyProvider dependencies={mockDeps}>
          <SignIn />
        </AuthDependencyProvider>,
      );

      // Complete sign-in
      fireEvent.changeText(getByPlaceholderText('your_email@example.com'), 'flow@test.com');
      fireEvent.press(getByText('Send Login Code'));

      await waitFor(() => {
        expect(mockDeps.router.push).toHaveBeenCalledWith(
          '/auth/verify-code?email=flow%40test.com',
        );
      });

      // Transition to VerifyCode (simulating navigation)
      rerender(
        <AuthDependencyProvider dependencies={mockDeps}>
          <VerifyCode />
        </AuthDependencyProvider>,
      );

      // Complete verification
      fireEvent.changeText(getByPlaceholderText('Enter the verification code'), '123456');
      fireEvent.press(getByText('Verify Code'));

      await waitFor(() => {
        expect(mockDeps.authApi.verifyEmailCode).toHaveBeenCalledWith({
          email: expect.any(String),
          code: '123456',
        });
        expect(mockDeps.router.replace).toHaveBeenCalledWith('/');
      });
    });

    it('should handle error recovery across component boundaries', async () => {
      const mockDeps = createMockDependencies();

      // First request fails
      mockDeps.authApi.requestEmailCode
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({ success: true });

      const { getByPlaceholderText, getByText } = render(
        <AuthDependencyProvider dependencies={mockDeps}>
          <SignIn />
        </AuthDependencyProvider>,
      );

      // First attempt fails
      fireEvent.changeText(getByPlaceholderText('your_email@example.com'), 'retry@test.com');
      fireEvent.press(getByText('Send Login Code'));

      await waitFor(() => {
        expect(mockDeps.toast.showToast).toHaveBeenCalledWith(
          'error',
          'Failed to send verification code. Please try again.',
        );
      });

      // Second attempt succeeds
      fireEvent.press(getByText('Send Login Code'));

      await waitFor(() => {
        expect(mockDeps.toast.showToast).toHaveBeenCalledWith(
          'success',
          'Verification code sent to your email!',
        );
        expect(mockDeps.router.push).toHaveBeenCalledWith(
          '/auth/verify-code?email=retry%40test.com',
        );
      });
    });
  });
});
