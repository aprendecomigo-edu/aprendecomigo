import { useState, useEffect, useCallback, useRef } from 'react';

import {
  TutorOnboardingData,
  OnboardingProgress,
  ProfilePublishingOptions,
  startTutorOnboarding,
  saveTutorOnboardingProgress,
  validateTutorOnboardingStep,
  completeTutorOnboarding,
  createTutorSchool,
  getCourseCatalog,
  EnhancedCourse,
  getEducationalSystems,
  getOnboardingGuidance,
} from '@/api/tutorApi';
import { EducationalSystem } from '@/api/userApi';
import { SelectedCourse, CustomSubject } from '@/components/onboarding/CourseSelectionManager';

export interface TutorOnboardingStep {
  id: string;
  title: string;
  description: string;
  component: string;
  isRequired: boolean;
  estimatedMinutes: number;
  dependencies?: string[];
}

export const TUTOR_ONBOARDING_STEPS: TutorOnboardingStep[] = [
  {
    id: 'school-creation',
    title: 'Create Your Practice',
    description: 'Set up your tutoring business profile',
    component: 'TutorSchoolCreation',
    isRequired: true,
    estimatedMinutes: 3,
  },
  {
    id: 'educational-system',
    title: 'Educational System',
    description: 'Choose your teaching curriculum',
    component: 'EducationalSystemSelector',
    isRequired: true,
    estimatedMinutes: 2,
  },
  {
    id: 'course-selection',
    title: 'Teaching Subjects',
    description: 'Select courses and configure rates',
    component: 'CourseSelectionManager',
    isRequired: true,
    estimatedMinutes: 10,
    dependencies: ['educational-system'],
  },
  {
    id: 'basic-info',
    title: 'Personal Information',
    description: 'Professional details and experience',
    component: 'BasicInfoStep',
    isRequired: true,
    estimatedMinutes: 5,
  },
  {
    id: 'biography',
    title: 'Professional Bio',
    description: 'Tell students about your approach',
    component: 'BiographyStep',
    isRequired: true,
    estimatedMinutes: 8,
  },
  {
    id: 'education',
    title: 'Education Background',
    description: 'Degrees and certifications',
    component: 'EducationStep',
    isRequired: true,
    estimatedMinutes: 7,
  },
  {
    id: 'availability',
    title: 'Availability',
    description: 'Weekly schedule and booking preferences',
    component: 'AvailabilityStep',
    isRequired: true,
    estimatedMinutes: 6,
  },
  {
    id: 'business-profile',
    title: 'Business Settings',
    description: 'Policies and preferences',
    component: 'TutorBusinessProfile',
    isRequired: false,
    estimatedMinutes: 4,
  },
  {
    id: 'preview',
    title: 'Profile Preview',
    description: 'Review your complete profile',
    component: 'ProfilePreview',
    isRequired: false,
    estimatedMinutes: 3,
  },
];

interface UseTutorOnboardingState {
  // Onboarding progress
  currentStep: number;
  onboardingId?: string;
  progress?: OnboardingProgress;

  // Form data
  formData: Partial<TutorOnboardingData>;
  selectedEducationalSystem?: EducationalSystem;
  selectedCourses: SelectedCourse[];
  customSubjects: CustomSubject[];

  // Available data
  availableSystems: EducationalSystem[];
  availableCourses: EnhancedCourse[];

  // UI state
  isLoading: boolean;
  isSaving: boolean;
  isSubmitting: boolean;
  error?: string;
  validationErrors: Record<string, string[]>;

  // Step-specific state
  stepData: Record<string, any>;
  completedSteps: Set<string>;
  guidance?: {
    tips: Array<{
      title: string;
      description: string;
      priority: 'high' | 'medium' | 'low';
      category: 'requirement' | 'suggestion' | 'best_practice';
    }>;
    recommendations: Array<{
      text: string;
      action?: string;
      url?: string;
    }>;
    common_mistakes: Array<{
      mistake: string;
      solution: string;
    }>;
    estimated_time: number;
  };
}

interface UseTutorOnboardingActions {
  // Navigation
  setCurrentStep: (step: number) => void;
  nextStep: () => Promise<boolean>;
  previousStep: () => void;
  goToStep: (stepId: string) => void;

  // Data management
  updateFormData: (stepId: string, data: any) => void;
  setSelectedEducationalSystem: (system: EducationalSystem | null) => void;
  setSelectedCourses: (courses: SelectedCourse[], customSubjects: CustomSubject[]) => void;

  // API operations
  initializeOnboarding: () => Promise<void>;
  saveProgress: () => Promise<void>;
  validateCurrentStep: () => Promise<boolean>;
  submitOnboarding: (publishingOptions: ProfilePublishingOptions) => Promise<void>;

  // Helper functions
  loadStepGuidance: (stepId: string) => Promise<void>;
  loadEducationalSystems: () => Promise<void>;
  loadCourses: (systemId: number) => Promise<void>;
  resetOnboarding: () => void;
}

