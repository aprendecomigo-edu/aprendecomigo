import apiClient from './apiClient';
import { UserProfile } from './authApi';

export interface ProfileCompletion {
  completion_percentage: number;
  missing_critical: string[];
  missing_optional: string[];
  recommendations: Array<{
    text: string;
    priority: 'high' | 'medium' | 'low';
  }>;
  is_complete: boolean;
  scores_breakdown: {
    basic_info: number;
    teaching_details: number;
    professional_info: number;
  };
}

export interface TeacherCourse {
  id: number;
  course_name: string;
  grade_level: string;
  is_active: boolean;
  subject_area: string;
}

export interface TeacherProfile {
  id: number;
  user: UserProfile;
  bio: string;
  specialty: string;
  education: string;
  hourly_rate: number;
  availability: string;
  address: string;
  phone_number: string;
  calendar_iframe?: string;

  // Enhanced fields from backend
  profile_completion_score: number;
  is_profile_complete: boolean;
  last_activity?: string;
  status?: 'active' | 'inactive' | 'pending';

  // Structured fields
  education_background?: Record<string, any>;
  teaching_subjects?: string[];
  rate_structure?: Record<string, any>;
  weekly_availability?: Record<string, any>;

  // Related data
  teacher_courses?: TeacherCourse[];
  profile_completion?: ProfileCompletion;

  // Timestamps
  created_at?: string;
  updated_at?: string;
  last_profile_update?: string;
}

export interface EducationalSystem {
  id: number;
  name: string;
  country: string;
  description: string;
  is_active: boolean;
}

export interface StudentProfile {
  id: number;
  user: UserProfile;
  educational_system: EducationalSystem;
  school_year: string;
  birth_date: string;
  address: string;
  cc_number: string;
  cc_photo?: string;
  calendar_iframe?: string;
  status?: 'active' | 'inactive' | 'graduated';
  parent_contact?: {
    name: string;
    email: string;
    phone: string;
    relationship: string;
  };
  created_at: string;
  updated_at: string;
}

export interface CreateStudentData {
  name: string;
  email: string;
  phone_number?: string;
  primary_contact: 'email' | 'phone';
  educational_system_id: number;
  school_year: string;
  birth_date: string;
  address?: string;
  school_id: number;
  parent_contact?: {
    name: string;
    email: string;
    phone: string;
    relationship: string;
  };
}

export interface UpdateStudentData {
  name?: string;
  email?: string;
  phone_number?: string;
  educational_system_id?: number;
  school_year?: string;
  birth_date?: string;
  address?: string;
  status?: 'active' | 'inactive' | 'graduated';
  parent_contact?: {
    name: string;
    email: string;
    phone: string;
    relationship: string;
  };
}

export interface StudentFilters {
  search?: string;
  educational_system?: number;
  school_year?: string;
  status?: 'active' | 'inactive' | 'graduated';
  page?: number;
  page_size?: number;
  ordering?: string;
}

export interface StudentListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: StudentProfile[];
}

export interface BulkImportResult {
  success: boolean;
  created_count: number;
  failed_count: number;
  errors: Array<{
    row: number;
    field: string;
    message: string;
  }>;
}

export interface DashboardInfo {
  user_info: {
    id: number;
    email: string;
    name: string;
    date_joined: string;
    is_admin: boolean;
    user_type: string;
    needs_onboarding?: boolean;
    calendar_iframe?: string;
    first_login_completed?: boolean;
  };
  stats: any;
}

/**
 * Get dashboard information for the current user
 */
export const getDashboardInfo = async () => {
  const response = await apiClient.get<DashboardInfo>('/accounts/users/dashboard_info/');
  return response.data;
};

/**
 * Get school profile information
 */
export const getSchoolProfile = async () => {
  const response = await apiClient.get('/users/school_profile/');
  return response.data;
};

/**
 * Get teacher profile by ID or current user
 */
export const getTeacherProfile = async (id?: number) => {
  const endpoint = id ? `/teachers/${id}/` : '/teachers/';
  const response = await apiClient.get<TeacherProfile>(endpoint);
  return response.data;
};

/**
 * Get list of teachers
 */
