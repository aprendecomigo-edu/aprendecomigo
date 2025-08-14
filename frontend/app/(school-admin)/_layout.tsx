import { Stack, Redirect } from 'expo-router';
import React from 'react';

import { useSchool } from '@/api/auth';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

export default function SchoolAdminLayout() {
  const { isSchoolAdmin, userSchools } = useSchool();

  // Show loading if schools are still being loaded
  if (userSchools.length === 0) {
    return (
      <VStack className="flex-1 justify-center items-center p-4 bg-background-50">
        <Spinner size="large" />
        <Text className="mt-4">Loading permissions...</Text>
      </VStack>
    );
  }

  // Redirect if user is not a school admin
  if (!isSchoolAdmin) {
    return <Redirect href="/auth/signin" />;
  }

  return (
    <Stack
      screenOptions={{
        headerShown: false,
      }}
    >
      <Stack.Screen name="dashboard/index" />
      <Stack.Screen name="settings" />
      <Stack.Screen name="invitations" />
      <Stack.Screen name="communication/index" />
      <Stack.Screen name="analytics/index" />
    </Stack>
  );
}
