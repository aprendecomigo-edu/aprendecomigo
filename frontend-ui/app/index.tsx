import { Redirect, type Href } from 'expo-router';
import React from 'react';

import { useAuth } from '@/api/auth';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

export default function Index() {
  const { isLoggedIn, isLoading, userProfile } = useAuth();

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

  // If authenticated, redirect to appropriate dashboard based on user type
  if (isLoggedIn && userProfile) {
    // For now, most users go to school admin dashboard
    // TODO: Add logic for different user types (student, parent, etc.)
    return <Redirect href={'/(school-admin)/dashboard' as Href} />;
  }

  // If authenticated but no profile yet, wait for profile to load
  if (isLoggedIn && !userProfile) {
    return (
      <VStack className="flex-1 justify-center items-center p-4 bg-background-50">
        <Spinner size="large" />
        <Text className="mt-4">Loading profile...</Text>
      </VStack>
    );
  }

  // If not authenticated, redirect to signin page
  return <Redirect href={"/auth/signin" as Href} />;
}
