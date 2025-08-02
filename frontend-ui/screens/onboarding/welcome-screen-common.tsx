import useRouter from '@unitools/router';
import {
  CheckCircle,
  ArrowRight,
  SkipForward,
  Building2,
  Users,
  GraduationCap,
} from 'lucide-react-native';
import React, { useState, useEffect } from 'react';

import { useAuth } from '@/api/authContext';
import { useOnboarding } from '@/hooks/useOnboarding';

export interface WelcomeScreenProps {
  onGetStarted?: () => void;
  onSkip?: () => void;
}

export interface PlatformCapability {
  icon: typeof CheckCircle;
  title: string;
  description: string;
}

// Shared platform capabilities data
export const platformCapabilities: PlatformCapability[] = [
  {
    icon: Building2,
    title: 'School Management',
    description: 'Manage school information, settings, and organizational structure',
  },
  {
    icon: Users,
    title: 'Teacher Coordination',
    description: 'Invite teachers, manage schedules, and track performance',
  },
  {
    icon: GraduationCap,
    title: 'Student Enrollment',
    description: 'Add students, manage enrollments, and track academic progress',
  },
];

// Shared icons for export
export const WelcomeScreenIcons = {
  CheckCircle,
  ArrowRight,
  SkipForward,
  Building2,
  Users,
  GraduationCap,
};

// Custom hook for welcome screen business logic
export function useWelcomeScreen({ onGetStarted, onSkip }: WelcomeScreenProps) {
  const router = useRouter();
  const { userProfile } = useAuth();
  const { skipOnboarding, createOnboardingTask, isLoading } = useOnboarding();
  const [showSkipDialog, setShowSkipDialog] = useState(false);
  const [isSkipping, setIsSkipping] = useState(false);

  // Create initial onboarding tasks when component mounts
  useEffect(() => {
    const createInitialTasks = async () => {
      if (!userProfile?.is_admin) return;

      try {
        // Create the first essential task
        await createOnboardingTask({
          title: 'Complete your school profile',
          description:
            'Add school information, logo, and contact details to personalize your account',
          priority: 'high',
          task_type: 'onboarding',
          due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days from now
        });
      } catch (error) {
        console.error('Error creating initial tasks:', error);
      }
    };

    createInitialTasks();
  }, [userProfile, createOnboardingTask]);

  const handleGetStarted = () => {
    if (onGetStarted) {
      onGetStarted();
    } else {
      router.push('/(school-admin)/dashboard');
    }
  };

  const handleSkipConfirm = async () => {
    try {
      setIsSkipping(true);
      await skipOnboarding();

      if (onSkip) {
        onSkip();
      } else {
        router.replace('/(school-admin)/dashboard');
      }
    } catch (error) {
      console.error('Error skipping onboarding:', error);
    } finally {
      setIsSkipping(false);
      setShowSkipDialog(false);
    }
  };

  return {
    userProfile,
    isLoading,
    showSkipDialog,
    setShowSkipDialog,
    isSkipping,
    handleGetStarted,
    handleSkipConfirm,
  };
}