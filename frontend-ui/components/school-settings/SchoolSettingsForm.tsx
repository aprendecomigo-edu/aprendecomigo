import { zodResolver } from '@hookform/resolvers/zod';
import React, { useState, useEffect } from 'react';
import { useForm, Controller, useFieldArray } from 'react-hook-form';
import { View, ScrollView, Alert } from 'react-native';
import { z } from 'zod';

import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Divider } from '@/components/ui/divider';
import {
  FormControl,
  FormControlLabel,
  FormControlHelper,
  FormControlError,
  FormControlErrorIcon,
  FormControlErrorText,
} from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon, AlertCircleIcon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import {
  Select,
  SelectTrigger,
  SelectInput,
  SelectPortal,
  SelectBackdrop,
  SelectContent,
  SelectDragIndicatorWrapper,
  SelectDragIndicator,
  SelectItem,
} from '@/components/ui/select';
import { Spinner } from '@/components/ui/spinner';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';

// Types for school settings
interface SchoolProfile {
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

interface SchoolSettings {
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

interface ComprehensiveSchoolSettings {
  school_profile: SchoolProfile;
  settings: SchoolSettings;
}

interface EducationalSystem {
  id: number;
  name: string;
  code: string;
  description: string;
  school_year_choices: [string, string][];
  education_level_choices: [string, string][];
}

// Validation schema
const schoolSettingsSchema = z.object({
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

type SchoolSettingsFormData = z.infer<typeof schoolSettingsSchema>;

interface SchoolSettingsFormProps {
  schoolId: number;
  initialData?: ComprehensiveSchoolSettings;
  educationalSystems?: EducationalSystem[];
  onSave: (data: SchoolSettingsFormData) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

const CURRENCY_OPTIONS = [
  { value: 'EUR', label: 'Euro (€)' },
  { value: 'USD', label: 'US Dollar ($)' },
  { value: 'BRL', label: 'Brazilian Real (R$)' },
  { value: 'GBP', label: 'British Pound (£)' },
];

const LANGUAGE_OPTIONS = [
  { value: 'pt', label: 'Portuguese' },
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
];

const TRIAL_COST_OPTIONS = [
  { value: 'school', label: 'School absorbs cost' },
  { value: 'teacher', label: 'Teacher absorbs cost' },
  { value: 'split', label: 'Split cost 50/50' },
];

const DATA_RETENTION_OPTIONS = [
  { value: '1_year', label: '1 Year' },
  { value: '2_years', label: '2 Years' },
  { value: '5_years', label: '5 Years' },
  { value: 'indefinite', label: 'Indefinite' },
];

const WEEKDAYS = [
  { value: 0, label: 'Monday' },
  { value: 1, label: 'Tuesday' },
  { value: 2, label: 'Wednesday' },
  { value: 3, label: 'Thursday' },
  { value: 4, label: 'Friday' },
  { value: 5, label: 'Saturday' },
  { value: 6, label: 'Sunday' },
];

export const SchoolSettingsForm: React.FC<SchoolSettingsFormProps> = ({
  schoolId,
  initialData,
  educationalSystems = [],
  onSave,
  onCancel,
  loading = false,
}) => {
  const [activeSection, setActiveSection] = useState<string>('profile');
  const [selectedEducationalSystem, setSelectedEducationalSystem] =
    useState<EducationalSystem | null>(null);

  const {
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<SchoolSettingsFormData>({
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

  const watchedEducationalSystem = watch('settings.educational_system');
  const watchedEnableCalendar = watch('settings.enable_calendar_integration');
  const watchedEnableEmail = watch('settings.enable_email_integration');

  useEffect(() => {
    const system = educationalSystems.find(s => s.id === watchedEducationalSystem);
    setSelectedEducationalSystem(system || null);
  }, [watchedEducationalSystem, educationalSystems]);

  const onSubmit = async (data: SchoolSettingsFormData) => {
    try {
      await onSave(data);
    } catch (error) {
      console.error('Error saving school settings:', error);
      Alert.alert('Error', 'Failed to save school settings. Please try again.');
    }
  };

  const renderSectionButtons = () => (
    <VStack space="sm" className="mb-4">
      <Text size="sm" className="text-typography-600 font-medium">
        Configuration Sections
      </Text>
      <HStack space="sm" flexWrap="wrap">
        {[
          { key: 'profile', label: 'Profile' },
          { key: 'educational', label: 'Education' },
          { key: 'operational', label: 'Operational' },
          { key: 'billing', label: 'Billing' },
          { key: 'schedule', label: 'Schedule' },
          { key: 'communication', label: 'Communication' },
          { key: 'permissions', label: 'Permissions' },
          { key: 'integrations', label: 'Integrations' },
          { key: 'privacy', label: 'Privacy' },
        ].map(section => (
          <Button
            key={section.key}
            size="sm"
            variant={activeSection === section.key ? 'solid' : 'outline'}
            action={activeSection === section.key ? 'primary' : 'secondary'}
            onPress={() => setActiveSection(section.key)}
            className="mb-2"
          >
            <ButtonText size="sm">{section.label}</ButtonText>
          </Button>
        ))}
      </HStack>
    </VStack>
  );

  const renderProfileSection = () => (
    <VStack space="md">
      <Heading size="lg">School Profile</Heading>

      <Controller
        control={control}
        name="school_profile.name"
        render={({ field: { onChange, onBlur, value } }) => (
          <FormControl isInvalid={!!errors.school_profile?.name}>
            <FormControlLabel>
              <Text>School Name *</Text>
            </FormControlLabel>
            <Input>
              <InputField
                placeholder="Enter school name"
                onBlur={onBlur}
                onChangeText={onChange}
                value={value}
              />
            </Input>
            <FormControlError>
              <FormControlErrorIcon as={AlertCircleIcon} />
              <FormControlErrorText>{errors.school_profile?.name?.message}</FormControlErrorText>
            </FormControlError>
          </FormControl>
        )}
      />

      <Controller
        control={control}
        name="school_profile.description"
        render={({ field: { onChange, onBlur, value } }) => (
          <FormControl>
            <FormControlLabel>
              <Text>Description</Text>
            </FormControlLabel>
            <Textarea>
              <TextareaInput
                placeholder="Brief description of your school"
                onBlur={onBlur}
                onChangeText={onChange}
                value={value}
              />
            </Textarea>
          </FormControl>
        )}
      />

      <Controller
        control={control}
        name="school_profile.address"
        render={({ field: { onChange, onBlur, value } }) => (
          <FormControl>
            <FormControlLabel>
              <Text>Address</Text>
            </FormControlLabel>
            <Textarea>
              <TextareaInput
                placeholder="School address"
                onBlur={onBlur}
                onChangeText={onChange}
                value={value}
              />
            </Textarea>
          </FormControl>
        )}
      />

      <VStack space="md" className="md:flex-row md:space-x-4 md:space-y-0">
        <Box className="flex-1">
          <Controller
            control={control}
            name="school_profile.contact_email"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl isInvalid={!!errors.school_profile?.contact_email}>
                <FormControlLabel>
                  <Text>Contact Email</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="contact@school.com"
                    onBlur={onBlur}
                    onChangeText={onChange}
                    value={value}
                    keyboardType="email-address"
                  />
                </Input>
                <FormControlError>
                  <FormControlErrorIcon as={AlertCircleIcon} />
                  <FormControlErrorText>
                    {errors.school_profile?.contact_email?.message}
                  </FormControlErrorText>
                </FormControlError>
              </FormControl>
            )}
          />
        </Box>

        <Box className="flex-1">
          <Controller
            control={control}
            name="school_profile.phone_number"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl>
                <FormControlLabel>
                  <Text>Phone Number</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="+351 123 456 789"
                    onBlur={onBlur}
                    onChangeText={onChange}
                    value={value}
                    keyboardType="phone-pad"
                  />
                </Input>
              </FormControl>
            )}
          />
        </Box>
      </VStack>

      <Controller
        control={control}
        name="school_profile.website"
        render={({ field: { onChange, onBlur, value } }) => (
          <FormControl isInvalid={!!errors.school_profile?.website}>
            <FormControlLabel>
              <Text>Website</Text>
            </FormControlLabel>
            <Input>
              <InputField
                placeholder="https://www.school.com"
                onBlur={onBlur}
                onChangeText={onChange}
                value={value}
                keyboardType="url"
              />
            </Input>
            <FormControlError>
              <FormControlErrorIcon as={AlertCircleIcon} />
              <FormControlErrorText>{errors.school_profile?.website?.message}</FormControlErrorText>
            </FormControlError>
          </FormControl>
        )}
      />

      <VStack space="md" className="md:flex-row md:space-x-4 md:space-y-0">
        <Box className="flex-1">
          <Controller
            control={control}
            name="school_profile.primary_color"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl isInvalid={!!errors.school_profile?.primary_color}>
                <FormControlLabel>
                  <Text>Primary Color</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="#3B82F6"
                    onBlur={onBlur}
                    onChangeText={onChange}
                    value={value}
                  />
                </Input>
                <FormControlHelper>
                  <Text size="sm">Hex color code (e.g., #3B82F6)</Text>
                </FormControlHelper>
                <FormControlError>
                  <FormControlErrorIcon as={AlertCircleIcon} />
                  <FormControlErrorText>
                    {errors.school_profile?.primary_color?.message}
                  </FormControlErrorText>
                </FormControlError>
              </FormControl>
            )}
          />
        </Box>

        <Box className="flex-1">
          <Controller
            control={control}
            name="school_profile.secondary_color"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl isInvalid={!!errors.school_profile?.secondary_color}>
                <FormControlLabel>
                  <Text>Secondary Color</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="#1F2937"
                    onBlur={onBlur}
                    onChangeText={onChange}
                    value={value}
                  />
                </Input>
                <FormControlHelper>
                  <Text size="sm">Hex color code (e.g., #1F2937)</Text>
                </FormControlHelper>
                <FormControlError>
                  <FormControlErrorIcon as={AlertCircleIcon} />
                  <FormControlErrorText>
                    {errors.school_profile?.secondary_color?.message}
                  </FormControlErrorText>
                </FormControlError>
              </FormControl>
            )}
          />
        </Box>
      </VStack>
    </VStack>
  );

  const renderEducationalSection = () => (
    <VStack space="md">
      <Heading size="lg">Educational System</Heading>

      <Controller
        control={control}
        name="settings.educational_system"
        render={({ field: { onChange, value } }) => (
          <FormControl isInvalid={!!errors.settings?.educational_system}>
            <FormControlLabel>
              <Text>Educational System *</Text>
            </FormControlLabel>
            <Select onValueChange={val => onChange(parseInt(val))} selectedValue={value.toString()}>
              <SelectTrigger>
                <SelectInput placeholder="Select educational system" />
              </SelectTrigger>
              <SelectPortal>
                <SelectBackdrop />
                <SelectContent>
                  <SelectDragIndicatorWrapper>
                    <SelectDragIndicator />
                  </SelectDragIndicatorWrapper>
                  {educationalSystems.map(system => (
                    <SelectItem key={system.id} label={system.name} value={system.id.toString()} />
                  ))}
                </SelectContent>
              </SelectPortal>
            </Select>
            <FormControlHelper>
              <Text size="sm">
                {selectedEducationalSystem?.description ||
                  'Choose the educational system used by your school'}
              </Text>
            </FormControlHelper>
            <FormControlError>
              <FormControlErrorIcon as={AlertCircleIcon} />
              <FormControlErrorText>
                {errors.settings?.educational_system?.message}
              </FormControlErrorText>
            </FormControlError>
          </FormControl>
        )}
      />

      {selectedEducationalSystem && (
        <Controller
          control={control}
          name="settings.grade_levels"
          render={({ field: { onChange, value } }) => (
            <FormControl>
              <FormControlLabel>
                <Text>Grade Levels Offered</Text>
              </FormControlLabel>
              <VStack space="sm">
                {selectedEducationalSystem.school_year_choices.map(([key, label]) => (
                  <HStack key={key} space="sm" alignItems="center">
                    <Switch
                      value={value.includes(key)}
                      onValueChange={checked => {
                        if (checked) {
                          onChange([...value, key]);
                        } else {
                          onChange(value.filter(level => level !== key));
                        }
                      }}
                    />
                    <Text flex={1}>{label}</Text>
                  </HStack>
                ))}
              </VStack>
              <FormControlHelper>
                <Text size="sm">Select all grade levels your school offers</Text>
              </FormControlHelper>
            </FormControl>
          )}
        />
      )}
    </VStack>
  );

  const renderOperationalSection = () => (
    <VStack space="md">
      <Heading size="lg">Operational Settings</Heading>

      <Controller
        control={control}
        name="settings.trial_cost_absorption"
        render={({ field: { onChange, value } }) => (
          <FormControl>
            <FormControlLabel>
              <Text>Trial Session Cost Absorption</Text>
            </FormControlLabel>
            <Select onValueChange={onChange} selectedValue={value}>
              <SelectTrigger>
                <SelectInput placeholder="Who absorbs trial session costs?" />
              </SelectTrigger>
              <SelectPortal>
                <SelectBackdrop />
                <SelectContent>
                  <SelectDragIndicatorWrapper>
                    <SelectDragIndicator />
                  </SelectDragIndicatorWrapper>
                  {TRIAL_COST_OPTIONS.map(option => (
                    <SelectItem key={option.value} label={option.label} value={option.value} />
                  ))}
                </SelectContent>
              </SelectPortal>
            </Select>
            <FormControlHelper>
              <Text size="sm">
                Determines who pays for trial sessions when students try the platform
              </Text>
            </FormControlHelper>
          </FormControl>
        )}
      />

      <VStack space="md" className="md:flex-row md:space-x-4 md:space-y-0">
        <Box className="flex-1">
          <Controller
            control={control}
            name="settings.default_session_duration"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl isInvalid={!!errors.settings?.default_session_duration}>
                <FormControlLabel>
                  <Text>Default Session Duration (minutes)</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="60"
                    onBlur={onBlur}
                    onChangeText={text => onChange(parseInt(text) || 60)}
                    value={value.toString()}
                    keyboardType="numeric"
                  />
                </Input>
                <FormControlHelper>
                  <Text size="sm">Default length for new sessions</Text>
                </FormControlHelper>
                <FormControlError>
                  <FormControlErrorIcon as={AlertCircleIcon} />
                  <FormControlErrorText>
                    {errors.settings?.default_session_duration?.message}
                  </FormControlErrorText>
                </FormControlError>
              </FormControl>
            )}
          />
        </Box>

