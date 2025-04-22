import React from 'react';
import { render, act } from '@testing-library/react-native';
import { AuthProvider, useAuth } from '../authContext';
import * as authApi from '../authApi';
import * as biometricAuth from '../biometricAuth';

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

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Mock default values
    (authApi.isAuthenticated as jest.Mock).mockResolvedValue(false);
    (authApi.getUserProfile as jest.Mock).mockResolvedValue(null);
    (biometricAuth.isBiometricAvailable as jest.Mock).mockResolvedValue(false);
    (biometricAuth.isBiometricEnabled as jest.Mock).mockResolvedValue(false);
  });

  it('should initialize with default values', async () => {
    let contextValue: any;

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    // Verify default state
    expect(authApi.isAuthenticated).toHaveBeenCalled();
    expect(biometricAuth.isBiometricAvailable).toHaveBeenCalled();
    expect(biometricAuth.isBiometricEnabled).toHaveBeenCalled();
  });

  it('should update auth state when checking auth status', async () => {
    const mockUserProfile = {
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
      user_type: 'student' as const,
      is_admin: false,
      created_at: '2023-01-01',
      updated_at: '2023-01-01',
    };

    (authApi.isAuthenticated as jest.Mock).mockResolvedValue(true);
    (authApi.getUserProfile as jest.Mock).mockResolvedValue(mockUserProfile);

    let checkAuthStatus: () => Promise<boolean>;
    let contextValue: any;

    await act(async () => {
      const { getByTestId } = render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    expect(authApi.isAuthenticated).toHaveBeenCalled();
    expect(authApi.getUserProfile).toHaveBeenCalled();
  });

  it('should handle logout correctly', async () => {
    (authApi.logout as jest.Mock).mockResolvedValue(undefined);

    let logout: () => Promise<void>;

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    // Simulate logout
    await act(async () => {
      await useAuth().logout();
    });

    expect(authApi.logout).toHaveBeenCalled();
  });

  it('should handle biometric login correctly', async () => {
    const mockAuthResponse = {
      token: 'test-token',
      expiry: '2023-01-01',
      user: {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        user_type: 'student' as const,
        is_admin: false,
        created_at: '2023-01-01',
        updated_at: '2023-01-01',
      },
    };

    (authApi.authenticateWithBiometricsAndGetToken as jest.Mock).mockResolvedValue(mockAuthResponse);

    let loginWithBiometrics: () => Promise<boolean>;

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    // Simulate biometric login
    let result: boolean = false;
    await act(async () => {
      result = await useAuth().loginWithBiometrics();
    });

    expect(authApi.authenticateWithBiometricsAndGetToken).toHaveBeenCalled();
    expect(result).toBe(true);
  });

  it('should handle enabling biometrics correctly', async () => {
    (biometricAuth.enableBiometricAuth as jest.Mock).mockResolvedValue(true);

    let enableBiometrics: (email: string) => Promise<boolean>;

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    // Simulate enabling biometrics
    let result: boolean = false;
    await act(async () => {
      result = await useAuth().enableBiometrics('test@example.com');
    });

    expect(biometricAuth.enableBiometricAuth).toHaveBeenCalledWith('test@example.com');
    expect(result).toBe(true);
  });

  it('should handle disabling biometrics correctly', async () => {
    (biometricAuth.disableBiometricAuth as jest.Mock).mockResolvedValue(true);

    let disableBiometrics: () => Promise<boolean>;

    await act(async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    // Simulate disabling biometrics
    let result: boolean = false;
    await act(async () => {
      result = await useAuth().disableBiometrics();
    });

    expect(biometricAuth.disableBiometricAuth).toHaveBeenCalled();
    expect(result).toBe(true);
  });
});
