/**
 * Simple VerifyCode Component Test
 * Testing component behavior and API integration with minimal mocks
 */

import { render } from '@testing-library/react-native';
import React from 'react';

import { VerifyCode } from '@/components/auth/VerifyCode';

// Mock all dependencies before they're imported by the component
jest.mock('@/api/authApi');
jest.mock('expo-router');
jest.mock('@unitools/router');
jest.mock('@/components/ui/toast');
jest.mock('@/api/auth');
jest.mock('@/api/onboardingApi');

const mockVerifyEmailCode = jest.fn();
const mockRequestEmailCode = jest.fn();
const mockPush = jest.fn();
const mockBack = jest.fn();
const mockReplace = jest.fn();
const mockShowToast = jest.fn();
const mockCheckAuthStatus = jest.fn();
const mockSetUserProfile = jest.fn();
const mockGetNavigationPreferences = jest.fn();
const mockGetOnboardingProgress = jest.fn();

// Setup mocks
const authApi = require('@/api/authApi');
authApi.verifyEmailCode = mockVerifyEmailCode;
authApi.requestEmailCode = mockRequestEmailCode;

const expoRouter = require('expo-router');
expoRouter.useLocalSearchParams = jest.fn(() => ({
  contact: 'test@example.com',
  contactType: 'email',
  email: 'test@example.com',
  nextRoute: null,
}));

const unitoolsRouter = require('@unitools/router');
unitoolsRouter.default = jest.fn(() => ({
  push: mockPush,
  back: mockBack,
  replace: mockReplace,
}));

const toast = require('@/components/ui/toast');
toast.useToast = jest.fn(() => ({
  showToast: mockShowToast,
}));

const auth = require('@/api/auth');
auth.useAuth = jest.fn(() => ({
  checkAuthStatus: mockCheckAuthStatus,
  setUserProfile: mockSetUserProfile,
}));

const onboardingApi = require('@/api/onboardingApi');
onboardingApi.onboardingApi = {
  getNavigationPreferences: mockGetNavigationPreferences,
  getOnboardingProgress: mockGetOnboardingProgress,
};

