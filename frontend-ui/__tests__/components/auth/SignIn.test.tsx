import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';

import { SignIn } from '@/components/auth/SignIn';

// Mock the auth API
const mockRequestEmailCode = jest.fn();
jest.mock('@/api/authApi', () => ({
  requestEmailCode: mockRequestEmailCode,
}));

// Mock router
const mockPush = jest.fn();
jest.mock('@unitools/router', () => ({
  __esModule: true,
  default: () => ({
    push: mockPush,
  }),
}));

// Mock toast
const mockShowToast = jest.fn();
jest.mock('@/components/ui/toast', () => ({
  useToast: () => ({
    show: mockShowToast,
  }),
}));

describe('SignIn Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render signin form', () => {
    const { getByText, getByPlaceholderText } = render(<SignIn />);
    
    expect(getByText('Sign in to your account')).toBeTruthy();
    expect(getByPlaceholderText('Enter your email')).toBeTruthy();
  });

  it('should show validation error for invalid email', async () => {
    const { getByPlaceholderText, getByText, getByTestId } = render(<SignIn />);
    
    const emailInput = getByPlaceholderText('Enter your email');
    const submitButton = getByText('Continue');
    
    fireEvent.changeText(emailInput, 'invalid-email');
    fireEvent.press(submitButton);
    
    await waitFor(() => {
      expect(getByText('Invalid email')).toBeTruthy();
    });
  });

  it('should handle email submission successfully', async () => {
    mockRequestEmailCode.mockResolvedValue({ success: true });
    
    const { getByPlaceholderText, getByText } = render(<SignIn />);
    
    const emailInput = getByPlaceholderText('Enter your email');
    const submitButton = getByText('Continue');
    
    fireEvent.changeText(emailInput, 'user@example.com');
    fireEvent.press(submitButton);
    
    await waitFor(() => {
      expect(mockRequestEmailCode).toHaveBeenCalledWith({
        email: 'user@example.com',
      });
    });
  });

  it('should handle API error gracefully', async () => {
    mockRequestEmailCode.mockRejectedValue(new Error('Network error'));
    
    const { getByPlaceholderText, getByText } = render(<SignIn />);
    
    const emailInput = getByPlaceholderText('Enter your email');
    const submitButton = getByText('Continue');
    
    fireEvent.changeText(emailInput, 'user@example.com');
    fireEvent.press(submitButton);
    
    await waitFor(() => {
      expect(mockShowToast).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'error',
        })
      );
    });
  });

  it('should disable submit button while loading', async () => {
    // Mock a delayed API response
    mockRequestEmailCode.mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 1000))
    );
    
    const { getByPlaceholderText, getByText } = render(<SignIn />);
    
    const emailInput = getByPlaceholderText('Enter your email');
    const submitButton = getByText('Continue');
    
    fireEvent.changeText(emailInput, 'user@example.com');
    fireEvent.press(submitButton);
    
    // Button should be disabled during loading
    expect(submitButton.props.accessibilityState?.disabled).toBe(true);
  });
});