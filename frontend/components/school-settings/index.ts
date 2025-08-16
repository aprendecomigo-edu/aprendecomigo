/**
 * School Settings module exports
 *
 * This module provides a refactored school settings form that has been
 * broken down from a monolithic 1513-line component into focused,
 * maintainable pieces.
 */

// Main component
export { SchoolSettingsForm } from './SchoolSettingsForm';

// Types
export type {
  SchoolSettingsFormProps,
  SchoolProfile,
  SchoolSettings,
  ComprehensiveSchoolSettings,
  EducationalSystem,
  SchoolSettingsFormData,
  SectionKey,
  Section,
} from './types';

// Constants
export {
  CURRENCY_OPTIONS,
  LANGUAGE_OPTIONS,
  TRIAL_COST_OPTIONS,
  DATA_RETENTION_OPTIONS,
  WEEKDAYS,
  CALENDAR_PROVIDERS,
  EMAIL_PROVIDERS,
  SECTIONS,
} from './constants';

// Hook
export { useSchoolSettings } from './hooks/useSchoolSettings';

// Validation
export { schoolSettingsSchema } from './validation';
