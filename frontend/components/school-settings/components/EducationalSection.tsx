import React, { memo } from 'react';
import { Controller, Control, FieldErrors } from 'react-hook-form';

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

import type { SchoolSettingsFormData, EducationalSystem } from '../types';

interface EducationalSectionProps {
  control: Control<SchoolSettingsFormData>;
  errors: FieldErrors<SchoolSettingsFormData>;
  educationalSystems: EducationalSystem[];
  selectedEducationalSystem: EducationalSystem | null;
}

export const EducationalSection = memo<EducationalSectionProps>(
  ({ control, errors, educationalSystems, selectedEducationalSystem }) => {
    return (
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
              <Select
                onValueChange={val => onChange(parseInt(val))}
                selectedValue={value.toString()}
              >
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
                      <SelectItem
                        key={system.id}
                        label={system.name}
                        value={system.id.toString()}
                      />
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
  },
);

EducationalSection.displayName = 'EducationalSection';
