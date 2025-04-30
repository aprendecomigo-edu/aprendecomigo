import React, { useEffect } from 'react';
import { Redirect, Stack } from 'expo-router';
import { useAuth } from '@/api/authContext';
import { View } from '@/components/ui/view';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';

// Wrap all dashboard routes with authentication check
export default function DashboardLayout() {
  const { isLoggedIn, isLoading, checkAuthStatus } = useAuth();

  // Force fresh auth check when entering dashboard routes
  useEffect(() => {
    checkAuthStatus();
  }, []);

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
    return <Redirect href="/auth/signin" />;
  }

  // User is authenticated, show dashboard routes
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="dashboard-layout" options={{ headerShown: false }} />
      {/* Add other dashboard screens here if needed */}
    </Stack>
  );
}
