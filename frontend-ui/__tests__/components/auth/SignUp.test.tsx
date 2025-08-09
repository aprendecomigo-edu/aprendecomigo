import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';

import { SignUp } from '@/components/auth/SignUp';
import { renderWithProviders, createMockRouter, createMockToast, AUTH_TEST_DATA } from '../../utils/auth-test-utils';

// Mock the auth API
const mockCreateUser = jest.fn();
jest.mock('@/api/authApi', () => ({
  createUser: mockCreateUser,
}));

// Mock useAuth and useUserProfile hooks
const mockSetToken = jest.fn();
const mockSetUser = jest.fn();
jest.mock('@/api/auth', () => ({
  useAuth: () => ({
    setToken: mockSetToken,
    setUser: mockSetUser,
  }),
  useUserProfile: () => ({
    profile: null,
    loading: false,
  }),
}));

// Mock router
const mockRouter = createMockRouter();
jest.mock('@unitools/router', () => ({
  __esModule: true,
  default: () => mockRouter,
}));

// Mock expo-router for useLocalSearchParams
const mockUseLocalSearchParams = jest.fn();
jest.mock('expo-router', () => ({
  useLocalSearchParams: mockUseLocalSearchParams,
}));

// Mock toast
const mockToast = createMockToast();
jest.mock('@/components/ui/toast', () => ({
  useToast: () => mockToast,
}));

// Mock Keyboard and ScrollView
jest.mock('react-native', () => ({
  ...jest.requireActual('react-native'),
  Keyboard: {
    dismiss: jest.fn(),
  },
  ScrollView: ({ children, ...props }: any) => {
    const React = require('react');
    return React.createElement('div', { ...props, className: 'scroll-view' }, children);
  },
}));

