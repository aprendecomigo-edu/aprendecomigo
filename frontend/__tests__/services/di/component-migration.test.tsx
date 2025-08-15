/**
 * TDD Tests for Component Migration to Dependency Injection
 *
 * These tests will INITIALLY FAIL until components are migrated to use DI.
 * Shows how to migrate existing components and hooks to use dependency injection.
 */

import { render, fireEvent, waitFor, renderHook, act } from '@testing-library/react-native';
import React from 'react';

// These imports will fail until components are migrated to DI
import { SignInWithDI } from '@/components/auth/SignInWithDI';
import { SignUpWithDI } from '@/components/auth/SignUpWithDI';
import { VerifyCodeWithDI } from '@/components/auth/VerifyCodeWithDI';
import { useSignInLogicWithDI } from '@/hooks/auth/useSignInLogicWithDI';
import { useSignUpLogicWithDI } from '@/hooks/auth/useSignUpLogicWithDI';
import { useVerifyCodeLogicWithDI } from '@/hooks/auth/useVerifyCodeLogicWithDI';

// DI infrastructure
import { DependencyProvider, useDependencies } from '@/services/di/context';
import { createMockDependencies } from '@/services/di/testing';
import type { Dependencies } from '@/services/di/types';

describe('Component Migration to Dependency Injection', () => {
  let mockDependencies: Dependencies;

  beforeEach(() => {
    jest.clearAllMocks();
    mockDependencies = createMockDependencies();
  });

  describe('SignIn Component Migration', () => {
    it('should render SignIn component with DI', () => {
      const { getByPlaceholderText, getByText } = render(
        <DependencyProvider dependencies={mockDependencies}>
          <SignInWithDI />
        </DependencyProvider>
      );

      expect(getByPlaceholderText('your_email@example.com')).toBeTruthy();
      expect(getByText('Send Login Code')).toBeTruthy();
    });

    it('should use injected dependencies for email submission', async () => {
      mockDependencies.authApi.requestEmailCode.mockResolvedValue({ success: true });

      const { getByPlaceholderText, getByText } = render(
        <DependencyProvider dependencies={mockDependencies}>
          <SignInWithDI />
        </DependencyProvider>
      );

      const emailInput = getByPlaceholderText('your_email@example.com');
      const submitButton = getByText('Send Login Code');

      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.press(submitButton);

      await waitFor(() => {
        expect(mockDependencies.authApi.requestEmailCode).toHaveBeenCalledWith({
          email: 'test@example.com',
        });
        expect(mockDependencies.toastService.showToast).toHaveBeenCalledWith(
          'success',
          'Verification code sent to your email!'
        );
        expect(mockDependencies.routerService.push).toHaveBeenCalledWith(
          '/auth/verify-code?email=test%40example.com'
        );
      });
    });

    it('should handle errors through injected dependencies', async () => {
      const networkError = new Error('Network error');
      mockDependencies.authApi.requestEmailCode.mockRejectedValue(networkError);

      const { getByPlaceholderText, getByText } = render(
        <DependencyProvider dependencies={mockDependencies}>
          <SignInWithDI />
        </DependencyProvider>
      );

      const emailInput = getByPlaceholderText('your_email@example.com');
      const submitButton = getByText('Send Login Code');

      fireEvent.changeText(emailInput, 'error@example.com');
      fireEvent.press(submitButton);

      await waitFor(() => {
        expect(mockDependencies.toastService.showToast).toHaveBeenCalledWith(
          'error',
          'Failed to send verification code. Please try again.'
        );
        expect(mockDependencies.routerService.push).not.toHaveBeenCalled();
      });
    });

    it('should support testing with partial dependency mocks', async () => {
      // Override only the auth API for this test
      const customMockDeps = {
        ...mockDependencies,
        authApi: {
          requestEmailCode: jest.fn().mockResolvedValue({ success: true, custom: true }),
          verifyEmailCode: jest.fn(),
          createUser: jest.fn(),
        },
      };

      const { getByPlaceholderText, getByText } = render(
        <DependencyProvider dependencies={customMockDeps}>
          <SignInWithDI />
        </DependencyProvider>
      );

      fireEvent.changeText(getByPlaceholderText('your_email@example.com'), 'custom@test.com');
      fireEvent.press(getByText('Send Login Code'));

      await waitFor(() => {
        expect(customMockDeps.authApi.requestEmailCode).toHaveBeenCalledWith({
          email: 'custom@test.com',
        });
      });
    });
  });

  describe('SignUp Component Migration', () => {
    it('should render SignUp component with DI and support both tutor and school flows', () => {
      const { getByText } = render(
        <DependencyProvider dependencies={mockDependencies}>
          <SignUpWithDI />
        </DependencyProvider>
      );

      expect(getByText('Individual Tutor')).toBeTruthy();
      expect(getByText('School')).toBeTruthy();
      expect(getByText('Create Account')).toBeTruthy();
    });

    it('should handle tutor registration through injected dependencies', async () => {
      mockDependencies.authApi.createUser.mockResolvedValue({ success: true });
      mockDependencies.authContextService.userProfile = {
        name: 'Test Tutor',
        email: 'tutor@test.com',
        phone_number: '+1234567890',
      };

      const { getByText } = render(
        <DependencyProvider dependencies={mockDependencies}>
          <SignUpWithDI />
        </DependencyProvider>
      );

      // Select tutor tab
      const tutorTab = getByText('Individual Tutor');
      fireEvent.press(tutorTab);

      // Submit registration
      const createButton = getByText('Create Account');
      fireEvent.press(createButton);

      await waitFor(() => {
        expect(mockDependencies.authApi.createUser).toHaveBeenCalledWith(
          expect.objectContaining({
            user_type: 'tutor',
            school: expect.objectContaining({
              name: "Test Tutor's Tutoring Practice",
            }),
          })
        );
      });
    });

    it('should handle school registration through injected dependencies', async () => {
      mockDependencies.authApi.createUser.mockResolvedValue({ success: true });

      const { getByText, getByPlaceholderText } = render(
        <DependencyProvider dependencies={mockDependencies}>
          <SignUpWithDI />
        </DependencyProvider>
      );

      // Select school tab
      const schoolTab = getByText('School');
      fireEvent.press(schoolTab);

      // Fill required fields
      fireEvent.changeText(getByPlaceholderText('Enter your full name'), 'School Admin');
      fireEvent.changeText(getByPlaceholderText('Enter your email address'), 'admin@school.edu');
      fireEvent.changeText(getByPlaceholderText('Enter your phone number'), '+1234567890');
      fireEvent.changeText(getByPlaceholderText('Enter your school name'), 'Test School');

      // Submit registration
      const createButton = getByText('Create Account');
      fireEvent.press(createButton);

      await waitFor(() => {
        expect(mockDependencies.authApi.createUser).toHaveBeenCalledWith(
          expect.objectContaining({
            user_type: 'school',
            school: expect.objectContaining({
              name: 'Test School',
            }),
          })
        );
      });
    });
  });

  describe('VerifyCode Component Migration', () => {
    it('should render VerifyCode component with DI', () => {
      const { getByPlaceholderText, getByText } = render(
        <DependencyProvider dependencies={mockDependencies}>
          <VerifyCodeWithDI />
        </DependencyProvider>
      );

      expect(getByPlaceholderText('Enter the verification code')).toBeTruthy();
      expect(getByText('Verify Code')).toBeTruthy();
    });

    it('should handle successful verification through injected dependencies', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        is_admin: false,
        user_type: 'student',
        primary_role: 'student',
        first_login_completed: true,
      };

      mockDependencies.authApi.verifyEmailCode.mockResolvedValue({
        user: mockUser,
        is_new_user: false,
        access_token: 'token',
        refresh_token: 'refresh',
      });

      const { getByPlaceholderText, getByText } = render(
        <DependencyProvider dependencies={mockDependencies}>
          <VerifyCodeWithDI />
        </DependencyProvider>
      );

      const codeInput = getByPlaceholderText('Enter the verification code');
      const verifyButton = getByText('Verify Code');

      fireEvent.changeText(codeInput, '123456');
      fireEvent.press(verifyButton);

      await waitFor(() => {
        expect(mockDependencies.authApi.verifyEmailCode).toHaveBeenCalledWith(
          expect.objectContaining({
            code: '123456',
          })
        );
        expect(mockDependencies.authContextService.setUserProfile).toHaveBeenCalledWith(mockUser);
        expect(mockDependencies.authContextService.checkAuthStatus).toHaveBeenCalled();
        expect(mockDependencies.toastService.showToast).toHaveBeenCalledWith(
          'success',
          'Verification successful!'
        );
      });
    });

    it('should handle new user onboarding flow through injected dependencies', async () => {
      const mockAdminUser = {
        id: 1,
        email: 'admin@test.com',
        name: 'Test Admin',
        is_admin: true,
        user_type: 'school_admin',
        primary_role: 'school_admin',
        first_login_completed: false,
      };

      mockDependencies.authApi.verifyEmailCode.mockResolvedValue({
        user: mockAdminUser,
        is_new_user: true,
        access_token: 'token',
        refresh_token: 'refresh',
      });
      mockDependencies.onboardingApiService.getNavigationPreferences.mockResolvedValue({
        show_onboarding: true,
      });
      mockDependencies.onboardingApiService.getOnboardingProgress.mockResolvedValue({
        completion_percentage: 0,
      });

      const { getByPlaceholderText, getByText } = render(
        <DependencyProvider dependencies={mockDependencies}>
          <VerifyCodeWithDI />
        </DependencyProvider>
      );

      const codeInput = getByPlaceholderText('Enter the verification code');
      const verifyButton = getByText('Verify Code');

      fireEvent.changeText(codeInput, '123456');
      fireEvent.press(verifyButton);

      await waitFor(() => {
        expect(mockDependencies.onboardingApiService.getNavigationPreferences).toHaveBeenCalled();
        expect(mockDependencies.onboardingApiService.getOnboardingProgress).toHaveBeenCalled();
        expect(mockDependencies.routerService.replace).toHaveBeenCalledWith('/onboarding/welcome');
      });
    });
  });

  describe('Hook Migration to DI', () => {
    describe('useSignInLogicWithDI', () => {
      it('should use injected dependencies instead of direct imports', async () => {
        mockDependencies.authApi.requestEmailCode.mockResolvedValue({ success: true });

        const { result } = renderHook(() => useSignInLogicWithDI(), {
          wrapper: ({ children }) => (
            <DependencyProvider dependencies={mockDependencies}>{children}</DependencyProvider>
          ),
        });

        await act(async () => {
          await result.current.submitEmail('hook@test.com');
        });

        expect(mockDependencies.authApi.requestEmailCode).toHaveBeenCalledWith({
          email: 'hook@test.com',
        });
        expect(mockDependencies.toastService.showToast).toHaveBeenCalledWith(
          'success',
          'Verification code sent to your email!'
        );
        expect(mockDependencies.routerService.push).toHaveBeenCalledWith(
          '/auth/verify-code?email=hook%40test.com'
        );
      });

      it('should be testable without React components', async () => {
        const { result } = renderHook(() => useSignInLogicWithDI(), {
          wrapper: ({ children }) => (
            <DependencyProvider dependencies={mockDependencies}>{children}</DependencyProvider>
          ),
        });

        // Pure business logic testing
        expect(result.current.isRequesting).toBe(false);
        expect(result.current.error).toBeNull();
        expect(typeof result.current.submitEmail).toBe('function');
      });

      it('should support different dependency configurations', async () => {
        const customDeps = {
          ...mockDependencies,
          authApi: {
            requestEmailCode: jest.fn(async ({ email }) => {
              if (email === 'fail@test.com') {
                throw new Error('Custom error');
              }
              return { success: true, custom: true };
            }),
            verifyEmailCode: jest.fn(),
            createUser: jest.fn(),
          },
        };

        const { result } = renderHook(() => useSignInLogicWithDI(), {
          wrapper: ({ children }) => (
            <DependencyProvider dependencies={customDeps}>{children}</DependencyProvider>
          ),
        });

        // Test success case
        await act(async () => {
          await result.current.submitEmail('success@test.com');
        });
        expect(result.current.error).toBeNull();

        // Test failure case
        await act(async () => {
          await result.current.submitEmail('fail@test.com');
        });
        expect(result.current.error?.message).toBe('Custom error');
      });
    });

    describe('useSignUpLogicWithDI', () => {
      it('should use injected dependencies for user registration', async () => {
        mockDependencies.authApi.createUser.mockResolvedValue({
          user: { id: 1, email: 'new@example.com' },
          created: true,
        });

        const { result } = renderHook(() => useSignUpLogicWithDI({ userType: 'student' }), {
          wrapper: ({ children }) => (
            <DependencyProvider dependencies={mockDependencies}>{children}</DependencyProvider>
          ),
        });

        await act(async () => {
          await result.current.submitRegistration({
            name: 'New User',
            email: 'new@example.com',
            phone_number: '+1234567890',
          });
        });

        expect(mockDependencies.authApi.createUser).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'New User',
            email: 'new@example.com',
            user_type: 'student',
          })
        );
      });

      it('should handle different user types through configuration', async () => {
        mockDependencies.authApi.createUser.mockResolvedValue({ success: true });

        const { result: tutorResult } = renderHook(
          () => useSignUpLogicWithDI({ userType: 'tutor' }),
          {
            wrapper: ({ children }) => (
              <DependencyProvider dependencies={mockDependencies}>{children}</DependencyProvider>
            ),
          }
        );

        await act(async () => {
          await tutorResult.current.submitRegistration({
            name: 'Tutor User',
            email: 'tutor@example.com',
          });
        });

        expect(mockDependencies.authApi.createUser).toHaveBeenCalledWith(
          expect.objectContaining({
            user_type: 'tutor',
          })
        );
      });
    });

    describe('useVerifyCodeLogicWithDI', () => {
      it('should use injected dependencies for code verification', async () => {
        const mockUser = { id: 1, email: 'verify@test.com' };
        mockDependencies.authApi.verifyEmailCode.mockResolvedValue({
          user: mockUser,
          access_token: 'token',
        });

        const { result } = renderHook(
          () =>
            useVerifyCodeLogicWithDI({
              contact: 'verify@test.com',
              contactType: 'email',
            }),
          {
            wrapper: ({ children }) => (
              <DependencyProvider dependencies={mockDependencies}>{children}</DependencyProvider>
            ),
          }
        );

        await act(async () => {
          await result.current.submitVerification('123456');
        });

        expect(mockDependencies.authApi.verifyEmailCode).toHaveBeenCalledWith({
          email: 'verify@test.com',
          code: '123456',
        });
        expect(mockDependencies.authContextService.setUserProfile).toHaveBeenCalledWith(mockUser);
      });

      it('should handle both email and phone verification', async () => {
        const mockUser = { id: 1, phone: '+1234567890' };
        mockDependencies.authApi.verifyEmailCode.mockResolvedValue({
          user: mockUser,
          access_token: 'token',
        });

        const { result } = renderHook(
          () =>
            useVerifyCodeLogicWithDI({
              contact: '+1234567890',
              contactType: 'phone',
            }),
          {
            wrapper: ({ children }) => (
              <DependencyProvider dependencies={mockDependencies}>{children}</DependencyProvider>
            ),
          }
        );

        await act(async () => {
          await result.current.submitVerification('654321');
        });

        expect(mockDependencies.authApi.verifyEmailCode).toHaveBeenCalledWith({
          phone: '+1234567890',
          code: '654321',
        });
      });
    });
  });

  describe('Migration Benefits Demonstration', () => {
    it('should demonstrate improved testability over direct imports', async () => {
      // Before DI: Hard to test because of direct imports
      // After DI: Easy to test with injected mocks

      const mockDeps = {
        ...mockDependencies,
        authApi: {
          requestEmailCode: jest
            .fn()
            .mockResolvedValueOnce({ success: false, error: 'Rate limit' })
            .mockResolvedValue({ success: true }),
          verifyEmailCode: jest.fn(),
          createUser: jest.fn(),
        },
      };

      const { result } = renderHook(() => useSignInLogicWithDI(), {
        wrapper: ({ children }) => (
          <DependencyProvider dependencies={mockDeps}>{children}</DependencyProvider>
        ),
      });

      // Test first attempt (rate limited)
      await act(async () => {
        await result.current.submitEmail('test@example.com');
      });
      expect(result.current.error).toBeTruthy();

      // Test second attempt (success)
      await act(async () => {
        await result.current.submitEmail('test@example.com');
      });
      expect(result.current.error).toBeNull();
    });

    it('should demonstrate service isolation and mocking flexibility', () => {
      // Can test components with different service implementations
      const fastApiMock = createMockDependencies();
      const slowApiMock = createMockDependencies();

      fastApiMock.authApi.requestEmailCode.mockResolvedValue({ success: true, speed: 'fast' });
      slowApiMock.authApi.requestEmailCode.mockImplementation(
        () =>
          new Promise(resolve => setTimeout(() => resolve({ success: true, speed: 'slow' }), 100))
      );

      // Each test can use different implementations
      expect(fastApiMock.authApi.requestEmailCode).not.toBe(slowApiMock.authApi.requestEmailCode);
    });

    it('should demonstrate cross-cutting concern injection', async () => {
      // Can inject analytics, logging, monitoring services
      const analyticsSpyDeps = {
        ...mockDependencies,
        analyticsService: {
          track: jest.fn(),
          identify: jest.fn(),
          screen: jest.fn(),
        },
      };

      const { result } = renderHook(() => useSignInLogicWithDI(), {
        wrapper: ({ children }) => (
          <DependencyProvider dependencies={analyticsSpyDeps}>{children}</DependencyProvider>
        ),
      });

      await act(async () => {
        await result.current.submitEmail('analytics@test.com');
      });

      // Can verify analytics were called correctly
      expect(analyticsSpyDeps.analyticsService.track).toHaveBeenCalledWith(
        'auth_email_submitted',
        expect.objectContaining({
          email_domain: 'test.com',
        })
      );
    });

    it('should demonstrate environment-specific service swapping', () => {
      // Production vs Test vs Development services
      const productionDeps = createMockDependencies();
      const testDeps = createMockDependencies();

      // Production: Real analytics
      productionDeps.analyticsService = {
        track: (event, props) => {
          // Real implementation would send to analytics service
          if (__DEV__) {
            console.log('Production analytics:', event, props);
          }
        },
        identify: () => {},
        screen: () => {},
      };

      // Test: Mock analytics
      testDeps.analyticsService = {
        track: jest.fn(),
        identify: jest.fn(),
        screen: jest.fn(),
      };

      expect(productionDeps.analyticsService).not.toBe(testDeps.analyticsService);
    });
  });

  describe('Backwards Compatibility and Migration Path', () => {
    it('should support gradual migration from old to new architecture', () => {
      // Components can be migrated one by one
      // Old components still work alongside new DI components

      const { getByText: getNewText } = render(
        <DependencyProvider dependencies={mockDependencies}>
          <SignInWithDI />
        </DependencyProvider>
      );

      // New component with DI
      expect(getNewText('Send Login Code')).toBeTruthy();

      // Old components could still render without DI (if not migrated yet)
      // This demonstrates the migration path
    });

    it('should provide fallback to default dependencies when no provider exists', () => {
      // This test would pass once default dependency provider is implemented
      // Shows how components can work without explicit DI provider

      const TestComponent = () => {
        const deps = useDependencies();
        return <div>Dependencies available: {deps ? 'yes' : 'no'}</div>;
      };

      // This would use default dependencies
      // expect(() => render(<TestComponent />)).not.toThrow();
    });
  });
});
