import { Redirect, Stack, type Href } from 'expo-router';
import React from 'react';

import { useAuth } from '@/api/authContext';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { View } from '@/components/ui/view';

// Wrap all chat routes with authentication check
export default function ChatLayout() {
  const { isLoggedIn, isLoading } = useAuth();

  // Show loading indicator while checking authentication
  if (isLoading) {
    return (
      <View className="flex-1 justify-center items-center">
        <Spinner size="large" />
        <Text className="mt-4">Verificando autenticação...</Text>
      </View>
    );
  }

  // Redirect to login if not authenticated
  if (!isLoggedIn) {
    return <Redirect href={'/auth/signin' as Href} />;
  }

  // User is authenticated, show chat routes
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="index" options={{ headerShown: false }} />
      {/* Add other chat screens here when needed */}
    </Stack>
  );
}
