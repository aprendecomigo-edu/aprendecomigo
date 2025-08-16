import React, { memo } from 'react';
import { Controller, Control } from 'react-hook-form';

import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

import type { SchoolSettingsFormData } from '../types';

interface CommunicationSectionProps {
  control: Control<SchoolSettingsFormData>;
}

export const CommunicationSection = memo<CommunicationSectionProps>(({ control }) => {
  return (
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
});

CommunicationSection.displayName = 'CommunicationSection';
