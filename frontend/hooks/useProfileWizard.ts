import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { useState, useCallback, useRef, useEffect } from 'react';

import { useSmartAutoSave } from './useDebounce';

import apiClient from '@/api/apiClient';

const WIZARD_STORAGE_KEY = '@teacher_profile_wizard';

// Type for form field updates
export interface ProfileFieldUpdate {
  field: keyof TeacherProfileWizardData;
  value: string | number | boolean | object | string[];
}

// Type for API responses
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  errors?: Record<string, string[]>;
}

// Type for validation response
export interface ValidationResponse {
  is_valid: boolean;
  errors?: Record<string, string[]>;
  warnings?: Record<string, string[]>;
}

// Type for save progress response
export interface SaveProgressResponse {
  success: boolean;
  completion_data?: CompletionData;
  message?: string;
}

// Comprehensive form data structure
export interface TeacherProfileWizardData {
  // Basic Info Step
  profile_photo?: string;
  first_name: string;
  last_name: string;
  professional_title: string;
  email: string;
  phone_number: string;
  location: {
    city: string;
    country: string;
    timezone: string;
  };
  languages: string[];
  years_experience: number;
  teaching_level: string;
  introduction: string;

  // Biography Step
  professional_bio: string;
  teaching_philosophy: string;
  specializations: string[];
  achievements: string[];
  teaching_approach: string;
  student_outcomes: string;

  // Education Step
  degrees: Array<{
    id: string;
    degree_type: string;
    field_of_study: string;
    institution: string;
    location: string;
    graduation_year: number;
    gpa?: string;
    honors?: string;
    description?: string;
  }>;
  certifications: Array<{
    id: string;
    name: string;
    issuing_organization: string;
    issue_date: string;
    expiration_date?: string;
    credential_id?: string;
    verification_url?: string;
  }>;
  additional_training: string[];

  // Subjects Step
  teaching_subjects: Array<{
    id: string;
    subject: string;
    grade_levels: string[];
    expertise_level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
    years_teaching: number;
    description?: string;
  }>;
  subject_categories: string[];

  // Rates Step
  rate_structure: {
    individual_rate: number;
    group_rate?: number;
    trial_lesson_rate?: number;
    package_deals?: Array<{
      id: string;
      name: string;
      sessions: number;
      price: number;
      discount_percentage: number;
    }>;
    currency: string;
  };
  payment_methods: string[];
  cancellation_policy: string;

  // Availability Step
  weekly_availability: {
    [key: string]: Array<{
      start_time: string;
      end_time: string;
      timezone: string;
    }>;
  };
  booking_preferences: {
    min_notice_hours: number;
    max_advance_days: number;
    session_duration_options: number[];
    auto_accept_bookings: boolean;
  };
  time_zone: string;
}

export interface CompletionData {
  completion_percentage: number;
  missing_critical: string[];
  missing_optional: string[];
  is_complete: boolean;
  step_completion: Record<
    string,
    {
      is_complete: boolean;
      completion_percentage: number;
      missing_fields: string[];
    }
  >;
  recommendations?: Array<{
    text: string;
    priority: 'high' | 'medium' | 'low';
  }>;
}

export interface ProfileWizardState {
  currentStep: number;
  formData: TeacherProfileWizardData;
  completionData: CompletionData | null;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  validationErrors: Record<string, string[]>;
  hasUnsavedChanges: boolean;
}

const DEFAULT_FORM_DATA: TeacherProfileWizardData = {
  // Basic Info
  first_name: '',
  last_name: '',
  professional_title: '',
  email: '',
  phone_number: '',
  location: {
    city: '',
    country: '',
    timezone: '',
  },
  languages: [],
  years_experience: 0,
  teaching_level: '',
  introduction: '',

  // Biography
  professional_bio: '',
  teaching_philosophy: '',
  specializations: [],
  achievements: [],
  teaching_approach: '',
  student_outcomes: '',

  // Education
  degrees: [],
  certifications: [],
  additional_training: [],

  // Subjects
  teaching_subjects: [],
  subject_categories: [],

  // Rates
  rate_structure: {
    individual_rate: 0,
    currency: 'EUR',
  },
  payment_methods: [],
  cancellation_policy: '',

  // Availability
  weekly_availability: {},
  booking_preferences: {
    min_notice_hours: 24,
    max_advance_days: 30,
    session_duration_options: [60],
    auto_accept_bookings: false,
  },
  time_zone: '',
};

