// Individual Tutor Onboarding Components
export { TutorOnboardingFlow } from './TutorOnboardingFlow';
export { TutorOnboardingProgress } from './TutorOnboardingProgress';
export { EducationalSystemSelector } from './EducationalSystemSelector';
export { CourseCatalogBrowser } from './CourseCatalogBrowser';
export { CourseSelectionManager } from './CourseSelectionManager';
export { RateConfigurationManager } from './RateConfigurationManager';
export { OnboardingSuccessScreen } from './OnboardingSuccessScreen';

// Export types
export type { Course } from './CourseCatalogBrowser';
export type { EducationalSystem } from './EducationalSystemSelector';
export type {
  TutorOnboardingData,
  OnboardingStep,
  DEFAULT_TUTOR_ONBOARDING_STEPS,
} from './TutorOnboardingProgress';

// Re-export from modal components for easy access
export { TutorSchoolCreationModal } from '@/components/modals/TutorSchoolCreationModal';
