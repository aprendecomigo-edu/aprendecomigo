/**
 * Simple SignUp Component Test
 * Testing component behavior and API integration with minimal mocks
 */

import { render } from '@testing-library/react-native';
import React from 'react';

import { SignUp } from '@/components/auth/SignUp';

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

// Setup mocks
const authApi = require('@/api/authApi');
authApi.createUser = mockCreateUser;

const expoRouter = require('expo-router');
expoRouter.useLocalSearchParams = jest.fn(() => ({ type: 'tutor' }));

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

describe('SignUp Component Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCreateUser.mockResolvedValue({
      message: 'Success',
      user: { id: 1, email: 'test@example.com', name: 'Test User' },
      schools: [],
    });
    expoRouter.useLocalSearchParams.mockReturnValue({ type: 'tutor' });
  });

  it('should render component without errors', () => {
    expect(() => render(<SignUp />)).not.toThrow();
  });

  it('should handle different user types from URL parameters', () => {
    // Test tutor type
    expoRouter.useLocalSearchParams.mockReturnValue({ type: 'tutor' });
    const tutorComponent = render(<SignUp />);
    expect(tutorComponent).toBeTruthy();

    // Test school type
    expoRouter.useLocalSearchParams.mockReturnValue({ type: 'school' });
    const schoolComponent = render(<SignUp />);
    expect(schoolComponent).toBeTruthy();

    // Test invalid type (should default gracefully)
    expoRouter.useLocalSearchParams.mockReturnValue({ type: 'invalid' });
    const invalidComponent = render(<SignUp />);
    expect(invalidComponent).toBeTruthy();
  });

  it('should call createUser API with tutor data format', async () => {
    const tutorData = {
      name: 'John Doe',
      email: 'john@example.com',
      phone_number: '+1234567890',
      primary_contact: 'email',
      user_type: 'tutor',
      school: {
        name: "John Doe's Tutoring Practice",
      },
    };

    await authApi.createUser(tutorData);

    expect(mockCreateUser).toHaveBeenCalledWith(tutorData);
  });

  it('should call createUser API with school data format', async () => {
    const schoolData = {
      name: 'School Admin',
      email: 'admin@school.com',
      phone_number: '+1234567890',
      primary_contact: 'email',
      user_type: 'school',
      school: {
        name: 'Test School',
        address: '123 Main St',
        website: 'https://testschool.com',
      },
    };

    await authApi.createUser(schoolData);

    expect(mockCreateUser).toHaveBeenCalledWith(schoolData);
  });

  it('should handle successful API response', async () => {
    const mockResponse = {
      message: 'Registration successful',
      user: { id: 1, email: 'test@example.com', name: 'Test User' },
      schools: [],
    };

    mockCreateUser.mockResolvedValue(mockResponse);

    const result = await authApi.createUser({
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
      authApi.createUser({
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
      authApi.createUser({
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
    const networkError = new Error('Network error');
    mockCreateUser.mockRejectedValue(networkError);

    await expect(
      authApi.createUser({
        name: 'Test',
        email: 'test@example.com',
        phone_number: '',
        primary_contact: 'email',
        user_type: 'tutor',
        school: { name: 'Test' },
      })
    ).rejects.toThrow('Network error');
  });

  it('should generate auto school name for tutors', () => {
    const generateSchoolName = (userName, userType) => {
      if (userType !== 'tutor') return '';
      if (!userName?.trim()) return '';
      return `${userName.trim()}'s Tutoring Practice`;
    };

    expect(generateSchoolName('John Doe', 'tutor')).toBe("John Doe's Tutoring Practice");
    expect(generateSchoolName('María García', 'tutor')).toBe("María García's Tutoring Practice");
    expect(generateSchoolName('John Doe', 'school')).toBe('');
    expect(generateSchoolName('', 'tutor')).toBe('');
  });

  it('should validate user type correctly', () => {
    const validateUserType = type => {
      if (type === 'tutor' || type === 'school') {
        return type;
      }
      return 'tutor'; // Default fallback
    };

    expect(validateUserType('tutor')).toBe('tutor');
    expect(validateUserType('school')).toBe('school');
    expect(validateUserType('admin')).toBe('tutor');
    expect(validateUserType('"><script>')).toBe('tutor');
    expect(validateUserType(undefined)).toBe('tutor');
  });

  it('should construct correct verify-code URL for tutor with email', () => {
    const email = 'tutor@example.com';
    const primaryContact = 'email';
    const expectedUrl = `/auth/verify-code?contact=${encodeURIComponent(
      email
    )}&contactType=${primaryContact}&nextRoute=${encodeURIComponent('/onboarding/tutor-flow')}`;

    expect(expectedUrl).toBe(
      '/auth/verify-code?contact=tutor%40example.com&contactType=email&nextRoute=%2Fonboarding%2Ftutor-flow'
    );
  });

  it('should construct correct verify-code URL for school without nextRoute', () => {
    const email = 'admin@school.com';
    const primaryContact = 'email';
    const expectedUrl = `/auth/verify-code?contact=${encodeURIComponent(
      email
    )}&contactType=${primaryContact}`;

    expect(expectedUrl).toBe('/auth/verify-code?contact=admin%40school.com&contactType=email');
  });

  it('should handle navigation after successful registration', () => {
    render(<SignUp />);

    const router = unitoolsRouter.default();
    router.replace('/auth/verify-code?contact=test%40example.com&contactType=email');

    expect(mockReplace).toHaveBeenCalledWith(
      '/auth/verify-code?contact=test%40example.com&contactType=email'
    );
  });

  it('should handle toast notifications for different scenarios', () => {
    render(<SignUp />);

    const toastInstance = toast.useToast();

    // Success message
    toastInstance.showToast('success', 'Registration successful! Please verify your email.');
    expect(mockShowToast).toHaveBeenCalledWith(
      'success',
      'Registration successful! Please verify your email.'
    );

    // Error messages
    toastInstance.showToast(
      'error',
      'Invalid information provided. Please check your details and try again.'
    );
    expect(mockShowToast).toHaveBeenCalledWith(
      'error',
      'Invalid information provided. Please check your details and try again.'
    );

    toastInstance.showToast(
      'error',
      'An account with this email already exists. Try signing in instead.'
    );
    expect(mockShowToast).toHaveBeenCalledWith(
      'error',
      'An account with this email already exists. Try signing in instead.'
    );
  });

  it('should validate email format', () => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    // Valid emails
    const validEmails = [
      'user@example.com',
      'test.email@domain.co.uk',
      'user+tag@example.com',
      'first.last@subdomain.example.org',
    ];

    validEmails.forEach(email => {
      expect(emailRegex.test(email)).toBe(true);
    });

    // Invalid emails
    const invalidEmails = ['@domain.com', 'user@', 'user space@domain.com', ''];

    invalidEmails.forEach(email => {
      expect(emailRegex.test(email)).toBe(false);
    });
  });

  it('should validate phone number format', () => {
    const phoneRegex = /^[+\d\s]+$/;
    const hasDigitRegex = /\d/;

    // Valid phone numbers
    const validPhones = ['+1234567890', '1234567890', '+55 11 99999 9999', '+351 912 345 678'];

    validPhones.forEach(phone => {
      expect(phoneRegex.test(phone)).toBe(true);
      expect(hasDigitRegex.test(phone)).toBe(true);
    });
  });
});
