// Main onboarding components
export { WelcomeScreen } from './welcome-screen';
export { OnboardingChecklist } from './onboarding-checklist';
export { OnboardingProgress } from './onboarding-progress';

// Guided flows
export { AddFirstTeacherFlow, AddFirstStudentFlow, SchoolProfileFlow } from './guided-flows';

// Help and tutorial components
export { ContextualHelp, useContextualHelp, ONBOARDING_HELP_TIPS } from './contextual-help';

export {
  OnboardingTutorial,
  useOnboardingTutorial,
  ONBOARDING_TUTORIAL_STEPS,
} from './onboarding-tutorial';

// Hooks and utilities
export { useOnboarding, ONBOARDING_STEPS } from '@/hooks/useOnboarding';
export * from '@/api/onboardingApi';
