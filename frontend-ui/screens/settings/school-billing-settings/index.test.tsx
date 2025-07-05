import { render, fireEvent, waitFor } from '@testing-library/react-native';
import React from 'react';
import { Alert } from 'react-native';

import SchoolBillingSettings from './index';

import apiClient from '@/api/apiClient';
import { GluestackUIProvider } from '@/components/ui/gluestack-ui-provider';

// Mock dependencies
jest.mock('@/api/apiClient');
jest.mock('@/components/layouts/main-layout', () => {
  const { View } = require('react-native');
  return ({ children }: { children: React.ReactNode }) => (
    <View testID="main-layout">{children}</View>
  );
});

// Mock Alert
jest.spyOn(Alert, 'alert');

// Mock API responses
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

const mockSettings = {
  id: 1,
  school: 1,
  school_name: 'Test School',
  trial_cost_absorption: 'school' as const,
  teacher_payment_frequency: 'monthly' as const,
  payment_day_of_month: 1,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

// Wrapper component with providers
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <GluestackUIProvider>{children}</GluestackUIProvider>
);

describe('SchoolBillingSettings', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    mockApiClient.get.mockImplementation(() => new Promise(() => {})); // Never resolves

    const { getByText } = render(
      <TestWrapper>
        <SchoolBillingSettings />
      </TestWrapper>
    );

    expect(getByText('Loading settings...')).toBeTruthy();
  });

  it('renders settings form when data is loaded', async () => {
    mockApiClient.get.mockResolvedValue({ data: mockSettings });

    const { getByText, getByDisplayValue } = render(
      <TestWrapper>
        <SchoolBillingSettings />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(getByText('School Billing Settings')).toBeTruthy();
      expect(getByText('Who pays for trial classes?')).toBeTruthy();
      expect(getByText('How often do you pay teachers?')).toBeTruthy();
      expect(getByText('Payment day of month')).toBeTruthy();
      expect(getByDisplayValue('1')).toBeTruthy(); // Payment day value
    });
  });

  it('renders default settings when no settings exist (404)', async () => {
    mockApiClient.get.mockRejectedValue({
      response: { status: 404 },
    });

    const { getByText, getByDisplayValue } = render(
      <TestWrapper>
        <SchoolBillingSettings />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(getByText('School Billing Settings')).toBeTruthy();
      expect(getByDisplayValue('1')).toBeTruthy(); // Default payment day
    });
  });

  it('displays error when API fails', async () => {
    mockApiClient.get.mockRejectedValue({
      response: { status: 500, data: { error: 'Server error' } },
    });

    const { getByText } = render(
      <TestWrapper>
        <SchoolBillingSettings />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(getByText('Server error')).toBeTruthy();
      expect(getByText('Retry')).toBeTruthy();
    });
  });

  it('saves settings successfully', async () => {
    mockApiClient.get.mockResolvedValue({ data: mockSettings });
    mockApiClient.patch.mockResolvedValue({ data: { ...mockSettings, payment_day_of_month: 15 } });

    const { getByText, getByDisplayValue } = render(
      <TestWrapper>
        <SchoolBillingSettings />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(getByText('Save Settings')).toBeTruthy();
    });

    // Change payment day
    const paymentDayInput = getByDisplayValue('1');
    fireEvent.changeText(paymentDayInput, '15');

    // Save settings
    const saveButton = getByText('Save Settings');
    fireEvent.press(saveButton);

    await waitFor(() => {
      expect(mockApiClient.patch).toHaveBeenCalledWith('/api/finances/school-billing-settings/1/', {
        trial_cost_absorption: 'school',
        teacher_payment_frequency: 'monthly',
        payment_day_of_month: 15,
      });
      expect(Alert.alert).toHaveBeenCalledWith('Success', 'Settings saved successfully!');
    });
  });

  it('creates new settings when none exist', async () => {
    const defaultSettings = {
      school: 1,
      trial_cost_absorption: 'school',
      teacher_payment_frequency: 'monthly',
      payment_day_of_month: 1,
    };

    mockApiClient.get.mockRejectedValue({ response: { status: 404 } });
    mockApiClient.post.mockResolvedValue({ data: { ...defaultSettings, id: 1 } });

    const { getByText } = render(
      <TestWrapper>
        <SchoolBillingSettings />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(getByText('Save Settings')).toBeTruthy();
    });

    // Save settings
    const saveButton = getByText('Save Settings');
    fireEvent.press(saveButton);

    await waitFor(() => {
      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/api/finances/school-billing-settings/',
        defaultSettings
      );
      expect(Alert.alert).toHaveBeenCalledWith('Success', 'Settings saved successfully!');
    });
  });

  it('handles validation errors when saving', async () => {
    mockApiClient.get.mockResolvedValue({ data: mockSettings });
    mockApiClient.patch.mockRejectedValue({
      response: {
        data: {
          details: {
            payment_day_of_month: ['Payment day must be between 1 and 28.'],
          },
        },
      },
    });

    const { getByText } = render(
      <TestWrapper>
        <SchoolBillingSettings />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(getByText('Save Settings')).toBeTruthy();
    });

    // Save settings
    const saveButton = getByText('Save Settings');
    fireEvent.press(saveButton);

    await waitFor(() => {
      expect(getByText(/Validation errors:/)).toBeTruthy();
      expect(getByText(/payment_day_of_month: Payment day must be between 1 and 28./)).toBeTruthy();
    });
  });

  it('resets settings when reset button is pressed', async () => {
    mockApiClient.get.mockResolvedValue({ data: mockSettings });

    const { getByText } = render(
      <TestWrapper>
        <SchoolBillingSettings />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(getByText('Reset')).toBeTruthy();
    });

    // Press reset button
    const resetButton = getByText('Reset');
    fireEvent.press(resetButton);

    // Should call the API again to reload settings
    await waitFor(() => {
      expect(mockApiClient.get).toHaveBeenCalledTimes(2);
    });
  });
});
