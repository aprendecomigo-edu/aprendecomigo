import apiClient from './apiClient';

// TypeScript interfaces for communication system
export interface EmailTemplateType {
  invitation: 'invitation';
  reminder: 'reminder';
  welcome: 'welcome';
  profile_reminder: 'profile_reminder';
  completion_celebration: 'completion_celebration';
  ongoing_support: 'ongoing_support';
}

export interface SchoolEmailTemplate {
  id: number;
  school: number;
  template_type: keyof EmailTemplateType;
  name: string;
  subject_template: string;
  html_content: string;
  text_content: string;
  is_active: boolean;
  is_default: boolean;
  use_school_branding: boolean;
  custom_css?: string;
  created_at: string;
  updated_at: string;
  variables_used: string[];
}

export interface SchoolBranding {
  id: number;
  school: number;
  primary_color: string;
  secondary_color: string;
  logo?: string;
  custom_messaging?: string;
  email_footer?: string;
  updated_at: string;
}

export interface EmailCommunication {
  id: number;
  recipient?: number;
  recipient_email: string;
  template_type: keyof EmailTemplateType;
  subject: string;
  sent_at?: string;
  delivered_at?: string;
  opened_at?: string;
  clicked_at?: string;
  failed_at?: string;
  status: 'pending' | 'sent' | 'delivered' | 'opened' | 'clicked' | 'failed';
  error_message?: string;
  school: number;
}

export interface EmailAnalytics {
  total_sent: number;
  delivered_count: number;
  opened_count: number;
  clicked_count: number;
  failed_count: number;
  delivery_rate: number;
  open_rate: number;
  click_rate: number;
  bounce_rate: number;
  template_performance: {
    template_type: keyof EmailTemplateType;
    sent_count: number;
    open_rate: number;
    click_rate: number;
  }[];
  recent_activity: EmailCommunication[];
}

export interface TeacherOnboardingProgress {
  id: number;
  teacher: number;
  school: number;
  current_step: number;
  total_steps: number;
  completed_steps: number[];
  milestones_achieved: string[];
  started_at: string;
  completed_at?: string;
  last_activity_at: string;
  profile_completion_percentage: number;
}

export interface FAQ {
  id: number;
  question: string;
  answer: string;
  category: string;
  order: number;
  is_active: boolean;
  helpful_count: number;
  view_count: number;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface FAQCategory {
  id: number;
  name: string;
  description: string;
  order: number;
  faq_count: number;
}

// API request/response types
export interface CreateTemplateRequest {
  template_type: keyof EmailTemplateType;
  name: string;
  subject_template: string;
  html_content: string;
  text_content: string;
  use_school_branding?: boolean;
  custom_css?: string;
}

export interface UpdateTemplateRequest extends Partial<CreateTemplateRequest> {
  is_active?: boolean;
}

export interface PreviewTemplateRequest {
  template_id?: number;
  template_type?: keyof EmailTemplateType;
  subject_template?: string;
  html_content?: string;
  text_content?: string;
  context_variables?: Record<string, any>;
}

export interface PreviewTemplateResponse {
  subject: string;
  html_content: string;
  text_content: string;
  variables_used: string[];
  missing_variables: string[];
}

export interface UpdateBrandingRequest {
  primary_color?: string;
  secondary_color?: string;
  custom_messaging?: string;
  email_footer?: string;
}

export interface TemplateListResponse {
  count: number;
  next?: string;
  previous?: string;
  results: SchoolEmailTemplate[];
}

export interface AnalyticsFilters {
  start_date?: string;
  end_date?: string;
  template_type?: keyof EmailTemplateType;
  status?: EmailCommunication['status'];
}

class CommunicationApi {
  // Email Template Management
  async getSchoolTemplates(params?: {
    template_type?: keyof EmailTemplateType;
    is_active?: boolean;
    page?: number;
  }): Promise<TemplateListResponse> {
    const response = await apiClient.get('/accounts/communication/templates/', { params });
    return response.data;
  }

  async getTemplate(id: number): Promise<SchoolEmailTemplate> {
    const response = await apiClient.get(`/accounts/communication/templates/${id}/`);
    return response.data;
  }

  async createTemplate(data: CreateTemplateRequest): Promise<SchoolEmailTemplate> {
    const response = await apiClient.post('/accounts/communication/templates/', data);
    return response.data;
  }

  async updateTemplate(id: number, data: UpdateTemplateRequest): Promise<SchoolEmailTemplate> {
    const response = await apiClient.patch(`/accounts/communication/templates/${id}/`, data);
    return response.data;
  }

  async deleteTemplate(id: number): Promise<void> {
    await apiClient.delete(`/accounts/communication/templates/${id}/`);
  }

  async duplicateTemplate(id: number, newName?: string): Promise<SchoolEmailTemplate> {
    const response = await apiClient.post(`/accounts/communication/templates/${id}/duplicate/`, {
      name: newName,
    });
    return response.data;
  }

