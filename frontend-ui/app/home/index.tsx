import { Redirect } from 'expo-router';
import React, { useEffect, useState } from 'react';

import { useAuth } from '@/api/authContext';
import { Center } from '@/components/ui/center';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Role-based home redirect component
const RoleBasedHome: React.FC = () => {
  const { userProfile, isLoading, ensureUserProfile } = useAuth();
  const [isUserProfileLoaded, setIsUserProfileLoaded] = useState(false);

  // Ensure user profile is loaded
  useEffect(() => {
    const loadProfile = async () => {
      await ensureUserProfile();
      setIsUserProfileLoaded(true);
    };

    if (!isUserProfileLoaded && !isLoading) {
      loadProfile();
    }
  }, [ensureUserProfile, isLoading, isUserProfileLoaded]);

  // Show loading while checking user profile
  if (isLoading || !isUserProfileLoaded || !userProfile) {
    return (
      <Center className="flex-1">
        <VStack space="md" className="items-center">
          <Spinner size="large" />
          <Text className="text-gray-600">Loading your dashboard...</Text>
        </VStack>
      </Center>
    );
  }

  // Route based on user type and role
  const getUserDashboardRoute = () => {
    // Check if user is a tutor (either user_type is tutor or is_admin for their own school)
    if (userProfile.user_type === 'admin' && userProfile.is_admin) {
      // Check if this is an individual tutor (has both admin and teacher roles for same school)
      // For now, assume all admins go to school admin dashboard
      // Individual tutors will be identified by additional logic if needed
      return '/(school-admin)/dashboard';
    }

    // Teachers go to teacher dashboard
    if (userProfile.user_type === 'teacher') {
      return '/(teacher)/dashboard';
    }

    // Students go to student dashboard
    if (userProfile.user_type === 'student') {
      return '/student/dashboard';
    }

    // Parents go to parent dashboard
    if (userProfile.user_type === 'parent') {
      return '/parents';
    }

    // Default fallback to admin dashboard
    return '/(school-admin)/dashboard';
  };

  const dashboardRoute = getUserDashboardRoute();

  return <Redirect href={dashboardRoute as any} />;
};

export default RoleBasedHome;
