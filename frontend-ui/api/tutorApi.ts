import apiClient from './apiClient';
import { EducationalSystem } from './userApi';

import { Course } from '@/components/onboarding/CourseCatalogBrowser';


// Course Catalog and Educational Systems
export interface EnhancedCourse extends Course {
  market_data?: {
    demand_level: 'low' | 'medium' | 'high';
    average_rate: number;
    tutor_count: number;
    student_demand: number;
  };
  rate_suggestions?: {
    min: number;
    max: number;
    average: number;
    currency: string;
  };
}

export interface CourseFilters {
  educational_system?: number;
  education_level?: string;
  subject_area?: string;
  difficulty_level?: 'beginner' | 'intermediate' | 'advanced';
  search?: string;
  with_market_data?: boolean;
  page?: number;
  page_size?: number;
}

export interface CourseListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: EnhancedCourse[];
}

// Tutor School Creation
export interface TutorSchoolData {
  schoolName: string;
  description?: string;
  website?: string;
}

export interface TutorSchoolCreationResponse {
  success: boolean;
  school_id: number;
  membership_id: number;
  message: string;
}

// Tutor Onboarding Data
export interface TutorOnboardingData {
  // Basic Information
  personal_info: {
    first_name: string;
    last_name: string;
    email: string;
    phone_number: string;
    profile_photo?: string;
    location: {
      city: string;
      country: string;
      timezone: string;
    };
    languages: string[];
    years_experience: number;
  };

  // Business Profile
  business_profile: {
    practice_name: string;
    description?: string;
    website?: string;
    specializations: string[];
    target_students: string[];
    teaching_approach: string;
  };

  // Educational Background
  education: {
    degrees: Array<{
      id: string;
      degree_type: string;
      field_of_study: string;
      institution: string;
      graduation_year: number;
      description?: string;
    }>;
    certifications: Array<{
      id: string;
      name: string;
      issuing_organization: string;
      issue_date: string;
      expiration_date?: string;
    }>;
  };

  // Course Selection
  course_selection: {
    educational_system_id: number;
    selected_courses: Array<{
      course_id: number;
      hourly_rate: number;
      expertise_level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
      description?: string;
    }>;
    custom_subjects?: Array<{
      id: string;
      name: string;
      description: string;
      grade_levels: string[];
      hourly_rate: number;
    }>;
  };

  // Availability and Scheduling
  availability: {
    weekly_schedule: {
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
  };

  // Pricing and Policies
  pricing: {
    default_rate: number;
    trial_lesson_rate?: number;
    group_discount?: number;
    package_deals?: Array<{
      id: string;
      name: string;
      sessions: number;
      discount_percentage: number;
    }>;
    currency: string;
    payment_methods: string[];
    cancellation_policy: string;
  };
}

// Tutor Discovery
export interface TutorDiscoveryProfile {
  id: number;
  name: string;
  profile_photo?: string;
  professional_title: string;
  bio: string;
  rating: number;
  review_count: number;
  hourly_rate_range: {
    min: number;
    max: number;
    currency: string;
  };
  subjects: string[];
  languages: string[];
  experience_years: number;
  location: {
    city: string;
    country: string;
  };
  availability_summary: string;
  is_available: boolean;
  response_time: string;
  completion_rate: number;
  school: {
    id: number;
    name: string;
  };
}

export interface TutorDiscoveryFilters {
  subjects?: string[];
  min_rate?: number;
  max_rate?: number;
  languages?: string[];
  experience_min?: number;
  location?: string;
  availability?: string;
  rating_min?: number;
  educational_system?: number;
  page?: number;
  page_size?: number;
  ordering?: string;
}

export interface TutorDiscoveryResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: TutorDiscoveryProfile[];
  facets: {
    subjects: Array<{ name: string; count: number }>;
    locations: Array<{ name: string; count: number }>;
    languages: Array<{ name: string; count: number }>;
    rate_ranges: Array<{ range: string; count: number }>;
  };
}

// Onboarding Progress Tracking
export interface OnboardingProgress {
  current_step: number;
  total_steps: number;
  completed_steps: number[];
  step_completion: {
    [stepId: string]: {
      is_complete: boolean;
      completion_percentage: number;
      validation_errors: string[];
      last_updated: string;
    };
  };
  overall_completion: number;
  estimated_time_remaining: number; // in minutes
  next_recommended_step?: string;
}

