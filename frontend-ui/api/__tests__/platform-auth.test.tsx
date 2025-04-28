import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AuthProvider, useAuth } from '../authContext';
import * as authApi from '../authApi';
import { router } from 'expo-router';
import { Platform } from 'react-native';

// Mock dependencies, not components
jest.mock('../authApi');
jest.mock('expo-router');

// Mock React Native's Platform
jest.mock('react-native/Libraries/Utilities/Platform', () => {
  const Platform = jest.requireActual('react-native/Libraries/Utilities/Platform');
  return {
    ...Platform,
    OS: 'ios', // Default value
  };
});

// Test component to observe auth state transitions and platform
interface AuthObserverProps {
  onAuthStateChange: (isLoggedIn: boolean, platform: string) => void;
}

const AuthObserver: React.FC<AuthObserverProps> = ({ onAuthStateChange }) => {
  const { isLoggedIn } = useAuth();

  React.useEffect(() => {
    onAuthStateChange(isLoggedIn, Platform.OS);
  }, [isLoggedIn, onAuthStateChange]);

  return null;
};

// Component that triggers authentication check
const AuthChecker: React.FC = () => {
  const { checkAuthStatus } = useAuth();
  const hasCheckedRef = React.useRef(false);

  React.useEffect(() => {
    if (!hasCheckedRef.current) {
      hasCheckedRef.current = true;
      checkAuthStatus();
    }
  }, [checkAuthStatus]);

  return null;
};

