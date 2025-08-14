import useRouter from '@unitools/router';
import React from 'react';
import { Platform } from 'react-native';

import { AuthGuard } from '@/components/auth/AuthGuard';
import { TeacherProfileWizard } from '@/components/onboarding/TeacherProfileWizard';

export default function TeacherProfileOnboardingPage() {
  const router = useRouter();

  const handleComplete = () => {
    // Navigate to dashboard after profile completion
    router.replace('/(school-admin)/dashboard');
  };

  const handleExit = () => {
    // Navigate back to previous screen or dashboard
    router.back();
  };

  return (
    <AuthGuard>
      <TeacherProfileWizard onComplete={handleComplete} onExit={handleExit} />
    </AuthGuard>
  );
}
