import { useState, useEffect, useCallback } from 'react';
import { Alert } from 'react-native';

import { apiClient } from '../api/apiClient';

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
  created_at: string;
  updated_at: string;
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

  // Timestamps
  created_at?: string;
  updated_at?: string;
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
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SchoolSettingsFormData {
  school_profile: Partial<SchoolProfile>;
  settings: Partial<SchoolSettings>;
}

interface UseSchoolSettingsReturn {
  // State
  schoolSettings: ComprehensiveSchoolSettings | null;
  educationalSystems: EducationalSystem[];
  loading: boolean;
  saving: boolean;
  error: string | null;

  // Actions
  fetchSchoolSettings: (schoolId: number) => Promise<void>;
  fetchEducationalSystems: (schoolId: number) => Promise<void>;
  updateSchoolSettings: (schoolId: number, data: SchoolSettingsFormData) => Promise<void>;
  uploadSchoolLogo: (schoolId: number, logoFile: File | any) => Promise<void>;
  refreshSettings: () => Promise<void>;
  clearError: () => void;
}

export const useSchoolSettings = (): UseSchoolSettingsReturn => {
  const [schoolSettings, setSchoolSettings] = useState<ComprehensiveSchoolSettings | null>(null);
  const [educationalSystems, setEducationalSystems] = useState<EducationalSystem[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentSchoolId, setCurrentSchoolId] = useState<number | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const fetchSchoolSettings = useCallback(async (schoolId: number) => {
    try {
      setLoading(true);
      setError(null);
      setCurrentSchoolId(schoolId);

      const response = await apiClient.get(`/api/accounts/schools/${schoolId}/settings/`);

      if (response.status === 200) {
        setSchoolSettings(response.data);
      } else {
        throw new Error('Failed to fetch school settings');
      }
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || 'Failed to fetch school settings';
      setError(errorMessage);
      console.error('Error fetching school settings:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchEducationalSystems = useCallback(async (schoolId: number) => {
    try {
      const response = await apiClient.get(
        `/api/accounts/schools/${schoolId}/settings/educational-systems/`
      );

      if (response.status === 200) {
        setEducationalSystems(response.data);
      } else {
        throw new Error('Failed to fetch educational systems');
      }
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || 'Failed to fetch educational systems';
      console.error('Error fetching educational systems:', err);
      // Don't set error state for this as it's not critical
    }
  }, []);

  const updateSchoolSettings = useCallback(
    async (schoolId: number, data: SchoolSettingsFormData) => {
      try {
        setSaving(true);
        setError(null);

        const response = await apiClient.patch(`/api/accounts/schools/${schoolId}/settings/`, data);

        if (response.status === 200) {
          setSchoolSettings(response.data);
          Alert.alert('Success', 'School settings updated successfully');
        } else {
          throw new Error('Failed to update school settings');
        }
      } catch (err: any) {
        const errorMessage =
          err.response?.data?.detail ||
          err.response?.data?.message ||
          err.message ||
          'Failed to update school settings';
        setError(errorMessage);

        // Show validation errors if available
        if (err.response?.data?.errors) {
          const validationErrors = Object.entries(err.response.data.errors)
            .map(
              ([field, messages]) =>
                `${field}: ${Array.isArray(messages) ? messages.join(', ') : messages}`
            )
            .join('\n');
          Alert.alert('Validation Error', validationErrors);
        } else {
          Alert.alert('Error', errorMessage);
        }

        throw err; // Re-throw to allow form to handle the error
      } finally {
        setSaving(false);
      }
    },
    []
  );

  const uploadSchoolLogo = useCallback(
    async (schoolId: number, logoFile: File | any) => {
      try {
        setSaving(true);
        setError(null);

        const formData = new FormData();
        formData.append('logo', logoFile);

        const response = await apiClient.post(
          `/api/accounts/schools/${schoolId}/settings/logo-upload/`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );

        if (response.status === 200) {
          // Update the school profile with the new logo URL
          if (schoolSettings) {
            setSchoolSettings({
              ...schoolSettings,
              school_profile: {
                ...schoolSettings.school_profile,
                logo: response.data.logo,
                logo_url: response.data.logo_url,
              },
            });
          }
          Alert.alert('Success', 'School logo uploaded successfully');
        } else {
          throw new Error('Failed to upload school logo');
        }
      } catch (err: any) {
        const errorMessage =
          err.response?.data?.error ||
          err.response?.data?.detail ||
          err.message ||
          'Failed to upload school logo';
        setError(errorMessage);
        Alert.alert('Error', errorMessage);
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [schoolSettings]
  );

  const refreshSettings = useCallback(async () => {
    if (currentSchoolId) {
      // Use Promise.allSettled for graceful degradation
      const results = await Promise.allSettled([
        fetchSchoolSettings(currentSchoolId),
        fetchEducationalSystems(currentSchoolId),
      ]);

      // Log any failures for monitoring
      const operations = ['school settings', 'educational systems'];
      results.forEach((result, index) => {
        if (result.status === 'rejected') {
          console.error(`Failed to refresh ${operations[index]}:`, result.reason);
        }
      });

      // School settings is critical, educational systems is optional
      // Individual error handling is done in the respective functions
    }
  }, [currentSchoolId, fetchSchoolSettings, fetchEducationalSystems]);

  // Auto-fetch educational systems when school settings are loaded
  useEffect(() => {
    if (schoolSettings && currentSchoolId && educationalSystems.length === 0) {
      fetchEducationalSystems(currentSchoolId);
    }
  }, [schoolSettings, currentSchoolId, educationalSystems.length, fetchEducationalSystems]);

  return {
    // State
    schoolSettings,
    educationalSystems,
    loading,
    saving,
    error,

    // Actions
    fetchSchoolSettings,
    fetchEducationalSystems,
    updateSchoolSettings,
    uploadSchoolLogo,
    refreshSettings,
    clearError,
  };
};
