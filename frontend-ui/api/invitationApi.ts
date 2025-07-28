import apiClient from './apiClient';

// TypeScript interfaces for invitation management
export interface TeacherInvitation {
  id: string;
  email: string;
  school: {
    id: number;
    name: string;
  };
  invited_by: {
    id: number;
    name: string;
    email: string;
  };
  role: SchoolRole;
  status: InvitationStatus;
  email_delivery_status: EmailDeliveryStatus;
  token: string;
  custom_message?: string;
  batch_id: string;
  created_at: string;
  expires_at: string;
  accepted_at?: string;
  is_accepted: boolean;
  invitation_link: string;
}

export interface BulkInvitationRequest {
  school_id: number;
  invitations: {
    email: string;
    role: SchoolRole;
    custom_message?: string;
  }[];
}

export interface BulkInvitationResponse {
  message: string;
  batch_id: string;
  summary: {
    total_requested: number;
    total_created: number;
    total_duplicates: number;
    total_errors: number;
  };
  successful_invitations: TeacherInvitation[];
  duplicate_invitations: {
    email: string;
    existing_invitation_id: string;
    reason: string;
  }[];
  failed_invitations: {
    email: string;
    errors: string[];
  }[];
}

export interface InvitationListResponse {
  count: number;
  next?: string;
  previous?: string;
  results: TeacherInvitation[];
}

export interface InvitationStatusResponse {
  invitation: TeacherInvitation;
  can_accept: boolean;
  reason?: string;
}

// Enums based on backend models
export enum SchoolRole {
  TEACHER = 'teacher',
  SCHOOL_ADMIN = 'school_admin',
  SCHOOL_OWNER = 'school_owner',
}

export enum InvitationStatus {
  PENDING = 'pending',
  SENT = 'sent',
  DELIVERED = 'delivered',
  VIEWED = 'viewed',
  ACCEPTED = 'accepted',
  DECLINED = 'declined',
  EXPIRED = 'expired',
  CANCELLED = 'cancelled',
}

export enum EmailDeliveryStatus {
  NOT_SENT = 'not_sent',
  PENDING = 'pending',
  SENT = 'sent',
  DELIVERED = 'delivered',
  BOUNCED = 'bounced',
  FAILED = 'failed',
}

// API service class
export class InvitationApi {
  /**
   * Send bulk teacher invitations
   */
  static async sendBulkInvitations(data: BulkInvitationRequest): Promise<BulkInvitationResponse> {
    const response = await apiClient.post('/accounts/teachers/invite_bulk/', data);
    return response.data;
  }

  /**
   * Send single teacher invitation to existing user
   */
  static async inviteExistingTeacher(data: {
    email: string;
    school_id: number;
    role: SchoolRole;
    custom_message?: string;
  }): Promise<TeacherInvitation> {
    const response = await apiClient.post('/accounts/teachers/invite_existing/', data);
    return response.data.invitation;
  }

  /**
   * Get all invitations for a school (admin view)
   */
  static async getSchoolInvitations(params?: {
    page?: number;
    status?: InvitationStatus;
    email?: string;
    role?: SchoolRole;
    ordering?: string;
  }): Promise<InvitationListResponse> {
    const response = await apiClient.get('/accounts/teacher-invitations/list_for_school/', {
      params
    });
    return response.data;
  }

  /**
   * Get invitation status by token
   */
  static async getInvitationStatus(token: string): Promise<InvitationStatusResponse> {
    const response = await apiClient.get(`/accounts/teacher-invitations/${token}/status/`);
    return response.data;
  }

  /**
   * Accept invitation by token
   */
  static async acceptInvitation(token: string): Promise<{
    message: string;
    invitation: TeacherInvitation;
    school_membership: {
      id: number;
      role: SchoolRole;
      is_active: boolean;
    };
  }> {
    const response = await apiClient.post(`/accounts/teacher-invitations/${token}/accept/`);
    return response.data;
  }

  /**
   * Cancel invitation (admin action)
   */
  static async cancelInvitation(token: string): Promise<{
    message: string;
    invitation: TeacherInvitation;
  }> {
    const response = await apiClient.patch(`/accounts/teacher-invitations/${token}/`, {
      status: InvitationStatus.CANCELLED
    });
    return response.data;
  }

  /**
   * Resend invitation email (admin action)
   */
  static async resendInvitation(token: string): Promise<{
    message: string;
    invitation: TeacherInvitation;
  }> {
    const response = await apiClient.post(`/accounts/teacher-invitations/${token}/resend/`);
    return response.data;
  }

  /**
   * Get invitation by token (detailed view)
   */
  static async getInvitation(token: string): Promise<TeacherInvitation> {
    const response = await apiClient.get(`/accounts/teacher-invitations/${token}/`);
    return response.data;
  }

  /**
   * Update invitation details (admin action)
   */
  static async updateInvitation(token: string, data: {
    custom_message?: string;
    role?: SchoolRole;
  }): Promise<TeacherInvitation> {
    const response = await apiClient.patch(`/accounts/teacher-invitations/${token}/`, data);
    return response.data;
  }
}

export default InvitationApi;