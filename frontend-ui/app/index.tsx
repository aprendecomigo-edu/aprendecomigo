import { Redirect, type Href } from 'expo-router';
import React from 'react';

import { useAuth } from '@/api/auth';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

export default function Index() {
  const { isLoggedIn, isLoading } = useAuth();

  // While checking auth status, show a loading spinner
  if (isLoading) {
    return (
      <VStack className="flex-1 justify-center items-center p-4 bg-background-50">
        <Spinner size="large" />
        <Text className="mt-4">Loading...</Text>
      </VStack>
    );
  }

  // If authenticated, redirect to main dashboard router which handles role-based routing
  // TODO: lets go straight to school-admin dashboard for now and fix other bits later
  if (isLoggedIn) {
    return <Redirect href={'/dashboard' as Href} />;
  }

  // If not authenticated, redirect to signin page
  return <Redirect href={'/auth/signin' as Href} />;
}
