/**
 * VerifyCode Logic Hook with Dependency Injection
 *
 * This hook contains the business logic for email/phone code verification
 * using dependency injection for better testability.
 */

import { useState } from 'react';

import { useDependencies } from '@/services/di';

interface UseVerifyCodeLogicWithDIParams {
  contact: string; // email or phone
  contactType: 'email' | 'phone';
}

export const useVerifyCodeLogicWithDI = ({
  contact,
  contactType,
}: UseVerifyCodeLogicWithDIParams) => {
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const {
    authApi,
    toastService,
    routerService,
    authContextService,
    onboardingApiService,
    analyticsService,
  } = useDependencies();

  const submitVerification = async (code: string) => {
    if (!code || code.length !== 6) {
      const error = new Error('Please enter a valid 6-digit code');
      setError(error);
      throw error;
    }

    setIsVerifying(true);
    setError(null);

    try {
      // Prepare verification params based on contact type
      const verifyParams =
        contactType === 'email' ? { email: contact, code } : { phone: contact, code };

      const response = await authApi.verifyEmailCode(verifyParams);

      // Update auth context with user profile
      if (authContextService.setUserProfile && response.user) {
        await authContextService.setUserProfile(response.user);
      }

      await authContextService.checkAuthStatus();

      // Track analytics
      analyticsService.track('auth_code_verified', {
        contact_type: contactType,
        is_new_user: response.is_new_user || false,
      });

      toastService.showToast('success', 'Verification successful!');

      // Handle navigation based on user type and onboarding status
      if (response.is_new_user || !response.user.first_login_completed) {
        try {
          // Check onboarding preferences
          const navPrefs = await onboardingApiService.getNavigationPreferences();
          const progress = await onboardingApiService.getOnboardingProgress();

          if (
            (navPrefs && navPrefs.show_onboarding) ||
            (progress && progress.completion_percentage === 0)
          ) {
            routerService.replace('/onboarding/welcome');
            return response;
          }
        } catch (error) {
          // If onboarding data is not available, go to welcome anyway for new users
          if (__DEV__) {
            if (__DEV__) {
              console.warn('Could not fetch onboarding data, defaulting to welcome screen');
            }
          }
          routerService.replace('/onboarding/welcome');
          return response;
        }
      }

      // Navigate to dashboard for returning users
      routerService.replace('/dashboard');

      return response;
    } catch (error: any) {
      if (__DEV__) {
        console.error('Failed to verify code:', error);
      }
      setError(error);
      toastService.showToast('error', 'Invalid verification code. Please try again.');
      throw error;
    } finally {
      setIsVerifying(false);
    }
  };

  return {
    isVerifying,
    error,
    submitVerification,
  };
};