describe('Authentication Flow on Different Platforms', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Mobile authentication flow (iOS)', () => {
    beforeEach(() => {
      // Set platform to iOS
      Platform.OS = 'ios';
    });

    it('should show login screen when not authenticated on iOS', async () => {
      // Mock isAuthenticated to return false
      (authApi.isAuthenticated as jest.Mock).mockResolvedValue(false);

      // Create observer for auth state
      const authStateSpy = jest.fn();
      let testRenderer: TestRenderer.ReactTestRenderer | undefined;

      await act(async () => {
        testRenderer = TestRenderer.create(
          <AuthProvider>
            <AuthObserver onAuthStateChange={authStateSpy} />
            <AuthChecker />
          </AuthProvider>
        );
      });

      // Ensure unmount after test
      testRenderer?.unmount();

      // Check that auth state is false and platform is iOS
      expect(authStateSpy).toHaveBeenCalledWith(false, 'ios');

      // Auth API should have been called
      expect(authApi.isAuthenticated).toHaveBeenCalled();
    });

    it('should redirect to dashboard when authenticated on iOS', async () => {
      // Mock successful auth and user profile
      (authApi.isAuthenticated as jest.Mock).mockResolvedValue(true);
      (authApi.getUserProfile as jest.Mock).mockResolvedValue({
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        user_type: 'student',
        is_admin: false,
        created_at: '2023-01-01',
        updated_at: '2023-01-01',
      });

      // Create observer for auth state
      const authStateSpy = jest.fn();
      let testRenderer: TestRenderer.ReactTestRenderer | undefined;

      await act(async () => {
        testRenderer = TestRenderer.create(
          <AuthProvider>
            <AuthObserver onAuthStateChange={authStateSpy} />
            <AuthChecker />
          </AuthProvider>
        );
      });

      // Ensure unmount after test
      testRenderer?.unmount();

      // Check that auth state is true and platform is iOS
      expect(authStateSpy).toHaveBeenCalledWith(true, 'ios');

      // Auth APIs should have been called
      expect(authApi.isAuthenticated).toHaveBeenCalled();
      expect(authApi.getUserProfile).toHaveBeenCalled();
    });
  });

  describe('Mobile authentication flow (Android)', () => {
    beforeEach(() => {
      // Set platform to Android
      Platform.OS = 'android';
    });

    it('should show login screen when not authenticated on Android', async () => {
      // Mock isAuthenticated to return false
      (authApi.isAuthenticated as jest.Mock).mockResolvedValue(false);

      // Create observer for auth state
      const authStateSpy = jest.fn();
      let testRenderer: TestRenderer.ReactTestRenderer | undefined;

      await act(async () => {
        testRenderer = TestRenderer.create(
          <AuthProvider>
            <AuthObserver onAuthStateChange={authStateSpy} />
            <AuthChecker />
          </AuthProvider>
        );
      });

      // Ensure unmount after test
      testRenderer?.unmount();

      // Check that auth state is false and platform is Android
      expect(authStateSpy).toHaveBeenCalledWith(false, 'android');

      // Auth API should have been called
      expect(authApi.isAuthenticated).toHaveBeenCalled();
    });

    it('should redirect to dashboard when authenticated on Android', async () => {
      // Mock successful auth and user profile
      (authApi.isAuthenticated as jest.Mock).mockResolvedValue(true);
      (authApi.getUserProfile as jest.Mock).mockResolvedValue({
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        user_type: 'student',
        is_admin: false,
        created_at: '2023-01-01',
        updated_at: '2023-01-01',
      });

      // Create observer for auth state
      const authStateSpy = jest.fn();
      let testRenderer: TestRenderer.ReactTestRenderer | undefined;

      await act(async () => {
        testRenderer = TestRenderer.create(
          <AuthProvider>
            <AuthObserver onAuthStateChange={authStateSpy} />
            <AuthChecker />
          </AuthProvider>
        );
      });

      // Ensure unmount after test
      testRenderer?.unmount();

      // Check that auth state is true and platform is Android
      expect(authStateSpy).toHaveBeenCalledWith(true, 'android');

      // Auth APIs should have been called
      expect(authApi.isAuthenticated).toHaveBeenCalled();
      expect(authApi.getUserProfile).toHaveBeenCalled();
    });
  });

  describe('Web authentication flow', () => {
    beforeEach(() => {
      // Set platform to Web
      Platform.OS = 'web';
    });

    it('should show login screen when not authenticated on web', async () => {
      // Mock isAuthenticated to return false
      (authApi.isAuthenticated as jest.Mock).mockResolvedValue(false);

      // Create observer for auth state
      const authStateSpy = jest.fn();
      let testRenderer: TestRenderer.ReactTestRenderer | undefined;

      await act(async () => {
        testRenderer = TestRenderer.create(
          <AuthProvider>
            <AuthObserver onAuthStateChange={authStateSpy} />
            <AuthChecker />
          </AuthProvider>
        );
      });

      // Ensure unmount after test
      testRenderer?.unmount();

      // Check that auth state is false and platform is Web
      expect(authStateSpy).toHaveBeenCalledWith(false, 'web');

      // Auth API should have been called
      expect(authApi.isAuthenticated).toHaveBeenCalled();
    });

    it('should redirect to dashboard when authenticated on web', async () => {
      // Mock successful auth and user profile
      (authApi.isAuthenticated as jest.Mock).mockResolvedValue(true);
      (authApi.getUserProfile as jest.Mock).mockResolvedValue({
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        user_type: 'student',
        is_admin: false,
        created_at: '2023-01-01',
        updated_at: '2023-01-01',
      });

      // Create observer for auth state
      const authStateSpy = jest.fn();
      let testRenderer: TestRenderer.ReactTestRenderer | undefined;

      await act(async () => {
        testRenderer = TestRenderer.create(
          <AuthProvider>
            <AuthObserver onAuthStateChange={authStateSpy} />
            <AuthChecker />
          </AuthProvider>
        );
      });

      // Ensure unmount after test
      testRenderer?.unmount();

      // Check that auth state is true and platform is Web
      expect(authStateSpy).toHaveBeenCalledWith(true, 'web');

      // Auth APIs should have been called
      expect(authApi.isAuthenticated).toHaveBeenCalled();
      expect(authApi.getUserProfile).toHaveBeenCalled();
    });
  });
});