export interface OnboardingStepValidation {
  is_valid: boolean;
  errors: Record<string, string[]>;
  warnings: Record<string, string[]>;
  completion_percentage: number;
}

// Profile Publishing
export interface ProfilePublishingOptions {
  make_discoverable: boolean;
  auto_accept_bookings: boolean;
  notification_preferences: {
    email_notifications: boolean;
    sms_notifications: boolean;
    booking_confirmations: boolean;
    student_messages: boolean;
  };
  marketing_consent: {
    promotional_emails: boolean;
    feature_updates: boolean;
    educational_content: boolean;
  };
}

export interface ProfilePublishingResponse {
  success: boolean;
  profile_url: string;
  discovery_url: string;
  booking_url: string;
  next_steps: Array<{
    title: string;
    description: string;
    action_url?: string;
  }>;
}

// ============================================================================
// API Functions
// ============================================================================


/**
 * Get enhanced course catalog with market data
 */
export const getCourseCatalog = async (filters?: CourseFilters): Promise<CourseListResponse> => {
  const queryParams = new URLSearchParams();

  if (filters?.educational_system)
    queryParams.append('educational_system', filters.educational_system.toString());
  if (filters?.education_level) queryParams.append('education_level', filters.education_level);
  if (filters?.subject_area) queryParams.append('subject_area', filters.subject_area);
  if (filters?.difficulty_level) queryParams.append('difficulty_level', filters.difficulty_level);
  if (filters?.search) queryParams.append('search', filters.search);
  if (filters?.with_market_data) queryParams.append('with_market_data', 'true');
  if (filters?.page) queryParams.append('page', filters.page.toString());
  if (filters?.page_size) queryParams.append('page_size', filters.page_size.toString());

  const url = `/accounts/courses/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiClient.get<CourseListResponse>(url);
  return response.data;
};

/**
 * Get educational systems
 */
export const getEducationalSystems = async (): Promise<EducationalSystem[]> => {
  const response = await apiClient.get<EducationalSystem[]>('/accounts/educational-systems/');
  return Array.isArray(response.data) ? response.data : response.data.results || [];
};

/**
 * Create tutor school (individual tutoring practice)
 */
export const createTutorSchool = async (
  data: TutorSchoolData
): Promise<TutorSchoolCreationResponse> => {
  const response = await apiClient.post<TutorSchoolCreationResponse>(
    '/accounts/schools/create-tutor-school/',
    data
  );
  return response.data;
};

/**
 * Start tutor onboarding process
 */
export const startTutorOnboarding = async (): Promise<{
  onboarding_id: string;
  initial_progress: OnboardingProgress;
}> => {
  const response = await apiClient.post<{
    onboarding_id: string;
    initial_progress: OnboardingProgress;
  }>('/accounts/tutors/onboarding/start/');
  return response.data;
};

/**
 * Save tutor onboarding progress
 */
export const saveTutorOnboardingProgress = async (data: {
  onboarding_id?: string;
  step: string;
  data: Partial<TutorOnboardingData>;
  current_step_index: number;
}): Promise<{ success: boolean; progress: OnboardingProgress }> => {
  const response = await apiClient.post<{ success: boolean; progress: OnboardingProgress }>(
    '/accounts/tutors/onboarding/save-progress/',
    data
  );
  return response.data;
};

/**
 * Validate tutor onboarding step
 */
export const validateTutorOnboardingStep = async (data: {
  step: string;
  data: Partial<TutorOnboardingData>;
}): Promise<OnboardingStepValidation> => {
  const response = await apiClient.post<OnboardingStepValidation>(
    '/accounts/tutors/onboarding/validate-step/',
    data
  );
  return response.data;
};

/**
 * Get tutor onboarding progress
 */
export const getTutorOnboardingProgress = async (
  onboardingId?: string
): Promise<OnboardingProgress> => {
  const endpoint = onboardingId
    ? `/accounts/tutors/onboarding/progress/${onboardingId}/`
    : '/accounts/tutors/onboarding/progress/';

  const response = await apiClient.get<OnboardingProgress>(endpoint);
  return response.data;
};

/**
 * Complete tutor onboarding
 */
export const completeTutorOnboarding = async (data: {
  onboarding_id?: string;
  final_data: TutorOnboardingData;
  publishing_options: ProfilePublishingOptions;
}): Promise<ProfilePublishingResponse> => {
  const response = await apiClient.post<ProfilePublishingResponse>(
    '/accounts/tutors/onboarding/complete/',
    data
  );
  return response.data;
};

/**
 * Get tutor discovery profiles (public endpoint)
 */
export const discoverTutors = async (
  filters?: TutorDiscoveryFilters
): Promise<TutorDiscoveryResponse> => {
  const queryParams = new URLSearchParams();

  if (filters?.subjects?.length) queryParams.append('subjects', filters.subjects.join(','));
  if (filters?.min_rate) queryParams.append('min_rate', filters.min_rate.toString());
  if (filters?.max_rate) queryParams.append('max_rate', filters.max_rate.toString());
  if (filters?.languages?.length) queryParams.append('languages', filters.languages.join(','));
  if (filters?.experience_min)
    queryParams.append('experience_min', filters.experience_min.toString());
  if (filters?.location) queryParams.append('location', filters.location);
  if (filters?.availability) queryParams.append('availability', filters.availability);
  if (filters?.rating_min) queryParams.append('rating_min', filters.rating_min.toString());
  if (filters?.educational_system)
    queryParams.append('educational_system', filters.educational_system.toString());
  if (filters?.page) queryParams.append('page', filters.page.toString());
  if (filters?.page_size) queryParams.append('page_size', filters.page_size.toString());
  if (filters?.ordering) queryParams.append('ordering', filters.ordering);

  const url = `/accounts/tutors/discover/${
    queryParams.toString() ? `?${queryParams.toString()}` : ''
  }`;
  const response = await apiClient.get<TutorDiscoveryResponse>(url);
  return response.data;
};

/**
 * Get rate suggestions for courses
 */
export const getCourseRateSuggestions = async (params: {
  course_ids: number[];
  location?: string;
  experience_level?: string;
}): Promise<
  Array<{
    course_id: number;
    suggested_rates: {
      min: number;
      max: number;
      average: number;
      currency: string;
    };
    market_data: {
      demand_level: 'low' | 'medium' | 'high';
      competition_level: 'low' | 'medium' | 'high';
      tutor_count: number;
    };
  }>
> => {
  const response = await apiClient.post('/accounts/courses/rate-suggestions/', params);
  return response.data;
};

/**
 * Upload tutor profile photo
 */
export const uploadTutorProfilePhoto = async (
  file: File | Blob
): Promise<{ photo_url: string }> => {
  const formData = new FormData();
  formData.append('photo', file);

  const response = await apiClient.post<{ photo_url: string }>(
    '/accounts/tutors/profile-photo/',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
};

/**
 * Search and suggest courses based on user input
 */
export const searchCourseSuggestions = async (params: {
  query: string;
  educational_system_id?: number;
  max_results?: number;
}): Promise<
  Array<{
    id: number;
    name: string;
    code: string;
    education_level: string;
    subject_area: string;
    description?: string;
    relevance_score: number;
  }>
> => {
  const queryParams = new URLSearchParams();
  queryParams.append('q', params.query);
  if (params.educational_system_id)
    queryParams.append('educational_system', params.educational_system_id.toString());
  if (params.max_results) queryParams.append('limit', params.max_results.toString());

  const response = await apiClient.get(`/accounts/courses/suggestions/?${queryParams.toString()}`);
  return response.data.suggestions || [];
};

/**
 * Validate tutor business name availability
 */
export const validateTutorBusinessName = async (
  name: string
): Promise<{
  is_available: boolean;
  suggestions?: string[];
  message: string;
}> => {
  const response = await apiClient.post('/accounts/tutors/validate-business-name/', {
    business_name: name,
  });
  return response.data;
};

/**
 * Get onboarding guidance and tips for a specific step
 */
export const getOnboardingGuidance = async (
  stepId: string,
  context?: Record<string, any>
): Promise<{
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
  estimated_time: number; // in minutes
}> => {
  const response = await apiClient.post('/accounts/tutors/onboarding/guidance/', {
    step_id: stepId,
    context: context || {},
  });
  return response.data;
};
