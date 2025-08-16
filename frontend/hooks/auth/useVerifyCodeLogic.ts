/**
 * Business Logic Hook for Code Verification Flow
 *
 * This hook contains verification business logic including onboarding detection,
 * separated from UI components for better testability and maintainability.
 * Uses dependency injection pattern for external services.
 */

import { useState, useCallback } from 'react';

import {
  AuthApiService,
  OnboardingApiService,
  AuthContextService,
  RouterService,
  ToastService,
} from '@/services/types';
import { safePromiseAllPreserveSuccessful } from '@/utils/promiseUtils';

export interface UseVerifyCodeLogicProps {
  contact: string;
  contactType: 'email' | 'phone';
  nextRoute: string | undefined;
  authApi: AuthApiService;
  onboardingApi: OnboardingApiService;
  authContext: AuthContextService;
  router: RouterService;
  toast: ToastService;
}

export interface UseVerifyCodeLogicReturn {
  isVerifying: boolean;
  isResending: boolean;
  error: Error | null;
  contact: string;
  contactType: 'email' | 'phone';
  submitVerification: (code: string) => Promise<void>;
  resendCode: () => Promise<void>;
}

export const useVerifyCodeLogic = ({
  contact,
  contactType,
  nextRoute,
  authApi,
  onboardingApi,
  authContext,
  router,
  toast,
}: UseVerifyCodeLogicProps): UseVerifyCodeLogicReturn => {
  const [isVerifying, setIsVerifying] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const determineNavigationRoute = useCallback(
    async (authResponse: any): Promise<string> => {
      // If explicit next route provided, use it
      if (nextRoute) {
        return nextRoute;
      }

      // If user is not new or not admin, go to root
      if (!authResponse.is_new_user || !authResponse.user.is_admin) {
        return '/';
      }

      // If first login is completed, go to root
      if (authResponse.user.first_login_completed) {
        return '/';
      }

      // For new admin users, check onboarding status with graceful error handling
      try {
        const { values, failures } = await safePromiseAllPreserveSuccessful([
          onboardingApi.getNavigationPreferences(),
          onboardingApi.getOnboardingProgress(),
        ]);

        const [preferences, progress] = values;

        // If both calls failed, default to home
        if (failures.length === 2) {
          console.warn('Failed to load onboarding data, defaulting to home');
          return '/';
        }

        // Skip onboarding if disabled or completed
        // Handle partial failures gracefully
        const shouldShowOnboarding = preferences?.show_onboarding ?? true; // Default to true if preferences failed
        const completionPercentage = progress?.completion_percentage ?? 0; // Default to 0 if progress failed

        if (!shouldShowOnboarding || completionPercentage >= 100) {
          return '/';
        }

        return '/onboarding/welcome';
      } catch (error) {
        // If onboarding API fails, default to showing onboarding for safety
        return '/onboarding/welcome';
      }
    },
    [nextRoute, onboardingApi],
  );

  const submitVerification = useCallback(
    async (code: string): Promise<void> => {
      try {
        setIsVerifying(true);
        setError(null);

        // Build verification parameters based on contact type
        const verifyParams =
          contactType === 'email' ? { email: contact, code } : { phone: contact, code };

        const authResponse = await authApi.verifyEmailCode(verifyParams);

        // Update auth state
        if (authContext.setUserProfile) {
          await authContext.setUserProfile(authResponse.user);
        }

        try {
          await authContext.checkAuthStatus();
        } catch (error) {
          // Continue even if auth state update fails
          if (__DEV__) {
            console.warn('Auth state update failed, continuing with verification:', error);
          }
        }

        toast.showToast('success', 'Verification successful!');

        // Determine and navigate to appropriate route
        const route = await determineNavigationRoute(authResponse);
        router.replace(route);
      } catch (err) {
        const error = err as any;
        setError(error);

        // Handle specific error types
        if (error?.response?.status === 400) {
          toast.showToast('error', 'Invalid verification code');
        } else if (error?.response?.status === 429) {
          toast.showToast('error', 'Too many attempts. Please wait and try again.');
        } else {
          toast.showToast('error', 'Invalid verification code. Please try again.');
        }
      } finally {
        setIsVerifying(false);
      }
    },
    [contact, contactType, authApi, authContext, toast, router, determineNavigationRoute],
  );

  const resendCode = useCallback(async (): Promise<void> => {
    try {
      setIsResending(true);
      setError(null);

      // Build resend parameters based on contact type
      const resendParams = contactType === 'email' ? { email: contact } : { phone: contact };

      await authApi.requestEmailCode(resendParams);

      const successMessage =
        contactType === 'email'
          ? 'New verification code sent to your email!'
          : 'New verification code sent to your phone!';

      toast.showToast('success', successMessage);
    } catch (err) {
      const error = err as Error;
      setError(error);
      toast.showToast('error', 'Failed to send new verification code. Please try again.');
    } finally {
      setIsResending(false);
    }
  }, [contact, contactType, authApi, toast]);

  return {
    isVerifying,
    isResending,
    error,
    contact,
    contactType,
    submitVerification,
    resendCode,
  };
};
