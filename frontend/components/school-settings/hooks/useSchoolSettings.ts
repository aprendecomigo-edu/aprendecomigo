import { useState, useEffect, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Alert } from 'react-native';

import type {
  ComprehensiveSchoolSettings,
  EducationalSystem,
  SchoolSettingsFormData,
  SectionKey,
} from '../types';
import { schoolSettingsSchema } from '../validation';

export interface UseSchoolSettingsProps {
  initialData?: ComprehensiveSchoolSettings;
  educationalSystems?: EducationalSystem[];
  onSave: (data: SchoolSettingsFormData) => Promise<void>;
}

export const useSchoolSettings = ({
  initialData,
  educationalSystems = [],
  onSave,
}: UseSchoolSettingsProps) => {
  const [activeSection, setActiveSection] = useState<SectionKey>('profile');
  const [selectedEducationalSystem, setSelectedEducationalSystem] =
    useState<EducationalSystem | null>(null);

  const form = useForm<SchoolSettingsFormData>({
    resolver: zodResolver(schoolSettingsSchema),
    defaultValues: {
      school_profile: {
        name: initialData?.school_profile?.name || '',
        description: initialData?.school_profile?.description || '',
        address: initialData?.school_profile?.address || '',
        contact_email: initialData?.school_profile?.contact_email || '',
        phone_number: initialData?.school_profile?.phone_number || '',
        website: initialData?.school_profile?.website || '',
        primary_color: initialData?.school_profile?.primary_color || '#3B82F6',
        secondary_color: initialData?.school_profile?.secondary_color || '#1F2937',
        email_domain: initialData?.school_profile?.email_domain || '',
      },
      settings: {
        educational_system: initialData?.settings?.educational_system || 1,
        grade_levels: initialData?.settings?.grade_levels || [],
        trial_cost_absorption: initialData?.settings?.trial_cost_absorption || 'school',
        default_session_duration: initialData?.settings?.default_session_duration || 60,
        timezone: initialData?.settings?.timezone || 'UTC',
        billing_contact_name: initialData?.settings?.billing_contact_name || '',
        billing_contact_email: initialData?.settings?.billing_contact_email || '',
        billing_address: initialData?.settings?.billing_address || '',
        tax_id: initialData?.settings?.tax_id || '',
        currency_code: initialData?.settings?.currency_code || 'EUR',
        language: initialData?.settings?.language || 'pt',
        working_hours_start: initialData?.settings?.working_hours_start || '08:00',
        working_hours_end: initialData?.settings?.working_hours_end || '18:00',
        working_days: initialData?.settings?.working_days || [0, 1, 2, 3, 4],
        email_notifications_enabled: initialData?.settings?.email_notifications_enabled ?? true,
        sms_notifications_enabled: initialData?.settings?.sms_notifications_enabled ?? false,
        allow_student_self_enrollment:
          initialData?.settings?.allow_student_self_enrollment ?? false,
        require_parent_approval: initialData?.settings?.require_parent_approval ?? true,
        auto_assign_teachers: initialData?.settings?.auto_assign_teachers ?? false,
        class_reminder_hours: initialData?.settings?.class_reminder_hours || 24,
        enable_calendar_integration: initialData?.settings?.enable_calendar_integration ?? false,
        calendar_integration_type: initialData?.settings?.calendar_integration_type || '',
        enable_email_integration: initialData?.settings?.enable_email_integration ?? false,
        email_integration_provider: initialData?.settings?.email_integration_provider || '',
        data_retention_policy: initialData?.settings?.data_retention_policy || '2_years',
        gdpr_compliance_enabled: initialData?.settings?.gdpr_compliance_enabled ?? true,
        allow_data_export: initialData?.settings?.allow_data_export ?? true,
        require_data_processing_consent:
          initialData?.settings?.require_data_processing_consent ?? true,
        dashboard_refresh_interval: initialData?.settings?.dashboard_refresh_interval || 30,
        activity_retention_days: initialData?.settings?.activity_retention_days || 90,
      },
    },
  });

  const watchedEducationalSystem = form.watch('settings.educational_system');
  const watchedEnableCalendar = form.watch('settings.enable_calendar_integration');
  const watchedEnableEmail = form.watch('settings.enable_email_integration');

  // Update selected educational system when form value changes
  useEffect(() => {
    const system = educationalSystems.find(s => s.id === watchedEducationalSystem);
    setSelectedEducationalSystem(system || null);
  }, [watchedEducationalSystem, educationalSystems]);

  const handleSubmit = useCallback(
    async (data: SchoolSettingsFormData) => {
      try {
        await onSave(data);
      } catch (error) {
        console.error('Error saving school settings:', error);
        Alert.alert('Error', 'Failed to save school settings. Please try again.');
      }
    },
    [onSave],
  );

  return {
    // Form state
    form,

    // Section navigation
    activeSection,
    setActiveSection,

    // Educational system
    selectedEducationalSystem,

    // Watched values for conditional rendering
    watchedEnableCalendar,
    watchedEnableEmail,

    // Form submission
    handleSubmit,

    // Computed state
    isSubmitting: form.formState.isSubmitting,
    errors: form.formState.errors,
  };
};
