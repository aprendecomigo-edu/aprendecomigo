import { Redirect, type Href } from 'expo-router';
import React, { useEffect } from 'react';

import { useAuth } from '@/api/authContext';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

export default function Index() {
  const { isLoggedIn, isLoading, checkAuthStatus } = useAuth();

  // Force a fresh auth check when the app loads
  useEffect(() => {
    checkAuthStatus();
  }, []);

  // While checking auth status, show a loading spinner
  if (isLoading) {
    return (
      <VStack className="flex-1 justify-center items-center p-4 bg-background-50">
        <Spinner size="large" />
        <Text className="mt-4">Loading...</Text>
      </VStack>
    );
  }

  // If authenticated, redirect to dashboard
  if (isLoggedIn) {
    return <Redirect href={'home' as Href} />;
  }

  // If not authenticated, redirect to login
  return <Redirect href="/auth/signin" />;
}
