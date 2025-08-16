/**
 * TDD Tests for useVerifyCodeLogic Hook - NEW ARCHITECTURE
 *
 * These tests will INITIALLY FAIL until the new architecture is implemented.
 * The hook should separate verification business logic from UI components.
 */

import { renderHook, act } from '@testing-library/react-native';

import { useVerifyCodeLogic } from '@/hooks/auth/useVerifyCodeLogic';

// Mock dependencies
jest.mock('@/api/authApi');
jest.mock('@/api/onboardingApi');
jest.mock('@/api/auth');

const mockVerifyEmailCode = jest.fn();
const mockRequestEmailCode = jest.fn();
const mockCheckAuthStatus = jest.fn();
const mockSetUserProfile = jest.fn();
const mockGetNavigationPreferences = jest.fn();
const mockGetOnboardingProgress = jest.fn();
const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockShowToast = jest.fn();

// Mock the dependencies that will be injected
const mockAuthApi = {
  verifyEmailCode: mockVerifyEmailCode,
  requestEmailCode: mockRequestEmailCode,
};

const mockOnboardingApi = {
  getNavigationPreferences: mockGetNavigationPreferences,
  getOnboardingProgress: mockGetOnboardingProgress,
};

const mockAuthContext = {
  checkAuthStatus: mockCheckAuthStatus,
  setUserProfile: mockSetUserProfile,
};

const mockRouter = {
  push: mockPush,
  back: jest.fn(),
  replace: mockReplace,
};

const mockToast = {
  showToast: mockShowToast,
};

// Sample verification data
const sampleVerificationData = {
  contact: 'test@example.com',
  contactType: 'email' as const,
  code: '123456',
};

const sampleAuthResponse = {
  user: {
    id: 1,
    email: 'test@example.com',
    name: 'Test User',
    is_admin: true,
    user_type: 'school_admin',
    primary_role: 'school_admin',
    first_login_completed: false,
  },
  is_new_user: true,
  access_token: 'fake-token',
  refresh_token: 'fake-refresh-token',
};

