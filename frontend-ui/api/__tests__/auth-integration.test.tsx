import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import * as authApi from '../authApi';
import { AuthProvider, useAuth } from '../authContext';

// Mock the modules
jest.mock('../authApi');
jest.mock('expo-router', () => ({
  router: {
    replace: jest.fn(),
  },
}));
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
}));
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

// Test component that uses the auth context
const TestComponent = () => {
  const auth = useAuth();
  return (
    <div data-testid="auth-state">{auth.isLoggedIn ? 'authenticated' : 'unauthenticated'}</div>
  );
};

describe('Auth Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('handles unauthenticated state', async () => {
    // Setup mocks
    (authApi.isAuthenticated as jest.Mock).mockResolvedValue(false);

    // Render component
    let testRenderer: TestRenderer.ReactTestRenderer;
    await act(async () => {
      testRenderer = TestRenderer.create(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    // Verify
    expect(authApi.isAuthenticated).toHaveBeenCalled();
    const instance = testRenderer.root;
    const divElement = instance.findByType('div');
    expect(divElement.children[0]).toBe('unauthenticated');

    // Cleanup
    testRenderer.unmount();
  });

  it('handles authenticated state', async () => {
    // Setup mocks
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

    // Render component
    let testRenderer: TestRenderer.ReactTestRenderer;
    await act(async () => {
      testRenderer = TestRenderer.create(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );
    });

    // Wait for all async operations to complete
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Verify auth status
    const CheckAuthComponent = () => {
      const auth = useAuth();

      React.useEffect(() => {
        auth.checkAuthStatus();
      }, []);

      return null;
    };

    await act(async () => {
      TestRenderer.create(
        <AuthProvider>
          <CheckAuthComponent />
        </AuthProvider>
      );
    });

    // Verify calls
    expect(authApi.isAuthenticated).toHaveBeenCalled();
    expect(authApi.getUserProfile).toHaveBeenCalled();

    // Cleanup
    testRenderer.unmount();
  });
});
