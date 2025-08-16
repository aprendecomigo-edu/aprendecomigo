import React, { memo } from 'react';
import { Controller, Control } from 'react-hook-form';

import type { SchoolSettingsFormData } from '../types';

import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface PermissionsSectionProps {
  control: Control<SchoolSettingsFormData>;
}

export const PermissionsSection = memo<PermissionsSectionProps>(({ control }) => {
  return (
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
});

PermissionsSection.displayName = 'PermissionsSection';