describe('SignUp Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCreateUser.mockClear();
    mockSetToken.mockClear();
    mockSetUser.mockClear();
    mockRouter._mocks.push.mockClear();
    mockRouter._mocks.back.mockClear();
    mockToast._mocks.showToast.mockClear();
    
    // Default mock for search params
    mockUseLocalSearchParams.mockReturnValue({
      userType: 'tutor',
    });
  });

  describe('Basic Rendering', () => {
    it('should render main elements for tutor signup', () => {
      const { getByText, getByPlaceholderText } = renderWithProviders(<SignUp />);
      
      // Check main heading
      expect(getByText('Set Up Your Tutoring Practice')).toBeTruthy();
      
      // Check subtitle
      expect(getByText('Create your professional tutoring account with Aprende Comigo')).toBeTruthy();
      
      // Check form fields for tutor
      expect(getByPlaceholderText('Enter your full name')).toBeTruthy();
      expect(getByPlaceholderText('Enter your email address')).toBeTruthy();
      
      // Check user type selection
      expect(getByText('Individual Tutor')).toBeTruthy();
      
      // Check create account button
      expect(getByText('Create Account')).toBeTruthy();
    });

    it('should render main elements for school signup', () => {
      mockUseLocalSearchParams.mockReturnValue({
        userType: 'school',
      });
      
      const { getByText, getByPlaceholderText } = renderWithProviders(<SignUp />);
      
      // Check main heading
      expect(getByText('Set Up Your School')).toBeTruthy();
      
      // Check subtitle
      expect(getByText('Create your school account with Aprende Comigo')).toBeTruthy();
      
      // Check form fields for school
      expect(getByPlaceholderText('Enter your full name')).toBeTruthy();
      expect(getByPlaceholderText('Enter your email address')).toBeTruthy();
      expect(getByPlaceholderText('Enter your school name')).toBeTruthy();
      
      // Check user type selection
      expect(getByText('School')).toBeTruthy();
      
      // Check create account button
      expect(getByText('Create Account')).toBeTruthy();
    });

    it('should handle missing userType in search params', () => {
      mockUseLocalSearchParams.mockReturnValue({});
      
      const { getByText } = renderWithProviders(<SignUp />);
      
      // Should still render the form
      expect(getByText('Create Account')).toBeTruthy();
    });
  });

  describe('User Type Selection', () => {
    it('should allow switching between user types', () => {
      const { getByText, getByLabelText } = renderWithProviders(<SignUp />);
      
      // Should start with tutor selected
      const tutorRadio = getByLabelText('Individual Tutor');
      const schoolRadio = getByLabelText('School');
      
      expect(tutorRadio.props.checked).toBe(true);
      expect(schoolRadio.props.checked).toBe(false);
      
      // Switch to school
      fireEvent.press(schoolRadio);
      
      expect(tutorRadio.props.checked).toBe(false);
      expect(schoolRadio.props.checked).toBe(true);
    });

    it('should update form fields when switching user types', () => {
      const { getByText, getByLabelText, queryByPlaceholderText } = renderWithProviders(<SignUp />);
      
      const schoolRadio = getByLabelText('School');
      
      // Initially tutor - no school name field
      expect(queryByPlaceholderText('Enter your school name')).toBeNull();
      
      // Switch to school
      fireEvent.press(schoolRadio);
      
      // Should now show school name field
      expect(queryByPlaceholderText('Enter your school name')).toBeTruthy();
    });
  });

  describe('Form Validation', () => {
    it('should show validation error for empty name', async () => {
      const { getByText, queryByText } = renderWithProviders(<SignUp />);
      
      const createButton = getByText('Create Account');
      
      // Submit without entering name
      fireEvent.press(createButton);
      
      await waitFor(() => {
        expect(queryByText('Name is required')).toBeTruthy();
      });
    });

    it('should show validation error for empty email', async () => {
      const { getByText, getByPlaceholderText, queryByText } = renderWithProviders(<SignUp />);
      
      const nameInput = getByPlaceholderText('Enter your full name');
      const createButton = getByText('Create Account');
      
      // Enter name but no email
      fireEvent.changeText(nameInput, 'John Doe');
      fireEvent.press(createButton);
      
      await waitFor(() => {
        expect(queryByText('Email is required')).toBeTruthy();
      });
    });

    it('should show validation error for invalid email format', async () => {
      const { getByText, getByPlaceholderText, queryByText } = renderWithProviders(<SignUp />);
      
      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const createButton = getByText('Create Account');
      
      fireEvent.changeText(nameInput, 'John Doe');
      fireEvent.changeText(emailInput, 'invalid-email');
      fireEvent.press(createButton);
      
      await waitFor(() => {
        expect(queryByText('Invalid email')).toBeTruthy();
      });
    });

    it('should show validation error for empty school name when school type is selected', async () => {
      const { getByText, getByPlaceholderText, getByLabelText, queryByText } = renderWithProviders(<SignUp />);
      
      const schoolRadio = getByLabelText('School');
      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const createButton = getByText('Create Account');
      
      // Switch to school type
      fireEvent.press(schoolRadio);
      
      // Fill other fields but not school name
      fireEvent.changeText(nameInput, 'John Doe');
      fireEvent.changeText(emailInput, 'john@example.com');
      fireEvent.press(createButton);
      
      await waitFor(() => {
        expect(queryByText('School name is required')).toBeTruthy();
      });
    });

    it('should validate terms of service acceptance', async () => {
      const { getByText, getByPlaceholderText, queryByText } = renderWithProviders(<SignUp />);
      
      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const createButton = getByText('Create Account');
      
      fireEvent.changeText(nameInput, 'John Doe');
      fireEvent.changeText(emailInput, 'john@example.com');
      fireEvent.press(createButton);
      
      await waitFor(() => {
        expect(queryByText('You must accept the terms of service')).toBeTruthy();
      });
    });
  });

  describe('User Interactions', () => {
    it('should handle valid form submission for tutor', async () => {
      mockCreateUser.mockResolvedValue({
        access_token: 'fake-token',
        user: { id: 1, email: 'john@example.com', name: 'John Doe' },
      });
      
      const { getByText, getByPlaceholderText, getByLabelText } = renderWithProviders(<SignUp />);
      
      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const termsCheckbox = getByLabelText(/I agree to the Terms of Service/);
      const createButton = getByText('Create Account');
      
      fireEvent.changeText(nameInput, 'John Doe');
      fireEvent.changeText(emailInput, 'john@example.com');
      fireEvent.press(termsCheckbox);
      
      await act(async () => {
        fireEvent.press(createButton);
      });
      
      await waitFor(() => {
        expect(mockCreateUser).toHaveBeenCalledWith({
          name: 'John Doe',
          email: 'john@example.com',
          userType: 'tutor',
          schoolName: undefined,
          acceptedTerms: true,
        });
      });
    });

    it('should handle valid form submission for school', async () => {
      mockCreateUser.mockResolvedValue({
        access_token: 'fake-token',
        user: { id: 1, email: 'admin@school.com', name: 'Admin User' },
      });
      
      const { getByText, getByPlaceholderText, getByLabelText } = renderWithProviders(<SignUp />);
      
      const schoolRadio = getByLabelText('School');
      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const termsCheckbox = getByLabelText(/I agree to the Terms of Service/);
      const createButton = getByText('Create Account');
      
      // Switch to school type
      fireEvent.press(schoolRadio);
      
      const schoolNameInput = getByPlaceholderText('Enter your school name');
      
      fireEvent.changeText(nameInput, 'Admin User');
      fireEvent.changeText(emailInput, 'admin@school.com');
      fireEvent.changeText(schoolNameInput, 'Test School');
      fireEvent.press(termsCheckbox);
      
      await act(async () => {
        fireEvent.press(createButton);
      });
      
      await waitFor(() => {
        expect(mockCreateUser).toHaveBeenCalledWith({
          name: 'Admin User',
          email: 'admin@school.com',
          userType: 'school',
          schoolName: 'Test School',
          acceptedTerms: true,
        });
      });
    });

    it('should set auth token and user on successful registration', async () => {
      const mockAuthResponse = {
        access_token: 'fake-token',
        user: { id: 1, email: 'john@example.com', name: 'John Doe' },
      };
      
      mockCreateUser.mockResolvedValue(mockAuthResponse);
      
      const { getByText, getByPlaceholderText, getByLabelText } = renderWithProviders(<SignUp />);
      
      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const termsCheckbox = getByLabelText(/I agree to the Terms of Service/);
      const createButton = getByText('Create Account');
      
      fireEvent.changeText(nameInput, 'John Doe');
      fireEvent.changeText(emailInput, 'john@example.com');
      fireEvent.press(termsCheckbox);
      
      await act(async () => {
        fireEvent.press(createButton);
      });
      
      await waitFor(() => {
        expect(mockSetToken).toHaveBeenCalledWith('fake-token');
        expect(mockSetUser).toHaveBeenCalledWith(mockAuthResponse.user);
      });
    });

    it('should navigate to onboarding after successful registration', async () => {
      mockCreateUser.mockResolvedValue({
        access_token: 'fake-token',
        user: { id: 1, email: 'john@example.com', name: 'John Doe' },
      });
      
      const { getByText, getByPlaceholderText, getByLabelText } = renderWithProviders(<SignUp />);
      
      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const termsCheckbox = getByLabelText(/I agree to the Terms of Service/);
      const createButton = getByText('Create Account');
      
      fireEvent.changeText(nameInput, 'John Doe');
      fireEvent.changeText(emailInput, 'john@example.com');
      fireEvent.press(termsCheckbox);
      
      await act(async () => {
        fireEvent.press(createButton);
      });
      
      await waitFor(() => {
        expect(mockRouter._mocks.push).toHaveBeenCalledWith('/onboarding/welcome');
      });
    });
  });

  describe('Loading States', () => {
    it('should show loading state during registration', async () => {
      // Create a delayed promise
      let resolvePromise: (value: any) => void;
      const delayedPromise = new Promise(resolve => {
        resolvePromise = resolve;
      });
      mockCreateUser.mockReturnValue(delayedPromise);
      
      const { getByText, getByPlaceholderText, getByLabelText } = renderWithProviders(<SignUp />);
      
      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const termsCheckbox = getByLabelText(/I agree to the Terms of Service/);
      const createButton = getByText('Create Account');
      
      fireEvent.changeText(nameInput, 'John Doe');
      fireEvent.changeText(emailInput, 'john@example.com');
      fireEvent.press(termsCheckbox);
      fireEvent.press(createButton);
      
      // Check loading state appears
      await waitFor(() => {
        expect(getByText('Creating Account...')).toBeTruthy();
      });
      
      // Resolve the promise
      await act(async () => {
        resolvePromise!({
          access_token: 'fake-token',
          user: { id: 1, email: 'john@example.com', name: 'John Doe' },
        });
      });
    });

    it('should disable button during registration', async () => {
      // Create a delayed promise
      let resolvePromise: (value: any) => void;
      const delayedPromise = new Promise(resolve => {
        resolvePromise = resolve;
      });
      mockCreateUser.mockReturnValue(delayedPromise);
      
      const { getByText, getByPlaceholderText, getByLabelText } = renderWithProviders(<SignUp />);
      
      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const termsCheckbox = getByLabelText(/I agree to the Terms of Service/);
      const createButton = getByText('Create Account');
      
      fireEvent.changeText(nameInput, 'John Doe');
      fireEvent.changeText(emailInput, 'john@example.com');
      fireEvent.press(termsCheckbox);
      fireEvent.press(createButton);
      
      // Check button becomes disabled
      await waitFor(() => {
        const loadingButton = getByText('Creating Account...');
        expect(loadingButton.props.disabled).toBe(true);
      });
      
      // Resolve the promise
      await act(async () => {
        resolvePromise!({
          access_token: 'fake-token',
          user: { id: 1, email: 'john@example.com', name: 'John Doe' },
        });
      });
    });
  });

  describe('Error Handling', () => {
    it('should show error toast for duplicate email', async () => {
      mockCreateUser.mockRejectedValue(new Error('Email already exists'));
      
      const { getByText, getByPlaceholderText, getByLabelText } = renderWithProviders(<SignUp />);
      
      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const termsCheckbox = getByLabelText(/I agree to the Terms of Service/);
      const createButton = getByText('Create Account');
      
      fireEvent.changeText(nameInput, 'John Doe');
      fireEvent.changeText(emailInput, 'john@example.com');
      fireEvent.press(termsCheckbox);
      
      await act(async () => {
        fireEvent.press(createButton);
      });
      
      await waitFor(() => {
        expect(mockToast._mocks.showToast).toHaveBeenCalledWith('error', 'Failed to create account. Please try again.');
      });
    });

    it('should show error toast for network failure', async () => {
      mockCreateUser.mockRejectedValue(new Error('Network error'));
      
      const { getByText, getByPlaceholderText, getByLabelText } = renderWithProviders(<SignUp />);
      
      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const termsCheckbox = getByLabelText(/I agree to the Terms of Service/);
      const createButton = getByText('Create Account');
      
      fireEvent.changeText(nameInput, 'John Doe');
      fireEvent.changeText(emailInput, 'john@example.com');
      fireEvent.press(termsCheckbox);
      
      await act(async () => {
        fireEvent.press(createButton);
      });
      
      await waitFor(() => {
        expect(mockToast._mocks.showToast).toHaveBeenCalledWith('error', 'Failed to create account. Please try again.');
      });
    });

    it('should reset loading state after error', async () => {
      mockCreateUser.mockRejectedValue(new Error('Network error'));
      
      const { getByText, getByPlaceholderText, getByLabelText } = renderWithProviders(<SignUp />);
      
      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const termsCheckbox = getByLabelText(/I agree to the Terms of Service/);
      const createButton = getByText('Create Account');
      
      fireEvent.changeText(nameInput, 'John Doe');
      fireEvent.changeText(emailInput, 'john@example.com');
      fireEvent.press(termsCheckbox);
      
      await act(async () => {
        fireEvent.press(createButton);
      });
      
      await waitFor(() => {
        expect(getByText('Create Account')).toBeTruthy();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle special characters in form fields', async () => {
      mockCreateUser.mockResolvedValue({
        access_token: 'fake-token',
        user: { id: 1, email: 'joão@example.com', name: 'João da Silva' },
      });
      
      const { getByText, getByPlaceholderText, getByLabelText } = renderWithProviders(<SignUp />);
      
      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const termsCheckbox = getByLabelText(/I agree to the Terms of Service/);
      const createButton = getByText('Create Account');
      
      const nameWithAccents = 'João da Silva';
      const emailWithAccents = 'joão@example.com';
      
      fireEvent.changeText(nameInput, nameWithAccents);
      fireEvent.changeText(emailInput, emailWithAccents);
      fireEvent.press(termsCheckbox);
      
      await act(async () => {
        fireEvent.press(createButton);
      });
      
      await waitFor(() => {
        expect(mockCreateUser).toHaveBeenCalledWith({
          name: nameWithAccents,
          email: emailWithAccents,
          userType: 'tutor',
          schoolName: undefined,
          acceptedTerms: true,
        });
      });
    });

    it('should handle rapid successive form submissions', async () => {
      mockCreateUser.mockResolvedValue({
        access_token: 'fake-token',
        user: { id: 1, email: 'john@example.com', name: 'John Doe' },
      });
      
      const { getByText, getByPlaceholderText, getByLabelText } = renderWithProviders(<SignUp />);
      
      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const termsCheckbox = getByLabelText(/I agree to the Terms of Service/);
      const createButton = getByText('Create Account');
      
      fireEvent.changeText(nameInput, 'John Doe');
      fireEvent.changeText(emailInput, 'john@example.com');
      fireEvent.press(termsCheckbox);
      
      // Click button multiple times rapidly
      await act(async () => {
        fireEvent.press(createButton);
        fireEvent.press(createButton);
        fireEvent.press(createButton);
      });
      
      // Should only be called once due to loading state
      await waitFor(() => {
        expect(mockCreateUser).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper accessibility labels', () => {
      const { getByText, getByPlaceholderText, getByLabelText } = renderWithProviders(<SignUp />);
      
      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      const createButton = getByText('Create Account');
      const tutorRadio = getByLabelText('Individual Tutor');
      
      // Check that elements are accessible
      expect(nameInput).toBeTruthy();
      expect(emailInput).toBeTruthy();
      expect(createButton).toBeTruthy();
      expect(tutorRadio).toBeTruthy();
    });

    it('should support keyboard navigation', () => {
      const { getByPlaceholderText } = renderWithProviders(<SignUp />);
      
      const nameInput = getByPlaceholderText('Enter your full name');
      const emailInput = getByPlaceholderText('Enter your email address');
      
      // Check keyboard properties
      expect(emailInput.props.keyboardType).toBe('email-address');
      expect(emailInput.props.autoCapitalize).toBe('none');
      expect(emailInput.props.autoComplete).toBe('email');
    });
  });
});
