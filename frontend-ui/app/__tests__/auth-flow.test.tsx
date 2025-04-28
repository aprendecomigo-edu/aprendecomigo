import React from 'react';
import { Platform } from 'react-native';
import { render, waitFor } from '@testing-library/react-native';
import RootLayout from '../_layout';
import * as authApi from '@/api/authApi';

// Mock modules
jest.mock('@/api/authApi');
jest.mock('expo-font');
jest.mock('expo-splash-screen', () => ({
  preventAutoHideAsync: jest.fn(),
  hideAsync: jest.fn(),
}));
jest.mock('@/components/useColorScheme', () => ({
  useColorScheme: () => 'light',
}));
jest.mock('expo-router', () => ({
  router: {
    push: jest.fn(),
    replace: jest.fn(),
  },
  Link: jest.fn(),
  Redirect: ({ href }: { href: string }) => (
    <div data-testid={`redirect-to-${href.replace('/', '')}`} />
  ),
  Stack: {
    Screen: ({ name }: { name: string }) => <div data-testid={`screen-${name}`} />,
  },
}));

// Mock platform-specific code to test both web and mobile
const mockPlatform = (platform: string): (() => void) => {
  const originalPlatform = Platform.OS;
  jest.spyOn(Platform, 'OS', 'get').mockReturnValue(platform);
  return () => {
    jest.spyOn(Platform, 'OS', 'get').mockReturnValue(originalPlatform);
  };
};

describe('Authentication Flow', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Set default mock returns
    (authApi.isAuthenticated as jest.Mock).mockResolvedValue(false);
    (authApi.getUserProfile as jest.Mock).mockResolvedValue(null);
  });

  describe('on Mobile (iOS/Android)', () => {
    let resetPlatform: () => void;

    beforeEach(() => {
      resetPlatform = mockPlatform('ios');
    });

    afterEach(() => {
      resetPlatform();
    });

    it('should redirect to login screen when not authenticated', async () => {
      (authApi.isAuthenticated as jest.Mock).mockResolvedValue(false);

      const { getByTestId } = render(<RootLayout />);

      await waitFor(() => {
        expect(authApi.isAuthenticated).toHaveBeenCalled();
      });

      // Should redirect to auth/signin
      await waitFor(() => {
        expect(getByTestId('redirect-to-authsignin')).toBeTruthy();
      });
    });

    it('should navigate to dashboard when authenticated', async () => {
      // Mock successful authentication
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

      const { getByTestId } = render(<RootLayout />);

      await waitFor(() => {
        expect(authApi.isAuthenticated).toHaveBeenCalled();
        expect(authApi.getUserProfile).toHaveBeenCalled();
      });

      // Should redirect to dashboard
      await waitFor(() => {
        expect(getByTestId('redirect-to-dashboarddashboard-layout')).toBeTruthy();
      });
    });
  });

  describe('on Web', () => {
    let resetPlatform: () => void;

    beforeEach(() => {
      resetPlatform = mockPlatform('web');
    });

    afterEach(() => {
      resetPlatform();
    });

    it('should redirect to login screen when not authenticated on web', async () => {
      (authApi.isAuthenticated as jest.Mock).mockResolvedValue(false);

      const { getByTestId } = render(<RootLayout />);

      await waitFor(() => {
        expect(authApi.isAuthenticated).toHaveBeenCalled();
      });

      // Should redirect to auth/signin
      await waitFor(() => {
        expect(getByTestId('redirect-to-authsignin')).toBeTruthy();
      });
    });

    it('should navigate to dashboard when authenticated on web', async () => {
      // Mock successful authentication
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

      const { getByTestId } = render(<RootLayout />);

      await waitFor(() => {
        expect(authApi.isAuthenticated).toHaveBeenCalled();
        expect(authApi.getUserProfile).toHaveBeenCalled();
      });

      // Should redirect to dashboard
      await waitFor(() => {
        expect(getByTestId('redirect-to-dashboarddashboard-layout')).toBeTruthy();
      });
    });
  });
});
