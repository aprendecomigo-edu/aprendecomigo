import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { VerifyCode } from '../verify-code';
import { verifyEmailCode } from '@/api/authApi';
import { useAuth } from '@/api/authContext';
import useRouter from '@unitools/router';
import { useLocalSearchParams } from 'expo-router';

// Mock navigation and auth hooks
jest.mock('expo-router', () => ({
  useLocalSearchParams: jest.fn(),
}));

jest.mock('@unitools/router', () => ({
  __esModule: true,
  default: jest.fn(),
}));

jest.mock('@/api/authContext', () => ({
  useAuth: jest.fn(),
}));

// Mock API calls
jest.mock('@/api/authApi', () => ({
  verifyEmailCode: jest.fn(),
}));

describe('VerifyCode Screen', () => {
  // Setup mocks
  const mockReplace = jest.fn();
  const mockBack = jest.fn();
  const mockCheckAuthStatus = jest.fn();
  const mockEnableBiometrics = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock router
    (useRouter as jest.Mock).mockReturnValue({
      replace: mockReplace,
      back: mockBack,
    });

    // Mock local search params
    (useLocalSearchParams as jest.Mock).mockReturnValue({
      contact: 'test@example.com',
      contactType: 'email',
    });

    // Mock auth context
    (useAuth as jest.Mock).mockReturnValue({
      checkAuthStatus: mockCheckAuthStatus,
      biometricSupport: {
        isAvailable: true,
        isEnabled: false,
      },
      enableBiometrics: mockEnableBiometrics,
    });

    // Default API response
    (verifyEmailCode as jest.Mock).mockResolvedValue({
      token: 'test-token',
      expiry: '2024-12-31T23:59:59Z',
      user: {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        user_type: 'teacher',
        is_admin: false,
        created_at: '2023-06-15T10:00:00Z',
        updated_at: '2023-06-15T10:00:00Z',
      },
    });

    mockEnableBiometrics.mockResolvedValue(true);
  });

  it('renders correctly with email contact', () => {
    const { getByText, getByPlaceholderText } = render(<VerifyCode />);
    expect(getByText('Verify Code')).toBeTruthy();
    expect(getByText('Enter the verification code sent to test@example.com')).toBeTruthy();
    expect(getByPlaceholderText('Enter the verification code')).toBeTruthy();
  });

  it('renders correctly with phone contact', () => {
    (useLocalSearchParams as jest.Mock).mockReturnValue({
      contact: '+1234567890',
      contactType: 'phone',
    });

    const { getByText, getByPlaceholderText } = render(<VerifyCode />);
    expect(getByText('Verify Code')).toBeTruthy();
    expect(getByText('Enter the verification code sent to +1234567890')).toBeTruthy();
    expect(getByPlaceholderText('Enter the verification code')).toBeTruthy();
  });

  it('verifies email code successfully', async () => {
    const { getByPlaceholderText, getByText } = render(<VerifyCode />);

    // Enter verification code
    fireEvent.changeText(getByPlaceholderText('Enter the verification code'), '123456');

    // Submit form
    fireEvent.press(getByText('Verify Code'));

    await waitFor(() => {
      // Check API was called with correct data
      expect(verifyEmailCode).toHaveBeenCalledWith({
        email: 'test@example.com',
        code: '123456',
      });

      // Check auth status was refreshed
      expect(mockCheckAuthStatus).toHaveBeenCalled();

      // Check navigation to dashboard
      expect(mockReplace).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('verifies phone code successfully', async () => {
    (useLocalSearchParams as jest.Mock).mockReturnValue({
      contact: '+1234567890',
      contactType: 'phone',
    });

    const { getByPlaceholderText, getByText } = render(<VerifyCode />);

    // Enter verification code
    fireEvent.changeText(getByPlaceholderText('Enter the verification code'), '123456');

    // Submit form
    fireEvent.press(getByText('Verify Code'));

    await waitFor(() => {
      // Check API was called with correct data
      expect(verifyEmailCode).toHaveBeenCalledWith({
        phone: '+1234567890',
        code: '123456',
      });

      // Check auth status was refreshed
      expect(mockCheckAuthStatus).toHaveBeenCalled();

      // Check navigation to dashboard
      expect(mockReplace).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('enables biometric authentication if selected', async () => {
    const { getByPlaceholderText, getByText, getByLabelText } = render(<VerifyCode />);

    // Enter verification code
    fireEvent.changeText(getByPlaceholderText('Enter the verification code'), '123456');

    // Enable biometric login
    fireEvent.press(getByLabelText('Enable biometric login'));

    // Submit form
    fireEvent.press(getByText('Verify Code'));

    await waitFor(() => {
      // Check biometric enablement was called with the contact value
      expect(mockEnableBiometrics).toHaveBeenCalledWith('test@example.com');
    });
  });

  it('handles API errors gracefully', async () => {
    // Mock API to throw an error
    (verifyEmailCode as jest.Mock).mockRejectedValue(new Error('Invalid code'));

    const { getByPlaceholderText, getByText } = render(<VerifyCode />);

    // Enter verification code
    fireEvent.changeText(getByPlaceholderText('Enter the verification code'), '123456');

    // Submit form
    fireEvent.press(getByText('Verify Code'));

    await waitFor(() => {
      // API should be called
      expect(verifyEmailCode).toHaveBeenCalled();

      // Navigation should not happen
      expect(mockReplace).not.toHaveBeenCalled();
    });
  });
});
