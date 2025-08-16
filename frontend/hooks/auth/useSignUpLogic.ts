/**
 * Business Logic Hook for Sign-Up Flow
 *
 * This hook contains complex signup business logic for both tutor and school types,
 * separated from UI components for better testability and maintainability.
 * Uses dependency injection pattern for external services.
 */

import { useState, useCallback } from 'react';

import { AuthApiService, RouterService, ToastService, AuthContextService } from '@/services/types';

export interface SignUpFormData {
  userName: string;
  userEmail: string;
  userPhone: string;
  schoolName: string;
  schoolAddress: string;
  schoolWebsite: string;
  primaryContact: 'email' | 'phone';
}

export interface UseSignUpLogicProps {
  userType: 'tutor' | 'school';
  authApi: AuthApiService;
  authContext: AuthContextService;
  router: RouterService;
  toast: ToastService;
}

export interface UseSignUpLogicReturn {
  isSubmitting: boolean;
  error: Error | null;
  userType: 'tutor' | 'school';
  submitRegistration: (data: SignUpFormData) => Promise<void>;
  generateSchoolName: (userName: string, userType: string) => string;
  validateUserType: (type: string | undefined | null) => 'tutor' | 'school';
}

export const useSignUpLogic = ({
  userType,
  authApi,
  authContext,
  router,
  toast,
}: UseSignUpLogicProps): UseSignUpLogicReturn => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const generateSchoolName = useCallback((userName: string, userType: string): string => {
    if (userType !== 'tutor') return '';
    if (!userName?.trim()) return '';
    return `${userName.trim()}'s Tutoring Practice`;
  }, []);

  const validateUserType = useCallback((type: string | undefined | null): 'tutor' | 'school' => {
    if (type === 'tutor' || type === 'school') {
      return type;
    }
    return 'tutor'; // Default fallback
  }, []);

  const validateFormData = useCallback(
    (data: SignUpFormData): string | null => {
      if (!data.userName?.trim()) {
        return 'Name is required and cannot be empty';
      }
      if (!data.userEmail?.trim()) {
        return 'Email is required and cannot be empty';
      }
      if (userType === 'school' && !data.schoolName?.trim()) {
        return 'School name is required';
      }
      return null;
    },
    [userType],
  );

  const sanitizeFormData = useCallback((data: SignUpFormData): SignUpFormData => {
    return {
      ...data,
      userName: data.userName?.trim() || '',
      userEmail: data.userEmail?.toLowerCase().trim() || '',
      userPhone: data.userPhone?.trim() || '',
      schoolName: data.schoolName?.trim() || '',
      schoolAddress: data.schoolAddress?.trim() || '',
      schoolWebsite: data.schoolWebsite?.trim() || '',
    };
  }, []);

  const submitRegistration = useCallback(
    async (formData: SignUpFormData): Promise<void> => {
      try {
        setIsSubmitting(true);
        setError(null);

        // Validate form data
        const validationError = validateFormData(formData);
        if (validationError) {
          toast.showToast('error', validationError);
          return;
        }

        // Sanitize form data
        const sanitizedData = sanitizeFormData(formData);

        // Build API payload
        const apiData = {
          name: sanitizedData.userName,
          email: sanitizedData.userEmail,
          phone_number: sanitizedData.userPhone,
          primary_contact: sanitizedData.primaryContact,
          user_type: userType,
          school: {
            name:
              userType === 'tutor'
                ? generateSchoolName(sanitizedData.userName, userType)
                : sanitizedData.schoolName,
            address: sanitizedData.schoolAddress || undefined,
            website: sanitizedData.schoolWebsite || undefined,
          },
        };

        await authApi.createUser(apiData);
        await authContext.checkAuthStatus();

        toast.showToast('success', 'Registration successful! Please verify your email.');

        // Navigate to verification with appropriate next route
        const baseUrl = `/auth/verify-code?contact=${encodeURIComponent(
          sanitizedData.userEmail,
        )}&contactType=${sanitizedData.primaryContact}`;
        const nextRoute =
          userType === 'tutor'
            ? `${baseUrl}&nextRoute=${encodeURIComponent('/onboarding/tutor-flow')}`
            : baseUrl;

        router.replace(nextRoute);
      } catch (err) {
        const error = err as any;
        setError(error);

        // Handle specific error types
        if (error?.response?.status === 409) {
          toast.showToast(
            'error',
            'An account with this email already exists. Try signing in instead.',
          );
        } else if (error?.response?.status === 400) {
          toast.showToast(
            'error',
            'Invalid information provided. Please check your details and try again.',
          );
        } else {
          toast.showToast('error', 'Failed to complete registration. Please try again.');
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [
      authApi,
      authContext,
      router,
      toast,
      userType,
      generateSchoolName,
      validateFormData,
      sanitizeFormData,
    ],
  );

  return {
    isSubmitting,
    error,
    userType,
    submitRegistration,
    generateSchoolName,
    validateUserType,
  };
};
