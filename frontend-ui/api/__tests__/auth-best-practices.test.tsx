import React from 'react';
import { Text } from 'react-native';
import TestRenderer, { act } from 'react-test-renderer';

import * as authApi from '../authApi';
import { AuthProvider, useAuth } from '../authContext';
import * as biometricAuth from '../biometricAuth';

// Mock API calls
jest.mock('../authApi', () => ({
  isAuthenticated: jest.fn(),
  logout: jest.fn(),
  getUserProfile: jest.fn(),
  authenticateWithBiometricsAndGetToken: jest.fn(),
  verifyEmailCode: jest.fn(),
}));

// Mock Secure Store
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

// Mock biometric authentication
jest.mock('../biometricAuth', () => ({
  isBiometricAvailable: jest.fn(),
  isBiometricEnabled: jest.fn(),
  enableBiometricAuth: jest.fn(),
  disableBiometricAuth: jest.fn(),
}));

// Mock the expo-router
jest.mock('expo-router', () => ({
  router: {
    replace: jest.fn(),
  },
}));

// Test component that uses the Auth context
const TestComponent = () => {
  const {
    isLoggedIn,
    userProfile,
    logout,
    loginWithBiometrics,
    biometricSupport,
    enableBiometrics,
    disableBiometrics,
  } = useAuth();

  return (
    <>
      <Text testID="authStatus">{isLoggedIn ? 'authenticated' : 'unauthenticated'}</Text>
      {userProfile && <Text testID="userData">{JSON.stringify(userProfile)}</Text>}
      <Text testID="logoutButton" onPress={logout}>
        Logout
      </Text>
      <Text testID="biometricLoginButton" onPress={loginWithBiometrics}>
        Biometric Login
      </Text>
      <Text testID="biometricsStatus">
        {biometricSupport.isAvailable ? 'available' : 'unavailable'} |
        {biometricSupport.isEnabled ? 'enabled' : 'disabled'}
      </Text>
      <Text testID="enableBiometricsButton" onPress={() => enableBiometrics('test@example.com')}>
        Enable Biometrics
      </Text>
      <Text testID="disableBiometricsButton" onPress={disableBiometrics}>
        Disable Biometrics
      </Text>
    </>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Set default mock values
    (biometricAuth.isBiometricAvailable as jest.Mock).mockResolvedValue(false);
    (biometricAuth.isBiometricEnabled as jest.Mock).mockResolvedValue(false);
  });

  it('should initialize with default values', async () => {
    // Render component
    const renderer = await createRendererWithAct();

    const authStatus = renderer.root.findByProps({ testID: 'authStatus' });
    expect(authStatus.props.children).toBe('unauthenticated');
  });

  it('should update auth state when user logs in', async () => {
    // Mock user profile data
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
      user_type: 'student',
      is_admin: false,
      created_at: '2023-01-01',
      updated_at: '2023-01-01',
    };

    // Setup mocks
    (authApi.isAuthenticated as jest.Mock).mockResolvedValue(true);
    (authApi.getUserProfile as jest.Mock).mockResolvedValue(mockUser);

    // Render component
    const renderer = await createRendererWithAct();

    // Assert - component should show authenticated status and user data
    const authStatus = renderer.root.findByProps({ testID: 'authStatus' });
    expect(authStatus.props.children).toBe('authenticated');

    const userData = renderer.root.findByProps({ testID: 'userData' });
    expect(JSON.parse(userData.props.children)).toEqual(mockUser);
  });

  it('should handle logout correctly', async () => {
    // Setup initial authenticated state
    (authApi.isAuthenticated as jest.Mock).mockResolvedValue(true);

    const mockUser = {
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
      user_type: 'student',
      is_admin: false,
      created_at: '2023-01-01',
      updated_at: '2023-01-01',
    };

    (authApi.getUserProfile as jest.Mock).mockResolvedValue(mockUser);

    // Render component
    const renderer = await createRendererWithAct();

    // Verify authenticated state
    expect(renderer.root.findByProps({ testID: 'authStatus' }).props.children).toBe(
      'authenticated'
    );

    // Perform logout
    await act(async () => {
      await renderer.root.findByProps({ testID: 'logoutButton' }).props.onPress();
    });

    // Verify logout was called
    expect(authApi.logout).toHaveBeenCalledTimes(1);
    expect(renderer.root.findByProps({ testID: 'authStatus' }).props.children).toBe(
      'unauthenticated'
    );
  });

  it('should handle biometric login', async () => {
    // Mock successful biometric login
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
      user_type: 'student',
      is_admin: false,
      created_at: '2023-01-01',
      updated_at: '2023-01-01',
    };

    const mockAuthResponse = {
      token: 'mock-token',
      expiry: '2023-12-31',
      user: mockUser,
    };

    (authApi.authenticateWithBiometricsAndGetToken as jest.Mock).mockResolvedValue(
      mockAuthResponse
    );

    // Render component in unauthenticated state
    (authApi.isAuthenticated as jest.Mock).mockResolvedValue(false);

    const renderer = await createRendererWithAct();

    // Verify unauthenticated state
    expect(renderer.root.findByProps({ testID: 'authStatus' }).props.children).toBe(
      'unauthenticated'
    );

    // Perform biometric login
    await act(async () => {
      await renderer.root.findByProps({ testID: 'biometricLoginButton' }).props.onPress();
    });

    // Verify biometric authentication was attempted
    expect(authApi.authenticateWithBiometricsAndGetToken).toHaveBeenCalledTimes(1);

    // Verify authenticated state after successful biometric login
    expect(renderer.root.findByProps({ testID: 'authStatus' }).props.children).toBe(
      'authenticated'
    );

    // Verify user profile is set
    const userData = renderer.root.findByProps({ testID: 'userData' });
    expect(JSON.parse(userData.props.children)).toEqual(mockUser);
  });

  it('should enable biometrics when requested', async () => {
    // Mock biometric availability
    (biometricAuth.isBiometricAvailable as jest.Mock).mockResolvedValue(true);
    (biometricAuth.enableBiometricAuth as jest.Mock).mockResolvedValue(true);

    // Render component
    const renderer = await createRendererWithAct();

    // Enable biometrics
    await act(async () => {
      await renderer.root.findByProps({ testID: 'enableBiometricsButton' }).props.onPress();
    });

    // Verify biometric auth was enabled
    expect(biometricAuth.enableBiometricAuth).toHaveBeenCalledWith('test@example.com');
  });

  it('should disable biometrics when requested', async () => {
    // Mock biometric state
    (biometricAuth.isBiometricAvailable as jest.Mock).mockResolvedValue(true);
    (biometricAuth.isBiometricEnabled as jest.Mock).mockResolvedValue(true);
    (biometricAuth.disableBiometricAuth as jest.Mock).mockResolvedValue(true);

    // Render component
    const renderer = await createRendererWithAct();

    // Disable biometrics
    await act(async () => {
      await renderer.root.findByProps({ testID: 'disableBiometricsButton' }).props.onPress();
    });

    // Verify biometric auth was disabled
    expect(biometricAuth.disableBiometricAuth).toHaveBeenCalledTimes(1);
  });
});

// Helper function to create a renderer with act
async function createRendererWithAct(): Promise<TestRenderer.ReactTestRenderer> {
  let renderer!: TestRenderer.ReactTestRenderer;

  await act(async () => {
    renderer = TestRenderer.create(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
  });

  return renderer;
}
