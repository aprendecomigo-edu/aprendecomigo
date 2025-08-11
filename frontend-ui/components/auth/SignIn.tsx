import useRouter from '@unitools/router';
import React from 'react';

import { AuthLayout } from './AuthLayout';
import { SignInForm } from './forms/SignInForm';

import { useToast } from '@/components/ui/toast';
import { useSignInLogic } from '@/hooks/auth/useSignInLogic';
import {
  defaultAuthApiService,
  createRouterService,
  createToastService,
} from '@/services/implementations';

const LoginForm = () => {
  const router = useRouter();
  const toast = useToast();

  // Create service dependencies for the business logic hook
  const routerService = createRouterService();
  const toastService = createToastService();

  // Use the business logic hook with dependency injection
  const logic = useSignInLogic({
    authApi: defaultAuthApiService,
    router: routerService,
    toast: toastService,
  });

  // Handle back navigation
  const handleBack = () => {
    router.back();
  };

  return (
    <SignInForm
      isRequesting={logic.isRequesting}
      error={logic.error}
      onSubmitEmail={logic.submitEmail}
      onKeyPress={() => logic.handleKeyPress('')}
      onBackPress={handleBack}
    />
  );
};

export const SignIn = () => {
  return (
    <AuthLayout>
      <LoginForm />
    </AuthLayout>
  );
};
