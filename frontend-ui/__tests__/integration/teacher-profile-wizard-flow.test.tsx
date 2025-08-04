import AsyncStorage from '@react-native-async-storage/async-storage';
import { fireEvent, waitFor, act } from '@testing-library/react-native';
import React from 'react';

import {
  render,
  createMockProfileData,
  createMockCompletionData,
  mockApiResponse,
  flushPromises,
  advanceTimersByTime,
  fillFormField,
  pressButton,
  navigateToStep,
} from '../utils/test-utils';

import apiClient from '@/api/apiClient';
import { useProfileWizard } from '@/hooks/useProfileWizard';
import { TeacherProfileWizard } from '@/components/onboarding/TeacherProfileWizard';

// Use real hook instead of mocking it for integration tests
jest.unmock('@/hooks/useProfileWizard');

// Mock API client
jest.mock('@/api/apiClient');
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage');
const mockAsyncStorage = AsyncStorage as jest.Mocked<typeof AsyncStorage>;

describe('TeacherProfileWizard - Integration Flow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();

    // Setup default API responses
    mockApiClient.get.mockResolvedValue(mockApiResponse({}));
    mockApiClient.post.mockResolvedValue(mockApiResponse({ success: true }));
    mockAsyncStorage.getItem.mockResolvedValue(null);
    mockAsyncStorage.setItem.mockResolvedValue();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('Complete Wizard Flow', () => {
    it('should complete the entire wizard flow successfully', async () => {
      const mockOnComplete = jest.fn();
      const mockProfileData = createMockProfileData();
      const mockCompletionData = createMockCompletionData();

      // Mock API responses for each step
      mockApiClient.get
        .mockResolvedValueOnce(mockApiResponse(mockProfileData))
        .mockResolvedValueOnce(mockApiResponse(mockCompletionData));

      mockApiClient.post
        .mockResolvedValue(mockApiResponse({ is_valid: true })) // validation
        .mockResolvedValue(mockApiResponse({ success: true, completion_data: mockCompletionData })) // save progress
        .mockResolvedValue(mockApiResponse({})); // final submission

      const { getByTestId, getByText } = render(
        <TeacherProfileWizard onComplete={mockOnComplete} />
      );

      // Wait for initialization
      await waitFor(() => {
        expect(getByText('Basic Information')).toBeTruthy();
      });

      // Step 1: Basic Information
      await act(async () => {
        const firstNameInput = getByTestId('first-name-input');
        fireEvent.changeText(firstNameInput, 'John');

        const lastNameInput = getByTestId('last-name-input');
        fireEvent.changeText(lastNameInput, 'Doe');

        const emailInput = getByTestId('email-input');
        fireEvent.changeText(emailInput, 'john.doe@example.com');

        fireEvent.press(getByTestId('next-button'));
      });

      // Wait for navigation to step 2
      await waitFor(() => {
        expect(getByText('Professional Biography')).toBeTruthy();
      });

      // Step 2: Biography
      await act(async () => {
        const bioTextarea = getByTestId('bio-textarea');
        fireEvent.changeText(
          bioTextarea,
          'I am an experienced mathematics teacher with over 5 years of experience...'
        );

        fireEvent.press(getByTestId('next-button'));
      });

      // Wait for navigation to step 3
      await waitFor(() => {
        expect(getByText('Education Background')).toBeTruthy();
      });

      // Step 3: Education
      await act(async () => {
        fireEvent.press(getByTestId('add-degree-button'));

        const degreeTypeSelect = getByTestId('degree-type-select');
        fireEvent(degreeTypeSelect, 'onValueChange', 'Bachelor');

        const fieldInput = getByTestId('field-of-study-input');
        fireEvent.changeText(fieldInput, 'Mathematics');

        fireEvent.press(getByTestId('next-button'));
      });

      // Wait for navigation to step 4
      await waitFor(() => {
        expect(getByText('Teaching Subjects')).toBeTruthy();
      });

      // Step 4: Subjects
      await act(async () => {
        fireEvent.press(getByTestId('add-subject-button'));

        const subjectSelect = getByTestId('subject-select');
        fireEvent(subjectSelect, 'onValueChange', 'Mathematics');

        const gradeLevelsSelect = getByTestId('grade-levels-select');
        fireEvent(gradeLevelsSelect, 'onValueChange', ['Grade 7', 'Grade 8']);

        fireEvent.press(getByTestId('next-button'));
      });

      // Wait for navigation to step 5
      await waitFor(() => {
        expect(getByText('Rates & Pricing')).toBeTruthy();
      });

      // Step 5: Rates
      await act(async () => {
        const rateInput = getByTestId('individual-rate-input');
        fireEvent.changeText(rateInput, '25');

        const currencySelect = getByTestId('currency-select');
        fireEvent(currencySelect, 'onValueChange', 'EUR');

        fireEvent.press(getByTestId('next-button'));
      });

      // Wait for navigation to step 6
      await waitFor(() => {
        expect(getByText('Availability')).toBeTruthy();
      });

      // Step 6: Availability
      await act(async () => {
        fireEvent.press(getByTestId('monday-time-slot'));

        const startTimeInput = getByTestId('start-time-input');
        fireEvent.changeText(startTimeInput, '09:00');

        const endTimeInput = getByTestId('end-time-input');
        fireEvent.changeText(endTimeInput, '17:00');

        fireEvent.press(getByTestId('save-time-slot'));
        fireEvent.press(getByTestId('next-button'));
      });

      // Wait for navigation to step 7 (preview)
      await waitFor(() => {
        expect(getByText('Profile Preview')).toBeTruthy();
      });

      // Step 7: Preview and Complete
      await act(async () => {
        fireEvent.press(getByTestId('complete-profile-button'));
      });

      // Wait for completion
      await waitFor(() => {
        expect(mockOnComplete).toHaveBeenCalled();
      });

      // Verify API calls were made correctly
      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/accounts/teachers/profile-wizard/submit/',
        expect.objectContaining({
          profile_data: expect.objectContaining({
            first_name: 'John',
            last_name: 'Doe',
            email: 'john.doe@example.com',
          }),
        })
      );
    });

    it('should handle validation errors and allow correction', async () => {
      // Mock validation error response
      mockApiClient.post
        .mockResolvedValueOnce(
          mockApiResponse({
            is_valid: false,
            errors: {
              first_name: ['First name is required'],
              email: ['Invalid email format'],
            },
          })
        )
        .mockResolvedValueOnce(mockApiResponse({ is_valid: true })); // Second attempt succeeds

      const { getByTestId, getByText } = render(<TeacherProfileWizard />);

      // Wait for initialization
      await waitFor(() => {
        expect(getByText('Basic Information')).toBeTruthy();
      });

      // Try to proceed without filling required fields
      await act(async () => {
        fireEvent.press(getByTestId('next-button'));
      });

      // Should show validation errors
      await waitFor(() => {
        expect(getByText('First name is required')).toBeTruthy();
        expect(getByText('Invalid email format')).toBeTruthy();
      });

      // Correct the errors
      await act(async () => {
        const firstNameInput = getByTestId('first-name-input');
        fireEvent.changeText(firstNameInput, 'John');

        const emailInput = getByTestId('email-input');
        fireEvent.changeText(emailInput, 'john@example.com');

        fireEvent.press(getByTestId('next-button'));
      });

      // Should proceed to next step
      await waitFor(() => {
        expect(getByText('Professional Biography')).toBeTruthy();
      });
    });

    it('should save progress automatically and restore on reload', async () => {
      const cachedFormData = createMockProfileData({
        first_name: 'Cached',
        last_name: 'User',
      });

      const cachedState = {
        currentStep: 2,
        formData: cachedFormData,
        completionData: createMockCompletionData(),
      };

      // Mock cached data
      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify(cachedState));

      const { getByText, getByDisplayValue } = render(<TeacherProfileWizard />);

      // Wait for cached data to load
      await waitFor(() => {
        expect(getByText('Education Background')).toBeTruthy(); // Step 2 (0-indexed)
        expect(getByDisplayValue('Cached')).toBeTruthy();
        expect(getByDisplayValue('User')).toBeTruthy();
      });

      // Verify AsyncStorage was called
      expect(mockAsyncStorage.getItem).toHaveBeenCalledWith('@teacher_profile_wizard');
    });

    it('should trigger auto-save after inactivity', async () => {
      const { getByTestId } = render(<TeacherProfileWizard />);

      // Wait for initialization
      await waitFor(() => {
        expect(getByTestId('first-name-input')).toBeTruthy();
      });

      // Make a change to trigger unsaved state
      await act(async () => {
        const firstNameInput = getByTestId('first-name-input');
        fireEvent.changeText(firstNameInput, 'Test');
      });

      // Advance timers to trigger auto-save (30 seconds)
      await act(async () => {
        advanceTimersByTime(30000);
      });

      // Verify save progress was called
      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/accounts/teachers/profile-wizard/save-progress/',
        expect.objectContaining({
          profile_data: expect.objectContaining({
            first_name: 'Test',
          }),
        })
      );
    });
  });

  describe('Error Recovery', () => {
    it('should handle API errors gracefully', async () => {
      // Mock API error
      mockApiClient.get.mockRejectedValue(new Error('Server error'));

      const { getByText } = render(<TeacherProfileWizard />);

      await waitFor(() => {
        expect(getByText('Server error')).toBeTruthy();
      });
    });

    it('should retry failed operations', async () => {
      // Mock initial failure then success
      mockApiClient.post
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockApiResponse({ success: true }));

      const { getByTestId, getByText } = render(<TeacherProfileWizard />);

      // Wait for initialization
      await waitFor(() => {
        expect(getByTestId('first-name-input')).toBeTruthy();
      });

      // Trigger save that will fail initially
      await act(async () => {
        const firstNameInput = getByTestId('first-name-input');
        fireEvent.changeText(firstNameInput, 'Test');
        fireEvent.press(getByTestId('manual-save-button'));
      });

      // Should show error
      await waitFor(() => {
        expect(getByText('Network error')).toBeTruthy();
      });

      // Retry should succeed
      await act(async () => {
        fireEvent.press(getByTestId('manual-save-button'));
      });

      // Error should be cleared
      await waitFor(() => {
        expect(() => getByText('Network error')).toThrow();
      });
    });

    it('should handle network disconnection gracefully', async () => {
      // Mock network error
      const networkError = new Error('Network Error');
      (networkError as any).isAxiosError = true;
      (networkError as any).code = 'NETWORK_ERROR';

      mockApiClient.post.mockRejectedValue(networkError);

      const { getByTestId, getByText } = render(<TeacherProfileWizard />);

      // Wait for initialization
      await waitFor(() => {
        expect(getByTestId('first-name-input')).toBeTruthy();
      });

      // Trigger network operation
      await act(async () => {
        fireEvent.press(getByTestId('manual-save-button'));
      });

      // Should show network error message
      await waitFor(() => {
        expect(getByText(/network/i)).toBeTruthy();
      });
    });
  });

  describe('Navigation and State Management', () => {
    it('should prevent navigation with invalid data', async () => {
      mockApiClient.post.mockResolvedValue(
        mockApiResponse({
          is_valid: false,
          errors: { first_name: ['Required'] },
        })
      );

      const { getByTestId, getByText } = render(<TeacherProfileWizard />);

      // Wait for initialization
      await waitFor(() => {
        expect(getByText('Basic Information')).toBeTruthy();
      });

      // Try to navigate without valid data
      await act(async () => {
        fireEvent.press(getByTestId('next-button'));
      });

      // Should stay on same step
      await waitFor(() => {
        expect(getByText('Basic Information')).toBeTruthy();
        expect(getByText('Required')).toBeTruthy();
      });
    });

    it('should allow backward navigation and preserve data', async () => {
      const { getByTestId, getByText, getByDisplayValue } = render(<TeacherProfileWizard />);

      // Wait for initialization
      await waitFor(() => {
        expect(getByText('Basic Information')).toBeTruthy();
      });

      // Fill first step
      await act(async () => {
        const firstNameInput = getByTestId('first-name-input');
        fireEvent.changeText(firstNameInput, 'John');

        fireEvent.press(getByTestId('next-button'));
      });

      // Move to second step
      await waitFor(() => {
        expect(getByText('Professional Biography')).toBeTruthy();
      });

      // Go back to first step
      await act(async () => {
        fireEvent.press(getByTestId('previous-button'));
      });

      // Should preserve previously entered data
      await waitFor(() => {
        expect(getByText('Basic Information')).toBeTruthy();
        expect(getByDisplayValue('John')).toBeTruthy();
      });
    });

    it('should handle concurrent state updates correctly', async () => {
      const { getByTestId } = render(<TeacherProfileWizard />);

      // Wait for initialization
      await waitFor(() => {
        expect(getByTestId('first-name-input')).toBeTruthy();
      });

      // Trigger multiple rapid updates
      await act(async () => {
        const firstNameInput = getByTestId('first-name-input');
        const lastNameInput = getByTestId('last-name-input');

        fireEvent.changeText(firstNameInput, 'John');
        fireEvent.changeText(lastNameInput, 'Doe');
        fireEvent.changeText(firstNameInput, 'Jane');
      });

      // Should handle all updates correctly
      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/accounts/teachers/profile-wizard/save-progress/',
        expect.objectContaining({
          profile_data: expect.objectContaining({
            first_name: 'Jane',
            last_name: 'Doe',
          }),
        })
      );
    });
  });

  describe('Exit and Resume Flow', () => {
    it('should show exit confirmation with unsaved changes', async () => {
      const mockOnExit = jest.fn();
      const { getByTestId, getByText } = render(<TeacherProfileWizard onExit={mockOnExit} />);

      // Wait for initialization
      await waitFor(() => {
        expect(getByTestId('first-name-input')).toBeTruthy();
      });

      // Make changes
      await act(async () => {
        const firstNameInput = getByTestId('first-name-input');
        fireEvent.changeText(firstNameInput, 'Test');

        fireEvent.press(getByTestId('exit-button'));
      });

      // Should show confirmation dialog
      await waitFor(() => {
        expect(getByText('Save Your Progress?')).toBeTruthy();
        expect(getByText('You have unsaved changes')).toBeTruthy();
      });

      // Save and exit
      await act(async () => {
        fireEvent.press(getByText('Save & Exit'));
      });

      expect(mockOnExit).toHaveBeenCalled();
    });

    it('should allow exit without saving', async () => {
      const mockOnExit = jest.fn();
      const { getByTestId, getByText } = render(<TeacherProfileWizard onExit={mockOnExit} />);

      // Wait for initialization and make changes
      await waitFor(() => {
        expect(getByTestId('first-name-input')).toBeTruthy();
      });

      await act(async () => {
        const firstNameInput = getByTestId('first-name-input');
        fireEvent.changeText(firstNameInput, 'Test');

        fireEvent.press(getByTestId('exit-button'));
      });

      // Exit without saving
      await act(async () => {
        fireEvent.press(getByText('Exit Without Saving'));
      });

      expect(mockOnExit).toHaveBeenCalled();
    });

    it('should resume from specific step', async () => {
      const { getByText } = render(<TeacherProfileWizard resumeFromStep={3} />);

      // Should start at step 3 (subjects)
      await waitFor(() => {
        expect(getByText('Teaching Subjects')).toBeTruthy();
      });
    });
  });

  describe('Performance and Memory Management', () => {
    it('should cleanup resources on unmount', async () => {
      const { unmount } = render(<TeacherProfileWizard />);

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      unmount();

      // Should not cause memory leaks or errors
      expect(consoleSpy).not.toHaveBeenCalled();
      consoleSpy.mockRestore();
    });

    it('should handle rapid navigation without performance issues', async () => {
      const { getByTestId } = render(<TeacherProfileWizard />);

      // Mock successful validation for all steps
      mockApiClient.post.mockResolvedValue(mockApiResponse({ is_valid: true }));

      // Wait for initialization
      await waitFor(() => {
        expect(getByTestId('next-button')).toBeTruthy();
      });

      // Rapidly navigate through steps
      for (let i = 0; i < 5; i++) {
        await act(async () => {
          fireEvent.press(getByTestId('next-button'));
        });
      }

      // Should handle rapid navigation without issues
      expect(mockApiClient.post).toHaveBeenCalledTimes(5);
    });

    it('should debounce auto-save correctly', async () => {
      const { getByTestId } = render(<TeacherProfileWizard />);

      // Wait for initialization
      await waitFor(() => {
        expect(getByTestId('first-name-input')).toBeTruthy();
      });

      // Make rapid changes
      await act(async () => {
        const firstNameInput = getByTestId('first-name-input');

        fireEvent.changeText(firstNameInput, 'J');
        fireEvent.changeText(firstNameInput, 'Jo');
        fireEvent.changeText(firstNameInput, 'Joh');
        fireEvent.changeText(firstNameInput, 'John');
      });

      // Advance timer partially
      await act(async () => {
        advanceTimersByTime(15000);
      });

      // Should not have auto-saved yet
      expect(mockApiClient.post).not.toHaveBeenCalledWith(
        '/accounts/teachers/profile-wizard/save-progress/',
        expect.any(Object)
      );

      // Complete the debounce period
      await act(async () => {
        advanceTimersByTime(15000);
      });

      // Should auto-save now
      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/accounts/teachers/profile-wizard/save-progress/',
        expect.objectContaining({
          profile_data: expect.objectContaining({
            first_name: 'John',
          }),
        })
      );
    });
  });

  describe('Accessibility Integration', () => {
    it('should announce step changes to screen readers', async () => {
      const { getByTestId, getByText } = render(<TeacherProfileWizard />);

      // Mock successful validation
      mockApiClient.post.mockResolvedValue(mockApiResponse({ is_valid: true }));

      // Wait for initialization
      await waitFor(() => {
        expect(getByText('Basic Information')).toBeTruthy();
      });

      // Navigate to next step
      await act(async () => {
        fireEvent.press(getByTestId('next-button'));
      });

      // Should announce step change
      await waitFor(() => {
        const announcement = getByTestId('step-announcement');
        expect(announcement.props.accessibilityLiveRegion).toBe('polite');
        expect(announcement.props.children).toContain('Step 2 of 7');
      });
    });

    it('should maintain focus management across steps', async () => {
      const { getByTestId } = render(<TeacherProfileWizard />);

      // Mock successful validation
      mockApiClient.post.mockResolvedValue(mockApiResponse({ is_valid: true }));

      // Wait for initialization
      await waitFor(() => {
        expect(getByTestId('first-name-input')).toBeTruthy();
      });

      // Navigate to next step
      await act(async () => {
        fireEvent.press(getByTestId('next-button'));
      });

      // Focus should move to first field in next step
      await waitFor(() => {
        const bioTextarea = getByTestId('bio-textarea');
        expect(bioTextarea.props.autoFocus).toBe(true);
      });
    });
  });
});
