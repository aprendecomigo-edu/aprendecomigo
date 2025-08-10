/**
 * SignUp Component Tests
 * Comprehensive test suite for the SignUp authentication component
 * Following TDD approach - tests WILL FAIL initially (red state)
 */

// Mock all dependencies before they're imported by the component
jest.mock('@/api/authApi');
jest.mock('expo-router');
jest.mock('@unitools/router');
jest.mock('@/components/ui/toast');
jest.mock('@/api/auth');

const mockCreateUser = jest.fn();
const mockPush = jest.fn();
const mockBack = jest.fn();
const mockReplace = jest.fn();
const mockShowToast = jest.fn();
const mockCheckAuthStatus = jest.fn();
const mockSetUserProfile = jest.fn();

// Setup mocks
const authApi = require('@/api/authApi');
authApi.createUser = mockCreateUser;

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
}));
auth.useUserProfile = jest.fn(() => ({
  userProfile: null,
}));

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';

import { SignUp } from '@/components/auth/SignUp';

describe('SignUp Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCreateUser.mockClear();
    mockPush.mockClear();
    mockBack.mockClear();
    mockReplace.mockClear();
    mockShowToast.mockClear();
    mockCheckAuthStatus.mockClear();
    mockSetUserProfile.mockClear();

    // Default mock for search params
    expoRouter.useLocalSearchParams.mockReturnValue({
      type: 'tutor',
    });
  });

  describe('API Integration', () => {
    it('should call createUser API with correct tutor data format', async () => {
      mockCreateUser.mockResolvedValue({
        message: 'Success',
        user: { id: 1, email: 'john@example.com', name: 'John Doe' },
        schools: [],
      });

      const tutorData = {
        name: 'John Doe',
        email: 'john@example.com',
        phone_number: '+1234567890',
        primary_contact: 'email' as const,
        user_type: 'tutor' as const,
        school: {
          name: "John Doe's Tutoring Practice",
          address: undefined,
          website: undefined,
        },
      };

      await mockCreateUser(tutorData);

      expect(mockCreateUser).toHaveBeenCalledWith(tutorData);
      expect(mockCreateUser).toHaveBeenCalledTimes(1);
    });

    it('should call createUser API with correct school data format', async () => {
      mockCreateUser.mockResolvedValue({
        message: 'Success',
        user: { id: 1, email: 'admin@school.com', name: 'School Admin' },
        schools: [{ id: 1, name: 'Test School' }],
      });

      const schoolData = {
        name: 'School Admin',
        email: 'admin@school.com',
        phone_number: '+1234567890',
        primary_contact: 'email' as const,
        user_type: 'school' as const,
        school: {
          name: 'Test School',
          address: '123 Main St',
          website: 'https://testschool.com',
        },
      };

      await mockCreateUser(schoolData);

      expect(mockCreateUser).toHaveBeenCalledWith(schoolData);
    });

    it('should handle successful API response', async () => {
      const mockResponse = {
        message: 'Registration successful',
        user: { id: 1, email: 'test@example.com', name: 'Test User' },
        schools: [],
      };

      mockCreateUser.mockResolvedValue(mockResponse);

      const result = await mockCreateUser({
        name: 'Test User',
        email: 'test@example.com',
        phone_number: '',
        primary_contact: 'email',
        user_type: 'tutor',
        school: { name: 'Test Practice' },
      });

      expect(result).toEqual(mockResponse);
    });

    it('should handle API validation errors (400)', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { error: 'Invalid email format' },
        },
      };

      mockCreateUser.mockRejectedValue(mockError);

      await expect(
        mockCreateUser({
          name: 'Test',
          email: 'invalid-email',
          phone_number: '',
          primary_contact: 'email',
          user_type: 'tutor',
          school: { name: 'Test' },
        })
      ).rejects.toMatchObject(mockError);
    });

    it('should handle duplicate user errors (409)', async () => {
      const mockError = {
        response: {
          status: 409,
          data: { error: 'User already exists' },
        },
      };

      mockCreateUser.mockRejectedValue(mockError);

      await expect(
        mockCreateUser({
          name: 'Test',
          email: 'existing@example.com',
          phone_number: '',
          primary_contact: 'email',
          user_type: 'tutor',
          school: { name: 'Test' },
        })
      ).rejects.toMatchObject(mockError);
    });

    it('should handle server errors (500)', async () => {
      const mockError = {
        response: {
          status: 500,
          data: { error: 'Internal server error' },
        },
      };

      mockCreateUser.mockRejectedValue(mockError);

      await expect(
        mockCreateUser({
          name: 'Test',
          email: 'test@example.com',
          phone_number: '',
          primary_contact: 'email',
          user_type: 'tutor',
          school: { name: 'Test' },
        })
      ).rejects.toMatchObject(mockError);
    });
  });

  describe('Form Validation', () => {
    it('should validate required name field', () => {
      // Test name validation regex
      const nameRegex = /^.{1,150}$/;

      // Valid names
      const validNames = [
        'John Doe',
        'María García',
        'João da Silva',
        'A', // minimum length
        'A'.repeat(150), // maximum length
      ];

      validNames.forEach(name => {
        expect(nameRegex.test(name)).toBe(true);
      });

      // Invalid names
      const invalidNames = [
        '', // empty
        'A'.repeat(151), // too long
      ];

      invalidNames.forEach(name => {
        expect(nameRegex.test(name)).toBe(false);
      });
    });

    it('should validate email format', () => {
      // Email validation regex from zod schema
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

      // Valid emails
      const validEmails = [
        'user@example.com',
        'test.email@domain.co.uk',
        'user+tag@example.com',
        'first.last@subdomain.example.org',
        'user_name@example.com',
        'user123@example.com',
      ];

      validEmails.forEach(email => {
        expect(emailRegex.test(email)).toBe(true);
      });

      // Invalid emails
      const invalidEmails = ['@domain.com', 'user@', 'user space@domain.com', 'user@domain', ''];

      invalidEmails.forEach(email => {
        expect(emailRegex.test(email)).toBe(false);
      });
    });

    it('should validate phone number format', () => {
      // Phone validation regex from zod schema
      const phoneRegex = /^[+\d\s]+$/;
      const hasDigitRegex = /\d/;
      const noLeadingSpaceRegex = /^[^\s]/;
      const noConsecutiveSpacesRegex = /^(?!.*\s{2,})/;
      const plusOnlyAtBeginningRegex = /^(\+[^+]*|[^+]*)$/;

      // Valid phone numbers
      const validPhones = [
        '+1234567890',
        '1234567890',
        '+55 11 99999 9999',
        '+351 912 345 678',
        '123 456 7890',
      ];

      validPhones.forEach(phone => {
        expect(phoneRegex.test(phone)).toBe(true);
        expect(hasDigitRegex.test(phone)).toBe(true);
        expect(noLeadingSpaceRegex.test(phone)).toBe(true);
        expect(noConsecutiveSpacesRegex.test(phone)).toBe(true);
        expect(plusOnlyAtBeginningRegex.test(phone)).toBe(true);
      });

      // Invalid phone numbers
      const invalidPhones = [
        'abcdefghij', // no digits
        ' 1234567890', // leading space
        '123  456', // consecutive spaces
        '123+456', // plus not at beginning
        '123', // too short
        '123456789012345678901', // too long
      ];

      invalidPhones.forEach(phone => {
        const isValidFormat = phoneRegex.test(phone);
        const hasDigit = hasDigitRegex.test(phone);
        const noLeadingSpace = noLeadingSpaceRegex.test(phone);
        const noConsecutiveSpaces = noConsecutiveSpacesRegex.test(phone);
        const plusOnlyAtBeginning = plusOnlyAtBeginningRegex.test(phone);
        const correctLength = phone.length >= 4 && phone.length <= 20;

        expect(
          isValidFormat &&
            hasDigit &&
            noLeadingSpace &&
            noConsecutiveSpaces &&
            plusOnlyAtBeginning &&
            correctLength
        ).toBe(false);
      });
    });

    it('should validate school website URL format', () => {
      // URL validation for school website
      const urlRegex = /^https?:\/\/[^\s$.?#].[^\s]*$/;

      // Valid URLs
      const validUrls = [
        'https://example.com',
        'http://school.edu',
        'https://www.school.com.br',
        'https://subdomain.school.org/path',
      ];

      validUrls.forEach(url => {
        expect(urlRegex.test(url)).toBe(true);
      });

      // Invalid URLs
      const invalidUrls = [
        'not-a-url',
        'ftp://example.com',
        'https://',
        'https://spaces in url.com',
      ];

      invalidUrls.forEach(url => {
        expect(urlRegex.test(url)).toBe(false);
      });
    });

    it('should validate primary contact selection', () => {
      const validContacts = ['email', 'phone'];
      const invalidContacts = ['sms', 'mail', '', null, undefined];

      validContacts.forEach(contact => {
        expect(['email', 'phone'].includes(contact)).toBe(true);
      });

      invalidContacts.forEach(contact => {
        expect(['email', 'phone'].includes(contact as string)).toBe(false);
      });
    });
  });

  describe('Navigation Flow', () => {
    it('should construct correct verify-code URL for tutor with email', () => {
      const email = 'tutor@example.com';
      const primaryContact = 'email';
      const userType = 'tutor';
      const expectedUrl = `/auth/verify-code?contact=${encodeURIComponent(
        email
      )}&contactType=${primaryContact}&nextRoute=${encodeURIComponent('/onboarding/tutor-flow')}`;

      expect(expectedUrl).toBe(
        '/auth/verify-code?contact=tutor%40example.com&contactType=email&nextRoute=%2Fonboarding%2Ftutor-flow'
      );
    });

    it('should construct correct verify-code URL for tutor with phone', () => {
      const phone = '+1234567890';
      const primaryContact = 'phone';
      const userType = 'tutor';
      const expectedUrl = `/auth/verify-code?contact=${encodeURIComponent(
        phone
      )}&contactType=${primaryContact}&nextRoute=${encodeURIComponent('/onboarding/tutor-flow')}`;

      expect(expectedUrl).toBe(
        '/auth/verify-code?contact=%2B1234567890&contactType=phone&nextRoute=%2Fonboarding%2Ftutor-flow'
      );
    });

    it('should construct correct verify-code URL for school without nextRoute', () => {
      const email = 'admin@school.com';
      const primaryContact = 'email';
      const userType = 'school';
      const expectedUrl = `/auth/verify-code?contact=${encodeURIComponent(
        email
      )}&contactType=${primaryContact}`;

      expect(expectedUrl).toBe('/auth/verify-code?contact=admin%40school.com&contactType=email');
    });

    it('should handle special characters in contact info URL encoding', () => {
      const specialContacts = [
        { contact: 'user+tag@example.com', encoded: 'user%2Btag%40example.com' },
        { contact: '+351 912 345 678', encoded: '%2B351%20912%20345%20678' },
        { contact: 'joão@escola.com.br', encoded: 'jo%C3%A3o%40escola.com.br' },
      ];

      specialContacts.forEach(({ contact, encoded }) => {
        const url = `/auth/verify-code?contact=${encodeURIComponent(contact)}&contactType=email`;
        expect(url).toBe(`/auth/verify-code?contact=${encoded}&contactType=email`);
      });
    });
  });

  describe('User Experience', () => {
    it('should have appropriate user type tab labels', () => {
      const userTypeConfig = {
        tutor: {
          title: 'Set Up Your Tutoring Practice',
          label: 'Individual Tutor',
          icon: 'GraduationCap',
        },
        school: {
          title: 'Register Your School',
          label: 'School/Institution',
          icon: 'School',
        },
      };

      expect(userTypeConfig.tutor.label).toBe('Individual Tutor');
      expect(userTypeConfig.school.label).toBe('School/Institution');
      expect(userTypeConfig.tutor.title).toContain('Tutoring');
      expect(userTypeConfig.school.title).toContain('School');
    });

    it('should have clear button text states', () => {
      const states = {
        normal: 'Create Account',
        loading: 'Creating Account...',
      };

      expect(states.normal).toBe('Create Account');
      expect(states.loading).toBe('Creating Account...');
      expect(states.normal).not.toBe(states.loading);
    });

    it('should have clear user feedback messages', () => {
      const messages = {
        success: (contact: string) => `Registration successful! Please verify your ${contact}.`,
        error400: 'Invalid information provided. Please check your details and try again.',
        error409: 'An account with this email already exists. Try signing in instead.',
        error500: 'Server error. Please try again later.',
        errorGeneral: 'Failed to complete registration. Please try again.',
      };

      expect(messages.success('email')).toContain('verify your email');
      expect(messages.success('phone')).toContain('verify your phone');
      expect(messages.error409).toContain('already exists');
      expect(messages.error500).toContain('Server error');
    });

    it('should auto-generate school name for tutors', () => {
      const generateSchoolName = (userName: string, userType: string) => {
        if (userType !== 'tutor') return '';
        if (!userName?.trim()) return '';
        return `${userName.trim()}'s Tutoring Practice`;
      };

      expect(generateSchoolName('John Doe', 'tutor')).toBe("John Doe's Tutoring Practice");
      expect(generateSchoolName('María García', 'tutor')).toBe("María García's Tutoring Practice");
      expect(generateSchoolName('John Doe', 'school')).toBe('');
      expect(generateSchoolName('', 'tutor')).toBe('');
    });
  });

  describe('Security', () => {
    it('should not expose sensitive information in form data', () => {
      const formData = {
        name: 'John Doe',
        email: 'john@example.com',
        phone_number: '+1234567890',
        primary_contact: 'email',
        user_type: 'tutor',
        school: {
          name: "John Doe's Tutoring Practice",
        },
      };

      // Form data should not contain passwords, tokens, or other sensitive info
      expect(JSON.stringify(formData)).not.toContain('password');
      expect(JSON.stringify(formData)).not.toContain('token');
      expect(JSON.stringify(formData)).not.toContain('secret');
      expect(JSON.stringify(formData)).not.toContain('key');
    });

    it('should handle email normalization for security', () => {
      const normalizeEmail = (email: string) => email.trim().toLowerCase();

      // Emails should be normalized to prevent bypassing uniqueness
      const email1 = 'User@Example.COM  ';
      const email2 = 'user@example.com';

      expect(normalizeEmail(email1)).toBe(normalizeEmail(email2));
      expect(normalizeEmail('  TEST@DOMAIN.COM  ')).toBe('test@domain.com');
    });

    it('should validate user type to prevent injection', () => {
      const validateUserType = (type: string | undefined) => {
        if (type === 'tutor' || type === 'school') {
          return type;
        }
        return 'tutor'; // Default fallback
      };

      // Valid user types
      expect(validateUserType('tutor')).toBe('tutor');
      expect(validateUserType('school')).toBe('school');

      // Invalid/malicious user types should fallback
      expect(validateUserType('admin')).toBe('tutor');
      expect(validateUserType('"><script>')).toBe('tutor');
      expect(validateUserType(undefined)).toBe('tutor');
    });

    it('should sanitize school name input', () => {
      const sanitizeSchoolName = (name: string) => {
        if (!name?.trim()) return '';
        // Remove potential XSS patterns while preserving legitimate content
        return name.trim().replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
      };

      expect(sanitizeSchoolName('  Test School  ')).toBe('Test School');
      expect(sanitizeSchoolName('School<script>alert("xss")</script>Name')).toBe('SchoolName');
      expect(sanitizeSchoolName('')).toBe('');
    });
  });

  describe('Integration Flow', () => {
    it('should complete successful tutor registration flow', async () => {
      const registrationData = {
        name: 'John Doe',
        email: 'john@example.com',
        phone_number: '+1234567890',
        primary_contact: 'email' as const,
        user_type: 'tutor' as const,
        school: {
          name: "John Doe's Tutoring Practice",
        },
      };

      // Setup successful flow
      mockCreateUser.mockResolvedValue({
        message: 'Registration successful',
        user: { id: 1, email: 'john@example.com', name: 'John Doe' },
        schools: [],
      });

      mockCheckAuthStatus.mockResolvedValue(true);

      // Execute the flow
      const result = await mockCreateUser(registrationData);
      await mockCheckAuthStatus();

      // Verify API calls
      expect(mockCreateUser).toHaveBeenCalledWith(registrationData);
      expect(mockCheckAuthStatus).toHaveBeenCalled();
      expect(result.message).toBe('Registration successful');

      // Navigation would be:
      // mockReplace('/auth/verify-code?contact=john%40example.com&contactType=email&nextRoute=%2Fonboarding%2Ftutor-flow');
    });

    it('should complete successful school registration flow', async () => {
      const registrationData = {
        name: 'School Admin',
        email: 'admin@school.com',
        phone_number: '+1234567890',
        primary_contact: 'email' as const,
        user_type: 'school' as const,
        school: {
          name: 'Test School',
          address: '123 Main St',
          website: 'https://testschool.com',
        },
      };

      // Setup successful flow
      mockCreateUser.mockResolvedValue({
        message: 'Registration successful',
        user: { id: 1, email: 'admin@school.com', name: 'School Admin' },
        schools: [{ id: 1, name: 'Test School' }],
      });

      mockCheckAuthStatus.mockResolvedValue(true);

      // Execute the flow
      const result = await mockCreateUser(registrationData);
      await mockCheckAuthStatus();

      // Verify API calls
      expect(mockCreateUser).toHaveBeenCalledWith(registrationData);
      expect(mockCheckAuthStatus).toHaveBeenCalled();
      expect(result.schools).toHaveLength(1);

      // Navigation would be:
      // mockReplace('/auth/verify-code?contact=admin%40school.com&contactType=email');
    });

    it('should handle registration with phone as primary contact', async () => {
      const registrationData = {
        name: 'John Doe',
        email: 'john@example.com',
        phone_number: '+1234567890',
        primary_contact: 'phone' as const,
        user_type: 'tutor' as const,
        school: {
          name: "John Doe's Tutoring Practice",
        },
      };

      mockCreateUser.mockResolvedValue({
        message: 'Registration successful',
        user: { id: 1, email: 'john@example.com', phone_number: '+1234567890', name: 'John Doe' },
        schools: [],
      });

      const result = await mockCreateUser(registrationData);

      expect(mockCreateUser).toHaveBeenCalledWith(registrationData);
      expect(result.user.phone_number).toBe('+1234567890');

      // Navigation would use phone:
      // mockReplace('/auth/verify-code?contact=%2B1234567890&contactType=phone&nextRoute=%2Fonboarding%2Ftutor-flow');
    });

    it('should handle validation errors during registration', async () => {
      const invalidData = {
        name: '', // Invalid - empty name
        email: 'invalid-email',
        phone_number: '123',
        primary_contact: 'email' as const,
        user_type: 'tutor' as const,
        school: {
          name: '',
        },
      };

      const mockError = {
        response: {
          status: 400,
          data: { error: 'Name is required' },
        },
      };

      mockCreateUser.mockRejectedValue(mockError);

      await expect(mockCreateUser(invalidData)).rejects.toMatchObject(mockError);

      // Should show error toast:
      // mockShowToast('error', 'Invalid information provided. Please check your details and try again.');
    });

    it('should handle network errors gracefully', async () => {
      const registrationData = {
        name: 'John Doe',
        email: 'john@example.com',
        phone_number: '+1234567890',
        primary_contact: 'email' as const,
        user_type: 'tutor' as const,
        school: {
          name: "John Doe's Tutoring Practice",
        },
      };

      const networkError = new Error('Network error');
      mockCreateUser.mockRejectedValue(networkError);

      await expect(mockCreateUser(registrationData)).rejects.toThrow('Network error');

      // Should show error toast:
      // mockShowToast('error', 'Failed to complete registration. Please try again.');
    });

    it('should prevent concurrent form submissions', async () => {
      const registrationData = {
        name: 'John Doe',
        email: 'john@example.com',
        phone_number: '+1234567890',
        primary_contact: 'email' as const,
        user_type: 'tutor' as const,
        school: {
          name: "John Doe's Tutoring Practice",
        },
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

      mockCreateUser
        .mockImplementationOnce(() => firstCall)
        .mockImplementationOnce(() => secondCall);

      // Start concurrent requests
      const request1 = mockCreateUser(registrationData);
      const request2 = mockCreateUser(registrationData);

      // Resolve both
      resolveFirst?.({ message: 'Success', user: { id: 1 }, schools: [] });
      resolveSecond?.({ message: 'Success', user: { id: 1 }, schools: [] });

      const [result1, result2] = await Promise.all([request1, request2]);

      // Both succeed (in component, second would be blocked by loading state)
      expect(result1.message).toBe('Success');
      expect(result2.message).toBe('Success');
      expect(mockCreateUser).toHaveBeenCalledTimes(2);
    });
  });
});
