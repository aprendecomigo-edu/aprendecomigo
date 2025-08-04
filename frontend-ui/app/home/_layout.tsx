import { Redirect, Stack, type Href } from 'expo-router';
import React from 'react';

import { useAuth } from '@/api/auth';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { View } from '@/components/ui/view';

// Wrap all dashboard routes with authentication check
export default function DashboardLayout() {
  const { isLoggedIn, isLoading } = useAuth();

  // We don't need to call checkAuthStatus() again here since it's already called in the main _layout
  // useEffect(() => {
  //   checkAuthStatus();
  // }, []);

  // Show loading indicator while checking authentication
  if (isLoading) {
    return (
      <View className="flex-1 justify-center items-center">
        <Spinner size="large" />
        <Text className="mt-4">Checking authentication...</Text>
      </View>
    );
  }

  // Redirect to login if not authenticated
  if (!isLoggedIn) {
    return <Redirect href={'/auth/signin' as Href} />;
  }

  // User is authenticated, show dashboard routes
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="home" options={{ headerShown: false }} />
      {/* Add other dashboard screens here if needed */}
    </Stack>
  );
}