export const getTeachers = async (): Promise<TeacherProfile[]> => {
  const response = await apiClient.get('/accounts/teachers/');

  // Handle paginated response - extract results
  if (response.data && Array.isArray(response.data.results)) {
    return response.data.results;
  } else if (Array.isArray(response.data)) {
    // Fallback for non-paginated response
    return response.data;
  } else {
    if (__DEV__) {
      console.warn('API did not return expected format:', response.data);
    }
    return [];
  }
};

/**
 * Get list of students with filtering and pagination
 */
export const getStudents = async (filters?: StudentFilters): Promise<StudentListResponse> => {
  const queryParams = new URLSearchParams();

  if (filters?.search) queryParams.append('search', filters.search);
  if (filters?.educational_system)
    queryParams.append('educational_system', filters.educational_system.toString());
  if (filters?.school_year) queryParams.append('school_year', filters.school_year);
  if (filters?.status) queryParams.append('status', filters.status);
  if (filters?.page) queryParams.append('page', filters.page.toString());
  if (filters?.page_size) queryParams.append('page_size', filters.page_size.toString());
  if (filters?.ordering) queryParams.append('ordering', filters.ordering);

  const url = `/accounts/students/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiClient.get<StudentListResponse>(url);

  // Handle both paginated and non-paginated responses
  if (response.data.results) {
    return response.data;
  } else if (Array.isArray(response.data)) {
    // Fallback for non-paginated response
    return {
      count: response.data.length,
      next: null,
      previous: null,
      results: response.data,
    };
  } else {
    if (__DEV__) {
      console.warn('API did not return expected format:', response.data);
    }
    return {
      count: 0,
      next: null,
      previous: null,
      results: [],
    };
  }
};

/**
 * Create a new student
 */
export const createStudent = async (data: CreateStudentData): Promise<StudentProfile> => {
  const response = await apiClient.post<StudentProfile>('/accounts/students/create_student/', data);
  return response.data;
};

/**
 * Update student profile
 */
export const updateStudent = async (
  id: number,
  data: UpdateStudentData
): Promise<StudentProfile> => {
  const response = await apiClient.patch<StudentProfile>(`/accounts/students/${id}/`, data);
  return response.data;
};

/**
 * Delete a student
 */
export const deleteStudent = async (id: number): Promise<void> => {
  await apiClient.delete(`/accounts/students/${id}/`);
};

/**
 * Get student by ID
 */
export const getStudentById = async (id: number): Promise<StudentProfile> => {
  const response = await apiClient.get<StudentProfile>(`/accounts/students/${id}/`);
  return response.data;
};

/**
 * Update student status
 */
export const updateStudentStatus = async (
  id: number,
  status: 'active' | 'inactive' | 'graduated'
): Promise<StudentProfile> => {
  const response = await apiClient.patch<StudentProfile>(`/accounts/students/${id}/`, { status });
  return response.data;
};

/**
 * Bulk import students from CSV
 */
export const bulkImportStudents = async (file: File): Promise<BulkImportResult> => {
  const formData = new FormData();
  formData.append('csv_file', file);

  const response = await apiClient.post<BulkImportResult>(
    '/accounts/students/bulk_import/',
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
 * Get educational systems
 */
export const getEducationalSystems = async (): Promise<EducationalSystem[]> => {
  const response = await apiClient.get<EducationalSystem[]>('/accounts/educational-systems/');
  return Array.isArray(response.data) ? response.data : response.data.results || [];
};

/**
 * Update teacher profile
 */
export const updateTeacherProfile = async (id: number, data: Partial<TeacherProfile>) => {
  const response = await apiClient.patch<TeacherProfile>(`/teachers/${id}/`, data);
  return response.data;
};

/**
 * Get student profile by ID or current user
 */
export const getStudentProfile = async (id?: number) => {
  const endpoint = id ? `/students/${id}/` : '/students/';
  const response = await apiClient.get<StudentProfile>(endpoint);
  return response.data;
};

/**
 * Update student profile
 */
export const updateStudentProfile = async (id: number, data: Partial<StudentProfile>) => {
  const response = await apiClient.patch<StudentProfile>(`/students/${id}/`, data);
  return response.data;
};

/**
 * Complete student onboarding
 */
export const completeStudentOnboarding = async (data: Partial<StudentProfile>) => {
  const response = await apiClient.post<StudentProfile>('/students/onboarding/', data);
  return response.data;
};

// School Dashboard Types and APIs

export interface SchoolMetrics {
  student_count: {
    total: number;
    active: number;
    inactive: number;
    trend: {
      daily: Array<{ date: string; count: number; change: number }>;
      weekly: Array<{ date: string; count: number; change: number }>;
      monthly: Array<{ date: string; count: number; change: number }>;
    };
  };
  teacher_count: {
    total: number;
    active: number;
    inactive: number;
    trend: {
      daily: Array<{ date: string; count: number; change: number }>;
      weekly: Array<{ date: string; count: number; change: number }>;
      monthly: Array<{ date: string; count: number; change: number }>;
    };
  };
  class_metrics: {
    active_classes: number;
    completed_today: number;
    scheduled_today: number;
    completion_rate: number;
    trend: {
      daily: Array<{ date: string; count: number; change: number }>;
      weekly: Array<{ date: string; count: number; change: number }>;
    };
  };
  engagement_metrics: {
    invitations_sent: number;
    invitations_accepted: number;
    acceptance_rate: number;
    avg_time_to_accept: string;
  };
}

export interface SchoolActivity {
  id: string;
  activity_type:
    | 'invitation_sent'
    | 'invitation_accepted'
    | 'invitation_declined'
    | 'student_joined'
    | 'teacher_joined'
    | 'class_created'
    | 'class_completed'
    | 'class_cancelled';
  timestamp: string;
  actor: {
    id: number;
    name: string;
    email: string;
    role: string;
  };
  target: {
    type: 'user' | 'class' | 'invitation';
    id: number;
    name: string;
  };
  metadata: Record<string, any>;
  description: string;
}

export interface SchoolActivityResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: SchoolActivity[];
}

export interface SchoolInfo {
  id: number;
  name: string;
  description: string;
  address: string;
  contact_email: string;
  phone_number: string;
  website: string;
  settings: {
    trial_cost_absorption: 'school' | 'teacher' | 'split';
    default_session_duration: number;
    timezone: string;
    dashboard_refresh_interval?: number;
    activity_retention_days?: number;
  };
  created_at: string;
  updated_at: string;
}

/**
 * Get school metrics for dashboard
 */
export const getSchoolMetrics = async (schoolId: number): Promise<SchoolMetrics> => {
  const response = await apiClient.get<SchoolMetrics>(`/accounts/schools/${schoolId}/metrics/`);
  return response.data;
};

/**
 * Get school activity feed
 */
export const getSchoolActivity = async (
  schoolId: number,
  params?: {
    page?: number;
    page_size?: number;
    activity_types?: string[];
    date_from?: string;
    date_to?: string;
  }
): Promise<SchoolActivityResponse> => {
  const queryParams = new URLSearchParams();

  if (params?.page) queryParams.append('page', params.page.toString());
  if (params?.page_size) queryParams.append('page_size', params.page_size.toString());
  if (params?.activity_types?.length)
    queryParams.append('activity_types', params.activity_types.join(','));
  if (params?.date_from) queryParams.append('date_from', params.date_from);
  if (params?.date_to) queryParams.append('date_to', params.date_to);

  const url = `/accounts/schools/${schoolId}/activity/${
    queryParams.toString() ? `?${queryParams.toString()}` : ''
  }`;
  const response = await apiClient.get<SchoolActivityResponse>(url);
  return response.data;
};

/**
 * Update school information
 */
export const updateSchoolInfo = async (
  schoolId: number,
  data: Partial<SchoolInfo>
): Promise<SchoolInfo> => {
  const response = await apiClient.patch<SchoolInfo>(`/accounts/schools/${schoolId}/`, data);
  return response.data;
};

/**
 * Get school information
 */
export const getSchoolInfo = async (schoolId: number): Promise<SchoolInfo> => {
  const response = await apiClient.get<SchoolInfo>(`/accounts/schools/${schoolId}/`);
  return response.data;
};

/**
 * School membership types
 */
export interface SchoolMembership {
  id: number;
  user: number;
  school: {
    id: number;
    name: string;
    description: string;
  };
  role: 'school_owner' | 'school_admin' | 'teacher' | 'student' | 'parent';
  is_active: boolean;
  joined_at: string;
}

export interface SchoolMembershipResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: SchoolMembership[];
}

/**
 * Get current user's school memberships
 */
export const getUserSchoolMemberships = async (): Promise<SchoolMembership[]> => {
  const response = await apiClient.get<SchoolMembershipResponse>('/accounts/school-memberships/');
  return response.data.results;
};

/**
 * Get user's school memberships with admin privileges (school_owner or school_admin)
 */
export const getUserAdminSchools = async (): Promise<SchoolMembership[]> => {
  const memberships = await getUserSchoolMemberships();
  return memberships.filter(
    membership =>
      membership.is_active &&
      (membership.role === 'school_owner' || membership.role === 'school_admin')
  );
};

// Teacher Management Interfaces and APIs

export interface TeacherFilters {
  search?: string;
  specialty?: string;
  status?: 'active' | 'inactive' | 'pending';
  completion_status?: 'complete' | 'incomplete' | 'critical_missing';
  min_completion?: number;
  has_courses?: boolean;
  page?: number;
  page_size?: number;
  ordering?: string;
}

export interface TeacherListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: TeacherProfile[];
}

export interface TeacherAnalytics {
  total_teachers: number;
  average_completion: number;
  complete_profiles: number;
  incomplete_profiles: number;
  completion_distribution: {
    '0-25%': number;
    '26-50%': number;
    '51-75%': number;
    '76-100%': number;
  };
  common_missing_fields: Array<{
    field: string;
    count: number;
    percentage: number;
  }>;
  profile_completion_stats: {
    average_score: number;
    complete_count: number;
    needs_attention: Array<{
      teacher_id: number;
      name: string;
      completion_percentage: number;
      missing_critical: string[];
    }>;
  };
  activity_metrics?: {
    active_this_week: number;
    total_courses_taught: number;
    avg_student_rating?: number;
  };
}

export interface BulkTeacherAction {
  action: 'update_status' | 'send_message' | 'export_data' | 'update_profile';
  teacher_ids: number[];
  parameters?: Record<string, any>;
}

export interface BulkActionResult {
  success: boolean;
  total_processed: number;
  successful_count: number;
  failed_count: number;
  errors: Array<{
    teacher_id: number;
    error: string;
  }>;
  export_url?: string; // For export actions
}

export interface TeacherMessageTemplate {
  id: string;
  name: string;
  subject: string;
  content: string;
  variables: string[];
}

export interface UpdateTeacherData {
  bio?: string;
  specialty?: string;
  education?: string;
  hourly_rate?: number;
  availability?: string;
  address?: string;
  phone_number?: string;
  calendar_iframe?: string;
  status?: 'active' | 'inactive' | 'pending';
}

/**
 * Get enhanced list of teachers with filtering and pagination
 */
export const getTeachersEnhanced = async (
  filters?: TeacherFilters
): Promise<TeacherListResponse> => {
  const queryParams = new URLSearchParams();

  if (filters?.search) queryParams.append('search', filters.search);
  if (filters?.specialty) queryParams.append('specialty', filters.specialty);
  if (filters?.status) queryParams.append('status', filters.status);
  if (filters?.completion_status)
    queryParams.append('completion_status', filters.completion_status);
  if (filters?.min_completion)
    queryParams.append('min_completion', filters.min_completion.toString());
  if (filters?.has_courses !== undefined)
    queryParams.append('has_courses', filters.has_courses.toString());
  if (filters?.page) queryParams.append('page', filters.page.toString());
  if (filters?.page_size) queryParams.append('page_size', filters.page_size.toString());
  if (filters?.ordering) queryParams.append('ordering', filters.ordering);

  const url = `/accounts/teachers/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiClient.get<TeacherListResponse>(url);
  return response.data;
};

