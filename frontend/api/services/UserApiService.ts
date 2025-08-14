/**
 * User API Service
 * Handles all user profile and management-related API operations using dependency injection
 */

import { ApiClient } from '../client/ApiClient';

export interface UserProfileUpdate {
  name?: string;
  phone_number?: string;
  email?: string;
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

export interface UserRole {
  school: {
    id: number;
    name: string;
  };
  role: string;
  role_display: string;
}

export interface DashboardInfo {
  user: UserProfile;
  schools: SchoolInfo[];
  notifications_count: number;
  pending_invitations: number;
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

export class UserApiService {
  constructor(private readonly apiClient: ApiClient) {}

  /**
   * Get current user's profile
   */
  async getUserProfile(): Promise<UserProfile> {
    const response = await this.apiClient.get<UserProfile>('/accounts/users/me/');
    return response.data;
  }

  /**
   * Update user profile
   */
  async updateUserProfile(data: UserProfileUpdate): Promise<UserProfile> {
    const response = await this.apiClient.patch<UserProfile>('/accounts/users/me/', data);
    return response.data;
  }

  /**
   * Get dashboard information
   */
  async getDashboardInfo(): Promise<DashboardInfo> {
    const response = await this.apiClient.get<DashboardInfo>('/accounts/dashboard_info/');
    return response.data;
  }

  /**
   * Delete user account
   */
  async deleteAccount(): Promise<void> {
    await this.apiClient.delete('/accounts/users/me/');
  }

  /**
   * Change user password
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await this.apiClient.post('/accounts/users/change-password/', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<void> {
    await this.apiClient.post('/accounts/users/reset-password/', { email });
  }
}
