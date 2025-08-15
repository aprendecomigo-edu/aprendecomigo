import { router } from 'expo-router';
import React, { createContext, useContext, useState, useEffect, useRef } from 'react';

import { setAuthErrorCallback } from '../apiClient';
import { isAuthenticated, logout, UserProfile } from '../authApi';

import { storage } from '@/utils/storage';

// Global flag to prevent multiple simultaneous auth checks
let isAuthCheckInProgress = false;

interface AuthContextType {
  isLoggedIn: boolean;
  isLoading: boolean;
  serverError: string | null;
  serverAlert: { type: 'error' | 'warning'; message: string } | null;
  userProfile: UserProfile | null;
  clearServerAlert: () => void;
  logout: () => Promise<void>;
  signOut: () => Promise<void>; // Alias for logout
  checkAuthStatus: () => Promise<boolean>;
  notifyAuthError: () => void;
  setUserProfile: (profile: UserProfile) => Promise<void>;
  // Legacy compatibility - this should use useUserProfile instead
  ensureUserProfile?: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [serverError, setServerError] = useState<string | null>(null);
  const [serverAlert, setServerAlert] = useState<{
    type: 'error' | 'warning';
    message: string;
  } | null>(null);
  const [userProfile, setUserProfileState] = useState<UserProfile | null>(null);
  const hasInitializedRef = useRef(false);

  // Store user profile data for immediate routing
  const setUserProfile = async (profile: UserProfile): Promise<void> => {
    setUserProfileState(profile);
    // Store user profile in local storage for persistence
    await storage.setItem('user_profile', JSON.stringify(profile));
  };

  // Load cached user profile from storage
  const loadCachedUserProfile = async (): Promise<void> => {
    try {
      const cachedProfile = await storage.getItem('user_profile');
      if (cachedProfile) {
        setUserProfileState(JSON.parse(cachedProfile));
      }
    } catch (error) {
      if (__DEV__) {
        console.error('Error loading cached user profile:', error);
      }
    }
  };

  // Optimized auth status check - LIGHT operation ONLY
  const checkAuthStatus = async (): Promise<boolean> => {
    // Prevent multiple simultaneous auth checks globally
    if (isAuthCheckInProgress) {
      return isLoggedIn; // Return current state
    }

    try {
      isAuthCheckInProgress = true;
      setIsLoading(true);
      setServerError(null); // Clear any previous errors
      setServerAlert(null); // Clear any previous alerts

      // ONLY check if token is valid - NO profile fetching
      const authenticated = await isAuthenticated();

      setIsLoggedIn(authenticated);

      // If not authenticated, clear cached user profile
      if (!authenticated) {
        setUserProfileState(null);
        await storage.removeItem('user_profile');
      } else if (!userProfile) {
        // If authenticated but no cached profile, try to load from storage
        await loadCachedUserProfile();
      }

      return authenticated;
    } catch (error: any) {
      // Check if this is a server connection error (server completely down)
      if (
        !error.response ||
        error.code === 'ERR_NETWORK' ||
        error.code === 'ERR_CONNECTION_REFUSED'
      ) {
        setServerError(
          'Unable to connect to server. Please check your internet connection or contact your administrator if this error persists.'
        );
        setServerAlert({
          type: 'error',
          message:
            'Server is currently unavailable. You have been logged out for security reasons.',
        });
        setIsLoggedIn(false);
        return false;
      }

      // Check if this is a server error (500, 503, etc.) - server is up but having issues
      if (error.response?.status >= 500) {
        setServerAlert({
          type: 'warning',
          message:
            'Server is experiencing issues. Some features may not work properly. Please try again later.',
        });
        // Don't logout for server errors - assume token is still valid
        return isLoggedIn; // Return current auth state
      }

      // For other errors (401, 403, etc.), assume auth failed
      setIsLoggedIn(false);
      return false;
    } finally {
      isAuthCheckInProgress = false;
      setIsLoading(false);
    }
  };

  const handleLogout = async (): Promise<void> => {
    try {
      await logout();
      setIsLoggedIn(false);
      setUserProfileState(null);
      await storage.removeItem('user_profile');
      router.replace('/auth/signin');
    } catch (error) {
      if (__DEV__) {
        console.error('Error during logout:', error);
      }
    }
  };

  // Handle authentication errors (called by API client)
  const handleNotifyAuthError = () => {
    if (__DEV__) {
      if (__DEV__) {
        console.log('Authentication error notified by API client');
      }
    }
    setIsLoggedIn(false);
    setUserProfileState(null);
    storage.removeItem('user_profile').catch((error) => {
      if (__DEV__) {
        console.error(error);
      }
    });
  };

  // Check auth status on mount
  useEffect(() => {
    // Prevent multiple initializations
    if (hasInitializedRef.current) {
      if (__DEV__) {
        if (__DEV__) {
          console.log('🔑 AuthContext: Already initialized, skipping');
        }
      }
      return;
    }

    if (__DEV__) {
      if (__DEV__) {
        console.log('🔑 AuthContext useEffect triggered');
      }
    }
    hasInitializedRef.current = true;

    const initializeAuth = async () => {
      if (__DEV__) {
        if (__DEV__) {
          console.log('🔑 AuthContext: Initializing auth...');
        }
      }
      await checkAuthStatus();
      if (__DEV__) {
        if (__DEV__) {
          console.log('🔑 AuthContext: Auth initialization complete');
        }
      }
    };

    // Set up the API client callback for auth errors
    setAuthErrorCallback(handleNotifyAuthError);

    initializeAuth();

    // Cleanup function to remove the callback
    return () => {
      setAuthErrorCallback(null);
    };
  }, []);

  const value = {
    isLoggedIn,
    isLoading,
    serverError,
    serverAlert,
    userProfile,
    clearServerAlert: () => setServerAlert(null),
    logout: handleLogout,
    signOut: handleLogout, // Alias for logout
    checkAuthStatus,
    notifyAuthError: handleNotifyAuthError,
    setUserProfile,
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
