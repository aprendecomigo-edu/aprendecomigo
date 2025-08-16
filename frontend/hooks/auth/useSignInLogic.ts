/**
 * Business Logic Hook for Sign-In Flow
 *
 * This hook contains pure business logic for sign-in authentication,
 * separated from UI components for better testability and maintainability.
 * Uses dependency injection pattern for external services.
 */

import { useState, useCallback } from 'react';

import { AuthApiService, RouterService, ToastService } from '@/services/types';

export interface UseSignInLogicProps {
  authApi: AuthApiService;
  router: RouterService;
  toast: ToastService;
}

export interface UseSignInLogicReturn {
  isRequesting: boolean;
  error: Error | null;
  submitEmail: (email: string) => Promise<void>;
  handleKeyPress: (email: string) => void;
}

export const useSignInLogic = ({
  authApi,
  router,
  toast,
}: UseSignInLogicProps): UseSignInLogicReturn => {
  const [isRequesting, setIsRequesting] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const submitEmail = useCallback(
    async (email: string): Promise<void> => {
      try {
        setIsRequesting(true);
        setError(null);

        await authApi.requestEmailCode({ email });

        toast.showToast('success', 'Verification code sent to your email!');
        router.push(`/auth/verify-code?email=${encodeURIComponent(email)}`);
      } catch (err) {
        const error = err as Error;
        setError(error);
        toast.showToast('error', 'Failed to send verification code. Please try again.');
      } finally {
        setIsRequesting(false);
      }
    },
    [authApi, router, toast],
  );

  const handleKeyPress = useCallback(
    (email: string) => {
      // This can be used by UI components to handle keyboard interactions
      // The actual form submission logic is handled by submitEmail
      submitEmail(email);
    },
    [submitEmail],
  );

  return {
    isRequesting,
    error,
    submitEmail,
    handleKeyPress,
  };
};
