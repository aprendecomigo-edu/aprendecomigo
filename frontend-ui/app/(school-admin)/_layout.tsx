import { Redirect, Stack } from 'expo-router';
import React from 'react';

import { useAuth } from '@/api/authContext';
import { Center } from '@/components/ui/center';
import { Text } from '@/components/ui/text';

export default function SchoolAdminLayout() {
  const { isLoggedIn, isLoading, userProfile } = useAuth();

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <Center className="flex-1">
        <Text className="text-gray-600">Verificando autenticação...</Text>
      </Center>
    );
  }

  // Redirect to login if not authenticated
  if (!isLoggedIn) {
    return <Redirect href="/auth/signin" />;
  }

  // Check if user has school admin role
  // This is a placeholder - you'll need to implement role checking based on your user model
  const isSchoolAdmin = userProfile?.user_type === 'admin' || userProfile?.is_admin;

  if (!isSchoolAdmin) {
    return <Redirect href="/home" />;
  }

  return (
    <Stack
      screenOptions={{
        headerShown: false,
      }}
    >
      <Stack.Screen name="dashboard/index" />
    </Stack>
  );
}