/**
 * Get teacher analytics for a school
 */
export const getTeacherAnalytics = async (schoolId: number): Promise<TeacherAnalytics> => {
  const response = await apiClient.get<TeacherAnalytics>(
    `/accounts/schools/${schoolId}/teacher-analytics/`
  );
  return response.data;
};

/**
 * Perform bulk actions on teachers
 */
export const performBulkTeacherActions = async (
  action: BulkTeacherAction
): Promise<BulkActionResult> => {
  const response = await apiClient.post<BulkActionResult>(
    '/accounts/teachers/bulk-actions/',
    action
  );
  return response.data;
};

/**
 * Get available message templates for teacher communication
 */
export const getTeacherMessageTemplates = async (): Promise<TeacherMessageTemplate[]> => {
  const response = await apiClient.get<TeacherMessageTemplate[]>(
    '/accounts/teachers/message-templates/'
  );
  return response.data;
};

/**
 * Update teacher profile (admin-editable fields only)
 */
export const updateTeacherProfileAdmin = async (
  id: number,
  data: UpdateTeacherData
): Promise<TeacherProfile> => {
  const response = await apiClient.patch<TeacherProfile>(`/accounts/teachers/${id}/`, data);
  return response.data;
};

/**
 * Get detailed teacher profile with completion data
 */
