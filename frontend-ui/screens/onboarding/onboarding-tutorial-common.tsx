import React, { useEffect } from 'react';

import { useTutorial } from '@/components/tutorial/TutorialContext';
import { TutorialConfig, TutorialStep } from '@/components/tutorial/types';
import { useOnboarding } from '@/hooks/useOnboarding';

export interface OnboardingTutorialProps {
  autoStart?: boolean;
  onComplete?: () => void;
  onSkip?: () => void;
  userType?: string;
}

// Desktop tutorial configuration
export const createDesktopOnboardingTutorialConfig = (userType: string = 'admin'): TutorialConfig => ({
  id: 'onboarding-tutorial',
  title: 'School Admin Onboarding',
  description: 'Learn how to set up and manage your school on the Aprende Comigo platform',
  canSkip: true,
  autoStart: false,
  showProgress: true,
  steps: [
    {
      id: 'welcome-overview',
      title: 'Welcome to Aprende Comigo!',
      content:
        'This tutorial will guide you through setting up your school and getting started with the platform. You can skip any step or exit at any time.',
      position: 'center',
      highlight: false,
      skippable: true,
    },
    {
      id: 'dashboard-overview',
      title: 'Your Dashboard',
      content:
        'This is your main dashboard where you can see school metrics, recent activities, and quick actions. Think of it as your command center.',
      targetElement: '[data-testid="dashboard-overview"]',
      position: 'bottom',
      highlight: true,
      skippable: true,
    },
    {
      id: 'school-profile',
      title: 'Complete School Profile',
      content:
        'Start by completing your school profile. This information will be visible to teachers, students, and parents.',
      targetElement: '[data-testid="school-profile-card"]',
      position: 'right',
      highlight: true,
      action: {
        label: 'Open School Profile',
        onPress: () => {
          // Navigate to school profile settings
          console.log('Navigate to school profile');
        },
      },
      skippable: true,
    },
    {
      id: 'invite-teachers',
      title: 'Invite Your Teachers',
      content:
        'Teachers are the backbone of your platform. Use the invitation system to bring your teaching team onboard.',
      targetElement: '[data-testid="invite-teachers-card"]',
      position: 'left',
      highlight: true,
      action: {
        label: 'Invite Teachers',
        onPress: () => {
          // Open teacher invitation modal
          console.log('Open teacher invitation modal');
        },
      },
      skippable: true,
    },
    {
      id: 'add-students',
      title: 'Add Students',
      content:
        'Add students individually or import them in bulk. Student information helps with class scheduling and progress tracking.',
      targetElement: '[data-testid="add-students-card"]',
      position: 'top',
      highlight: true,
      action: {
        label: 'Add Students',
        onPress: () => {
          // Open student addition modal
          console.log('Open student addition modal');
        },
      },
      skippable: true,
    },
    {
      id: 'billing-setup',
      title: 'Set Up Billing',
      content:
        'Configure your payment methods and billing preferences to enable seamless transactions for your school.',
      targetElement: '[data-testid="billing-setup-card"]',
      position: 'bottom',
      highlight: true,
      action: {
        label: 'Set Up Billing',
        onPress: () => {
          // Navigate to billing settings
          console.log('Navigate to billing settings');
        },
      },
      skippable: true,
    },
    {
      id: 'create-schedule',
      title: 'Create Your First Schedule',
      content:
        'Set up class schedules to organize tutoring sessions and manage teacher-student assignments effectively.',
      targetElement: '[data-testid="create-schedule-card"]',
      position: 'right',
      highlight: true,
      action: {
        label: 'Create Schedule',
        onPress: () => {
          // Navigate to calendar/scheduling
          console.log('Navigate to calendar');
        },
      },
      skippable: true,
    },
    {
      id: 'navigation-help',
      title: 'Navigation & Help',
      content:
        'Use the sidebar to navigate between different sections. Look for help icons (?) throughout the platform for contextual assistance.',
      targetElement: '[data-testid="sidebar-navigation"]',
      position: 'right',
      highlight: true,
      skippable: true,
    },
    {
      id: 'completion',
      title: 'Tutorial Complete!',
      content:
        'Congratulations! You now know the basics of managing your school on Aprende Comigo. You can always access this tutorial again from the help menu.',
      position: 'center',
      highlight: false,
      skippable: false,
    },
  ],
});

// Mobile-specific tutorial steps
export const createMobileOnboardingTutorialConfig = (): TutorialConfig => ({
  id: 'mobile-onboarding-tutorial',
  title: 'Mobile School Admin Guide',
  description: 'Learn how to manage your school on mobile devices',
  canSkip: true,
  autoStart: false,
  showProgress: true,
  steps: [
    {
      id: 'mobile-welcome',
      title: 'Welcome to Mobile Management',
      content:
        'Manage your school on the go! This mobile tutorial will show you the key features optimized for your device.',
      position: 'center',
      highlight: false,
      skippable: true,
    },
    {
      id: 'mobile-navigation',
      title: 'Mobile Navigation',
      content:
        'Use the hamburger menu to access all features. Swipe gestures are supported throughout the app.',
      targetElement: '[data-testid="mobile-menu-button"]',
      position: 'bottom',
      highlight: true,
      skippable: true,
    },
    {
      id: 'mobile-quick-actions',
      title: 'Quick Actions',
      content:
        'Access the most common actions directly from your dashboard for faster school management.',
      targetElement: '[data-testid="quick-actions-panel"]',
      position: 'top',
      highlight: true,
      skippable: true,
    },
    {
      id: 'mobile-notifications',
      title: 'Stay Updated',
      content:
        'Enable push notifications to stay informed about important school activities and teacher communications.',
      targetElement: '[data-testid="notifications-bell"]',
      position: 'bottom',
      highlight: true,
      skippable: true,
    },
    {
      id: 'mobile-completion',
      title: 'Mobile Setup Complete!',
      content:
        "You're all set to manage your school from anywhere. Remember to sync data when you have a stable internet connection.",
      position: 'center',
      highlight: false,
      skippable: false,
    },
  ],
});