  async previewTemplate(data: PreviewTemplateRequest): Promise<PreviewTemplateResponse> {
    const response = await apiClient.post('/accounts/communication/templates/preview/', data);
    return response.data;
  }

  async sendTestEmail(
    templateId: number,
    testEmail: string,
  ): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post(`/accounts/communication/templates/${templateId}/test/`, {
      test_email: testEmail,
    });
    return response.data;
  }

  // School Branding Management
  async getSchoolBranding(): Promise<SchoolBranding> {
    const response = await apiClient.get('/accounts/communication/branding/');
    return response.data;
  }

  async updateSchoolBranding(data: UpdateBrandingRequest): Promise<SchoolBranding> {
    const response = await apiClient.patch('/accounts/communication/branding/', data);
    return response.data;
  }

  async uploadLogo(logoFile: File): Promise<SchoolBranding> {
    const formData = new FormData();
    formData.append('logo', logoFile);

    const response = await apiClient.patch('/accounts/communication/branding/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Email Analytics
  async getEmailAnalytics(filters?: AnalyticsFilters): Promise<EmailAnalytics> {
    const response = await apiClient.get('/accounts/communication/analytics/', { params: filters });
    return response.data;
  }

  async getEmailCommunications(params?: {
    template_type?: keyof EmailTemplateType;
    status?: EmailCommunication['status'];
    start_date?: string;
    end_date?: string;
    page?: number;
  }): Promise<{
    count: number;
    next?: string;
    previous?: string;
    results: EmailCommunication[];
  }> {
    const response = await apiClient.get('/accounts/communication/emails/', { params });
    return response.data;
  }

  // Teacher Onboarding Progress
  async getOnboardingProgress(teacherId?: number): Promise<TeacherOnboardingProgress> {
    const endpoint = teacherId
      ? `/communication/onboarding/${teacherId}/`
      : '/communication/onboarding/me/';
    const response = await apiClient.get(endpoint);
    return response.data;
  }

  async updateOnboardingProgress(
    step: number,
    data?: Record<string, any>,
  ): Promise<TeacherOnboardingProgress> {
    const response = await apiClient.patch('/communication/onboarding/me/', {
      current_step: step,
      step_data: data,
    });
    return response.data;
  }

  async markMilestoneAchieved(milestone: string): Promise<TeacherOnboardingProgress> {
    const response = await apiClient.post('/communication/onboarding/milestone/', {
      milestone,
    });
    return response.data;
  }

  // FAQ System
  async getFAQs(params?: {
    category?: string;
    search?: string;
    is_active?: boolean;
  }): Promise<FAQ[]> {
    const response = await apiClient.get('/communication/faqs/', { params });
    return response.data;
  }

  async getFAQCategories(): Promise<FAQCategory[]> {
    const response = await apiClient.get('/communication/faq-categories/');
    return response.data;
  }

  async searchFAQs(query: string): Promise<FAQ[]> {
    const response = await apiClient.get('/communication/faqs/search/', {
      params: { q: query },
    });
    return response.data;
  }

  async markFAQHelpful(faqId: number, helpful: boolean): Promise<{ success: boolean }> {
    const response = await apiClient.post(`/communication/faqs/${faqId}/helpful/`, {
      helpful,
    });
    return response.data;
  }

  async getContextualFAQs(context: string, step?: number): Promise<FAQ[]> {
    const response = await apiClient.get('/communication/faqs/contextual/', {
      params: { context, step },
    });
    return response.data;
  }

  // Admin FAQ Management
  async createFAQ(data: {
    question: string;
    answer: string;
    category: string;
    tags?: string[];
    order?: number;
  }): Promise<FAQ> {
    const response = await apiClient.post('/communication/admin/faqs/', data);
    return response.data;
  }

  async updateFAQ(
    id: number,
    data: Partial<{
      question: string;
      answer: string;
      category: string;
      tags: string[];
      order: number;
      is_active: boolean;
    }>,
  ): Promise<FAQ> {
    const response = await apiClient.patch(`/communication/admin/faqs/${id}/`, data);
    return response.data;
  }

  async deleteFAQ(id: number): Promise<void> {
    await apiClient.delete(`/communication/admin/faqs/${id}/`);
  }

  // Template Variables
  async getAvailableVariables(): Promise<{
    default_variables: Record<string, string>;
    school_variables: Record<string, string>;
    teacher_variables: Record<string, string>;
    invitation_variables: Record<string, string>;
  }> {
    const response = await apiClient.get('/accounts/communication/template-variables/');
    return response.data;
  }

  async validateTemplate(templateContent: {
    subject_template: string;
    html_content: string;
    text_content: string;
  }): Promise<{
    is_valid: boolean;
    errors: string[];
    warnings: string[];
    variables_used: string[];
    missing_variables: string[];
  }> {
    const response = await apiClient.post(
      '/accounts/communication/templates/validate/',
      templateContent,
    );
    return response.data;
  }
}

export default new CommunicationApi();