export const getTeacherProfileDetailed = async (id: number): Promise<TeacherProfile> => {
  const response = await apiClient.get<TeacherProfile>(`/accounts/teachers/${id}/`);
  return response.data;
};

// Teacher Profile Wizard APIs

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

export interface WizardValidationResponse {
  is_valid: boolean;
  errors: Record<string, string[]>;
  warnings: Record<string, string[]>;
}

export interface WizardProgressResponse {
  success: boolean;
  completion_data: ProfileCompletion;
  next_step_suggestion?: string;
}

export interface RateSuggestion {
  subject: string;
  location: string;
  suggested_rate: {
    min: number;
    max: number;
    average: number;
    currency: string;
  };
  market_data: {
    total_teachers: number;
    demand_level: 'low' | 'medium' | 'high';
    competition_level: 'low' | 'medium' | 'high';
  };
}

/**
 * Save teacher profile wizard progress
 */
export const saveTeacherProfileWizardProgress = async (data: {
  profile_data: TeacherProfileWizardData;
  current_step: number;
}): Promise<WizardProgressResponse> => {
  const response = await apiClient.post<WizardProgressResponse>(
    '/accounts/teachers/profile-wizard/save-progress/',
    data
  );
  return response.data;
};

/**
 * Validate teacher profile wizard step
 */
