import { router } from 'expo-router';
import React, { createContext, useContext, useState, useEffect } from 'react';

import {
  isAuthenticated,
  logout,
  authenticateWithBiometricsAndGetToken,
  UserProfile,
} from './authApi';
import {
  enableBiometricAuth,
  disableBiometricAuth,
  isBiometricAvailable,
  isBiometricEnabled,
} from './biometricAuth';
import { getDashboardInfo } from './userApi';

interface AuthContextType {
  isLoggedIn: boolean;
  isLoading: boolean;
  userProfile: UserProfile | null;
  logout: () => Promise<void>;
  checkAuthStatus: () => Promise<boolean>;
  refreshUserProfile: () => Promise<void>;
  ensureUserProfile: () => Promise<void>;
  biometricSupport: {
    isAvailable: boolean;
    isEnabled: boolean;
  };
  enableBiometrics: (email: string) => Promise<boolean>;
  disableBiometrics: () => Promise<boolean>;
  loginWithBiometrics: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [userProfileCached, setUserProfileCached] = useState<boolean>(false);
  const [biometricSupport, setBiometricSupport] = useState<{
    isAvailable: boolean;
    isEnabled: boolean;
  }>({
    isAvailable: false,
    isEnabled: false,
  });

  // Check biometric availability and status
  const checkBiometricStatus = async () => {
    try {
      const available = await isBiometricAvailable();
      const enabled = await isBiometricEnabled();

      setBiometricSupport({
        isAvailable: available,
        isEnabled: enabled,
      });
    } catch (error) {
      console.error('Error checking biometric status:', error);
      setBiometricSupport({
        isAvailable: false,
        isEnabled: false,
      });
    }
  };

  // Fetch user profile (separate from auth check)
  const fetchUserProfile = async (): Promise<void> => {
    try {
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
        roles: [], // Would need to map from dashboard roles if needed
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
    }
  };

  // Refresh user profile (public method)
  const refreshUserProfile = async (): Promise<void> => {
    setUserProfileCached(false);
    await fetchUserProfile();
  };

  // Enable biometric authentication
  const handleEnableBiometrics = async (email: string): Promise<boolean> => {
    const result = await enableBiometricAuth(email);
    if (result) {
      setBiometricSupport({
        ...biometricSupport,
        isEnabled: true,
      });
    }
    return result;
  };

  // Disable biometric authentication
  const handleDisableBiometrics = async (): Promise<boolean> => {
    const result = await disableBiometricAuth();
    if (result) {
      setBiometricSupport({
        ...biometricSupport,
        isEnabled: false,
      });
    }
    return result;
  };

  // Login with biometrics
  const handleLoginWithBiometrics = async (): Promise<boolean> => {
    try {
      setIsLoading(true);
      const authResponse = await authenticateWithBiometricsAndGetToken();

      if (authResponse) {
        setIsLoggedIn(true);
        setUserProfile(authResponse.user);
        setUserProfileCached(true);
        return true;
      }

      return false;
    } catch (error) {
      console.error('Error during biometric login:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // Optimized auth status check - LIGHT operation ONLY
  const checkAuthStatus = async (): Promise<boolean> => {
    try {
      setIsLoading(true);
      console.log('Checking authentication status...');

      // ONLY check if token is valid - NO profile fetching
      const authenticated = await isAuthenticated();
      console.log('Is authenticated:', authenticated);

      setIsLoggedIn(authenticated);

      if (!authenticated) {
        // Clear cached profile if not authenticated
        setUserProfile(null);
        setUserProfileCached(false);
      }
      // NOTE: We do NOT fetch user profile here anymore
      // Profile should be fetched explicitly by pages that need it

      return authenticated;
    } catch (error) {
      console.error('Error checking auth status:', error);
      setIsLoggedIn(false);
      setUserProfile(null);
      setUserProfileCached(false);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // Ensure user profile is loaded (for pages that need it)
  const ensureUserProfile = async (): Promise<void> => {
    if (isLoggedIn && !userProfileCached && !userProfile) {
      console.log('Explicitly fetching user profile...');
      await fetchUserProfile();
    } else if (userProfileCached) {
      console.log('User profile already cached');
    } else if (!isLoggedIn) {
      console.log('User not logged in, skipping profile fetch');
    }
  };

  const handleLogout = async (): Promise<void> => {
    try {
      await logout();
      setIsLoggedIn(false);
      setUserProfile(null);
      setUserProfileCached(false);
      router.replace('/auth/signin');
    } catch (error) {
      console.error('Error during logout:', error);
    }
  };

  // Check auth status and biometric status on mount
  useEffect(() => {
    const initializeAuth = async () => {
      await checkAuthStatus();
      await checkBiometricStatus();
    };

    initializeAuth();
  }, []);

  const value = {
    isLoggedIn,
    isLoading,
    userProfile,
    logout: handleLogout,
    checkAuthStatus,
    refreshUserProfile,
    ensureUserProfile,
    biometricSupport,
    enableBiometrics: handleEnableBiometrics,
    disableBiometrics: handleDisableBiometrics,
    loginWithBiometrics: handleLoginWithBiometrics,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
