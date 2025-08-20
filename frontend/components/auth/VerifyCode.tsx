/**
 * Container Component for Code Verification using New Architecture
 *
 * This component orchestrates the business logic and UI components.
 * The actual form logic is in VerifyCodeForm, and business logic is in useVerifyCodeLogic hook.
 */

import { useRouter, useLocalSearchParams } from 'expo-router';
import React from 'react';

import { AuthLayout } from './AuthLayout';
import { VerifyCodeForm } from './forms/VerifyCodeForm';

import { useVerifyCodeLogic } from '@/hooks/auth/useVerifyCodeLogic';
import {
  defaultAuthApiService,
  defaultOnboardingApiService,
  createRouterService,
  createToastService,
  createAuthContextService,
} from '@/services/implementations';

const VerifyCodeForm_Container = () => {
  const router = useRouter();
  const { contact, contactType, email, nextRoute } = useLocalSearchParams<{
    contact: string;
    contactType: 'email' | 'phone';
    email: string;
    nextRoute?: string;
  }>();

  // Handle both 'contact' and 'email' parameters for backward compatibility
  const actualContact = contact || email || '';
  const actualContactType = contactType || 'email'; // Default to email

  // Create service dependencies for the business logic hook
  const routerService = createRouterService();
  const toastService = createToastService();
  const authContextService = createAuthContextService();

  // Use the business logic hook with dependency injection
  const logic = useVerifyCodeLogic({
    contact: actualContact,
    contactType: actualContactType as 'email' | 'phone',
    nextRoute: nextRoute ? decodeURIComponent(nextRoute) : undefined,
    authApi: defaultAuthApiService,
    onboardingApi: defaultOnboardingApiService,
    authContext: authContextService,
    router: routerService,
    toast: toastService,
  });

  // Handle back navigation
  const handleBack = () => {
    router.back();
  };

  return <VerifyCodeForm logic={logic} onBack={handleBack} />;
};

export const VerifyCode = () => {
  return (
    <AuthLayout>
      <VerifyCodeForm_Container />
    </AuthLayout>
  );
};
