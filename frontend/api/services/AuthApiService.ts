/**
 * Authentication API Service
 * Handles all authentication-related API operations using dependency injection
 */

import { ApiClient } from '../client/ApiClient';

// Import types from the existing auth API
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
  primary_role?: string;
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

export class AuthApiService {
  constructor(private readonly apiClient: ApiClient) {}

  /**
   * Request verification code (TOTP)
   */
  async requestEmailCode(
    params: RequestEmailCodeParams | RequestPhoneCodeParams,
  ): Promise<TOTPEmailCodeResponse> {
    const response = await this.apiClient.post<TOTPEmailCodeResponse>(
      '/accounts/auth/request-code/',
      params,
    );
    return response.data;
  }

  /**
   * Verify code and get authentication token
   */
  async verifyEmailCode(params: VerifyEmailCodeParams): Promise<AuthResponse> {
    const response = await this.apiClient.post<AuthResponse>('/accounts/auth/verify-code/', params);
    return response.data;
  }

  /**
   * Create user account
   */
  async createUser(data: OnboardingData): Promise<OnboardingResponse> {
    const response = await this.apiClient.post<OnboardingResponse>('/accounts/users/signup/', data);
    return response.data;
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    await this.apiClient.post('/accounts/auth/logout/');
  }

  /**
   * Validate current authentication token
   */
  async validateToken(): Promise<void> {
    await this.apiClient.get('/accounts/auth/validate-token/');
  }

  /**
   * Mark first login as completed
   */
  async markFirstLoginCompleted(): Promise<void> {
    await this.apiClient.post('/accounts/users/complete_first_login/');
  }
}
