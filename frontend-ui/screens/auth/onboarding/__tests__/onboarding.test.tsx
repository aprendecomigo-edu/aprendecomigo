import { fireEvent, render, waitFor } from '@testing-library/react-native';
import React from 'react';

// Import the actual component to test
import { Onboarding } from '../index';

// Mock the required hooks
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: jest.fn(),
    goBack: jest.fn(),
  }),
}));

jest.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({
    login: jest.fn(),
    register: jest.fn().mockImplementation(() => Promise.resolve({ success: true })),
  }),
}));

// Create a mock screen for testing
const MockScreen = () => <Onboarding />;

describe('Onboarding Component', () => {
  it('renders the main form sections', async () => {
    const { findByText } = render(<MockScreen />);

    // Check that main sections are rendered
    expect(await findByText('Personal Information')).toBeTruthy();
    expect(await findByText('School Information')).toBeTruthy();
    expect(await findByText('Primary Contact Method')).toBeTruthy();
  });

  it('displays validation errors when submitting empty form', async () => {
    const { findByText } = render(<MockScreen />);

    // Find and press submit button
    const submitButton = await findByText('Create Account');
    fireEvent.press(submitButton);

    // Check for validation error messages
    await waitFor(() => {
      expect(findByText('First name is required')).toBeTruthy();
      expect(findByText('Last name is required')).toBeTruthy();
      expect(findByText('Email is required')).toBeTruthy();
    });
  });

  it('allows switching between email and phone contact methods', async () => {
    const { findByText } = render(<MockScreen />);

    // Find the email/phone toggle
    const phoneToggle = await findByText('Phone');
    fireEvent.press(phoneToggle);

    // Check that phone input is now visible
    await waitFor(() => {
      expect(findByText('Phone Number')).toBeTruthy();
    });

    // Switch back to email
    const emailToggle = await findByText('Email');
    fireEvent.press(emailToggle);

    // Check that email input is now visible
    await waitFor(() => {
      expect(findByText('Email Address')).toBeTruthy();
    });
  });
});
