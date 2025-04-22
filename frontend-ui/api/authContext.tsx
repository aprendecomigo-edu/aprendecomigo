import React, { createContext, useContext, useEffect, useState } from 'react';
import {
  isAuthenticated,
  logout,
  getUserProfile,
  UserProfile,
  authenticateWithBiometricsAndGetToken
} from './authApi';
import { router } from 'expo-router';
import {
  enableBiometricAuth,
  disableBiometricAuth,
  isBiometricAvailable,
  isBiometricEnabled
} from './biometricAuth';

interface AuthContextType {
  isLoggedIn: boolean;
  isLoading: boolean;
  userProfile: UserProfile | null;
  logout: () => Promise<void>;
  checkAuthStatus: () => Promise<boolean>;
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

  const checkAuthStatus = async (): Promise<boolean> => {
    try {
      setIsLoading(true);
      console.log('Checking authentication status...');
      const authenticated = await isAuthenticated();
      console.log('Is authenticated:', authenticated);
      setIsLoggedIn(authenticated);

      if (authenticated) {
        // Fetch user profile
        try {
          console.log('Fetching user profile...');
          const profile = await getUserProfile();
          console.log('User profile received:', profile);
          setUserProfile(profile);
        } catch (error) {
          console.error('Error fetching user profile:', error);
          // Print more detailed error info
          if (error instanceof Error) {
            console.error('Error message:', error.message);
            console.error('Error stack:', error.stack);
          }

          // Continue without profile - don't logout automatically
          console.warn('Continuing without user profile');
          return authenticated;
        }
      }

      return authenticated;
    } catch (error) {
      console.error('Error checking auth status:', error);
      setIsLoggedIn(false);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async (): Promise<void> => {
    try {
      await logout();
      setIsLoggedIn(false);
      setUserProfile(null);
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
