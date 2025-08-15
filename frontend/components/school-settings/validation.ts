import { z } from 'zod';

/**
 * Validation schema for School Settings form
 */
export const schoolSettingsSchema = z.object({
  // School profile
  school_profile: z.object({
    name: z.string().min(1, 'School name is required').max(150, 'Name too long'),
    description: z.string(),
    address: z.string(),
    contact_email: z.string().email('Invalid email address').or(z.literal('')),
    phone_number: z.string(),
    website: z.string().url('Invalid URL').or(z.literal('')),
    primary_color: z
      .string()
      .regex(/^#[0-9A-Fa-f]{6}$/, 'Invalid hex color')
      .or(z.literal('')),
    secondary_color: z
      .string()
      .regex(/^#[0-9A-Fa-f]{6}$/, 'Invalid hex color')
      .or(z.literal('')),
    email_domain: z.string(),
  }),

  // Settings
  settings: z
    .object({
      educational_system: z.number().min(1, 'Educational system is required'),
      grade_levels: z.array(z.string()),
      trial_cost_absorption: z.enum(['school', 'teacher', 'split']),
      default_session_duration: z
        .number()
        .min(15, 'Minimum 15 minutes')
        .max(480, 'Maximum 8 hours'),
      timezone: z.string().min(1, 'Timezone is required'),

      // Billing
      billing_contact_name: z.string(),
      billing_contact_email: z.string().email('Invalid email').or(z.literal('')),
      billing_address: z.string(),
      tax_id: z.string(),
      currency_code: z.enum(['EUR', 'USD', 'BRL', 'GBP']),
      language: z.enum(['pt', 'en', 'es', 'fr']),

      // Schedule
      working_hours_start: z
        .string()
        .regex(/^([01]?[0-9]|2[0-3]):[0-5][0-9]$/, 'Invalid time format'),
      working_hours_end: z
        .string()
        .regex(/^([01]?[0-9]|2[0-3]):[0-5][0-9]$/, 'Invalid time format'),
      working_days: z.array(z.number().min(0).max(6)),

      // Booleans
      email_notifications_enabled: z.boolean(),
      sms_notifications_enabled: z.boolean(),
      allow_student_self_enrollment: z.boolean(),
      require_parent_approval: z.boolean(),
      auto_assign_teachers: z.boolean(),
      enable_calendar_integration: z.boolean(),
      calendar_integration_type: z.enum(['google', 'outlook', 'caldav', '']),
      enable_email_integration: z.boolean(),
      email_integration_provider: z.enum(['gmail', 'outlook', 'custom', '']),
      gdpr_compliance_enabled: z.boolean(),
      allow_data_export: z.boolean(),
      require_data_processing_consent: z.boolean(),

      // Numbers
      class_reminder_hours: z.number().min(1, 'Minimum 1 hour').max(168, 'Maximum 1 week'),
      dashboard_refresh_interval: z
        .number()
        .min(5, 'Minimum 5 seconds')
        .max(300, 'Maximum 5 minutes'),
      activity_retention_days: z.number().min(30, 'Minimum 30 days').max(365, 'Maximum 1 year'),

      data_retention_policy: z.enum(['1_year', '2_years', '5_years', 'indefinite']),
    })
    .refine(
      data => {
        // Validate working hours
        if (data.working_hours_start >= data.working_hours_end) {
          return false;
        }
        return true;
      },
      {
        message: 'End time must be after start time',
        path: ['working_hours_end'],
      }
    )
    .refine(
      data => {
        // Validate integration settings
        if (data.enable_calendar_integration && !data.calendar_integration_type) {
          return false;
        }
        if (data.enable_email_integration && !data.email_integration_provider) {
          return false;
        }
        return true;
      },
      {
        message: 'Integration type is required when integration is enabled',
        path: ['calendar_integration_type'],
      }
    ),
});

export type SchoolSettingsFormData = z.infer<typeof schoolSettingsSchema>;