import React, { createContext, useContext, useEffect, useState } from 'react';
import { isAuthenticated, logout, getUserProfile, UserProfile } from './authApi';
import { router } from 'expo-router';

interface AuthContextType {
  isLoggedIn: boolean;
  isLoading: boolean;
  userProfile: UserProfile | null;
  logout: () => Promise<void>;
  checkAuthStatus: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);

  const checkAuthStatus = async (): Promise<boolean> => {
    try {
      setIsLoading(true);
      const authenticated = await isAuthenticated();
      setIsLoggedIn(authenticated);

      if (authenticated) {
        // Fetch user profile
        try {
          const profile = await getUserProfile();
          setUserProfile(profile);
        } catch (error) {
          console.error('Error fetching user profile:', error);
          // If we can't get the profile but have a token, logout as safety measure
          await handleLogout();
          return false;
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

  // Check auth status on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const value = {
    isLoggedIn,
    isLoading,
    userProfile,
    logout: handleLogout,
    checkAuthStatus,
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