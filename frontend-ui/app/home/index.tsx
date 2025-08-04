import { Redirect } from 'expo-router';
import React, { useEffect, useState } from 'react';

import { useAuth, useUserProfile } from '@/api/auth';
import { Center } from '@/components/ui/center';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Role-based home redirect component
const RoleBasedHome: React.FC = () => {
  const { isLoading } = useAuth();
  const { userProfile, isLoading: isProfileLoading } = useUserProfile();

  // Show loading while checking user profile
  if (isLoading || isProfileLoading || !userProfile) {
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
      return '/(student)/dashboard';
    }

    // Parents go to parent dashboard
    if (userProfile.user_type === 'parent') {
      return '/(parent)/dashboard';
    }

    // Default fallback to admin dashboard
    return '/(school-admin)/dashboard';
  };

  const dashboardRoute = getUserDashboardRoute();

  return <Redirect href={dashboardRoute as any} />;
};

export default RoleBasedHome;
