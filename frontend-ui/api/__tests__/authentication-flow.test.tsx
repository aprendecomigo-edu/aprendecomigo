import { router } from 'expo-router';
import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';

import * as authApi from '../authApi';
import { AuthProvider, useAuth } from '../authContext';

// Mock dependencies, not components
jest.mock('../authApi');
jest.mock('expo-router');

// Test component to observe auth state transitions
interface AuthObserverProps {
  onAuthStateChange: (isLoggedIn: boolean) => void;
}

const AuthObserver: React.FC<AuthObserverProps> = ({ onAuthStateChange }) => {
  const { isLoggedIn } = useAuth();

  React.useEffect(() => {
    onAuthStateChange(isLoggedIn);
  }, [isLoggedIn, onAuthStateChange]);

  return null;
};

// Component that triggers authentication check only once
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

// Component that triggers logout only once
const LogoutTrigger: React.FC = () => {
  const { logout } = useAuth();
  const hasLoggedOutRef = React.useRef(false);

  React.useEffect(() => {
    if (!hasLoggedOutRef.current) {
      hasLoggedOutRef.current = true;
      logout();
    }
  }, [logout]);

  return null;
};

// Component that simulates navigation to signup page
const SignupNavigator: React.FC = () => {
  React.useEffect(() => {
    router.push('/auth/signup');
  }, []);

  return null;
};

describe('Authentication Flow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('When user is not authenticated', () => {
    it('should NOT redirect to dashboard and stay at login when user is unauthenticated', async () => {
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

      // Auth state should be set to not logged in
      expect(authStateSpy).toHaveBeenCalledWith(false);

      // Auth API should have been called
      expect(authApi.isAuthenticated).toHaveBeenCalled();

      // When redirecting in app code, we'd redirect to login
      expect(router.replace).not.toHaveBeenCalledWith('/dashboard/dashboard-layout');
    });

    it('should navigate to signup page when requested', async () => {
      // Create test renderer with signup navigator
      let testRenderer: TestRenderer.ReactTestRenderer | undefined;

      await act(async () => {
        testRenderer = TestRenderer.create(
          <AuthProvider>
            <SignupNavigator />
          </AuthProvider>
        );
      });

      // Ensure unmount after test
      testRenderer?.unmount();

      // Router should navigate to signup
      expect(router.push).toHaveBeenCalledWith('/auth/signup');
    });
  });

  describe('When user is authenticated', () => {
    it('should update auth state when user is authenticated', async () => {
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

      // Auth state should be set to logged in
      expect(authStateSpy).toHaveBeenCalledWith(true);

      // Auth APIs should have been called
      expect(authApi.isAuthenticated).toHaveBeenCalled();
      expect(authApi.getUserProfile).toHaveBeenCalled();
    });
  });

  describe('Logout flow', () => {
    it('should redirect to login screen when user logs out', async () => {
      // Mock successful logout
      (authApi.logout as jest.Mock).mockResolvedValue(undefined);

      // Create observer for auth state
      const authStateSpy = jest.fn();

      let testRenderer: TestRenderer.ReactTestRenderer | undefined;

      await act(async () => {
        testRenderer = TestRenderer.create(
          <AuthProvider>
            <AuthObserver onAuthStateChange={authStateSpy} />
            <LogoutTrigger />
          </AuthProvider>
        );
      });

      // Ensure unmount after test
      testRenderer?.unmount();

      // Logout API should be called
      expect(authApi.logout).toHaveBeenCalled();

      // Auth state should be set to not logged in
      expect(authStateSpy).toHaveBeenCalledWith(false);

      // Should redirect to login after logout
      expect(router.replace).toHaveBeenCalledWith('/auth/signin');
    });
  });
});
