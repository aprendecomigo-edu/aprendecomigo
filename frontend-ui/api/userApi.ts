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
    console.warn('API did not return expected format:', response.data);
    return [];
  }
};

/**
 * Get list of students with filtering and pagination
 */
export const getStudents = async (filters?: StudentFilters): Promise<StudentListResponse> => {
  const queryParams = new URLSearchParams();
  
  if (filters?.search) queryParams.append('search', filters.search);
  if (filters?.educational_system) queryParams.append('educational_system', filters.educational_system.toString());
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
    console.warn('API did not return expected format:', response.data);
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
export const updateStudent = async (id: number, data: UpdateStudentData): Promise<StudentProfile> => {
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
export const updateStudentStatus = async (id: number, status: 'active' | 'inactive' | 'graduated'): Promise<StudentProfile> => {
  const response = await apiClient.patch<StudentProfile>(`/accounts/students/${id}/`, { status });
  return response.data;
};

/**
 * Bulk import students from CSV
 */
export const bulkImportStudents = async (file: File): Promise<BulkImportResult> => {
  const formData = new FormData();
  formData.append('csv_file', file);
  
  const response = await apiClient.post<BulkImportResult>('/accounts/students/bulk_import/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
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
