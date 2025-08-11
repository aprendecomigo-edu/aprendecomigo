/**
 * School API Service
 * Handles all school-related API operations using dependency injection
 */

import { ApiClient } from '../client/ApiClient';

export interface School {
  id: number;
  name: string;
  description?: string;
  address?: string;
  contact_email?: string;
  phone_number?: string;
  website?: string;
  created_at: string;
  updated_at: string;
  owner?: {
    id: number;
    name: string;
    email: string;
  };
}

export interface CreateSchoolData {
  name: string;
  description?: string;
  address?: string;
  contact_email?: string;
  phone_number?: string;
  website?: string;
}

export interface UpdateSchoolData {
  name?: string;
  description?: string;
  address?: string;
  contact_email?: string;
  phone_number?: string;
  website?: string;
}

export interface SchoolMember {
  id: number;
  user: {
    id: number;
    name: string;
    email: string;
  };
  role: string;
  role_display: string;
  joined_at: string;
}

export interface InviteUserData {
  email: string;
  role: string;
  message?: string;
}

export class SchoolApiService {
  constructor(private readonly apiClient: ApiClient) {}

  /**
   * Get all schools for the current user
   */
  async getSchools(): Promise<School[]> {
    const response = await this.apiClient.get<School[]>('/schools/');
    return response.data;
  }

  /**
   * Get a specific school
   */
  async getSchool(schoolId: number): Promise<School> {
    const response = await this.apiClient.get<School>(`/schools/${schoolId}/`);
    return response.data;
  }

  /**
   * Create a new school
   */
  async createSchool(data: CreateSchoolData): Promise<School> {
    const response = await this.apiClient.post<School>('/schools/', data);
    return response.data;
  }

  /**
   * Update a school
   */
  async updateSchool(schoolId: number, data: UpdateSchoolData): Promise<School> {
    const response = await this.apiClient.patch<School>(`/schools/${schoolId}/`, data);
    return response.data;
  }

  /**
   * Delete a school
   */
  async deleteSchool(schoolId: number): Promise<void> {
    await this.apiClient.delete(`/schools/${schoolId}/`);
  }

  /**
   * Get school members
   */
  async getSchoolMembers(schoolId: number): Promise<SchoolMember[]> {
    const response = await this.apiClient.get<SchoolMember[]>(`/schools/${schoolId}/members/`);
    return response.data;
  }

  /**
   * Invite user to school
   */
  async inviteUser(schoolId: number, data: InviteUserData): Promise<void> {
    await this.apiClient.post(`/schools/${schoolId}/invite/`, data);
  }

  /**
   * Remove member from school
   */
  async removeMember(schoolId: number, userId: number): Promise<void> {
    await this.apiClient.delete(`/schools/${schoolId}/members/${userId}/`);
  }

  /**
   * Update member role
   */
  async updateMemberRole(schoolId: number, userId: number, role: string): Promise<SchoolMember> {
    const response = await this.apiClient.patch<SchoolMember>(
      `/schools/${schoolId}/members/${userId}/`,
      { role }
    );
    return response.data;
  }
}
