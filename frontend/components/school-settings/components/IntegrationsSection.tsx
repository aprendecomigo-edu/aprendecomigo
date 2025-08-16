import React, { memo } from 'react';
import { Controller, Control, FieldErrors } from 'react-hook-form';

import { CALENDAR_PROVIDERS, EMAIL_PROVIDERS } from '../constants';
import type { SchoolSettingsFormData } from '../types';

import {
  FormControl,
  FormControlLabel,
  FormControlError,
  FormControlErrorIcon,
  FormControlErrorText,
} from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon, AlertCircleIcon } from '@/components/ui/icon';
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

interface IntegrationsSectionProps {
  control: Control<SchoolSettingsFormData>;
  errors: FieldErrors<SchoolSettingsFormData>;
  watchedEnableCalendar: boolean;
  watchedEnableEmail: boolean;
}

export const IntegrationsSection = memo<IntegrationsSectionProps>(
  ({ control, errors, watchedEnableCalendar, watchedEnableEmail }) => {
    return (
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
                        {CALENDAR_PROVIDERS.map(provider => (
                          <SelectItem
                            key={provider.value}
                            label={provider.label}
                            value={provider.value}
                          />
                        ))}
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
                        {EMAIL_PROVIDERS.map(provider => (
                          <SelectItem
                            key={provider.value}
                            label={provider.label}
                            value={provider.value}
                          />
                        ))}
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
  },
);

IntegrationsSection.displayName = 'IntegrationsSection';
