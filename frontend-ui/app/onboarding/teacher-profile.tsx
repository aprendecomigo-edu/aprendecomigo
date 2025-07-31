import React from 'react';
import { Platform } from 'react-native';
import useRouter from '@unitools/router';

import { TeacherProfileWizard } from '@/screens/onboarding/teacher-profile-wizard';
import { AuthGuard } from '@/components/auth/auth-guard';

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
      <TeacherProfileWizard
        onComplete={handleComplete}
        onExit={handleExit}
      />
    </AuthGuard>
  );
}