export const validateTeacherProfileWizardStep = async (data: {
  step: number;
  data: TeacherProfileWizardData;
}): Promise<WizardValidationResponse> => {
  const response = await apiClient.post<WizardValidationResponse>(
    '/accounts/teachers/profile-wizard/validate-step/',
    data
  );
  return response.data;
};

/**
 * Submit complete teacher profile
 */
export const submitTeacherProfile = async (data: {
  profile_data: TeacherProfileWizardData;
}): Promise<{ success: boolean; profile_id: number }> => {
  const response = await apiClient.post<{ success: boolean; profile_id: number }>(
    '/accounts/teachers/profile-wizard/submit/',
    data
  );
  return response.data;
};

/**
 * Get rate suggestions for a subject and location
 */
export const getRateSuggestions = async (params: {
  subject: string;
  location: string;
}): Promise<RateSuggestion> => {
  const response = await apiClient.get<RateSuggestion>('/accounts/teachers/rate-suggestions/', {
    params,
  });
  return response.data;
};

/**
 * Upload teacher profile photo
 */
export const uploadTeacherProfilePhoto = async (
  file: File | Blob
): Promise<{ photo_url: string }> => {
  const formData = new FormData();
  formData.append('photo', file);

  const response = await apiClient.post<{ photo_url: string }>(
    '/accounts/teachers/profile/photo/',
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
 * Get teacher profile completion score
 */
export const getTeacherProfileCompletionScore = async (): Promise<ProfileCompletion> => {
  const response = await apiClient.get<ProfileCompletion>(
    '/accounts/teachers/profile-completion-score/'
  );
  return response.data;
};
