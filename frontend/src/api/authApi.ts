import apiClient from './apiClient';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface RequestEmailCodeParams {
  email: string;
}

export interface VerifyEmailCodeParams {
  email: string;
  code: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface UserProfile {
  id: number;
  email: string;
  name: string;
  phone_number?: string;
  user_type: 'admin' | 'teacher' | 'student' | 'parent';
  is_admin: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Request email verification code
 */
export const requestEmailCode = async (params: RequestEmailCodeParams) => {
  const response = await apiClient.post('/auth/request-code/', params);
  return response.data;
};

/**
 * Verify email code and get authentication tokens
 */
export const verifyEmailCode = async (params: VerifyEmailCodeParams) => {
  const response = await apiClient.post<AuthTokens>('/auth/verify-code/', params);
  
  // Store tokens in AsyncStorage
  await AsyncStorage.setItem('access_token', response.data.access);
  await AsyncStorage.setItem('refresh_token', response.data.refresh);
  
  return response.data;
};

/**
 * Get current user profile
 */
export const getUserProfile = async () => {
  const response = await apiClient.get<UserProfile>('/auth/profile/');
  return response.data;
};

/**
 * Logout user by removing tokens
 */
export const logout = async () => {
  await AsyncStorage.removeItem('access_token');
  await AsyncStorage.removeItem('refresh_token');
};

/**
 * Check if user is logged in
 */
export const isAuthenticated = async (): Promise<boolean> => {
  const token = await AsyncStorage.getItem('access_token');
  return token !== null;
}; 