import { Stack } from 'expo-router';
import React from 'react';

import { useSchool } from '@/api/auth';

export default function SchoolAdminLayout() {
  const { isSchoolAdmin } = useSchool();

  return (
    <Stack
      screenOptions={{
        headerShown: false,
      }}
    >
      <Stack.Protected guard={isSchoolAdmin}>
        <Stack.Screen name="dashboard/index" />
        <Stack.Screen name="settings" />
        <Stack.Screen name="invitations" />
        <Stack.Screen name="communication" />
        <Stack.Screen name="analytics" />
      </Stack.Protected>
    </Stack>
  );
}