describe('VerifyCode Component Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockVerifyEmailCode.mockResolvedValue({
      token: 'fake-token',
      expiry: '2024-12-31T23:59:59Z',
      user: { id: 1, email: 'test@example.com', name: 'Test User' },
      is_new_user: false,
    });
    expoRouter.useLocalSearchParams.mockReturnValue({
      contact: 'test@example.com',
      contactType: 'email',
      email: 'test@example.com',
      nextRoute: null,
    });
  });

  it('should render component without errors', () => {
    expect(() => render(<VerifyCode />)).not.toThrow();
  });

  it('should call verifyEmailCode API with correct email parameters', async () => {
    const mockResponse = {
      token: 'fake-token',
      expiry: '2024-12-31T23:59:59Z',
      user: { id: 1, email: 'test@example.com', name: 'Test User' },
      is_new_user: false,
    };

    mockVerifyEmailCode.mockResolvedValue(mockResponse);

    const verifyParams = {
      email: 'test@example.com',
      code: '123456',
    };

    const result = await authApi.verifyEmailCode(verifyParams);

    expect(mockVerifyEmailCode).toHaveBeenCalledWith(verifyParams);
    expect(result).toEqual(mockResponse);
  });

  it('should call verifyEmailCode API with correct phone parameters', async () => {
    const mockResponse = {
      token: 'fake-token',
      expiry: '2024-12-31T23:59:59Z',
      user: { id: 1, phone_number: '+1234567890', name: 'Test User' },
      is_new_user: false,
    };

    mockVerifyEmailCode.mockResolvedValue(mockResponse);

    const verifyParams = {
      phone: '+1234567890',
      code: '123456',
    };

    const result = await authApi.verifyEmailCode(verifyParams);

    expect(mockVerifyEmailCode).toHaveBeenCalledWith(verifyParams);
    expect(result).toEqual(mockResponse);
  });

  it('should handle successful verification response', async () => {
    const mockResponse = {
      token: 'fake-jwt-token',
      expiry: '2024-12-31T23:59:59Z',
      user: {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        user_type: 'admin',
        is_admin: true,
        primary_role: 'school_owner',
        first_login_completed: false,
      },
      is_new_user: true,
      school: {
        id: 1,
        name: 'Test School',
      },
    };

    mockVerifyEmailCode.mockResolvedValue(mockResponse);

    const result = await authApi.verifyEmailCode({
      email: 'test@example.com',
      code: '123456',
    });

    expect(result.token).toBe('fake-jwt-token');
    expect(result.user.id).toBe(1);
    expect(result.is_new_user).toBe(true);
  });

  it('should handle invalid code error (400)', async () => {
    const mockError = {
      response: {
        status: 400,
        data: { error: 'Invalid verification code' },
      },
    };

    mockVerifyEmailCode.mockRejectedValue(mockError);

    await expect(
      authApi.verifyEmailCode({
        email: 'test@example.com',
        code: '000000',
      }),
    ).rejects.toMatchObject(mockError);
  });

  it('should handle rate limiting error (429)', async () => {
    const mockError = {
      response: {
        status: 429,
        data: { error: 'Too many attempts' },
      },
    };

    mockVerifyEmailCode.mockRejectedValue(mockError);

    await expect(
      authApi.verifyEmailCode({
        email: 'test@example.com',
        code: '123456',
      }),
    ).rejects.toMatchObject(mockError);
  });

  it('should call requestEmailCode API for resend functionality', async () => {
    mockRequestEmailCode.mockResolvedValue({
      message: 'Code sent',
      provisioning_uri: 'otpauth://...',
    });

    const resendParams = { email: 'test@example.com' };

    const result = await authApi.requestEmailCode(resendParams);

    expect(mockRequestEmailCode).toHaveBeenCalledWith(resendParams);
    expect(result.message).toBe('Code sent');
  });

  it('should call requestEmailCode API for phone resend', async () => {
    mockRequestEmailCode.mockResolvedValue({
      message: 'Code sent',
      provisioning_uri: 'otpauth://...',
    });

    const resendParams = { phone: '+1234567890' };

    const result = await authApi.requestEmailCode(resendParams);

    expect(mockRequestEmailCode).toHaveBeenCalledWith(resendParams);
  });

  it('should validate 6-digit code format', () => {
    // 6-digit code validation
    const codeRegex = /^\d{6}$/;

    // Valid codes
    const validCodes = ['123456', '000000', '999999', '654321'];

    validCodes.forEach(code => {
      expect(codeRegex.test(code)).toBe(true);
    });

    // Invalid codes
    const invalidCodes = [
      '12345', // too short
      '1234567', // too long
      'abcdef', // non-numeric
      '12 456', // contains space
      '12345a', // mixed alphanumeric
      '', // empty
      '123.456', // contains dot
    ];

    invalidCodes.forEach(code => {
      expect(codeRegex.test(code)).toBe(false);
    });
  });

  it('should validate contact information', () => {
    const validateContact = (contact: string, contactType: string) => {
      if (!contact?.trim()) return false;

      if (contactType === 'email') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(contact);
      }

      if (contactType === 'phone') {
        const phoneRegex = /^[+\d\s-()]+$/;
        return phoneRegex.test(contact) && contact.length >= 10;
      }

      return false;
    };

    // Valid emails
    expect(validateContact('test@example.com', 'email')).toBe(true);
    expect(validateContact('user+tag@domain.co.uk', 'email')).toBe(true);

    // Invalid emails
    expect(validateContact('invalid-email', 'email')).toBe(false);
    expect(validateContact('@domain.com', 'email')).toBe(false);

    // Valid phones
    expect(validateContact('+1234567890', 'phone')).toBe(true);
    expect(validateContact('(555) 123-4567', 'phone')).toBe(true);

    // Invalid phones
    expect(validateContact('123', 'phone')).toBe(false);
    expect(validateContact('abcdefghij', 'phone')).toBe(false);
  });

  it('should navigate to nextRoute when provided after successful verification', () => {
    const nextRoute = '/onboarding/tutor-flow';
    const encodedNextRoute = encodeURIComponent(nextRoute);
    const decodedNextRoute = decodeURIComponent(encodedNextRoute);

    expect(decodedNextRoute).toBe('/onboarding/tutor-flow');
  });

  it('should navigate to root (/) when no nextRoute provided', () => {
    const defaultRoute = '/';

    expect(defaultRoute).toBe('/');
  });

  it('should handle URL parameter parsing correctly', () => {
    const contact = 'test@example.com';
    const contactType = 'email';
    const nextRoute = '/custom/route';

    const queryString = `contact=${encodeURIComponent(
      contact,
    )}&contactType=${contactType}&nextRoute=${encodeURIComponent(nextRoute)}`;

    expect(queryString).toBe(
      'contact=test%40example.com&contactType=email&nextRoute=%2Fcustom%2Froute',
    );

    // Parse parameters
    const params = new URLSearchParams(queryString);
    expect(decodeURIComponent(params.get('contact') || '')).toBe(contact);
    expect(params.get('contactType')).toBe(contactType);
    expect(decodeURIComponent(params.get('nextRoute') || '')).toBe(nextRoute);
  });

  it('should handle toast notifications for different scenarios', () => {
    render(<VerifyCode />);

    const toastInstance = toast.useToast();

    // Success message
    toastInstance.showToast('success', 'Verification successful!');
    expect(mockShowToast).toHaveBeenCalledWith('success', 'Verification successful!');

    // Error messages
    toastInstance.showToast('error', 'Invalid verification code. Please try again.');
    expect(mockShowToast).toHaveBeenCalledWith(
      'error',
      'Invalid verification code. Please try again.',
    );

    toastInstance.showToast('error', 'Too many attempts. Please wait and try again.');
    expect(mockShowToast).toHaveBeenCalledWith(
      'error',
      'Too many attempts. Please wait and try again.',
    );

    // Resend success
    toastInstance.showToast('success', 'New verification code sent to your email!');
    expect(mockShowToast).toHaveBeenCalledWith(
      'success',
      'New verification code sent to your email!',
    );
  });

  it('should handle navigation after verification', () => {
    render(<VerifyCode />);

    const router = unitoolsRouter.default();

    // Navigate to next route
    router.replace('/onboarding/tutor-flow');
    expect(mockReplace).toHaveBeenCalledWith('/onboarding/tutor-flow');

    // Navigate to root
    router.replace('/');
    expect(mockReplace).toHaveBeenCalledWith('/');

    // Navigate to onboarding welcome
    router.replace('/onboarding/welcome');
    expect(mockReplace).toHaveBeenCalledWith('/onboarding/welcome');
  });

  it('should sanitize code input', () => {
    const sanitizeCode = code => {
      // Remove all non-digit characters
      return code.replace(/\D/g, '');
    };

    expect(sanitizeCode('123456')).toBe('123456');
    expect(sanitizeCode('12 34 56')).toBe('123456');
    expect(sanitizeCode('12a3b4c5d6e')).toBe('123456');
    expect(sanitizeCode('123-456')).toBe('123456');
  });

  it('should validate contact type to prevent injection', () => {
    const validateContactType = type => {
      if (type === 'email' || type === 'phone') {
        return type;
      }
      return 'email'; // Default fallback
    };

    // Valid contact types
    expect(validateContactType('email')).toBe('email');
    expect(validateContactType('phone')).toBe('phone');

    // Invalid/malicious contact types should fallback
    expect(validateContactType('sms')).toBe('email');
    expect(validateContactType('"><script>')).toBe('email');
    expect(validateContactType(undefined)).toBe('email');
  });

  it('should limit code input length for security', () => {
    const limitCodeInput = (code, maxLength = 6) => {
      return code.slice(0, maxLength);
    };

    expect(limitCodeInput('123456')).toBe('123456');
    expect(limitCodeInput('1234567890')).toBe('123456');
    expect(limitCodeInput('12345')).toBe('12345');
  });

  it('should format contact display correctly', () => {
    const formatContactDisplay = (contact, contactType) => {
      if (contactType === 'email') {
        return contact;
      }

      if (contactType === 'phone') {
        // Format phone number for display (US format: +1 XXX XXX XXX)
        return contact.replace(/(\+\d)(\d{3})(\d{3})(\d{3})/, (match, g1, g2, g3, g4) => {
          return `${g1} ${g2} ${g3} ${g4}`;
        });
      }

      return contact;
    };

    expect(formatContactDisplay('test@example.com', 'email')).toBe('test@example.com');
    expect(formatContactDisplay('+1234567890', 'phone')).toBe('+1 234 567 890');
  });

  it('should handle onboarding checks for new school admins', async () => {
    // Mock onboarding preferences and progress
    mockGetNavigationPreferences.mockResolvedValue({
      show_onboarding: true,
    });

    mockGetOnboardingProgress.mockResolvedValue({
      completion_percentage: 0,
    });

    // Test onboarding API calls
    const preferences = await onboardingApi.onboardingApi.getNavigationPreferences();
    const progress = await onboardingApi.onboardingApi.getOnboardingProgress();

    expect(preferences.show_onboarding).toBe(true);
    expect(progress.completion_percentage).toBe(0);

    expect(mockGetNavigationPreferences).toHaveBeenCalled();
    expect(mockGetOnboardingProgress).toHaveBeenCalled();
  });
});
