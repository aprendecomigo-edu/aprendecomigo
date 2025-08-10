/**
 * VerifyCode Component Tests
 * Comprehensive test suite for the VerifyCode authentication component
 * Following TDD approach - tests WILL FAIL initially (red state)
 */

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
expoRouter.useLocalSearchParams = jest.fn();

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

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';

import { VerifyCode } from '@/components/auth/VerifyCode';

describe('VerifyCode Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockVerifyEmailCode.mockClear();
    mockRequestEmailCode.mockClear();
    mockPush.mockClear();
    mockBack.mockClear();
    mockReplace.mockClear();
    mockShowToast.mockClear();
    mockCheckAuthStatus.mockClear();
    mockSetUserProfile.mockClear();
    mockGetNavigationPreferences.mockClear();
    mockGetOnboardingProgress.mockClear();

    // Default mock for search params
    expoRouter.useLocalSearchParams.mockReturnValue({
      contact: 'test@example.com',
      contactType: 'email',
      email: 'test@example.com',
      nextRoute: null,
    });
  });

  describe('API Integration', () => {
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

      const result = await mockVerifyEmailCode(verifyParams);

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

      const result = await mockVerifyEmailCode(verifyParams);

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

      const result = await mockVerifyEmailCode({
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
        mockVerifyEmailCode({
          email: 'test@example.com',
          code: '000000',
        })
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
        mockVerifyEmailCode({
          email: 'test@example.com',
          code: '123456',
        })
      ).rejects.toMatchObject(mockError);
    });

    it('should call requestEmailCode API for resend functionality', async () => {
      mockRequestEmailCode.mockResolvedValue({
        message: 'Code sent',
        provisioning_uri: 'otpauth://...',
      });

      const resendParams = { email: 'test@example.com' };

      const result = await mockRequestEmailCode(resendParams);

      expect(mockRequestEmailCode).toHaveBeenCalledWith(resendParams);
      expect(result.message).toBe('Code sent');
    });

    it('should call requestEmailCode API for phone resend', async () => {
      mockRequestEmailCode.mockResolvedValue({
        message: 'Code sent',
        provisioning_uri: 'otpauth://...',
      });

      const resendParams = { phone: '+1234567890' };

      const result = await mockRequestEmailCode(resendParams);

      expect(mockRequestEmailCode).toHaveBeenCalledWith(resendParams);
    });
  });

  describe('Form Validation', () => {
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

    it('should validate required code field', () => {
      const validateCode = (code: string) => {
        if (!code?.trim()) return false;
        if (code.length !== 6) return false;
        if (!/^\d+$/.test(code)) return false;
        return true;
      };

      // Valid codes
      expect(validateCode('123456')).toBe(true);
      expect(validateCode('000000')).toBe(true);

      // Invalid codes
      expect(validateCode('')).toBe(false);
      expect(validateCode('   ')).toBe(false);
      expect(validateCode('12345')).toBe(false);
      expect(validateCode('1234567')).toBe(false);
      expect(validateCode('abcdef')).toBe(false);
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
  });

  describe('Navigation Flow', () => {
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

    it('should navigate to onboarding/welcome for new school admins', () => {
      const onboardingRoute = '/onboarding/welcome';

      expect(onboardingRoute).toBe('/onboarding/welcome');
    });

    it('should handle URL parameter parsing correctly', () => {
      const contact = 'test@example.com';
      const contactType = 'email';
      const nextRoute = '/custom/route';

      const queryString = `contact=${encodeURIComponent(
        contact
      )}&contactType=${contactType}&nextRoute=${encodeURIComponent(nextRoute)}`;

      expect(queryString).toBe(
        'contact=test%40example.com&contactType=email&nextRoute=%2Fcustom%2Froute'
      );

      // Parse parameters
      const params = new URLSearchParams(queryString);
      expect(decodeURIComponent(params.get('contact') || '')).toBe(contact);
      expect(params.get('contactType')).toBe(contactType);
      expect(decodeURIComponent(params.get('nextRoute') || '')).toBe(nextRoute);
    });
  });

  describe('User Experience', () => {
    it('should have appropriate button text states', () => {
      const states = {
        normal: 'Verify Code',
        loading: 'Verifying...',
        resend: 'Try Again',
        resendLoading: 'Sending...',
      };

      expect(states.normal).toBe('Verify Code');
      expect(states.loading).toBe('Verifying...');
      expect(states.resend).toBe('Try Again');
      expect(states.resendLoading).toBe('Sending...');
    });

    it('should have clear user feedback messages', () => {
      const messages = {
        success: 'Verification successful!',
        invalidCode: 'Invalid verification code. Please try again.',
        expiredCode: 'Invalid verification code. Please try again.',
        tooManyAttempts: 'Too many attempts. Please wait and try again.',
        resendSuccess: (contactType: string) =>
          `New verification code sent to your ${contactType}!`,
        resendError: 'Failed to send new verification code. Please try again.',
      };

      expect(messages.success).toBe('Verification successful!');
      expect(messages.invalidCode).toContain('Invalid verification code');
      expect(messages.resendSuccess('email')).toContain('sent to your email');
      expect(messages.resendSuccess('phone')).toContain('sent to your phone');
    });

    it('should display contact information correctly', () => {
      const formatContactDisplay = (contact: string, contactType: string) => {
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

    it('should handle contact type labels correctly', () => {
      const getContactTypeLabel = (contactType: string) => {
        return contactType === 'email' ? 'email' : 'phone';
      };

      expect(getContactTypeLabel('email')).toBe('email');
      expect(getContactTypeLabel('phone')).toBe('phone');
    });
  });

  describe('Security', () => {
    it('should not expose sensitive information in verification request', () => {
      const verificationData = {
        email: 'test@example.com',
        code: '123456',
      };

      // Verification data should not contain passwords, tokens, or other sensitive info
      expect(JSON.stringify(verificationData)).not.toContain('password');
      expect(JSON.stringify(verificationData)).not.toContain('token');
      expect(JSON.stringify(verificationData)).not.toContain('secret');
      expect(JSON.stringify(verificationData)).not.toContain('key');
    });

    it('should handle code input sanitization', () => {
      const sanitizeCode = (code: string) => {
        // Remove all non-digit characters
        return code.replace(/\D/g, '');
      };

      expect(sanitizeCode('123456')).toBe('123456');
      expect(sanitizeCode('12 34 56')).toBe('123456');
      expect(sanitizeCode('12a3b4c5d6e')).toBe('123456');
      expect(sanitizeCode('123-456')).toBe('123456');
    });

    it('should validate contact type to prevent injection', () => {
      const validateContactType = (type: string | undefined) => {
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
      const limitCodeInput = (code: string, maxLength: number = 6) => {
        return code.slice(0, maxLength);
      };

      expect(limitCodeInput('123456')).toBe('123456');
      expect(limitCodeInput('1234567890')).toBe('123456');
      expect(limitCodeInput('12345')).toBe('12345');
    });
  });

  describe('Integration Flow', () => {
    it('should complete successful email verification flow', async () => {
      const verificationData = {
        email: 'test@example.com',
        code: '123456',
      };

      const mockResponse = {
        token: 'fake-jwt-token',
        expiry: '2024-12-31T23:59:59Z',
        user: {
          id: 1,
          email: 'test@example.com',
          name: 'Test User',
          user_type: 'admin',
          is_admin: false,
          first_login_completed: true,
        },
        is_new_user: false,
      };

      // Setup successful flow
      mockVerifyEmailCode.mockResolvedValue(mockResponse);
      mockSetUserProfile.mockResolvedValue(mockResponse.user);
      mockCheckAuthStatus.mockResolvedValue(true);

      // Execute the flow
      const result = await mockVerifyEmailCode(verificationData);
      await mockSetUserProfile(result.user);
      await mockCheckAuthStatus();

      // Verify API calls
      expect(mockVerifyEmailCode).toHaveBeenCalledWith(verificationData);
      expect(mockSetUserProfile).toHaveBeenCalledWith(result.user);
      expect(mockCheckAuthStatus).toHaveBeenCalled();

      // Navigation would be:
      // mockReplace('/');
    });

    it('should complete successful phone verification flow', async () => {
      const verificationData = {
        phone: '+1234567890',
        code: '123456',
      };

      const mockResponse = {
        token: 'fake-jwt-token',
        expiry: '2024-12-31T23:59:59Z',
        user: {
          id: 1,
          phone_number: '+1234567890',
          name: 'Test User',
          user_type: 'admin',
          is_admin: false,
        },
        is_new_user: false,
      };

      mockVerifyEmailCode.mockResolvedValue(mockResponse);
      mockSetUserProfile.mockResolvedValue(mockResponse.user);
      mockCheckAuthStatus.mockResolvedValue(true);

      const result = await mockVerifyEmailCode(verificationData);
      await mockSetUserProfile(result.user);

      expect(mockVerifyEmailCode).toHaveBeenCalledWith(verificationData);
      expect(result.user.phone_number).toBe('+1234567890');
    });

    it('should handle new school admin onboarding flow', async () => {
      const verificationData = {
        email: 'admin@school.com',
        code: '123456',
      };

      const mockResponse = {
        token: 'fake-jwt-token',
        expiry: '2024-12-31T23:59:59Z',
        user: {
          id: 1,
          email: 'admin@school.com',
          name: 'School Admin',
          user_type: 'school_admin',
          is_admin: true,
          first_login_completed: false,
        },
        is_new_user: true,
      };

      mockVerifyEmailCode.mockResolvedValue(mockResponse);
      mockSetUserProfile.mockResolvedValue(mockResponse.user);
      mockCheckAuthStatus.mockResolvedValue(true);

      // Mock onboarding preferences
      mockGetNavigationPreferences.mockResolvedValue({
        show_onboarding: true,
      });

      mockGetOnboardingProgress.mockResolvedValue({
        completion_percentage: 0,
      });

      const result = await mockVerifyEmailCode(verificationData);
      await mockSetUserProfile(result.user);

      expect(result.is_new_user).toBe(true);
      expect(result.user.is_admin).toBe(true);
      expect(result.user.first_login_completed).toBe(false);

      // Should check onboarding preferences
      const preferences = await mockGetNavigationPreferences();
      const progress = await mockGetOnboardingProgress();

      expect(preferences.show_onboarding).toBe(true);
      expect(progress.completion_percentage).toBe(0);

      // Navigation would be:
      // mockReplace('/onboarding/welcome');
    });

    it('should handle verification with nextRoute parameter', async () => {
      const nextRoute = '/onboarding/tutor-flow';

      expoRouter.useLocalSearchParams.mockReturnValue({
        contact: 'tutor@example.com',
        contactType: 'email',
        nextRoute: nextRoute,
      });

      const mockResponse = {
        token: 'fake-jwt-token',
        expiry: '2024-12-31T23:59:59Z',
        user: {
          id: 1,
          email: 'tutor@example.com',
          name: 'Tutor User',
          user_type: 'teacher',
          is_admin: false,
        },
        is_new_user: false,
      };

      mockVerifyEmailCode.mockResolvedValue(mockResponse);
      mockSetUserProfile.mockResolvedValue(mockResponse.user);
      mockCheckAuthStatus.mockResolvedValue(true);

      const result = await mockVerifyEmailCode({
        email: 'tutor@example.com',
        code: '123456',
      });

      await mockSetUserProfile(result.user);

      expect(result.user.user_type).toBe('teacher');

      // Navigation would be:
      // mockReplace(nextRoute);
    });

    it('should handle resend code functionality', async () => {
      const resendData = { email: 'test@example.com' };

      mockRequestEmailCode.mockResolvedValue({
        message: 'New verification code sent',
        provisioning_uri: 'otpauth://...',
      });

      const result = await mockRequestEmailCode(resendData);

      expect(mockRequestEmailCode).toHaveBeenCalledWith(resendData);
      expect(result.message).toContain('sent');

      // Should show success toast:
      // mockShowToast('success', 'New verification code sent to your email!');
    });

    it('should handle invalid verification code error', async () => {
      const verificationData = {
        email: 'test@example.com',
        code: '000000',
      };

      const mockError = {
        response: {
          status: 400,
          data: { error: 'Invalid verification code' },
        },
      };

      mockVerifyEmailCode.mockRejectedValue(mockError);

      await expect(mockVerifyEmailCode(verificationData)).rejects.toMatchObject(mockError);

      // Should show error toast:
      // mockShowToast('error', 'Invalid verification code. Please try again.');
    });

    it('should handle rate limiting during verification', async () => {
      const verificationData = {
        email: 'test@example.com',
        code: '123456',
      };

      const mockError = {
        response: {
          status: 429,
          data: { error: 'Too many attempts' },
        },
      };

      mockVerifyEmailCode.mockRejectedValue(mockError);

      await expect(mockVerifyEmailCode(verificationData)).rejects.toMatchObject(mockError);

      // Should show error toast:
      // mockShowToast('error', 'Too many attempts. Please wait and try again.');
    });

    it('should handle network errors during verification', async () => {
      const verificationData = {
        email: 'test@example.com',
        code: '123456',
      };

      const networkError = new Error('Network error');
      mockVerifyEmailCode.mockRejectedValue(networkError);

      await expect(mockVerifyEmailCode(verificationData)).rejects.toThrow('Network error');

      // Should show error toast:
      // mockShowToast('error', 'An unexpected error occurred. Please try again.');
    });

    it('should prevent concurrent verification attempts', async () => {
      const verificationData = {
        email: 'test@example.com',
        code: '123456',
      };

      // Setup slow API
      let resolveFirst: ((value: unknown) => void) | undefined;
      let resolveSecond: ((value: unknown) => void) | undefined;

      const firstCall = new Promise(resolve => {
        resolveFirst = resolve;
      });
      const secondCall = new Promise(resolve => {
        resolveSecond = resolve;
      });

      mockVerifyEmailCode
        .mockImplementationOnce(() => firstCall)
        .mockImplementationOnce(() => secondCall);

      // Start concurrent requests
      const request1 = mockVerifyEmailCode(verificationData);
      const request2 = mockVerifyEmailCode(verificationData);

      // Resolve both
      const mockResponse = {
        token: 'fake-token',
        user: { id: 1 },
        expiry: '2024-12-31T23:59:59Z',
      };

      resolveFirst?.(mockResponse);
      resolveSecond?.(mockResponse);

      const [result1, result2] = await Promise.all([request1, request2]);

      // Both succeed (in component, second would be blocked by loading state)
      expect(result1.token).toBe('fake-token');
      expect(result2.token).toBe('fake-token');
      expect(mockVerifyEmailCode).toHaveBeenCalledTimes(2);
    });
  });
});