const DEFAULT_STATE: ProfileWizardState = {
  currentStep: 0,
  formData: DEFAULT_FORM_DATA,
  completionData: null,
  isLoading: false,
  isSaving: false,
  error: null,
  validationErrors: {},
  hasUnsavedChanges: false,
};

export function useProfileWizard() {
  const [state, setState] = useState<ProfileWizardState>(DEFAULT_STATE);
  const saveTimeoutRef = useRef<NodeJS.Timeout>();
  const cancelTokenSourceRef = useRef<axios.CancelTokenSource | null>(null);
  const isMountedRef = useRef(true);

  // Track component mount status for cleanup
  useEffect(() => {
    isMountedRef.current = true;

    return () => {
      isMountedRef.current = false;

      // Cleanup timeouts
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }

      // Cancel any ongoing API requests
      if (cancelTokenSourceRef.current) {
        cancelTokenSourceRef.current.cancel('Component unmounted');
      }
    };
  }, []);

  // Load cached wizard state
  const loadCachedState = useCallback(async () => {
    try {
      const cached = await AsyncStorage.getItem(WIZARD_STORAGE_KEY);
      if (cached) {
        const parsedState = JSON.parse(cached);
        setState(prev => ({
          ...prev,
          ...parsedState,
          isLoading: false,
        }));
      }
    } catch (error) {
      console.error('Error loading cached wizard state:', error);
    }
  }, []);

  // Cache wizard state
  const cacheState = useCallback(async (newState: Partial<ProfileWizardState>) => {
    try {
      const stateToCache = {
        currentStep: newState.currentStep,
        formData: newState.formData,
        completionData: newState.completionData,
      };
      await AsyncStorage.setItem(WIZARD_STORAGE_KEY, JSON.stringify(stateToCache));
    } catch (error) {
      console.error('Error caching wizard state:', error);
    }
  }, []);

  // Load existing profile data and progress
  const loadProgress = useCallback(async (): Promise<void> => {
    if (!isMountedRef.current) return;

    // Cancel any existing request
    if (cancelTokenSourceRef.current) {
      cancelTokenSourceRef.current.cancel('New request initiated');
    }

    // Create new cancel token
    cancelTokenSourceRef.current = axios.CancelToken.source();

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      // Load cached state first
      await loadCachedState();

      // Load from API with cancellation support
      const [profileResponse, completionResponse] = await Promise.all([
        apiClient.get<ApiResponse>('/accounts/teachers/profile/', {
          cancelToken: cancelTokenSourceRef.current.token,
        }),
        apiClient.get<ApiResponse<CompletionData>>('/accounts/teachers/profile-completion-score/', {
          cancelToken: cancelTokenSourceRef.current.token,
        }),
      ]);

      if (!isMountedRef.current) return;

      const profileData = profileResponse.data.data;
      const completionData = completionResponse.data.data;

      // Merge API data with form structure
      const formData: TeacherProfileWizardData = {
        // Map API data to form structure
        ...DEFAULT_FORM_DATA,
        first_name: profileData?.user?.name?.split(' ')[0] || '',
        last_name: profileData?.user?.name?.split(' ').slice(1).join(' ') || '',
        professional_title: profileData?.specialty || '',
        email: profileData?.user?.email || '',
        phone_number: profileData?.phone_number || '',
        professional_bio: profileData?.bio || '',
        teaching_subjects: profileData?.teaching_subjects || [],
        rate_structure: profileData?.rate_structure || DEFAULT_FORM_DATA.rate_structure,
        weekly_availability: profileData?.weekly_availability || {},
        ...profileData,
      };

      const newState = {
        formData,
        completionData,
        isLoading: false,
        error: null,
      };

      setState(prev => ({ ...prev, ...newState }));
      await cacheState(newState);
    } catch (error) {
      if (!isMountedRef.current) return;

      // Don't update state if request was cancelled
      if (axios.isCancel(error)) {
        return;
      }

      const errorMessage = error instanceof Error ? error.message : 'Failed to load profile data';
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
    } finally {
      cancelTokenSourceRef.current = null;
    }
  }, [loadCachedState, cacheState]);

  // Update form data with proper typing
  const updateFormData = useCallback(
    (updates: Partial<TeacherProfileWizardData>) => {
      if (!isMountedRef.current) return;

      setState(prev => {
        const newFormData = { ...prev.formData, ...updates };
        const newState = {
          ...prev,
          formData: newFormData,
          hasUnsavedChanges: true,
          validationErrors: {}, // Clear validation errors on update
        };

        // Cache updated state (fire and forget)
        cacheState(newState).catch(error => {
          console.error('Failed to cache wizard state:', error);
        });

        return newState;
      });
    },
    [cacheState],
  );

  // Update single field with type safety
  const updateFormField = useCallback(
    (update: ProfileFieldUpdate) => {
      if (!isMountedRef.current) return;

      setState(prev => {
        const newFormData = {
          ...prev.formData,
          [update.field]: update.value,
        };

        const newState = {
          ...prev,
          formData: newFormData,
          hasUnsavedChanges: true,
          validationErrors: {
            ...prev.validationErrors,
            [update.field]: [], // Clear field-specific validation errors
          },
        };

        // Cache updated state (fire and forget)
        cacheState(newState).catch(error => {
          console.error('Failed to cache wizard state:', error);
        });

        return newState;
      });
    },
    [cacheState],
  );

  // Set current step with bounds checking
  const setCurrentStep = useCallback(
    (step: number) => {
      if (!isMountedRef.current) return;

      // Ensure step is within valid bounds
      const clampedStep = Math.max(0, Math.min(step, 6)); // 0-6 for 7 steps

      setState(prev => {
        if (prev.currentStep === clampedStep) return prev;

        const newState = { ...prev, currentStep: clampedStep };

        // Cache updated state (fire and forget)
        cacheState(newState).catch(error => {
          console.error('Failed to cache wizard state:', error);
        });

        return newState;
      });
    },
    [cacheState],
  );

  // Validate current step with proper error handling
  const validateStep = useCallback(
    async (stepIndex: number): Promise<boolean> => {
      if (!isMountedRef.current) return false;

      try {
        const response = await apiClient.post<ApiResponse<ValidationResponse>>(
          '/accounts/teachers/profile-wizard/validate-step/',
          {
            step: stepIndex,
            data: state.formData,
          },
        );

        if (!isMountedRef.current) return false;

        const validationData = response.data.data;

        if (validationData.is_valid) {
          setState(prev => ({ ...prev, validationErrors: {} }));
          return true;
        } else {
          setState(prev => ({
            ...prev,
            validationErrors: validationData.errors || {},
          }));
          return false;
        }
      } catch (error) {
        if (!isMountedRef.current) return false;

        console.error('Step validation error:', error);

        // Set generic validation error
        setState(prev => ({
          ...prev,
          error: 'Validation failed. Please check your input and try again.',
        }));

        return false;
      }
    },
    [state.formData],
  );

  // Save progress to backend with improved error handling
  const saveProgress = useCallback(async (): Promise<void> => {
    if (!isMountedRef.current) return;

    setState(prev => ({ ...prev, isSaving: true, error: null }));

    try {
      const response = await apiClient.post<ApiResponse<SaveProgressResponse>>(
        '/accounts/teachers/profile-wizard/save-progress/',
        {
          profile_data: state.formData,
          current_step: state.currentStep,
        },
      );

      if (!isMountedRef.current) return;

      const saveData = response.data.data;

      const newState = {
        isSaving: false,
        hasUnsavedChanges: false,
        completionData: saveData?.completion_data || state.completionData,
        error: null,
      };

      setState(prev => ({ ...prev, ...newState }));
      await cacheState({ ...state, ...newState });
    } catch (error) {
      if (!isMountedRef.current) return;

      const errorMessage = error instanceof Error ? error.message : 'Failed to save progress';
      setState(prev => ({
        ...prev,
        isSaving: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, [state.formData, state.currentStep, state.completionData, cacheState]);

  // Submit complete profile
  const submitProfile = useCallback(async (): Promise<void> => {
    if (!isMountedRef.current) return;

    setState(prev => ({ ...prev, isSaving: true, error: null }));

    try {
      await apiClient.post<ApiResponse>('/accounts/teachers/profile-wizard/submit/', {
        profile_data: state.formData,
      });

      if (!isMountedRef.current) return;

      setState(prev => ({
        ...prev,
        isSaving: false,
        hasUnsavedChanges: false,
        error: null,
      }));

      // Clear cached wizard state after successful submission
      await AsyncStorage.removeItem(WIZARD_STORAGE_KEY);
    } catch (error) {
      if (!isMountedRef.current) return;

      const errorMessage = error instanceof Error ? error.message : 'Failed to submit profile';
      setState(prev => ({
        ...prev,
        isSaving: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, [state.formData]);

  // Get rate suggestions with proper typing
  const getRateSuggestions = useCallback(
    async (subject: string, location: string): Promise<any | null> => {
      if (!isMountedRef.current) return null;

      try {
        const response = await apiClient.get<ApiResponse>('/accounts/teachers/rate-suggestions/', {
          params: { subject, location },
        });
        return response.data.data;
      } catch (error) {
        console.error('Error fetching rate suggestions:', error);
        return null;
      }
    },
    [],
  );

  // Upload profile photo with proper typing
  const uploadProfilePhoto = useCallback(
    async (imageUri: string): Promise<string> => {
      if (!isMountedRef.current) {
        throw new Error('Component unmounted');
      }

      try {
        const formData = new FormData();

        // Type assertion for FormData append
        formData.append('photo', {
          uri: imageUri,
          type: 'image/jpeg',
          name: 'profile-photo.jpg',
        } as any);

        const response = await apiClient.post<ApiResponse<{ photo_url: string }>>(
          '/accounts/teachers/profile/photo/',
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          },
        );

        if (!isMountedRef.current) {
          throw new Error('Component unmounted during upload');
        }

        const photoUrl = response.data.data.photo_url;
        updateFormData({ profile_photo: photoUrl });
        return photoUrl;
      } catch (error) {
        console.error('Error uploading profile photo:', error);
        throw error;
      }
    },
    [updateFormData],
  );

  // Reset wizard state
  const resetWizard = useCallback(async (): Promise<void> => {
    if (!isMountedRef.current) return;

    // Cancel any ongoing requests
    if (cancelTokenSourceRef.current) {
      cancelTokenSourceRef.current.cancel('Wizard reset');
    }

    // Clear any pending timeouts
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    setState(DEFAULT_STATE);
    await AsyncStorage.removeItem(WIZARD_STORAGE_KEY);
  }, []);

  return {
    // State
    currentStep: state.currentStep,
    formData: state.formData,
    completionData: state.completionData,
    isLoading: state.isLoading,
    isSaving: state.isSaving,
    error: state.error,
    validationErrors: state.validationErrors,
    hasUnsavedChanges: state.hasUnsavedChanges,

    // Actions
    setCurrentStep,
    updateFormData,
    updateFormField,
    validateStep,
    saveProgress,
    submitProfile,
    loadProgress,
    getRateSuggestions,
    uploadProfilePhoto,
    resetWizard,
  };
}
