import apiClient from './apiClient';
import { UserProfile } from './authApi';

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
}

export interface StudentProfile {
  id: number;
  user: UserProfile;
  school_year: string;
  birth_date: string;
  address: string;
  cc_number: string;
  cc_photo?: string;
  calendar_iframe?: string;
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
    console.warn('API did not return expected format:', response.data);
    return [];
  }
};

/**
 * Get list of students
 */
export const getStudents = async (): Promise<StudentProfile[]> => {
  const response = await apiClient.get('/accounts/students/');

  // Handle paginated response - extract results
  if (response.data && Array.isArray(response.data.results)) {
    return response.data.results;
  } else if (Array.isArray(response.data)) {
    // Fallback for non-paginated response
    return response.data;
  } else {
    console.warn('API did not return expected format:', response.data);
    return [];
  }
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
  activity_type: 'invitation_sent' | 'invitation_accepted' | 'invitation_declined' | 'student_joined' | 'teacher_joined' | 'class_created' | 'class_completed' | 'class_cancelled';
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
  if (params?.activity_types?.length) queryParams.append('activity_types', params.activity_types.join(','));
  if (params?.date_from) queryParams.append('date_from', params.date_from);
  if (params?.date_to) queryParams.append('date_to', params.date_to);

  const url = `/accounts/schools/${schoolId}/activity/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await apiClient.get<SchoolActivityResponse>(url);
  return response.data;
};

/**
 * Update school information
 */
export const updateSchoolInfo = async (schoolId: number, data: Partial<SchoolInfo>): Promise<SchoolInfo> => {
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
