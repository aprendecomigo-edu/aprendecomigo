import { router } from 'expo-router';
import React from 'react';

import { useAuth } from '@/api/authContext';
import { Center } from '@/components/ui/center';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const AuthGuard: React.FC<AuthGuardProps> = ({ children, fallback }) => {
  const { isLoggedIn, isLoading } = useAuth();

  // Show loading state during auth check
  if (isLoading) {
    return (
      fallback || (
        <Center className="h-full w-full">
          <VStack className="items-center" space="md">
            <Spinner size="large" />
            <Text className="text-gray-500">Checking authentication...</Text>
          </VStack>
        </Center>
      )
    );
  }

  // Redirect to login if not authenticated
  if (!isLoggedIn) {
    router.replace('/auth/signin');
    return null;
  }

  // User is authenticated, render children
  return <>{children}</>;
};