// Custom hook for onboarding tutorial business logic
export function useOnboardingTutorial(props: OnboardingTutorialProps) {
  const { autoStart = false, onComplete, onSkip, userType = 'admin' } = props;
  const { startTutorial, completeTutorial, skipTutorial, state } = useTutorial();
  const { completeStep, progress } = useOnboarding();

  // Start tutorial automatically if requested and conditions are met
  useEffect(() => {
    if (autoStart && !state.isActive && progress?.shouldShowOnboarding) {
      const hasCompletedTutorial = progress.completed_steps.some(
        step => step.includes('tutorial') || step.includes('onboarding')
      );

      if (!hasCompletedTutorial) {
        // Let platform-specific component decide which config to use
        // startTutorial will be called by the platform component
      }
    }
  }, [autoStart, state.isActive, progress]);

  // Handle tutorial completion
  useEffect(() => {
    if (!state.isActive && state.config && state.currentStep > 0) {
      const isOnboardingTutorial = 
        state.config.id === 'onboarding-tutorial' || 
        state.config.id === 'mobile-onboarding-tutorial';
        
      if (isOnboardingTutorial) {
        const handleTutorialEnd = async () => {
          try {
            // Mark tutorial completion in onboarding progress
            await completeStep('onboarding_tutorial_completed');

            if (onComplete) {
              onComplete();
            }
          } catch (error) {
            console.error('Error completing onboarding tutorial:', error);
          }
        };

        handleTutorialEnd();
      }
    }
  }, [
    state.isActive,
    state.config,
    state.currentStep,
    completeStep,
    onComplete,
  ]);

  // Public methods to control tutorial
  const startOnboardingTutorial = (tutorialConfig: TutorialConfig) => {
    startTutorial(tutorialConfig);
  };

  const skipOnboardingTutorial = async () => {
    try {
      await skipTutorial();
      await completeStep('onboarding_tutorial_skipped');

      if (onSkip) {
        onSkip();
      }
    } catch (error) {
      console.error('Error skipping onboarding tutorial:', error);
    }
  };

  const completeOnboardingTutorial = async () => {
    try {
      await completeTutorial();
      await completeStep('onboarding_tutorial_completed');

      if (onComplete) {
        onComplete();
      }
    } catch (error) {
      console.error('Error completing onboarding tutorial:', error);
    }
  };

  const canStartTutorial = () => {
    return !state.isActive && progress?.shouldShowOnboarding;
  };

  const isOnboardingTutorialActive = () => {
    return (
      state.isActive &&
      (state.config?.id === 'onboarding-tutorial' ||
        state.config?.id === 'mobile-onboarding-tutorial')
    );
  };

  return {
    startOnboardingTutorial,
    skipOnboardingTutorial,
    completeOnboardingTutorial,
    canStartTutorial,
    isOnboardingTutorialActive,
    tutorialState: state,
    progress,
  };
}

// Tutorial step configurations for specific onboarding actions
export const ONBOARDING_TUTORIAL_STEPS = {
  schoolProfile: {
    id: 'school-profile-tutorial',
    title: 'Complete Your School Profile',
    content:
      'Add essential information about your school including name, description, contact details, and logo.',
    targetElement: '[data-testid="school-profile-form"]',
    position: 'right' as const,
    highlight: true,
  },

  teacherInvitation: {
    id: 'teacher-invitation-tutorial',
    title: 'Invite Teachers to Your School',
    content:
      "Send email invitations to teachers. They'll receive a link to join your school and set up their accounts.",
    targetElement: '[data-testid="invite-teacher-modal"]',
    position: 'left' as const,
    highlight: true,
  },

  studentManagement: {
    id: 'student-management-tutorial',
    title: 'Add and Manage Students',
    content:
      'Add students individually or use bulk import. Include parent contact information for better communication.',
    targetElement: '[data-testid="add-student-modal"]',
    position: 'top' as const,
    highlight: true,
  },

  billingSetup: {
    id: 'billing-setup-tutorial',
    title: 'Configure Billing Settings',
    content: 'Set up payment methods, pricing plans, and billing preferences for your school.',
    targetElement: '[data-testid="billing-settings"]',
    position: 'bottom' as const,
    highlight: true,
  },

  scheduling: {
    id: 'scheduling-tutorial',
    title: 'Create Class Schedules',
    content:
      'Set up recurring schedules, book individual sessions, and manage teacher-student assignments.',
    targetElement: '[data-testid="calendar-interface"]',
    position: 'left' as const,
    highlight: true,
  },
};