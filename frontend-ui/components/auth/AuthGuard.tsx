import { router } from 'expo-router';
import React, { useEffect, useState } from 'react';

import { useAuth, useUserProfile, useSchool } from '@/api/auth';
import { Center } from '@/components/ui/center';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  allowedRoles?: string[];
  allowedUserTypes?: string[];
  redirectTo?: string;
}

export const AuthGuard: React.FC<AuthGuardProps> = ({ 
  children, 
  fallback, 
  allowedRoles, 
  allowedUserTypes, 
  redirectTo = '/auth/signin' 
}) => {
  const { isLoggedIn, isLoading } = useAuth();
  const { userProfile } = useUserProfile();
  const { userSchools } = useSchool();
  const [isNavigating, setIsNavigating] = useState(false);
  const [navigationError, setNavigationError] = useState<string | null>(null);

  useEffect(() => {
    // Don't navigate if still loading auth state
    if (isLoading) {
      return;
    }

    // Don't navigate if already navigating
    if (isNavigating) {
      return;
    }

    try {
      // Redirect to login if not authenticated
      if (!isLoggedIn) {
        setIsNavigating(true);
        router.replace(redirectTo as any);
        return;
      }

      // Check role-based access if allowedRoles is specified
      if (allowedRoles && allowedRoles.length > 0) {
        const userRoles = userSchools.map(school => school.role);
        const hasAllowedRole = allowedRoles.some(role => userRoles.includes(role));
        
        if (!hasAllowedRole) {
          setIsNavigating(true);
          router.replace('/dashboard' as any); // Redirect to smart dashboard router
          return;
        }
      }

      // Check user type-based access if allowedUserTypes is specified
      if (allowedUserTypes && allowedUserTypes.length > 0 && userProfile) {
        const hasAllowedUserType = allowedUserTypes.includes(userProfile.user_type);
        
        if (!hasAllowedUserType) {
          setIsNavigating(true);
          router.replace('/dashboard' as any); // Redirect to smart dashboard router
          return;
        }
      }

      // If we got here, user has proper access - reset any navigation state
      setIsNavigating(false);
      setNavigationError(null);
    } catch (error) {
      console.error('AuthGuard navigation error:', error);
      setNavigationError('Navigation failed');
      setIsNavigating(false);
    }
  }, [isLoggedIn, isLoading, userProfile, userSchools, allowedRoles, allowedUserTypes, redirectTo, isNavigating]);

  // Show loading state during auth check or navigation
  if (isLoading || isNavigating) {
    return (
      fallback || (
        <Center className="h-full w-full">
          <VStack className="items-center" space="md">
            <Spinner size="large" />
            <Text className="text-gray-500">
              {isLoading ? 'Checking authentication...' : 'Redirecting...'}
            </Text>
          </VStack>
        </Center>
      )
    );
  }

  // Show error state if navigation failed
  if (navigationError) {
    return (
      <Center className="h-full w-full">
        <VStack className="items-center" space="md">
          <Text className="text-red-500 text-center">
            {navigationError}
          </Text>
          <Text className="text-gray-500 text-center text-sm">
            Please try refreshing the page.
          </Text>
        </VStack>
      </Center>
    );
  }

  // If not authenticated but haven't navigated yet, show loading
  if (!isLoggedIn) {
    return (
      fallback || (
        <Center className="h-full w-full">
          <VStack className="items-center" space="md">
            <Spinner size="large" />
            <Text className="text-gray-500">Redirecting to login...</Text>
          </VStack>
        </Center>
      )
    );
  }

  // User is authenticated and has required permissions, render children
  return <>{children}</>;
};