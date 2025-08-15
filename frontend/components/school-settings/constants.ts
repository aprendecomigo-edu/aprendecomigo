/**
 * Constants for School Settings components
 */
import type { Section } from './types';

export const CURRENCY_OPTIONS = [
  { value: 'EUR', label: 'Euro (€)' },
  { value: 'USD', label: 'US Dollar ($)' },
  { value: 'BRL', label: 'Brazilian Real (R$)' },
  { value: 'GBP', label: 'British Pound (£)' },
] as const;

export const LANGUAGE_OPTIONS = [
  { value: 'pt', label: 'Portuguese' },
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
] as const;

export const TRIAL_COST_OPTIONS = [
  { value: 'school', label: 'School absorbs cost' },
  { value: 'teacher', label: 'Teacher absorbs cost' },
  { value: 'split', label: 'Split cost 50/50' },
] as const;

export const DATA_RETENTION_OPTIONS = [
  { value: '1_year', label: '1 Year' },
  { value: '2_years', label: '2 Years' },
  { value: '5_years', label: '5 Years' },
  { value: 'indefinite', label: 'Indefinite' },
] as const;

export const WEEKDAYS = [
  { value: 0, label: 'Monday' },
  { value: 1, label: 'Tuesday' },
  { value: 2, label: 'Wednesday' },
  { value: 3, label: 'Thursday' },
  { value: 4, label: 'Friday' },
  { value: 5, label: 'Saturday' },
  { value: 6, label: 'Sunday' },
] as const;

export const CALENDAR_PROVIDERS = [
  { value: 'google', label: 'Google Calendar' },
  { value: 'outlook', label: 'Microsoft Outlook' },
  { value: 'caldav', label: 'CalDAV' },
] as const;

export const EMAIL_PROVIDERS = [
  { value: 'gmail', label: 'Gmail' },
  { value: 'outlook', label: 'Microsoft Outlook' },
  { value: 'custom', label: 'Custom SMTP' },
] as const;

export const SECTIONS: Section[] = [
  { key: 'profile', label: 'Profile' },
  { key: 'educational', label: 'Education' },
  { key: 'operational', label: 'Operational' },
  { key: 'billing', label: 'Billing' },
  { key: 'schedule', label: 'Schedule' },
  { key: 'communication', label: 'Communication' },
  { key: 'permissions', label: 'Permissions' },
  { key: 'integrations', label: 'Integrations' },
  { key: 'privacy', label: 'Privacy' },
] as const;