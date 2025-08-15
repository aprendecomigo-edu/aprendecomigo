/**
 * Container Component for Sign-Up using New Architecture
 *
 * This component orchestrates the business logic and UI components.
 * The actual form logic is in SignUpForm, and business logic is in useSignUpLogic hook.
 */

import useRouter from '@unitools/router';
import { useLocalSearchParams } from 'expo-router';
import React from 'react';

import { AuthLayout } from './AuthLayout';
import { SignUpForm } from './forms/SignUpForm';

import { useAuth, useUserProfile } from '@/api/auth';
import { useToast } from '@/components/ui/toast';
import { useSignUpLogic } from '@/hooks/auth/useSignUpLogic';
import {
  defaultAuthApiService,
  createRouterService,
  createToastService,
  createAuthContextService,
} from '@/services/implementations';

export type UserType = 'tutor' | 'school';

// Helper function to validate and normalize user type
const validateUserType = (type: string | undefined): UserType => {
  if (type === 'tutor' || type === 'school') {
    return type;
  }

  // Log warning for invalid type but gracefully fallback
  if (type && type !== 'tutor' && type !== 'school') {
    if (__DEV__) {
      console.warn(`Invalid user type "${type}" provided. Defaulting to "tutor".`);
    }
  }

  return 'tutor'; // Default to tutor
};

const SignUpForm_Container = () => {
  const router = useRouter();
  const toast = useToast();
  const { type } = useLocalSearchParams<{ type: string }>();
  const userType = validateUserType(type);

  // Create service dependencies for the business logic hook
  const routerService = createRouterService();
  const toastService = createToastService();
  const authContextService = createAuthContextService();

  // Use the business logic hook with dependency injection
  const logic = useSignUpLogic({
    userType,
    authApi: defaultAuthApiService,
    authContext: authContextService,
    router: routerService,
    toast: toastService,
  });

  // Handle back navigation
  const handleBack = () => {
    router.back();
  };

  return <SignUpForm logic={logic} onBack={handleBack} />;
};

export const SignUp = () => {
  return (
    <AuthLayout>
      <SignUpForm_Container />
    </AuthLayout>
  );
};
