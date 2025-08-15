import React, { memo, useMemo, useCallback } from 'react';
import { ScrollView } from 'react-native';

import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

import type { SchoolSettingsFormProps } from './types';
import { useSchoolSettings } from './hooks/useSchoolSettings';
import { SectionNavigation } from './components/SectionNavigation';
import {
  ProfileSection,
  EducationalSection,
  OperationalSection,
  BillingSection,
  ScheduleSection,
  CommunicationSection,
  PermissionsSection,
  IntegrationsSection,
  PrivacySection,
} from './components';

/**
 * Refactored SchoolSettingsForm component
 * 
 * This component has been broken down from 1513 lines to under 200 lines by:
 * - Extracting form logic to useSchoolSettings hook
 * - Breaking down large render methods into focused section components
 * - Moving types and constants to separate files
 * - Adding performance optimizations with React.memo
 */
export const SchoolSettingsForm = memo<SchoolSettingsFormProps>(({
  schoolId,
  initialData,
  educationalSystems = [],
  onSave,
  onCancel,
  loading = false,
}) => {
  const {
    form,
    activeSection,
    setActiveSection,
    selectedEducationalSystem,
    watchedEnableCalendar,
    watchedEnableEmail,
    handleSubmit,
    isSubmitting,
    errors,
  } = useSchoolSettings({
    initialData,
    educationalSystems,
    onSave,
  });

  const renderActiveSection = useMemo(() => {
    const { control } = form;
    
    switch (activeSection) {
      case 'profile':
        return <ProfileSection control={control} errors={errors} />;
      case 'educational':
        return (
          <EducationalSection
            control={control}
            errors={errors}
            educationalSystems={educationalSystems}
            selectedEducationalSystem={selectedEducationalSystem}
          />
        );
      case 'operational':
        return <OperationalSection control={control} errors={errors} />;
      case 'billing':
        return <BillingSection control={control} errors={errors} />;
      case 'schedule':
        return <ScheduleSection control={control} errors={errors} />;
      case 'communication':
        return <CommunicationSection control={control} />;
      case 'permissions':
        return <PermissionsSection control={control} />;
      case 'integrations':
        return (
          <IntegrationsSection
            control={control}
            errors={errors}
            watchedEnableCalendar={watchedEnableCalendar}
            watchedEnableEmail={watchedEnableEmail}
          />
        );
      case 'privacy':
        return <PrivacySection control={control} errors={errors} />;
      default:
        return null;
    }
  }, [
    activeSection,
    form.control,
    errors,
    educationalSystems,
    selectedEducationalSystem,
    watchedEnableCalendar,
    watchedEnableEmail,
  ]);

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
          {/* Header */}
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

          {/* Section Navigation */}
          <SectionNavigation 
            activeSection={activeSection} 
            onSectionChange={setActiveSection} 
          />

          {/* Active Section Content */}
          <Box className="bg-background-50 rounded-lg p-4 min-h-[400px]">
            {renderActiveSection}
          </Box>

          <Divider />

          {/* Form Actions */}
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
              onPress={form.handleSubmit(handleSubmit)}
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
});

SchoolSettingsForm.displayName = 'SchoolSettingsForm';