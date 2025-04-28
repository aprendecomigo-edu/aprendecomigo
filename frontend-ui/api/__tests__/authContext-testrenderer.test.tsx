import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AuthProvider, useAuth } from '../authContext';
import * as authApi from '../authApi';
import * as biometricAuth from '../biometricAuth';
import { router } from 'expo-router';

// Mock the modules
jest.mock('../authApi');
jest.mock('../biometricAuth');
jest.mock('expo-router', () => ({
  router: {
    replace: jest.fn(),
  },
}));

// Test component to access context
const TestComponent = () => {
  const auth = useAuth();
  return null;
};

describe('AuthContext with TestRenderer', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Mock default values
    (authApi.isAuthenticated as jest.Mock).mockResolvedValue(false);
    (authApi.getUserProfile as jest.Mock).mockResolvedValue(null);
    (biometricAuth.isBiometricAvailable as jest.Mock).mockResolvedValue(false);
    (biometricAuth.isBiometricEnabled as jest.Mock).mockResolvedValue(false);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('should initialize with default values', async () => {
    let testRenderer: TestRenderer.ReactTestRenderer | undefined;

    await act(async () => {
      testRenderer = TestRenderer.create(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    // Verify default state
    expect(authApi.isAuthenticated).toHaveBeenCalled();
    expect(biometricAuth.isBiometricAvailable).toHaveBeenCalled();
    expect(biometricAuth.isBiometricEnabled).toHaveBeenCalled();

    // Clean up
    testRenderer?.unmount();
  });

  it('should update auth state when checking auth status', async () => {
    const mockUserProfile = {
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
      user_type: 'student',
      is_admin: false,
      created_at: '2023-01-01',
      updated_at: '2023-01-01',
    };

    (authApi.isAuthenticated as jest.Mock).mockResolvedValue(true);
    (authApi.getUserProfile as jest.Mock).mockResolvedValue(mockUserProfile);

    // Create a component that calls checkAuthStatus
    const AuthCheckerComponent = () => {
      const auth = useAuth();

      React.useEffect(() => {
        auth.checkAuthStatus();
      }, []);

      return null;
    };

    let testRenderer: TestRenderer.ReactTestRenderer | undefined;

    await act(async () => {
      testRenderer = TestRenderer.create(
        <AuthProvider>
          <AuthCheckerComponent />
        </AuthProvider>
      );
    });

    expect(authApi.isAuthenticated).toHaveBeenCalled();
    expect(authApi.getUserProfile).toHaveBeenCalled();

    testRenderer?.unmount();
  });

  it('should handle logout correctly', async () => {
    (authApi.logout as jest.Mock).mockResolvedValue(undefined);

    // Create a component that triggers logout
    const LogoutComponent = () => {
      const auth = useAuth();

      React.useEffect(() => {
        auth.logout();
      }, []);

      return null;
    };

    let testRenderer: TestRenderer.ReactTestRenderer | undefined;

    await act(async () => {
      testRenderer = TestRenderer.create(
        <AuthProvider>
          <LogoutComponent />
        </AuthProvider>
      );
    });

    expect(authApi.logout).toHaveBeenCalled();
    expect(router.replace).toHaveBeenCalledWith('/auth/signin');

    testRenderer?.unmount();
  });

  it('should handle biometric login correctly', async () => {
    const mockAuthResponse = {
      token: 'test-token',
      expiry: '2023-01-01',
      user: {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        user_type: 'student',
        is_admin: false,
        created_at: '2023-01-01',
        updated_at: '2023-01-01',
      },
    };

    (authApi.authenticateWithBiometricsAndGetToken as jest.Mock).mockResolvedValue(
      mockAuthResponse
    );

    // Create a component that triggers biometric login
    const BiometricLoginComponent = () => {
      const auth = useAuth();
      const [result, setResult] = React.useState<boolean | null>(null);

      React.useEffect(() => {
        const login = async () => {
          const success = await auth.loginWithBiometrics();
          setResult(success);
        };
        login();
      }, []);

      return null;
    };

    let testRenderer: TestRenderer.ReactTestRenderer | undefined;

    await act(async () => {
      testRenderer = TestRenderer.create(
        <AuthProvider>
          <BiometricLoginComponent />
        </AuthProvider>
      );
    });

    expect(authApi.authenticateWithBiometricsAndGetToken).toHaveBeenCalled();

    testRenderer?.unmount();
  });

  it('should handle enabling biometrics correctly', async () => {
    (biometricAuth.enableBiometricAuth as jest.Mock).mockResolvedValue(true);

    // Create a component that enables biometrics
    const EnableBiometricsComponent = () => {
      const auth = useAuth();
      const [result, setResult] = React.useState<boolean | null>(null);

      React.useEffect(() => {
        const enable = async () => {
          const success = await auth.enableBiometrics('test@example.com');
          setResult(success);
        };
        enable();
      }, []);

      return null;
    };

    let testRenderer: TestRenderer.ReactTestRenderer | undefined;

    await act(async () => {
      testRenderer = TestRenderer.create(
        <AuthProvider>
          <EnableBiometricsComponent />
        </AuthProvider>
      );
    });

    expect(biometricAuth.enableBiometricAuth).toHaveBeenCalledWith('test@example.com');

    testRenderer?.unmount();
  });

  it('should handle disabling biometrics correctly', async () => {
    (biometricAuth.disableBiometricAuth as jest.Mock).mockResolvedValue(true);

    // Create a component that disables biometrics
    const DisableBiometricsComponent = () => {
      const auth = useAuth();
      const [result, setResult] = React.useState<boolean | null>(null);

      React.useEffect(() => {
        const disable = async () => {
          const success = await auth.disableBiometrics();
          setResult(success);
        };
        disable();
      }, []);

      return null;
    };

    let testRenderer: TestRenderer.ReactTestRenderer | undefined;

    await act(async () => {
      testRenderer = TestRenderer.create(
        <AuthProvider>
          <DisableBiometricsComponent />
        </AuthProvider>
      );
    });

    expect(biometricAuth.disableBiometricAuth).toHaveBeenCalled();

    testRenderer?.unmount();
  });
});
