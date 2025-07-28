import { useState, useEffect, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { 
  onboardingApi, 
  OnboardingProgress, 
  NavigationPreferences,
  UpdateOnboardingProgressData,
  UpdateNavigationPreferencesData 
} from '@/api/onboardingApi';
import { tasksApi, CreateTaskData } from '@/api/tasksApi';

const ONBOARDING_STORAGE_KEY = '@onboarding_state';

export interface OnboardingState {
  progress: OnboardingProgress | null;
  preferences: NavigationPreferences | null;
  isLoading: boolean;
  error: string | null;
  currentStep: number;
  isCompleted: boolean;
  shouldShowOnboarding: boolean;
}

export interface OnboardingActions {
  loadOnboardingData: () => Promise<void>;
  completeStep: (stepId: string) => Promise<void>;
  skipStep: (stepId: string) => Promise<void>;
  skipOnboarding: () => Promise<void>;
  enableOnboarding: () => Promise<void>;
  updatePreferences: (data: UpdateNavigationPreferencesData) => Promise<void>;
  createOnboardingTask: (taskData: CreateTaskData) => Promise<void>;
  resetOnboarding: () => Promise<void>;
}

const DEFAULT_STATE: OnboardingState = {
  progress: null,
  preferences: null,
  isLoading: true,
  error: null,
  currentStep: 0,
  isCompleted: false,
  shouldShowOnboarding: false,
};

// Define the 5 core onboarding steps
export const ONBOARDING_STEPS = [
  {
    id: 'complete_school_profile',
    name: 'Complete School Profile',
    description: 'Add your school information, logo, and contact details',
    icon: 'building',
    taskTitle: 'Complete your school profile',
    taskDescription: 'Add school information, logo, and contact details to personalize your account'
  },
  {
    id: 'invite_first_teacher',
    name: 'Invite First Teacher',
    description: 'Send an invitation to your first teacher to join the platform',
    icon: 'user-plus',
    taskTitle: 'Invite your first teacher',
    taskDescription: 'Send an invitation to a teacher to start building your team'
  },
  {
    id: 'add_first_student',
    name: 'Add First Student',
    description: 'Add student information to start managing enrollments',
    icon: 'graduation-cap',
    taskTitle: 'Add your first student',
    taskDescription: 'Add student information to start managing enrollments and classes'
  },
  {
    id: 'setup_billing',
    name: 'Set Up Billing',
    description: 'Configure payment methods and billing preferences',
    icon: 'credit-card',
    taskTitle: 'Set up billing information',
    taskDescription: 'Configure payment methods and billing preferences for your school'
  },
  {
    id: 'create_first_schedule',
    name: 'Create First Class Schedule',
    description: 'Schedule your first class or tutoring session',
    icon: 'calendar',
    taskTitle: 'Create your first class schedule',
    taskDescription: 'Schedule a class or tutoring session to get started with the platform'
  }
];

export function useOnboarding(): OnboardingState & OnboardingActions {
  const [state, setState] = useState<OnboardingState>(DEFAULT_STATE);

  // Load cached state from AsyncStorage
  const loadCachedState = useCallback(async () => {
    try {
      const cachedState = await AsyncStorage.getItem(ONBOARDING_STORAGE_KEY);
      if (cachedState) {
        const parsed = JSON.parse(cachedState);
        setState(prev => ({ ...prev, ...parsed, isLoading: false }));
      }
    } catch (error) {
      console.error('Error loading cached onboarding state:', error);
    }
  }, []);

  // Cache state to AsyncStorage
  const cacheState = useCallback(async (newState: Partial<OnboardingState>) => {
    try {
      const stateToCache = {
        progress: newState.progress,
        preferences: newState.preferences,
        currentStep: newState.currentStep,
        isCompleted: newState.isCompleted,
        shouldShowOnboarding: newState.shouldShowOnboarding,
      };
      await AsyncStorage.setItem(ONBOARDING_STORAGE_KEY, JSON.stringify(stateToCache));
    } catch (error) {
      console.error('Error caching onboarding state:', error);
    }
  }, []);

  // Load onboarding data from API
  const loadOnboardingData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));

      const [progress, preferences] = await Promise.all([
        onboardingApi.getOnboardingProgress(),
        onboardingApi.getNavigationPreferences()
      ]);

      const currentStep = progress.completed_steps.length;
      const isCompleted = progress.completion_percentage >= 100;
      const shouldShowOnboarding = preferences.show_onboarding && !isCompleted;

      const newState = {
        progress,
        preferences,
        currentStep,
        isCompleted,
        shouldShowOnboarding,
        isLoading: false,
        error: null,
      };

      setState(prev => ({ ...prev, ...newState }));
      await cacheState(newState);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load onboarding data';
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: errorMessage 
      }));
      console.error('Error loading onboarding data:', error);
    }
  }, [cacheState]);

  // Complete an onboarding step
  const completeStep = useCallback(async (stepId: string) => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));

      const updatedProgress = await onboardingApi.completeOnboardingStep(stepId);
      
      const currentStep = updatedProgress.completed_steps.length;
      const isCompleted = updatedProgress.completion_percentage >= 100;

      const newState = {
        progress: updatedProgress,
        currentStep,
        isCompleted,
        isLoading: false,
      };

      setState(prev => ({ ...prev, ...newState }));
      await cacheState({ ...state, ...newState });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to complete step';
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: errorMessage 
      }));
      console.error('Error completing step:', error);
    }
  }, [state, cacheState]);

  // Skip an onboarding step
  const skipStep = useCallback(async (stepId: string) => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));

      const updatedProgress = await onboardingApi.skipOnboardingStep(stepId);
      
      const currentStep = updatedProgress.completed_steps.length + updatedProgress.skipped_steps.length;
      const isCompleted = updatedProgress.completion_percentage >= 100;

      const newState = {
        progress: updatedProgress,
        currentStep,
        isCompleted,
        isLoading: false,
      };

      setState(prev => ({ ...prev, ...newState }));
      await cacheState({ ...state, ...newState });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to skip step';
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: errorMessage 
      }));
      console.error('Error skipping step:', error);
    }
  }, [state, cacheState]);

  // Skip entire onboarding process
  const skipOnboarding = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));

      const updatedPreferences = await onboardingApi.skipOnboarding();

      const newState = {
        preferences: updatedPreferences,
        shouldShowOnboarding: false,
        isLoading: false,
      };

      setState(prev => ({ ...prev, ...newState }));
      await cacheState({ ...state, ...newState });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to skip onboarding';
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: errorMessage 
      }));
      console.error('Error skipping onboarding:', error);
    }
  }, [state, cacheState]);

  // Enable onboarding (for re-access)
  const enableOnboarding = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));

      const updatedPreferences = await onboardingApi.enableOnboarding();

      const newState = {
        preferences: updatedPreferences,
        shouldShowOnboarding: true,
        isLoading: false,
      };

      setState(prev => ({ ...prev, ...newState }));
      await cacheState({ ...state, ...newState });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to enable onboarding';
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: errorMessage 
      }));
      console.error('Error enabling onboarding:', error);
    }
  }, [state, cacheState]);

  // Update navigation preferences
  const updatePreferences = useCallback(async (data: UpdateNavigationPreferencesData) => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));

      const updatedPreferences = await onboardingApi.updateNavigationPreferences(data);

      const newState = {
        preferences: updatedPreferences,
        shouldShowOnboarding: updatedPreferences.show_onboarding && !state.isCompleted,
        isLoading: false,
      };

      setState(prev => ({ ...prev, ...newState }));
      await cacheState({ ...state, ...newState });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update preferences';
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: errorMessage 
      }));
      console.error('Error updating preferences:', error);
    }
  }, [state, cacheState]);

  // Create onboarding task
  const createOnboardingTask = useCallback(async (taskData: CreateTaskData) => {
    try {
      await tasksApi.createTask({
        ...taskData,
        task_type: 'onboarding',
        priority: taskData.priority || 'medium',
      });
    } catch (error) {
      console.error('Error creating onboarding task:', error);
      // Don't throw error as this is not critical for onboarding flow
    }
  }, []);

  // Reset onboarding state
  const resetOnboarding = useCallback(async () => {
    try {
      await AsyncStorage.removeItem(ONBOARDING_STORAGE_KEY);
      setState(DEFAULT_STATE);
      await loadOnboardingData();
    } catch (error) {
      console.error('Error resetting onboarding:', error);
    }
  }, [loadOnboardingData]);

  // Initialize on mount
  useEffect(() => {
    const initialize = async () => {
      await loadCachedState();
      await loadOnboardingData();
    };
    
    initialize();
  }, [loadCachedState, loadOnboardingData]);

  return {
    ...state,
    loadOnboardingData,
    completeStep,
    skipStep,
    skipOnboarding,
    enableOnboarding,
    updatePreferences,
    createOnboardingTask,
    resetOnboarding,
  };
}