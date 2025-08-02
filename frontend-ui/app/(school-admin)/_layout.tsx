import { Redirect, Stack } from 'expo-router';
import React, { useEffect, useState } from 'react';

import { useAuth } from '@/api/authContext';
import { getUserAdminSchools } from '@/api/userApi';
import { Center } from '@/components/ui/center';
import { Text } from '@/components/ui/text';

export default function SchoolAdminLayout() {
  console.log('🔧 SchoolAdminLayout rendered');
  const { isLoggedIn, isLoading, userProfile } = useAuth();
  const [hasAdminAccess, setHasAdminAccess] = useState<boolean | null>(null);
  const [checkingAccess, setCheckingAccess] = useState(true);

  console.log('🔧 Auth state:', { isLoggedIn, isLoading, hasProfile: !!userProfile });

  // Check if user has admin access to any schools
  useEffect(() => {
    const checkAdminAccess = async () => {
      if (!userProfile) {
        setHasAdminAccess(false);
        setCheckingAccess(false);
        return;
      }

      try {
        const adminSchools = await getUserAdminSchools();
        setHasAdminAccess(adminSchools.length > 0);
      } catch (error) {
        console.error('Error checking admin access:', error);
        setHasAdminAccess(false);
      } finally {
        setCheckingAccess(false);
      }
    };

    if (isLoggedIn && userProfile) {
      checkAdminAccess();
    } else {
      setCheckingAccess(false);
    }
  }, [isLoggedIn, userProfile]);

  // Show loading state while checking authentication
  if (isLoading || checkingAccess) {
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

  // Temporarily bypass admin check for testing - GitHub Issue #42
  // Allow access for testing school settings functionality
  // TODO: Re-enable admin check once user data is properly set up
  // if (hasAdminAccess === false) {
  //   console.log('No admin access, redirecting to home');
  //   return <Redirect href="/home" />;
  // }

  return (
    <Stack
      screenOptions={{
        headerShown: false,
      }}
    >
      <Stack.Screen name="dashboard/index" />
      <Stack.Screen name="settings" />
      <Stack.Screen name="invitations" />
      <Stack.Screen name="communication" />
      <Stack.Screen name="analytics" />
    </Stack>
  );
}
