/**
 * Type definitions for School Settings components
 */

export interface SchoolProfile {
  id: number;
  name: string;
  description: string;
  address: string;
  contact_email: string;
  phone_number: string;
  website: string;
  logo?: string;
  logo_url?: string;
  primary_color: string;
  secondary_color: string;
  email_domain: string;
}

export interface SchoolSettings {
  // Educational system configuration
  educational_system: number;
  educational_system_name?: string;
  grade_levels: string[];
  grade_levels_display?: string[];

  // Operational settings
  trial_cost_absorption: 'school' | 'teacher' | 'split';
  default_session_duration: number;
  timezone: string;

  // Billing configuration
  billing_contact_name: string;
  billing_contact_email: string;
  billing_address: string;
  tax_id: string;
  currency_code: 'EUR' | 'USD' | 'BRL' | 'GBP';
  currency_display?: string;

  // Localization
  language: 'pt' | 'en' | 'es' | 'fr';
  language_display?: string;

  // Schedule and availability
  working_hours_start: string;
  working_hours_end: string;
  working_days: number[];
  working_days_display?: string[];

  // Communication preferences
  email_notifications_enabled: boolean;
  sms_notifications_enabled: boolean;

  // User permissions and access control
  allow_student_self_enrollment: boolean;
  require_parent_approval: boolean;
  auto_assign_teachers: boolean;
  class_reminder_hours: number;

  // Integration settings
  enable_calendar_integration: boolean;
  calendar_integration_type: 'google' | 'outlook' | 'caldav' | '';
  enable_email_integration: boolean;
  email_integration_provider: 'gmail' | 'outlook' | 'custom' | '';

  // Privacy and data handling
  data_retention_policy: '1_year' | '2_years' | '5_years' | 'indefinite';
  gdpr_compliance_enabled: boolean;
  allow_data_export: boolean;
  require_data_processing_consent: boolean;

  // Dashboard preferences
  dashboard_refresh_interval: number;
  activity_retention_days: number;
}

export interface ComprehensiveSchoolSettings {
  school_profile: SchoolProfile;
  settings: SchoolSettings;
}

export interface EducationalSystem {
  id: number;
  name: string;
  code: string;
  description: string;
  school_year_choices: [string, string][];
  education_level_choices: [string, string][];
}

export interface SchoolSettingsFormProps {
  schoolId: number;
  initialData?: ComprehensiveSchoolSettings;
  educationalSystems?: EducationalSystem[];
  onSave: (data: SchoolSettingsFormData) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

// This will be re-exported from validation.ts
export type { SchoolSettingsFormData } from './validation';

// Section types for navigation
export type SectionKey =
  | 'profile'
  | 'educational'
  | 'operational'
  | 'billing'
  | 'schedule'
  | 'communication'
  | 'permissions'
  | 'integrations'
  | 'privacy';

export interface Section {
  key: SectionKey;
  label: string;
}
