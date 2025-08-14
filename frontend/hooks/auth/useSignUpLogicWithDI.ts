/**
 * SignUp Logic Hook with Dependency Injection
 *
 * This hook contains the business logic for sign-up functionality
 * using dependency injection for better testability.
 */

import { useState } from 'react';

import { useDependencies } from '@/services/di';

interface UseSignUpLogicWithDIParams {
  userType: 'tutor' | 'school' | 'student';
}

interface RegistrationData {
  name: string;
  email: string;
  phone_number?: string;
  school_name?: string;
}

export const useSignUpLogicWithDI = ({ userType }: UseSignUpLogicWithDIParams) => {
  const [isRegistering, setIsRegistering] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const { authApi, toastService, routerService, analyticsService } = useDependencies();

  const submitRegistration = async (data: RegistrationData) => {
    if (!data.name || !data.email) {
      const error = new Error('Name and email are required');
      setError(error);
      throw error;
    }

    setIsRegistering(true);
    setError(null);

    try {
      const userData: any = {
        name: data.name,
        email: data.email,
        phone_number: data.phone_number,
        user_type: userType,
      };

      if (userType === 'tutor') {
        // For tutors, create a personal school
        userData.school = {
          name: `${data.name}'s Tutoring Practice`,
        };
      } else if (userType === 'school') {
        // For schools, use the provided school name
        userData.school = {
          name: data.school_name || 'New School',
        };
      }

      const response = await authApi.createUser(userData);

      // Track analytics
      analyticsService.track('user_registration', {
        user_type: userType,
        has_school: !!userData.school,
      });

      toastService.showToast('success', 'Account created successfully!');
      routerService.push('/dashboard');

      return response;
    } catch (error: any) {
      console.error('Failed to create account:', error);
      setError(error);
      toastService.showToast('error', 'Failed to create account. Please try again.');
      throw error;
    } finally {
      setIsRegistering(false);
    }
  };

  return {
    isRegistering,
    error,
    submitRegistration,
  };
};
