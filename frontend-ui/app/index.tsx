import { Redirect, type Href } from 'expo-router';
import React from 'react';

import { useAuth } from '@/api/authContext';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

export default function Index() {
  const { isLoggedIn, isLoading } = useAuth();

  // AuthContext already handles auth check on initialization
  // No need to call checkAuthStatus() again here

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

  // If not authenticated, redirect to landing page
  return <Redirect href={"/landing" as Href} />;
}
