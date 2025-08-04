import React, { createContext, useContext, useState, useEffect } from 'react';

import { getDashboardInfo } from '../userApi';
import { UserProfile } from '../authApi';
import { useAuth } from './AuthContext';

interface UserProfileContextType {
  userProfile: UserProfile | null;
  isProfileLoading: boolean;
  refreshUserProfile: () => Promise<void>;
  ensureUserProfile: () => Promise<void>;
}

const UserProfileContext = createContext<UserProfileContextType | undefined>(undefined);

export const UserProfileProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isLoggedIn } = useAuth();
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [isProfileLoading, setIsProfileLoading] = useState<boolean>(false);
  const [userProfileCached, setUserProfileCached] = useState<boolean>(false);

  // Fetch user profile (separate from auth check)
  const fetchUserProfile = async (): Promise<void> => {
    if (!isLoggedIn) {
      console.log('User not logged in, skipping profile fetch');
      return;
    }

    try {
      setIsProfileLoading(true);
      console.log('Fetching user profile...');
      const dashboardData = await getDashboardInfo();
      console.log('Dashboard data received:', dashboardData);

      // Extract user_info and convert to UserProfile format
      const userProfile: UserProfile = {
        id: dashboardData.user_info.id,
        email: dashboardData.user_info.email,
        name: dashboardData.user_info.name,
        phone_number: undefined, // This field is not in dashboard_info
        user_type: dashboardData.user_info.user_type as 'admin' | 'teacher' | 'student' | 'parent',
        is_admin: dashboardData.user_info.is_admin,
        created_at: dashboardData.user_info.date_joined,
        updated_at: dashboardData.user_info.date_joined, // Using date_joined as fallback
        roles: (dashboardData.user_info as any).roles || [], // Map from dashboard roles - may not be available
      };

      setUserProfile(userProfile);
      setUserProfileCached(true);
    } catch (error) {
      console.error('Error fetching user profile:', error);
      if (error instanceof Error) {
        console.error('Error message:', error.message);
        console.error('Error stack:', error.stack);
      }
      // Don't throw error - user profile fetch failure shouldn't break auth
      console.warn('Continuing without user profile');
    } finally {
      setIsProfileLoading(false);
    }
  };

  // Refresh user profile (public method)
  const refreshUserProfile = async (): Promise<void> => {
    setUserProfileCached(false);
    await fetchUserProfile();
  };

  // Ensure user profile is loaded (for pages that need it)
  const ensureUserProfile = async (): Promise<void> => {
    if (isLoggedIn && !userProfileCached && !userProfile && !isProfileLoading) {
      console.log('Explicitly fetching user profile...');
      await fetchUserProfile();
    } else if (userProfileCached) {
      console.log('User profile already cached');
    } else if (!isLoggedIn) {
      console.log('User not logged in, skipping profile fetch');
    }
  };

  // Clear profile data when user logs out
  useEffect(() => {
    if (!isLoggedIn) {
      setUserProfile(null);
      setUserProfileCached(false);
    }
  }, [isLoggedIn]);

  // Auto-fetch profile when user logs in (if not already cached)
  useEffect(() => {
    if (isLoggedIn && !userProfileCached && !userProfile && !isProfileLoading) {
      console.log('🔑 User authenticated, auto-fetching profile...');
      fetchUserProfile();
    }
  }, [isLoggedIn, userProfileCached, userProfile, isProfileLoading]);

  const value = {
    userProfile,
    isProfileLoading,
    refreshUserProfile,
    ensureUserProfile,
  };

  return <UserProfileContext.Provider value={value}>{children}</UserProfileContext.Provider>;
};

export const useUserProfile = (): UserProfileContextType => {
  const context = useContext(UserProfileContext);
  if (context === undefined) {
    throw new Error('useUserProfile must be used within a UserProfileProvider');
  }
  return context;
};