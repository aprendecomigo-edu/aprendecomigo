import React, { useEffect } from 'react';

import {
  OnboardingTutorialProps,
  useOnboardingTutorial,
  createDesktopOnboardingTutorialConfig,
} from './onboarding-tutorial-common';

export const OnboardingTutorial: React.FC<OnboardingTutorialProps> = ({
  autoStart = false,
  onComplete,
  onSkip,
  userType = 'admin',
}) => {
  const {
    startOnboardingTutorial,
    skipOnboardingTutorial,
    completeOnboardingTutorial,
    canStartTutorial,
    isOnboardingTutorialActive,
    tutorialState,
    progress,
  } = useOnboardingTutorial({ autoStart, onComplete, onSkip, userType });

  // Desktop tutorial configuration
  const tutorialConfig = createDesktopOnboardingTutorialConfig(userType);

  // Start tutorial automatically if requested and conditions are met
  useEffect(() => {
    if (autoStart && canStartTutorial()) {
      const hasCompletedTutorial = progress?.completed_steps.some(
        step => step.includes('tutorial') || step.includes('onboarding')
      );

      if (!hasCompletedTutorial) {
        startOnboardingTutorial(tutorialConfig);
      }
    }
  }, [autoStart, canStartTutorial, progress, startOnboardingTutorial, tutorialConfig]);

  // This component doesn't render anything visible - it's a logic controller
  return null;
};

// Hook for managing onboarding tutorial state (web-specific)
export function useOnboardingTutorialWeb() {
  const tutorialHook = useOnboardingTutorial({ userType: 'admin' });

  const startOnboardingTutorial = (userType: string = 'admin') => {
    const config = createDesktopOnboardingTutorialConfig(userType);
    tutorialHook.startOnboardingTutorial(config);
  };

  return {
    ...tutorialHook,
    startOnboardingTutorial,
  };
}

// Re-export common items for compatibility
export { ONBOARDING_TUTORIAL_STEPS } from './onboarding-tutorial-common';