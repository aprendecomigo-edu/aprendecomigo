import React, { memo } from 'react';
import { Controller, Control, FieldErrors } from 'react-hook-form';

import { DATA_RETENTION_OPTIONS } from '../constants';
import type { SchoolSettingsFormData } from '../types';

import { Box } from '@/components/ui/box';
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
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface PrivacySectionProps {
  control: Control<SchoolSettingsFormData>;
  errors: FieldErrors<SchoolSettingsFormData>;
}

export const PrivacySection = memo<PrivacySectionProps>(({ control, errors }) => {
  return (
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
});

PrivacySection.displayName = 'PrivacySection';