        <Box className="flex-1">
          <Controller
            control={control}
            name="settings.timezone"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl isInvalid={!!errors.settings?.timezone}>
                <FormControlLabel>
                  <Text>Timezone</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="Europe/Lisbon"
                    onBlur={onBlur}
                    onChangeText={onChange}
                    value={value}
                  />
                </Input>
                <FormControlHelper>
                  <Text size="sm">School's primary timezone</Text>
                </FormControlHelper>
                <FormControlError>
                  <FormControlErrorIcon as={AlertCircleIcon} />
                  <FormControlErrorText>{errors.settings?.timezone?.message}</FormControlErrorText>
                </FormControlError>
              </FormControl>
            )}
          />
        </Box>
      </VStack>

      <VStack space="md" className="md:flex-row md:space-x-4 md:space-y-0">
        <Box className="flex-1">
          <Controller
            control={control}
            name="settings.currency_code"
            render={({ field: { onChange, value } }) => (
              <FormControl>
                <FormControlLabel>
                  <Text>Currency</Text>
                </FormControlLabel>
                <Select onValueChange={onChange} selectedValue={value}>
                  <SelectTrigger>
                    <SelectInput placeholder="Select currency" />
                  </SelectTrigger>
                  <SelectPortal>
                    <SelectBackdrop />
                    <SelectContent>
                      <SelectDragIndicatorWrapper>
                        <SelectDragIndicator />
                      </SelectDragIndicatorWrapper>
                      {CURRENCY_OPTIONS.map(option => (
                        <SelectItem key={option.value} label={option.label} value={option.value} />
                      ))}
                    </SelectContent>
                  </SelectPortal>
                </Select>
              </FormControl>
            )}
          />
        </Box>

        <Box className="flex-1">
          <Controller
            control={control}
            name="settings.language"
            render={({ field: { onChange, value } }) => (
              <FormControl>
                <FormControlLabel>
                  <Text>Language</Text>
                </FormControlLabel>
                <Select onValueChange={onChange} selectedValue={value}>
                  <SelectTrigger>
                    <SelectInput placeholder="Select language" />
                  </SelectTrigger>
                  <SelectPortal>
                    <SelectBackdrop />
                    <SelectContent>
                      <SelectDragIndicatorWrapper>
                        <SelectDragIndicator />
                      </SelectDragIndicatorWrapper>
                      {LANGUAGE_OPTIONS.map(option => (
                        <SelectItem key={option.value} label={option.label} value={option.value} />
                      ))}
                    </SelectContent>
                  </SelectPortal>
                </Select>
              </FormControl>
            )}
          />
        </Box>
      </VStack>
    </VStack>
  );

  const renderBillingSection = () => (
    <VStack space="md">
      <Heading size="lg">Billing Configuration</Heading>

      <VStack space="md" className="md:flex-row md:space-x-4 md:space-y-0">
        <Box className="flex-1">
          <Controller
            control={control}
            name="settings.billing_contact_name"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl>
                <FormControlLabel>
                  <Text>Billing Contact Name</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="John Doe"
                    onBlur={onBlur}
                    onChangeText={onChange}
                    value={value}
                  />
                </Input>
              </FormControl>
            )}
          />
        </Box>

        <Box className="flex-1">
          <Controller
            control={control}
            name="settings.billing_contact_email"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl isInvalid={!!errors.settings?.billing_contact_email}>
                <FormControlLabel>
                  <Text>Billing Contact Email</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="billing@school.com"
                    onBlur={onBlur}
                    onChangeText={onChange}
                    value={value}
                    keyboardType="email-address"
                  />
                </Input>
                <FormControlError>
                  <FormControlErrorIcon as={AlertCircleIcon} />
                  <FormControlErrorText>
                    {errors.settings?.billing_contact_email?.message}
                  </FormControlErrorText>
                </FormControlError>
              </FormControl>
            )}
          />
        </Box>
      </VStack>

      <Controller
        control={control}
        name="settings.billing_address"
        render={({ field: { onChange, onBlur, value } }) => (
          <FormControl>
            <FormControlLabel>
              <Text>Billing Address</Text>
            </FormControlLabel>
            <Textarea>
              <TextareaInput
                placeholder="Complete billing address for invoices"
                onBlur={onBlur}
                onChangeText={onChange}
                value={value}
              />
            </Textarea>
          </FormControl>
        )}
      />

      <Controller
        control={control}
        name="settings.tax_id"
        render={({ field: { onChange, onBlur, value } }) => (
          <FormControl>
            <FormControlLabel>
              <Text>Tax ID / VAT Number</Text>
            </FormControlLabel>
            <Input>
              <InputField
                placeholder="PT123456789"
                onBlur={onBlur}
                onChangeText={onChange}
                value={value}
              />
            </Input>
            <FormControlHelper>
              <Text size="sm">Tax identification number for billing purposes</Text>
            </FormControlHelper>
          </FormControl>
        )}
      />
    </VStack>
  );

  const renderScheduleSection = () => (
    <VStack space="md">
      <Heading size="lg">Schedule & Availability</Heading>

      <VStack space="md" className="md:flex-row md:space-x-4 md:space-y-0">
        <Box className="flex-1">
          <Controller
            control={control}
            name="settings.working_hours_start"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl isInvalid={!!errors.settings?.working_hours_start}>
                <FormControlLabel>
                  <Text>Working Hours Start</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="08:00"
                    onBlur={onBlur}
                    onChangeText={onChange}
                    value={value}
                  />
                </Input>
                <FormControlHelper>
                  <Text size="sm">Format: HH:MM (24-hour)</Text>
                </FormControlHelper>
                <FormControlError>
                  <FormControlErrorIcon as={AlertCircleIcon} />
                  <FormControlErrorText>
                    {errors.settings?.working_hours_start?.message}
                  </FormControlErrorText>
                </FormControlError>
              </FormControl>
            )}
          />
        </Box>

        <Box className="flex-1">
          <Controller
            control={control}
            name="settings.working_hours_end"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl isInvalid={!!errors.settings?.working_hours_end}>
                <FormControlLabel>
                  <Text>Working Hours End</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="18:00"
                    onBlur={onBlur}
                    onChangeText={onChange}
                    value={value}
                  />
                </Input>
                <FormControlHelper>
                  <Text size="sm">Format: HH:MM (24-hour)</Text>
                </FormControlHelper>
                <FormControlError>
                  <FormControlErrorIcon as={AlertCircleIcon} />
                  <FormControlErrorText>
                    {errors.settings?.working_hours_end?.message}
                  </FormControlErrorText>
                </FormControlError>
              </FormControl>
            )}
          />
        </Box>
      </VStack>

      <Controller
        control={control}
        name="settings.working_days"
        render={({ field: { onChange, value } }) => (
          <FormControl>
            <FormControlLabel>
              <Text>Working Days</Text>
            </FormControlLabel>
            <VStack space="sm">
              {WEEKDAYS.map(day => (
                <HStack key={day.value} space="sm" alignItems="center">
                  <Switch
                    value={value.includes(day.value)}
                    onValueChange={checked => {
                      if (checked) {
                        onChange([...value, day.value]);
                      } else {
                        onChange(value.filter(d => d !== day.value));
                      }
                    }}
                  />
                  <Text flex={1}>{day.label}</Text>
                </HStack>
              ))}
            </VStack>
            <FormControlHelper>
              <Text size="sm">Select the days when your school operates</Text>
            </FormControlHelper>
          </FormControl>
        )}
      />

      <Controller
        control={control}
        name="settings.class_reminder_hours"
        render={({ field: { onChange, onBlur, value } }) => (
          <FormControl isInvalid={!!errors.settings?.class_reminder_hours}>
            <FormControlLabel>
              <Text>Class Reminder Hours</Text>
            </FormControlLabel>
            <Input>
              <InputField
                placeholder="24"
                onBlur={onBlur}
                onChangeText={text => onChange(parseInt(text) || 24)}
                value={value.toString()}
                keyboardType="numeric"
              />
            </Input>
            <FormControlHelper>
              <Text size="sm">Hours before class to send reminder notifications</Text>
            </FormControlHelper>
            <FormControlError>
              <FormControlErrorIcon as={AlertCircleIcon} />
              <FormControlErrorText>
                {errors.settings?.class_reminder_hours?.message}
              </FormControlErrorText>
            </FormControlError>
          </FormControl>
        )}
      />
    </VStack>
  );

  const renderCommunicationSection = () => (
    <VStack space="md">
      <Heading size="lg">Communication Preferences</Heading>

      <Controller
        control={control}
        name="settings.email_notifications_enabled"
        render={({ field: { onChange, value } }) => (
          <HStack space="sm" alignItems="center">
            <Switch value={value} onValueChange={onChange} />
            <VStack flex={1}>
              <Text>Email Notifications</Text>
              <Text size="sm" color="$textLight600">
                Send email notifications for class reminders, updates, and announcements
              </Text>
            </VStack>
          </HStack>
        )}
      />

      <Controller
        control={control}
        name="settings.sms_notifications_enabled"
        render={({ field: { onChange, value } }) => (
          <HStack space="sm" alignItems="center">
            <Switch value={value} onValueChange={onChange} />
            <VStack flex={1}>
              <Text>SMS Notifications</Text>
              <Text size="sm" color="$textLight600">
                Send SMS notifications for urgent updates and reminders
              </Text>
            </VStack>
          </HStack>
        )}
      />
    </VStack>
  );

  const renderPermissionsSection = () => (
    <VStack space="md">
      <Heading size="lg">Permissions & Access Control</Heading>

      <Controller
        control={control}
        name="settings.allow_student_self_enrollment"
        render={({ field: { onChange, value } }) => (
          <HStack space="sm" alignItems="center">
            <Switch value={value} onValueChange={onChange} />
            <VStack flex={1}>
              <Text>Allow Student Self-Enrollment</Text>
              <Text size="sm" color="$textLight600">
                Students can enroll themselves without admin approval
              </Text>
            </VStack>
          </HStack>
        )}
      />

      <Controller
        control={control}
        name="settings.require_parent_approval"
        render={({ field: { onChange, value } }) => (
          <HStack space="sm" alignItems="center">
            <Switch value={value} onValueChange={onChange} />
            <VStack flex={1}>
              <Text>Require Parent Approval</Text>
              <Text size="sm" color="$textLight600">
                Parental consent required for student actions and enrollment
              </Text>
            </VStack>
          </HStack>
        )}
      />

      <Controller
        control={control}
        name="settings.auto_assign_teachers"
        render={({ field: { onChange, value } }) => (
          <HStack space="sm" alignItems="center">
            <Switch value={value} onValueChange={onChange} />
            <VStack flex={1}>
              <Text>Auto-Assign Teachers</Text>
              <Text size="sm" color="$textLight600">
                Automatically assign available teachers to new classes
              </Text>
            </VStack>
          </HStack>
        )}
      />
    </VStack>
  );

  const renderIntegrationsSection = () => (
    <VStack space="md">
      <Heading size="lg">Integrations</Heading>

      <VStack space="md">
        <Controller
          control={control}
          name="settings.enable_calendar_integration"
          render={({ field: { onChange, value } }) => (
            <HStack space="sm" alignItems="center">
              <Switch value={value} onValueChange={onChange} />
              <VStack flex={1}>
                <Text>Calendar Integration</Text>
                <Text size="sm" color="$textLight600">
                  Sync classes with external calendar systems
                </Text>
              </VStack>
            </HStack>
          )}
        />

        {watchedEnableCalendar && (
          <Controller
            control={control}
            name="settings.calendar_integration_type"
            render={({ field: { onChange, value } }) => (
              <FormControl isInvalid={!!errors.settings?.calendar_integration_type}>
                <FormControlLabel>
                  <Text>Calendar Provider</Text>
                </FormControlLabel>
                <Select onValueChange={onChange} selectedValue={value}>
                  <SelectTrigger>
                    <SelectInput placeholder="Select calendar provider" />
                  </SelectTrigger>
                  <SelectPortal>
                    <SelectBackdrop />
                    <SelectContent>
                      <SelectDragIndicatorWrapper>
                        <SelectDragIndicator />
                      </SelectDragIndicatorWrapper>
                      <SelectItem label="Google Calendar" value="google" />
                      <SelectItem label="Microsoft Outlook" value="outlook" />
                      <SelectItem label="CalDAV" value="caldav" />
                    </SelectContent>
                  </SelectPortal>
                </Select>
                <FormControlError>
                  <FormControlErrorIcon as={AlertCircleIcon} />
                  <FormControlErrorText>
                    {errors.settings?.calendar_integration_type?.message}
                  </FormControlErrorText>
                </FormControlError>
              </FormControl>
            )}
          />
        )}
      </VStack>

      <VStack space="md">
        <Controller
          control={control}
          name="settings.enable_email_integration"
          render={({ field: { onChange, value } }) => (
            <HStack space="sm" alignItems="center">
              <Switch value={value} onValueChange={onChange} />
              <VStack flex={1}>
                <Text>Email Integration</Text>
                <Text size="sm" color="$textLight600">
                  Connect with external email providers for automated communications
                </Text>
              </VStack>
            </HStack>
          )}
        />

        {watchedEnableEmail && (
          <Controller
            control={control}
            name="settings.email_integration_provider"
            render={({ field: { onChange, value } }) => (
              <FormControl isInvalid={!!errors.settings?.email_integration_provider}>
                <FormControlLabel>
                  <Text>Email Provider</Text>
                </FormControlLabel>
                <Select onValueChange={onChange} selectedValue={value}>
                  <SelectTrigger>
                    <SelectInput placeholder="Select email provider" />
                  </SelectTrigger>
                  <SelectPortal>
                    <SelectBackdrop />
                    <SelectContent>
                      <SelectDragIndicatorWrapper>
                        <SelectDragIndicator />
                      </SelectDragIndicatorWrapper>
                      <SelectItem label="Gmail" value="gmail" />
                      <SelectItem label="Microsoft Outlook" value="outlook" />
                      <SelectItem label="Custom SMTP" value="custom" />
                    </SelectContent>
                  </SelectPortal>
                </Select>
                <FormControlError>
                  <FormControlErrorIcon as={AlertCircleIcon} />
                  <FormControlErrorText>
                    {errors.settings?.email_integration_provider?.message}
                  </FormControlErrorText>
                </FormControlError>
              </FormControl>
            )}
          />
        )}
      </VStack>
    </VStack>
  );

  const renderPrivacySection = () => (
    <VStack space="md">
      <Heading size="lg">Privacy & Compliance</Heading>

      <Controller
        control={control}
        name="settings.data_retention_policy"
        render={({ field: { onChange, value } }) => (
          <FormControl>
            <FormControlLabel>
              <Text>Data Retention Policy</Text>
            </FormControlLabel>
            <Select onValueChange={onChange} selectedValue={value}>
              <SelectTrigger>
                <SelectInput placeholder="Select data retention period" />
              </SelectTrigger>
              <SelectPortal>
                <SelectBackdrop />
                <SelectContent>
                  <SelectDragIndicatorWrapper>
                    <SelectDragIndicator />
                  </SelectDragIndicatorWrapper>
                  {DATA_RETENTION_OPTIONS.map(option => (
                    <SelectItem key={option.value} label={option.label} value={option.value} />
                  ))}
                </SelectContent>
              </SelectPortal>
            </Select>
            <FormControlHelper>
              <Text size="sm">How long to retain student and class data after account closure</Text>
            </FormControlHelper>
          </FormControl>
        )}
      />

      <Controller
        control={control}
        name="settings.gdpr_compliance_enabled"
        render={({ field: { onChange, value } }) => (
          <HStack space="sm" alignItems="center">
            <Switch value={value} onValueChange={onChange} />
            <VStack flex={1}>
              <Text>GDPR Compliance</Text>
              <Text size="sm" color="$textLight600">
                Enable GDPR compliance features and data protection measures
              </Text>
            </VStack>
          </HStack>
        )}
      />

      <Controller
        control={control}
        name="settings.allow_data_export"
        render={({ field: { onChange, value } }) => (
          <HStack space="sm" alignItems="center">
            <Switch value={value} onValueChange={onChange} />
            <VStack flex={1}>
              <Text>Allow Data Export</Text>
              <Text size="sm" color="$textLight600">
                Users can request and download their personal data
              </Text>
            </VStack>
          </HStack>
        )}
      />

      <Controller
        control={control}
        name="settings.require_data_processing_consent"
        render={({ field: { onChange, value } }) => (
          <HStack space="sm" alignItems="center">
            <Switch value={value} onValueChange={onChange} />
            <VStack flex={1}>
              <Text>Require Data Processing Consent</Text>
              <Text size="sm" color="$textLight600">
                Explicit user consent required for data processing activities
              </Text>
            </VStack>
          </HStack>
        )}
      />

      <VStack space="md" className="md:flex-row md:space-x-4 md:space-y-0">
        <Box className="flex-1">
          <Controller
            control={control}
            name="settings.dashboard_refresh_interval"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl isInvalid={!!errors.settings?.dashboard_refresh_interval}>
                <FormControlLabel>
                  <Text>Dashboard Refresh Interval (seconds)</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="30"
                    onBlur={onBlur}
                    onChangeText={text => onChange(parseInt(text) || 30)}
                    value={value.toString()}
                    keyboardType="numeric"
                  />
                </Input>
                <FormControlHelper>
                  <Text size="sm">How often to refresh dashboard data</Text>
                </FormControlHelper>
                <FormControlError>
                  <FormControlErrorIcon as={AlertCircleIcon} />
                  <FormControlErrorText>
                    {errors.settings?.dashboard_refresh_interval?.message}
                  </FormControlErrorText>
                </FormControlError>
              </FormControl>
            )}
          />
        </Box>

        <Box className="flex-1">
          <Controller
            control={control}
            name="settings.activity_retention_days"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl isInvalid={!!errors.settings?.activity_retention_days}>
                <FormControlLabel>
                  <Text>Activity Log Retention (days)</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="90"
                    onBlur={onBlur}
                    onChangeText={text => onChange(parseInt(text) || 90)}
                    value={value.toString()}
                    keyboardType="numeric"
                  />
                </Input>
                <FormControlHelper>
                  <Text size="sm">Days to keep activity logs</Text>
                </FormControlHelper>
                <FormControlError>
                  <FormControlErrorIcon as={AlertCircleIcon} />
                  <FormControlErrorText>
                    {errors.settings?.activity_retention_days?.message}
                  </FormControlErrorText>
                </FormControlError>
              </FormControl>
            )}
          />
        </Box>
      </VStack>
    </VStack>
  );

  if (loading) {
    return (
      <Center flex={1}>
        <Spinner size="large" />
        <Text mt="$2">Loading school settings...</Text>
      </Center>
    );
  }

  return (
    <ScrollView showsVerticalScrollIndicator={false} className="flex-1">
      <Box className="p-4 max-w-4xl mx-auto w-full">
        <VStack space="lg">
          <VStack space="sm" className="mb-4">
            <HStack justifyContent="space-between" alignItems="center" className="flex-wrap">
              <Heading size="xl" className="flex-1 mb-2 md:mb-0">
                School Settings
              </Heading>
              <Badge variant="outline" action="muted">
                <BadgeText size="sm">Configuration</BadgeText>
              </Badge>
            </HStack>
            <Text size="sm" className="text-typography-600">
              Configure your school's settings, preferences, and integrations
            </Text>
          </VStack>

          {renderSectionButtons()}

          <Box className="bg-background-50 rounded-lg p-4 min-h-[400px]">
            {activeSection === 'profile' && renderProfileSection()}
            {activeSection === 'educational' && renderEducationalSection()}
            {activeSection === 'operational' && renderOperationalSection()}
            {activeSection === 'billing' && renderBillingSection()}
            {activeSection === 'schedule' && renderScheduleSection()}
            {activeSection === 'communication' && renderCommunicationSection()}
            {activeSection === 'permissions' && renderPermissionsSection()}
            {activeSection === 'integrations' && renderIntegrationsSection()}
            {activeSection === 'privacy' && renderPrivacySection()}
          </Box>

          <Divider />

          <HStack space="md" className="justify-end flex-wrap">
            <Button
              variant="outline"
              onPress={onCancel}
              disabled={isSubmitting}
              className="mb-2 md:mb-0 min-w-[120px]"
            >
              <ButtonText>Cancel</ButtonText>
            </Button>
            <Button
              onPress={handleSubmit(onSubmit)}
              disabled={isSubmitting}
              action="primary"
              className="min-w-[140px]"
            >
              <ButtonText>{isSubmitting ? 'Saving...' : 'Save Settings'}</ButtonText>
            </Button>
          </HStack>
        </VStack>
      </Box>
    </ScrollView>
  );
};
