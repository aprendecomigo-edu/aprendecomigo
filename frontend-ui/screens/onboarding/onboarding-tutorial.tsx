// Fallback implementation with Platform.OS conditional
// This file should be overridden by platform-specific files (.web.tsx, .native.tsx)
import { Platform } from 'react-native';

// Import platform-specific implementations
import { OnboardingTutorial as WebOnboardingTutorial } from './onboarding-tutorial.web';
import { OnboardingTutorial as NativeOnboardingTutorial } from './onboarding-tutorial.native';

// Export the appropriate implementation based on platform
export const OnboardingTutorial = Platform.OS === 'web' ? WebOnboardingTutorial : NativeOnboardingTutorial;

// Hook for managing onboarding tutorial state
export function useOnboardingTutorial() {
  if (Platform.OS === 'web') {
    // Import web-specific hook dynamically
    const { useOnboardingTutorialWeb } = require('./onboarding-tutorial.web');
    return useOnboardingTutorialWeb();
  } else {
    // Import native-specific hook dynamically
    const { useOnboardingTutorialNative } = require('./onboarding-tutorial.native');
    return useOnboardingTutorialNative();
  }
}

// Re-export common items for compatibility
export { ONBOARDING_TUTORIAL_STEPS } from './onboarding-tutorial-common';