export type UseTutorOnboardingReturn = UseTutorOnboardingState & UseTutorOnboardingActions;

export const useTutorOnboarding = (): UseTutorOnboardingReturn => {
  const [state, setState] = useState<UseTutorOnboardingState>({
    currentStep: 0,
    formData: {},
    selectedCourses: [],
    customSubjects: [],
    availableSystems: [],
    availableCourses: [],
    isLoading: false,
    isSaving: false,
    isSubmitting: false,
    validationErrors: {},
    stepData: {},
    completedSteps: new Set(),
  });

  const autoSaveTimeout = useRef<NodeJS.Timeout>();

  // Get current step configuration
  const currentStepConfig = TUTOR_ONBOARDING_STEPS[state.currentStep];

  // Initialize onboarding
  const initializeOnboarding = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: undefined }));

      const { onboarding_id, initial_progress } = await startTutorOnboarding();

      setState(prev => ({
        ...prev,
        onboardingId: onboarding_id,
        progress: initial_progress,
        isLoading: false,
      }));

      // Load educational systems by default
      await loadEducationalSystems();
    } catch (error) {
      console.error('Failed to initialize onboarding:', error);
      setState(prev => ({
        ...prev,
        error: 'Failed to start onboarding. Please try again.',
        isLoading: false,
      }));
    }
  }, []);

  // Load educational systems
  const loadEducationalSystems = useCallback(async () => {
    try {
      const systems = await getEducationalSystems();
      setState(prev => ({
        ...prev,
        availableSystems: systems,
      }));
    } catch (error) {
      console.error('Failed to load educational systems:', error);
    }
  }, []);

  // Load courses for selected educational system
  const loadCourses = useCallback(async (systemId: number) => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));

      const response = await getCourseCatalog({
        educational_system: systemId,
        with_market_data: true,
        page_size: 100,
      });

      setState(prev => ({
        ...prev,
        availableCourses: response.results,
        isLoading: false,
      }));
    } catch (error) {
      console.error('Failed to load courses:', error);
      setState(prev => ({
        ...prev,
        error: 'Failed to load courses. Please try again.',
        isLoading: false,
      }));
    }
  }, []);

  // Load step guidance
  const loadStepGuidance = useCallback(
    async (stepId: string) => {
      try {
        const guidance = await getOnboardingGuidance(stepId, {
          currentStep: state.currentStep,
          formData: state.formData,
          selectedCourses: state.selectedCourses.length,
          customSubjects: state.customSubjects.length,
        });

        setState(prev => ({ ...prev, guidance }));
      } catch (error) {
        console.error('Failed to load guidance:', error);
      }
    },
    [state.currentStep, state.formData, state.selectedCourses.length, state.customSubjects.length],
  );

  // Update form data
  const updateFormData = useCallback((stepId: string, data: any) => {
    setState(prev => ({
      ...prev,
      stepData: {
        ...prev.stepData,
        [stepId]: { ...prev.stepData[stepId], ...data },
      },
      formData: {
        ...prev.formData,
        ...data,
      },
    }));

    // Trigger auto-save
    if (autoSaveTimeout.current) {
      clearTimeout(autoSaveTimeout.current);
    }

    autoSaveTimeout.current = setTimeout(() => {
      saveProgress();
    }, 30000); // Auto-save after 30 seconds
  }, []);

  // Set selected educational system
  const setSelectedEducationalSystem = useCallback(
    (system: EducationalSystem | null) => {
      setState(prev => ({
        ...prev,
        selectedEducationalSystem: system || undefined,
        selectedCourses: [], // Clear courses when system changes
        customSubjects: [], // Clear custom subjects when system changes
        availableCourses: [], // Clear available courses
      }));

      if (system) {
        loadCourses(system.id);

        // Update form data
        updateFormData('educational-system', {
          course_selection: {
            educational_system_id: system.id,
            selected_courses: [],
            custom_subjects: [],
          },
        });
      }
    },
    [loadCourses, updateFormData],
  );

  // Set selected courses
  const setSelectedCourses = useCallback(
    (courses: SelectedCourse[], customSubjects: CustomSubject[]) => {
      setState(prev => ({
        ...prev,
        selectedCourses: courses,
        customSubjects: customSubjects,
      }));

      // Update form data
      updateFormData('course-selection', {
        course_selection: {
          educational_system_id: state.selectedEducationalSystem?.id,
          selected_courses: courses.map(c => ({
            course_id: c.course.id,
            hourly_rate: c.hourly_rate,
            expertise_level: c.expertise_level,
            description: c.description,
          })),
          custom_subjects: customSubjects.map(s => ({
            id: s.id,
            name: s.name,
            description: s.description,
            grade_levels: s.grade_levels,
            hourly_rate: s.hourly_rate,
          })),
        },
      });
    },
    [state.selectedEducationalSystem?.id, updateFormData],
  );

  // Navigation functions
  const setCurrentStep = useCallback(
    (step: number) => {
      setState(prev => ({ ...prev, currentStep: step }));

      const stepConfig = TUTOR_ONBOARDING_STEPS[step];
      if (stepConfig) {
        loadStepGuidance(stepConfig.id);
      }
    },
    [loadStepGuidance],
  );

  const goToStep = useCallback(
    (stepId: string) => {
      const stepIndex = TUTOR_ONBOARDING_STEPS.findIndex(s => s.id === stepId);
      if (stepIndex !== -1) {
        setCurrentStep(stepIndex);
      }
    },
    [setCurrentStep],
  );

  // Validation
  const validateCurrentStep = useCallback(async (): Promise<boolean> => {
    try {
      setState(prev => ({ ...prev, validationErrors: {} }));

      const stepId = currentStepConfig.id;
      const stepData = state.stepData[stepId] || {};

      const validation = await validateTutorOnboardingStep({
        step: stepId,
        data: {
          ...state.formData,
          ...stepData,
        },
      });

      if (!validation.is_valid) {
        setState(prev => ({
          ...prev,
          validationErrors: validation.errors,
        }));
        return false;
      }

      return true;
    } catch (error) {
      console.error('Validation error:', error);
      setState(prev => ({
        ...prev,
        error: 'Validation failed. Please check your input.',
      }));
      return false;
    }
  }, [currentStepConfig, state.stepData, state.formData]);

  // Save progress
  const saveProgress = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isSaving: true }));

      const stepId = currentStepConfig.id;
      const stepData = state.stepData[stepId] || {};

      const { success, progress } = await saveTutorOnboardingProgress({
        onboarding_id: state.onboardingId,
        step: stepId,
        data: {
          ...state.formData,
          ...stepData,
        },
        current_step_index: state.currentStep,
      });

      if (success) {
        setState(prev => ({
          ...prev,
          progress,
          isSaving: false,
        }));
      }
    } catch (error) {
      console.error('Save progress error:', error);
      setState(prev => ({
        ...prev,
        error: 'Failed to save progress.',
        isSaving: false,
      }));
    }
  }, [currentStepConfig, state.stepData, state.formData, state.onboardingId, state.currentStep]);

  const nextStep = useCallback(async (): Promise<boolean> => {
    try {
      const isValid = await validateCurrentStep();
      if (!isValid) return false;

      await saveProgress();

      setState(prev => ({
        ...prev,
        completedSteps: new Set([...prev.completedSteps, currentStepConfig.id]),
      }));

      if (state.currentStep < TUTOR_ONBOARDING_STEPS.length - 1) {
        setCurrentStep(state.currentStep + 1);
      }

      return true;
    } catch (error) {
      console.error('Error moving to next step:', error);
      return false;
    }
  }, [validateCurrentStep, saveProgress, currentStepConfig, state.currentStep, setCurrentStep]);

  const previousStep = useCallback(() => {
    if (state.currentStep > 0) {
      setCurrentStep(state.currentStep - 1);
    }
  }, [state.currentStep, setCurrentStep]);

  // Submit onboarding
  const submitOnboarding = useCallback(
    async (publishingOptions: ProfilePublishingOptions) => {
      try {
        setState(prev => ({ ...prev, isSubmitting: true }));

        // Create tutor school first if needed
        if (state.stepData['school-creation']) {
          await createTutorSchool(state.stepData['school-creation']);
        }

        const result = await completeTutorOnboarding({
          onboarding_id: state.onboardingId,
          final_data: state.formData as TutorOnboardingData,
          publishing_options: publishingOptions,
        });

        setState(prev => ({
          ...prev,
          isSubmitting: false,
        }));

        return result;
      } catch (error) {
        console.error('Submit onboarding error:', error);
        setState(prev => ({
          ...prev,
          error: 'Failed to complete onboarding.',
          isSubmitting: false,
        }));
        throw error;
      }
    },
    [state.stepData, state.onboardingId, state.formData],
  );

  // Reset onboarding
  const resetOnboarding = useCallback(() => {
    setState({
      currentStep: 0,
      formData: {},
      selectedCourses: [],
      customSubjects: [],
      availableSystems: [],
      availableCourses: [],
      isLoading: false,
      isSaving: false,
      isSubmitting: false,
      validationErrors: {},
      stepData: {},
      completedSteps: new Set(),
    });
  }, []);

  // Load step guidance when current step changes
  useEffect(() => {
    if (currentStepConfig) {
      loadStepGuidance(currentStepConfig.id);
    }
  }, [currentStepConfig, loadStepGuidance]);

  // Cleanup auto-save timeout
  useEffect(() => {
    return () => {
      if (autoSaveTimeout.current) {
        clearTimeout(autoSaveTimeout.current);
      }
    };
  }, []);

  return {
    // State
    ...state,

    // Actions
    setCurrentStep,
    nextStep,
    previousStep,
    goToStep,
    updateFormData,
    setSelectedEducationalSystem,
    setSelectedCourses,
    initializeOnboarding,
    saveProgress,
    validateCurrentStep,
    submitOnboarding,
    loadStepGuidance,
    loadEducationalSystems,
    loadCourses,
    resetOnboarding,
  };
};
