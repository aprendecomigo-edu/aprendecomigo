import { router, useRouter } from 'expo-router';
import React, { useEffect, useState } from 'react';

import { useAuth, useUserProfile, useSchool } from '@/api/auth';
import { Center } from '@/components/ui/center';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

/**
 * Smart Dashboard Router
 * 
 * This component acts as an intelligent router that redirects users to their
 * appropriate role-based dashboard. It handles the navigation timing issue
 * by using useEffect to ensure navigation happens after component mount.
 */
export default function DashboardRouter() {
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
      
      // Determine the appropriate dashboard based on user roles and type
      const redirectPath = determineUserDashboard(userProfile, userSchools);
      
      if (redirectPath) {
        console.log('🔄 Dashboard router: Redirecting to', redirectPath);
        router.replace(redirectPath);
      } else {
        setNavigationError('Unable to determine appropriate dashboard');
        setIsNavigating(false);
      }
    } catch (error) {
      console.error('Dashboard router navigation error:', error);
      setNavigationError('Navigation failed');
      setIsNavigating(false);
    }
  }, [isLoggedIn, isLoading, userProfile, userSchools, isNavigating]);

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
          <Text className="text-red-500 text-center">
            {navigationError}
          </Text>
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
 * Determines the appropriate dashboard route based on user profile and schools
 */
function determineUserDashboard(userProfile: any, userSchools: any[]): string | null {
  // If user has no schools, redirect to onboarding
  if (!userSchools || userSchools.length === 0) {
    return '/onboarding/welcome';
  }

  // Get the first school role (primary role)
  const primarySchool = userSchools[0];
  const primaryRole = primarySchool?.role;

  // Route based on primary role
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
      // Fallback to user type if role is unclear
      switch (userProfile.user_type) {
        case 'teacher':
          return '/(teacher)/dashboard';
        case 'student':
          return '/(student)/dashboard';
        case 'parent':
          return '/(parent)/dashboard';
        default:  //  TODO type should be known! If it isn't, either something is wrong with saving and getting the user type OR should return to login page. Defaulting to admin dashboard could be a security issue. 
          return '/(school-admin)/dashboard';
      }
  }
}