import { router } from 'expo-router';
import React, { useEffect, useState } from 'react';

import { useAuth } from '@/api/auth';
import { Center } from '@/components/ui/center';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

/**
 * Smart Dashboard Router
 *
 * This component acts as an intelligent router that redirects users to their
 * appropriate role-based dashboard using cached user data for immediate routing.
 * No longer waits for API calls to complete before redirecting.
 */
export default function DashboardRouter() {
  const { isLoggedIn, isLoading, userProfile } = useAuth();
  const [isNavigating, setIsNavigating] = useState(false);
  const [navigationError, setNavigationError] = useState<string | null>(null);

  useEffect(() => {
    // Don't navigate if still loading auth state
    if (isLoading) {
      return;
    }

    // Don't navigate if not authenticated
    if (!isLoggedIn) {
      setIsNavigating(true);
      router.replace('/auth/signin');
      return;
    }

    // Don't navigate if user profile is not loaded yet
    if (!userProfile) {
      return;
    }

    // Don't navigate if already navigating
    if (isNavigating) {
      return;
    }

    try {
      setIsNavigating(true);

      // Use primary_role from cached user data for immediate redirect
      const redirectPath = determineUserDashboardFromPrimaryRole(
        userProfile.primary_role,
        userProfile.user_type,
      );

      if (redirectPath) {
        if (__DEV__) {
          if (__DEV__) {
            console.log(
              '🔄 Dashboard router: Immediate redirect to',
              redirectPath,
              'based on primary_role:',
              userProfile.primary_role,
            );
          }
        }
        router.replace(redirectPath);
      } else {
        setNavigationError('Unable to determine appropriate dashboard');
        setIsNavigating(false);
      }
    } catch (error) {
      if (__DEV__) {
        console.error('Dashboard router navigation error:', error); // TODO: Review for sensitive data
      }
      setNavigationError('Navigation failed');
      setIsNavigating(false);
    }
  }, [isLoggedIn, isLoading, userProfile, isNavigating]);

  // Show loading state while checking auth or navigating
  if (isLoading || isNavigating) {
    return (
      <Center className="h-full w-full">
        <VStack className="items-center" space="md">
          <Spinner size="large" />
          <Text className="text-gray-500">
            {isLoading ? 'Checking authentication...' : 'Redirecting to dashboard...'}
          </Text>
        </VStack>
      </Center>
    );
  }

  // Show error state if navigation failed
  if (navigationError) {
    return (
      <Center className="h-full w-full">
        <VStack className="items-center" space="md">
          <Text className="text-red-500 text-center">{navigationError}</Text>
          <Text className="text-gray-500 text-center text-sm">
            Please try refreshing the page or contact support if the issue persists.
          </Text>
        </VStack>
      </Center>
    );
  }

  // Fallback - should not be reached under normal circumstances
  return (
    <Center className="h-full w-full">
      <VStack className="items-center" space="md">
        <Spinner size="large" />
        <Text className="text-gray-500">Loading dashboard...</Text>
      </VStack>
    </Center>
  );
}

/**
 * Determines the appropriate dashboard route based on primary_role from cached user data
 * This provides immediate routing without waiting for API calls
 */
function determineUserDashboardFromPrimaryRole(
  primaryRole: string | undefined,
  userType: string,
): string | null {
  // Route based on primary role from cached user data
  switch (primaryRole) {
    case 'school_owner':
    case 'school_admin':
      return '/(school-admin)/dashboard';

    case 'teacher':
      return '/(teacher)/dashboard';

    case 'student':
      return '/(student)/dashboard';

    case 'parent':
      return '/(parent)/dashboard';

    default:
      // Fallback to user type if primary_role is missing
      switch (userType) {
        case 'teacher':
          return '/(teacher)/dashboard';
        case 'student':
          return '/(student)/dashboard';
        case 'parent':
          return '/(parent)/dashboard';
        case 'admin':
          return '/(school-admin)/dashboard';
        default:
          // If we can't determine the role, redirect to onboarding
          return '/onboarding/welcome';
      }
  }
}
