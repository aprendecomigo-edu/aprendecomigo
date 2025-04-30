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
  };
  stats: any;
}

/**
 * Get dashboard information for the current user
 */
export const getDashboardInfo = async () => {
  const response = await apiClient.get<DashboardInfo>('/users/dashboard_info/');
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