describe('useVerifyCodeLogic Hook - New Architecture', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockVerifyEmailCode.mockResolvedValue(sampleAuthResponse);
    mockCheckAuthStatus.mockResolvedValue(undefined);
    mockSetUserProfile.mockResolvedValue(undefined);
    mockGetNavigationPreferences.mockResolvedValue({ show_onboarding: true });
    mockGetOnboardingProgress.mockResolvedValue({ completion_percentage: 0 });
  });

  describe('Hook Initialization', () => {
    it('should initialize with correct default state', () => {
      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      expect(result.current.isVerifying).toBe(false);
      expect(result.current.isResending).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.contact).toBe('test@example.com');
      expect(result.current.contactType).toBe('email');
      expect(typeof result.current.submitVerification).toBe('function');
      expect(typeof result.current.resendCode).toBe('function');
    });

    it('should accept dependency injection for all external dependencies', () => {
      const customAuthApi = { verifyEmailCode: jest.fn(), requestEmailCode: jest.fn() };
      const customOnboardingApi = {
        getNavigationPreferences: jest.fn(),
        getOnboardingProgress: jest.fn(),
      };
      const customAuthContext = { checkAuthStatus: jest.fn(), setUserProfile: jest.fn() };
      const customRouter = { push: jest.fn(), back: jest.fn(), replace: jest.fn() };
      const customToast = { showToast: jest.fn() };

      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: customAuthApi,
          onboardingApi: customOnboardingApi,
          authContext: customAuthContext,
          router: customRouter,
          toast: customToast,
        }),
      );

      expect(result.current.isVerifying).toBe(false);
      expect(typeof result.current.submitVerification).toBe('function');
    });

    it('should handle phone contact type initialization', () => {
      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: '+1234567890',
          contactType: 'phone',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      expect(result.current.contact).toBe('+1234567890');
      expect(result.current.contactType).toBe('phone');
    });
  });

  describe('Code Verification Logic', () => {
    it('should handle successful email verification', async () => {
      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      await act(async () => {
        await result.current.submitVerification('123456');
      });

      expect(mockVerifyEmailCode).toHaveBeenCalledWith({
        email: 'test@example.com',
        code: '123456',
      });
      expect(mockSetUserProfile).toHaveBeenCalledWith(sampleAuthResponse.user);
      expect(mockCheckAuthStatus).toHaveBeenCalled();
      expect(mockShowToast).toHaveBeenCalledWith('success', 'Verification successful!');
    });

    it('should handle successful phone verification', async () => {
      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: '+1234567890',
          contactType: 'phone',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      await act(async () => {
        await result.current.submitVerification('123456');
      });

      expect(mockVerifyEmailCode).toHaveBeenCalledWith({
        phone: '+1234567890',
        code: '123456',
      });
    });

    it('should handle verification API errors', async () => {
      const apiError = {
        response: {
          status: 400,
          data: { error: 'Invalid verification code' },
        },
      };
      mockVerifyEmailCode.mockRejectedValue(apiError);

      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      await act(async () => {
        await result.current.submitVerification('invalid');
      });

      expect(mockShowToast).toHaveBeenCalledWith('error', 'Invalid verification code');
      expect(result.current.error).toBe(apiError);
      expect(mockReplace).not.toHaveBeenCalled();
    });

    it('should handle rate limiting errors', async () => {
      const rateLimitError = {
        response: { status: 429 },
      };
      mockVerifyEmailCode.mockRejectedValue(rateLimitError);

      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      await act(async () => {
        await result.current.submitVerification('123456');
      });

      expect(mockShowToast).toHaveBeenCalledWith(
        'error',
        'Too many attempts. Please wait and try again.',
      );
    });

    it('should set loading state during verification', async () => {
      let resolvePromise: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolvePromise = resolve;
      });
      mockVerifyEmailCode.mockReturnValue(pendingPromise);

      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      // Start verification
      act(() => {
        result.current.submitVerification('123456');
      });

      // Should be verifying
      expect(result.current.isVerifying).toBe(true);

      // Complete verification
      await act(async () => {
        resolvePromise(sampleAuthResponse);
      });

      // Should no longer be verifying
      expect(result.current.isVerifying).toBe(false);
    });
  });

  describe('Code Resending Logic', () => {
    it('should handle successful code resend for email', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });

      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      await act(async () => {
        await result.current.resendCode();
      });

      expect(mockRequestEmailCode).toHaveBeenCalledWith({
        email: 'test@example.com',
      });
      expect(mockShowToast).toHaveBeenCalledWith(
        'success',
        'New verification code sent to your email!',
      );
    });

    it('should handle successful code resend for phone', async () => {
      mockRequestEmailCode.mockResolvedValue({ success: true });

      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: '+1234567890',
          contactType: 'phone',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      await act(async () => {
        await result.current.resendCode();
      });

      expect(mockRequestEmailCode).toHaveBeenCalledWith({
        phone: '+1234567890',
      });
      expect(mockShowToast).toHaveBeenCalledWith(
        'success',
        'New verification code sent to your phone!',
      );
    });

    it('should handle resend API errors', async () => {
      const resendError = new Error('Failed to resend');
      mockRequestEmailCode.mockRejectedValue(resendError);

      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      await act(async () => {
        await result.current.resendCode();
      });

      expect(mockShowToast).toHaveBeenCalledWith(
        'error',
        'Failed to send new verification code. Please try again.',
      );
    });

    it('should set loading state during code resend', async () => {
      let resolvePromise: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolvePromise = resolve;
      });
      mockRequestEmailCode.mockReturnValue(pendingPromise);

      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      // Start resend
      act(() => {
        result.current.resendCode();
      });

      // Should be resending
      expect(result.current.isResending).toBe(true);

      // Complete resend
      await act(async () => {
        resolvePromise({ success: true });
      });

      // Should no longer be resending
      expect(result.current.isResending).toBe(false);
    });
  });

  describe('Navigation Logic', () => {
    it('should navigate to specific next route when provided', async () => {
      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: '/onboarding/tutor-flow',
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      await act(async () => {
        await result.current.submitVerification('123456');
      });

      expect(mockReplace).toHaveBeenCalledWith('/onboarding/tutor-flow');
    });

    it('should navigate to onboarding for new school admins', async () => {
      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      await act(async () => {
        await result.current.submitVerification('123456');
      });

      expect(mockGetNavigationPreferences).toHaveBeenCalled();
      expect(mockGetOnboardingProgress).toHaveBeenCalled();
      expect(mockReplace).toHaveBeenCalledWith('/onboarding/welcome');
    });

    it('should navigate to root for completed users', async () => {
      const completedUser = {
        ...sampleAuthResponse,
        user: {
          ...sampleAuthResponse.user,
          first_login_completed: true,
        },
        is_new_user: false,
      };
      mockVerifyEmailCode.mockResolvedValue(completedUser);

      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      await act(async () => {
        await result.current.submitVerification('123456');
      });

      expect(mockReplace).toHaveBeenCalledWith('/');
    });

    it('should navigate to root for non-admin users', async () => {
      const nonAdminUser = {
        ...sampleAuthResponse,
        user: {
          ...sampleAuthResponse.user,
          is_admin: false,
          user_type: 'student',
        },
      };
      mockVerifyEmailCode.mockResolvedValue(nonAdminUser);

      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      await act(async () => {
        await result.current.submitVerification('123456');
      });

      expect(mockReplace).toHaveBeenCalledWith('/');
    });
  });

  describe('Onboarding Detection Logic', () => {
    it('should detect when onboarding is required', async () => {
      mockGetNavigationPreferences.mockResolvedValue({ show_onboarding: true });
      mockGetOnboardingProgress.mockResolvedValue({ completion_percentage: 0 });

      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      await act(async () => {
        await result.current.submitVerification('123456');
      });

      expect(mockReplace).toHaveBeenCalledWith('/onboarding/welcome');
    });

    it('should skip onboarding when disabled', async () => {
      mockGetNavigationPreferences.mockResolvedValue({ show_onboarding: false });

      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      await act(async () => {
        await result.current.submitVerification('123456');
      });

      expect(mockReplace).toHaveBeenCalledWith('/');
    });

    it('should skip onboarding when completed', async () => {
      mockGetOnboardingProgress.mockResolvedValue({ completion_percentage: 100 });

      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      await act(async () => {
        await result.current.submitVerification('123456');
      });

      expect(mockReplace).toHaveBeenCalledWith('/');
    });

    it('should handle onboarding API errors gracefully', async () => {
      mockGetNavigationPreferences.mockRejectedValue(new Error('API Error'));

      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      await act(async () => {
        await result.current.submitVerification('123456');
      });

      // Should default to showing onboarding when API fails
      expect(mockReplace).toHaveBeenCalledWith('/onboarding/welcome');
    });
  });

  describe('Error Recovery', () => {
    it('should continue with successful verification even if auth state update fails', async () => {
      mockCheckAuthStatus.mockRejectedValue(new Error('Auth state update failed'));

      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: '/custom-route',
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      await act(async () => {
        await result.current.submitVerification('123456');
      });

      // Should still show success and navigate
      expect(mockShowToast).toHaveBeenCalledWith('success', 'Verification successful!');
      expect(mockReplace).toHaveBeenCalledWith('/custom-route');
    });

    it('should clear errors on successful submission', async () => {
      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      // First, cause an error
      const error = new Error('Verification failed');
      mockVerifyEmailCode.mockRejectedValue(error);
      await act(async () => {
        await result.current.submitVerification('invalid');
      });
      expect(result.current.error).toBeTruthy();

      // Then, successful verification should clear the error
      mockVerifyEmailCode.mockResolvedValue(sampleAuthResponse);
      await act(async () => {
        await result.current.submitVerification('123456');
      });
      expect(result.current.error).toBeNull();
    });
  });

  describe('Pure Business Logic', () => {
    it('should be testable without any React components', async () => {
      // This test demonstrates that the hook contains pure business logic
      // that can be tested independently of UI components

      const { result } = renderHook(() =>
        useVerifyCodeLogic({
          contact: 'test@example.com',
          contactType: 'email',
          nextRoute: undefined,
          authApi: mockAuthApi,
          onboardingApi: mockOnboardingApi,
          authContext: mockAuthContext,
          router: mockRouter,
          toast: mockToast,
        }),
      );

      // Test the complete business logic flow
      await act(async () => {
        await result.current.submitVerification('123456');
      });

      // Verify all business logic was executed correctly
      expect(mockVerifyEmailCode).toHaveBeenCalledTimes(1);
      expect(mockSetUserProfile).toHaveBeenCalledTimes(1);
      expect(mockCheckAuthStatus).toHaveBeenCalledTimes(1);
      expect(mockGetNavigationPreferences).toHaveBeenCalledTimes(1);
      expect(mockGetOnboardingProgress).toHaveBeenCalledTimes(1);
      expect(mockShowToast).toHaveBeenCalledWith('success', 'Verification successful!');
      expect(mockReplace).toHaveBeenCalledTimes(1);
    });
  });
});
