// Individual Tutor Onboarding Components
export { TutorOnboardingFlow } from './tutor-onboarding-flow';
export { TutorOnboardingProgress } from './tutor-onboarding-progress';
export { EducationalSystemSelector } from './educational-system-selector';
export { CourseCatalogBrowser } from './course-catalog-browser';
export { CourseSelectionManager } from './course-selection-manager';
export { RateConfigurationManager } from './rate-configuration-manager';
export { OnboardingSuccessScreen } from './onboarding-success-screen';

// Export types
export type { Course } from './course-catalog-browser';
export type { EducationalSystem } from './educational-system-selector';
export type { 
  TutorOnboardingData, 
  OnboardingStep,
  DEFAULT_TUTOR_ONBOARDING_STEPS 
} from './tutor-onboarding-progress';

// Re-export from modal components for easy access
export { TutorSchoolCreationModal } from '@/components/modals/tutor-school-creation-modal';