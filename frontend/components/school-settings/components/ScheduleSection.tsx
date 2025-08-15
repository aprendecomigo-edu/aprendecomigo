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
import { HStack } from '@/components/ui/hstack';
import { Icon, AlertCircleIcon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

import type { SchoolSettingsFormData } from '../types';
import { WEEKDAYS } from '../constants';

interface ScheduleSectionProps {
  control: Control<SchoolSettingsFormData>;
  errors: FieldErrors<SchoolSettingsFormData>;
}

export const ScheduleSection = memo<ScheduleSectionProps>(({ control, errors }) => {
  return (
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
});

ScheduleSection.displayName = 'ScheduleSection';