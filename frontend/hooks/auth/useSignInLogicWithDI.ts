/**
 * SignIn Logic Hook with Dependency Injection
 *
 * This hook contains the business logic for sign-in functionality
 * using dependency injection for better testability.
 */

import { useState } from 'react';

import { useDependencies } from '@/services/di';

export const useSignInLogicWithDI = () => {
  const [isRequesting, setIsRequesting] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const { authApi, toastService, routerService, analyticsService } = useDependencies();

  const submitEmail = async (email: string) => {
    if (!email) {
      const error = new Error('Email is required');
      setError(error);
      throw error;
    }

    setIsRequesting(true);
    setError(null);

    try {
      await authApi.requestEmailCode({ email });

      // Track analytics
      analyticsService.track('auth_email_submitted', {
        email_domain: email.split('@')[1],
      });

      toastService.showToast('success', 'Verification code sent to your email!');
      routerService.push(`/auth/verify-code?email=${encodeURIComponent(email)}`);
    } catch (error: any) {
      if (__DEV__) {
        console.error('Failed to request email code:', error); // TODO: Review for sensitive data
      }
      setError(error);
      toastService.showToast('error', 'Failed to send verification code. Please try again.');
      throw error;
    } finally {
      setIsRequesting(false);
    }
  };

  return {
    isRequesting,
    error,
    submitEmail,
  };
};
