import axios from 'axios';

import apiClient from './apiClient';
import { storage } from '@/utils/storage';

export interface RequestEmailCodeParams {
  email: string;
}

export interface RequestPhoneCodeParams {
  phone: string;
}

export interface VerifyEmailCodeParams {
  email?: string;
  phone?: string;
  code: string;
}

export interface TOTPEmailCodeResponse {
  message: string;
  provisioning_uri: string;
}

export interface AuthResponse {
  token: string;
  expiry: string;
  user: UserProfile;
  is_new_user?: boolean;
  school?: SchoolInfo;
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
  roles?: UserRole[];
  first_login_completed?: boolean;
}

export interface SchoolInfo {
  id: number;
  name: string;
  description?: string;
  address?: string;
  contact_email?: string;
  phone_number?: string;
  website?: string;
  created_at?: string;
  updated_at?: string;
}

export interface UserRole {
  school: {
    id: number;
    name: string;
  };
  role: string;
  role_display: string;
}

export interface OnboardingData {
  name: string;
  email: string;
  phone_number: string;
  primary_contact: 'email' | 'phone';
  user_type: 'tutor' | 'school';
  school: {
    name: string;
    description?: string;
    address?: string;
    contact_email?: string;
    phone_number?: string;
    website?: string;
  };
}

export interface OnboardingResponse {
  message: string;
  user: UserProfile;
  schools: SchoolInfo[];
}

const storeToken = async (token: string) => {
  await storage.setItem('auth_token', token);
};

const getToken = async (): Promise<string | null> => {
  return await storage.getItem('auth_token');
};

const removeToken = async () => {
  await storage.removeItem('auth_token');
  // Clean up old tokens (if any)
  await storage.removeItem('access_token');
  await storage.removeItem('refresh_token');
};

/**
 * Request verification code (TOTP)
 */
export const requestEmailCode = async (
  params: RequestEmailCodeParams | RequestPhoneCodeParams
): Promise<TOTPEmailCodeResponse> => {
  const response = await apiClient.post<TOTPEmailCodeResponse>(
    '/accounts/auth/request-code/',
    params
  );
  return response.data;
};

/**
 * Verify code and get authentication token
 */
export const verifyEmailCode = async (params: VerifyEmailCodeParams) => {
  const response = await apiClient.post<AuthResponse>('/accounts/auth/verify-code/', params);

  // Store token in secure storage
  await storeToken(response.data.token);

  return response.data;
};

/**
 * Logout user
 */
export const logout = async () => {
  // Call the server logout endpoint to invalidate the token
  try {
    await apiClient.post('accounts/auth/logout/');
  } catch (error) {
    // Continue with local logout even if server call fails
    console.error('Error logging out on server:', error);
  }

  // Remove token from storage
  await removeToken();
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = async (): Promise<boolean> => {
  const token = await getToken();
  if (!token) {
    return false;
  }

  // Validate token with server
  try {
    await apiClient.get('/accounts/users/dashboard_info/');
    return true;
  } catch (error: any) {
    // If server is unreachable, we can't verify auth - logout user
    if (
      !error.response ||
      error.code === 'ERR_NETWORK' ||
      error.code === 'ERR_CONNECTION_REFUSED'
    ) {
      await removeToken();
      return false;
    }

    // If 401, token is invalid
    if (error.response?.status === 401) {
      await removeToken();
      return false;
    }

    // For other HTTP errors (500, 503, etc.), assume token is still valid
    // but server is having issues
    return true;
  }
};

/**
 * Fill out form and create user
 */
export const createUser = async (data: OnboardingData): Promise<OnboardingResponse> => {
  try {
    const response = await apiClient.post<OnboardingResponse>('/accounts/users/signup/', data);
    return response.data;
  } catch (error) {
    console.error('Error creating user:', error);
    if (axios.isAxiosError(error)) {
      console.error('API Error Response:', error.response?.data);
      console.error('API Error Status:', error.response?.status);
    }
    throw error;
  }
};

/**
 * Mark first login as completed
 */
export const markFirstLoginCompleted = async (): Promise<void> => {
  try {
    await apiClient.post('/accounts/users/complete_first_login/');
  } catch (error) {
    console.error('Error marking first login as completed:', error);
    throw error;
  }
};
