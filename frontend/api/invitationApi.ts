import apiClient from './apiClient';

// TypeScript interfaces for comprehensive teacher profile data
export interface ContactPreferences {
  email_notifications: boolean;
  sms_notifications: boolean;
  call_notifications: boolean;
  preferred_contact_method: 'email' | 'sms' | 'call';
}

export interface SubjectExpertise {
  subject: string;
  level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  years_experience?: number;
}

export enum GradeLevel {
  ELEMENTARY = 'elementary',
  MIDDLE_SCHOOL = 'middle_school',
  HIGH_SCHOOL = 'high_school',
  UNIVERSITY = 'university',
}

export interface WeeklySchedule {
  monday: TimeSlot[];
  tuesday: TimeSlot[];
  wednesday: TimeSlot[];
  thursday: TimeSlot[];
  friday: TimeSlot[];
  saturday: TimeSlot[];
  sunday: TimeSlot[];
}

export interface TimeSlot {
  start_time: string; // HH:MM format
  end_time: string; // HH:MM format
  available: boolean;
}

export interface PaymentPreferences {
  preferred_payment_method: 'bank_transfer' | 'paypal' | 'stripe';
  invoice_frequency: 'weekly' | 'biweekly' | 'monthly';
  tax_information_provided: boolean;
}

export interface EducationEntry {
  degree: string;
  field_of_study: string;
  institution: string;
  graduation_year: number;
  is_highest_degree: boolean;
}

export interface ExperienceEntry {
  role: string;
  institution: string;
  start_date: string; // YYYY-MM-DD
  end_date?: string; // YYYY-MM-DD, null if current
  description: string;
  is_current: boolean;
}

export interface CertificationFile {
  name: string;
  file: File | string; // File object or URL for uploaded files
  expiry_date?: string; // YYYY-MM-DD
  issuing_organization: string;
}

// Comprehensive teacher profile data for invitation acceptance
export interface TeacherProfileData {
  // Step 1: Basic Information
  profile_photo?: File | string;
  contact_preferences?: ContactPreferences;
  introduction?: string;

  // Step 2: Teaching Subjects
  teaching_subjects: SubjectExpertise[];
  custom_subjects?: string[];

  // Step 3: Grade Level Preferences
  grade_levels: GradeLevel[];

  // Step 4: Availability & Scheduling
  availability_schedule?: WeeklySchedule;
  timezone: string;
  availability_notes?: string;

  // Step 5: Rates & Compensation
  hourly_rate: number;
  rate_negotiable: boolean;
  payment_preferences?: PaymentPreferences;

  // Step 6: Credentials & Experience
  education_background: EducationEntry[];
  teaching_experience: ExperienceEntry[];
  certifications: CertificationFile[];

  // Step 7: Profile Marketing
  teaching_philosophy: string;
  teaching_approach: string;
  specializations: string[];
  achievements?: string[];

  // Legacy fields for backward compatibility
  bio?: string;
  specialty?: string;
  course_ids?: number[];
}

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
  needs_profile_wizard?: boolean;
  wizard_metadata?: {
    requires_profile_completion: boolean;
    completed_steps?: string[];
    current_step?: number;
  };
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
      params,
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
   * Accept invitation by token with comprehensive profile data
   */
  static async acceptInvitation(
    token: string,
    profileData?: TeacherProfileData,
  ): Promise<{
    message: string;
    teacher: any;
    school_membership: {
      id: number;
      role: SchoolRole;
      is_active: boolean;
    };
    school: {
      id: number;
      name: string;
    };
  }> {
    const response = await apiClient.post(
      `/accounts/teacher-invitations/${token}/accept/`,
      profileData || {},
    );
    return response.data;
  }

  /**
   * Decline invitation by token
   */
  static async declineInvitation(token: string): Promise<{
    message: string;
  }> {
    const response = await apiClient.post(`/accounts/teacher-invitations/${token}/decline/`);
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
      status: InvitationStatus.CANCELLED,
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
  static async updateInvitation(
    token: string,
    data: {
      custom_message?: string;
      role?: SchoolRole;
    },
  ): Promise<TeacherInvitation> {
    const response = await apiClient.patch(`/accounts/teacher-invitations/${token}/`, data);
    return response.data;
  }
}

export default InvitationApi;
