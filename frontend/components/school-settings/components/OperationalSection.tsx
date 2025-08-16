import React, { memo } from 'react';
import { Controller, Control, FieldErrors } from 'react-hook-form';

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
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

import type { SchoolSettingsFormData } from '../types';
import { TRIAL_COST_OPTIONS, CURRENCY_OPTIONS, LANGUAGE_OPTIONS } from '../constants';

interface OperationalSectionProps {
  control: Control<SchoolSettingsFormData>;
  errors: FieldErrors<SchoolSettingsFormData>;
}

export const OperationalSection = memo<OperationalSectionProps>(({ control, errors }) => {
  return (
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
});

OperationalSection.displayName = 'OperationalSection';
