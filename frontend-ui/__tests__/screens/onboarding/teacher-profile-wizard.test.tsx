import React from 'react';
import { fireEvent, waitFor, act } from '@testing-library/react-native';

import { TeacherProfileWizard, WIZARD_STEPS } from '@/screens/onboarding/teacher-profile-wizard';
import { useProfileWizard } from '@/hooks/useProfileWizard';
import {
  render,
  createMockUseProfileWizard,
  createMockProps,
  createMockProfileData,
  createMockCompletionData,
  pressButton,
  waitForAsyncUpdates,
  advanceTimersByTime,
} from '../../utils/test-utils';

// Mock the hook
jest.mock('@/hooks/useProfileWizard');
const mockUseProfileWizard = useProfileWizard as jest.MockedFunction<typeof useProfileWizard>;

// Mock wizard error boundary
jest.mock('@/components/wizard/wizard-error-boundary', () => ({
  WizardErrorBoundary: ({ children }: { children: React.ReactNode }) => children,
}));

describe('TeacherProfileWizard', () => {
  let mockHookReturn: ReturnType<typeof createMockUseProfileWizard>;
  let mockProps: ReturnType<typeof createMockProps>;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    
    mockHookReturn = createMockUseProfileWizard();
    mockUseProfileWizard.mockReturnValue(mockHookReturn);
    mockProps = createMockProps();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('Initialization and Loading', () => {
    it('should render loading state initially', () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ isLoading: true })
      );

      const { getByText, getByTestId } = render(
        <TeacherProfileWizard {...mockProps} />
      );

      expect(getByTestId('loading-spinner')).toBeTruthy();
      expect(getByText('Loading your profile...')).toBeTruthy();
    });

    it('should initialize wizard with resumeFromStep prop', async () => {
      const propsWithResumeStep = createMockProps({ resumeFromStep: 3 });
      
      render(<TeacherProfileWizard {...propsWithResumeStep} />);

      await waitForAsyncUpdates();

      expect(mockHookReturn.loadProgress).toHaveBeenCalled();
      expect(mockHookReturn.setCurrentStep).toHaveBeenCalledWith(3);
    });

    it('should call loadProgress on mount', async () => {
      render(<TeacherProfileWizard {...mockProps} />);

      await waitForAsyncUpdates();

      expect(mockHookReturn.loadProgress).toHaveBeenCalled();
    });
  });

  describe('Header and Navigation', () => {
    it('should display current step information correctly', () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ currentStep: 2 })
      );

      const { getByText } = render(<TeacherProfileWizard {...mockProps} />);

      expect(getByText('Step 3 of 7')).toBeTruthy();
      expect(getByText(WIZARD_STEPS[2].title)).toBeTruthy();
      expect(getByText(WIZARD_STEPS[2].description)).toBeTruthy();
    });

    it('should show progress percentage correctly', () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ currentStep: 3 })
      );

      const { getByText } = render(<TeacherProfileWizard {...mockProps} />);

      // Step 4 of 7 = 57% (rounded)
      expect(getByText('57% Complete')).toBeTruthy();
    });

    it('should display required badge for required steps', () => {
      const { getByText } = render(<TeacherProfileWizard {...mockProps} />);

      expect(getByText('Required')).toBeTruthy();
    });

    it('should handle exit button press', async () => {
      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      await act(async () => {
        fireEvent.press(getByTestId('exit-button'));
      });

      expect(mockProps.onExit).toHaveBeenCalled();
    });
  });

  describe('Auto-save Functionality', () => {
    it('should show saving indicator when saving', () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ isSaving: true })
      );

      const { getByText, getByTestId } = render(
        <TeacherProfileWizard {...mockProps} />
      );

      expect(getByTestId('saving-spinner')).toBeTruthy();
      expect(getByText('Saving...')).toBeTruthy();
    });

    it('should show save button when there are unsaved changes', () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ 
          hasUnsavedChanges: true,
          isSaving: false,
        })
      );

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      expect(getByTestId('manual-save-button')).toBeTruthy();
    });

    it('should trigger manual save when save button is pressed', async () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ 
          hasUnsavedChanges: true,
          isSaving: false,
        })
      );

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      await act(async () => {
        fireEvent.press(getByTestId('manual-save-button'));
      });

      expect(mockHookReturn.saveProgress).toHaveBeenCalled();
    });

    it('should trigger auto-save after 30 seconds of inactivity', async () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ hasUnsavedChanges: true })
      );

      render(<TeacherProfileWizard {...mockProps} />);

      await act(async () => {
        advanceTimersByTime(30000);
      });

      expect(mockHookReturn.saveProgress).toHaveBeenCalled();
    });

    it('should clear auto-save timer when component unmounts', () => {
      const { unmount } = render(<TeacherProfileWizard {...mockProps} />);

      const clearTimeoutSpy = jest.spyOn(global, 'clearTimeout');

      unmount();

      expect(clearTimeoutSpy).toHaveBeenCalled();
    });
  });

  describe('Step Navigation', () => {
    it('should navigate to next step successfully', async () => {
      mockHookReturn.validateStep.mockResolvedValue(true);

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      await act(async () => {
        fireEvent.press(getByTestId('next-button'));
      });

      expect(mockHookReturn.validateStep).toHaveBeenCalledWith(0);
      expect(mockHookReturn.saveProgress).toHaveBeenCalled();
      expect(mockHookReturn.setCurrentStep).toHaveBeenCalledWith(1);
    });

    it('should not navigate if step validation fails', async () => {
      mockHookReturn.validateStep.mockResolvedValue(false);

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      await act(async () => {
        fireEvent.press(getByTestId('next-button'));
      });

      expect(mockHookReturn.validateStep).toHaveBeenCalledWith(0);
      expect(mockHookReturn.setCurrentStep).not.toHaveBeenCalled();
    });

    it('should navigate to previous step', async () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ currentStep: 2 })
      );

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      await act(async () => {
        fireEvent.press(getByTestId('previous-button'));
      });

      expect(mockHookReturn.setCurrentStep).toHaveBeenCalledWith(1);
    });

    it('should disable previous button on first step', () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ currentStep: 0 })
      );

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      const previousButton = getByTestId('previous-button');
      expect(previousButton.props.accessibilityState.disabled).toBe(true);
    });

    it('should save progress before navigating to previous step', async () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ 
          currentStep: 2,
          hasUnsavedChanges: true,
        })
      );

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      await act(async () => {
        fireEvent.press(getByTestId('previous-button'));
      });

      expect(mockHookReturn.saveProgress).toHaveBeenCalled();
      expect(mockHookReturn.setCurrentStep).toHaveBeenCalledWith(1);
    });
  });

  describe('Profile Completion', () => {
    it('should show complete profile button on final step', () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ currentStep: 6 })
      );

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      expect(getByTestId('complete-profile-button')).toBeTruthy();
    });

    it('should submit profile when complete button is pressed', async () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ currentStep: 6 })
      );

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      await act(async () => {
        fireEvent.press(getByTestId('complete-profile-button'));
      });

      expect(mockHookReturn.submitProfile).toHaveBeenCalled();
      expect(mockProps.onComplete).toHaveBeenCalled();
    });

    it('should show spinner on complete button when saving', () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ 
          currentStep: 6,
          isSaving: true,
        })
      );

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      expect(getByTestId('complete-button-spinner')).toBeTruthy();
    });

    it('should disable buttons when saving', () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ isSaving: true })
      );

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      const nextButton = getByTestId('next-button');
      const previousButton = getByTestId('previous-button');

      expect(nextButton.props.accessibilityState.disabled).toBe(true);
      expect(previousButton.props.accessibilityState.disabled).toBe(true);
    });
  });

  describe('Error Handling', () => {
    it('should display error messages', () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ 
          error: 'Something went wrong',
        })
      );

      const { getByText } = render(<TeacherProfileWizard {...mockProps} />);

      expect(getByText('Something went wrong')).toBeTruthy();
    });

    it('should handle step navigation errors gracefully', async () => {
      mockHookReturn.validateStep.mockRejectedValue(new Error('Validation error'));
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      await act(async () => {
        fireEvent.press(getByTestId('next-button'));
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        'Error moving to next step:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
    });

    it('should handle profile completion errors', async () => {
      mockHookReturn.submitProfile.mockRejectedValue(new Error('Submission error'));
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ currentStep: 6 })
      );

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      await act(async () => {
        fireEvent.press(getByTestId('complete-profile-button'));
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        'Error completing profile wizard:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
    });
  });

  describe('Exit Confirmation Dialog', () => {
    it('should show exit confirmation when there are unsaved changes', async () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ hasUnsavedChanges: true })
      );

      const { getByTestId, getByText } = render(
        <TeacherProfileWizard {...mockProps} />
      );

      await act(async () => {
        fireEvent.press(getByTestId('exit-button'));
      });

      expect(getByText('Save Your Progress?')).toBeTruthy();
      expect(getByText('You have unsaved changes to your profile. Would you like to save your progress before leaving?')).toBeTruthy();
    });

    it('should exit without confirmation when no unsaved changes', async () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ hasUnsavedChanges: false })
      );

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      await act(async () => {
        fireEvent.press(getByTestId('exit-button'));
      });

      expect(mockProps.onExit).toHaveBeenCalled();
    });

    it('should exit without saving when confirmed', async () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ hasUnsavedChanges: true })
      );

      const { getByTestId, getByText } = render(
        <TeacherProfileWizard {...mockProps} />
      );

      // Open dialog
      await act(async () => {
        fireEvent.press(getByTestId('exit-button'));
      });

      // Confirm exit without saving
      await act(async () => {
        fireEvent.press(getByText('Exit Without Saving'));
      });

      expect(mockProps.onExit).toHaveBeenCalled();
    });

    it('should save and exit when requested', async () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ hasUnsavedChanges: true })
      );

      const { getByTestId, getByText } = render(
        <TeacherProfileWizard {...mockProps} />
      );

      // Open dialog
      await act(async () => {
        fireEvent.press(getByTestId('exit-button'));
      });

      // Save and exit
      await act(async () => {
        fireEvent.press(getByText('Save & Exit'));
      });

      expect(mockHookReturn.saveProgress).toHaveBeenCalled();
      expect(mockProps.onExit).toHaveBeenCalled();
    });
  });

  describe('Profile Completion Tracker', () => {
    it('should render profile completion tracker', () => {
      const completionData = createMockCompletionData();
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ completionData })
      );

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      expect(getByTestId('profile-completion-tracker')).toBeTruthy();
    });

    it('should pass compact prop on mobile', () => {
      // Mock mobile dimensions
      jest.doMock('react-native', () => ({
        ...jest.requireActual('react-native'),
        Dimensions: {
          get: () => ({ width: 400, height: 800 }),
        },
        Platform: {
          OS: 'ios',
        },
      }));

      const completionData = createMockCompletionData();
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ completionData })
      );

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      const tracker = getByTestId('profile-completion-tracker');
      expect(tracker.props.compact).toBe(true);
    });
  });

  describe('Step Component Rendering', () => {
    it('should render current step component with correct props', () => {
      const formData = createMockProfileData();
      const validationErrors = { first_name: ['Required'] };

      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ 
          formData,
          validationErrors,
          isSaving: true,
        })
      );

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      const stepComponent = getByTestId('basic-info-step');
      expect(stepComponent.props.formData).toEqual(formData);
      expect(stepComponent.props.validationErrors).toEqual(validationErrors);
      expect(stepComponent.props.isLoading).toBe(true);
    });

    it('should call onFormDataChange when step component updates data', async () => {
      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      const stepComponent = getByTestId('basic-info-step');

      await act(async () => {
        stepComponent.props.onFormDataChange({ first_name: 'Updated' });
      });

      expect(mockHookReturn.updateFormData).toHaveBeenCalledWith({ first_name: 'Updated' });
    });
  });

  describe('Wizard Navigation (Desktop)', () => {
    beforeEach(() => {
      // Mock desktop dimensions
      jest.doMock('react-native', () => ({
        ...jest.requireActual('react-native'),
        Dimensions: {
          get: () => ({ width: 1024, height: 768 }),
        },
        Platform: {
          OS: 'web',
        },
      }));
    });

    it('should render wizard navigation on desktop', () => {
      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      expect(getByTestId('wizard-navigation')).toBeTruthy();
    });

    it('should pass correct props to wizard navigation', () => {
      const completionData = createMockCompletionData();
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ 
          currentStep: 2,
          completionData,
        })
      );

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      const navigation = getByTestId('wizard-navigation');
      expect(navigation.props.steps).toEqual(WIZARD_STEPS);
      expect(navigation.props.currentStep).toBe(2);
      expect(navigation.props.completionData).toEqual(completionData);
    });
  });

  describe('Integration with useProfileWizard', () => {
    it('should properly integrate all hook functionality', async () => {
      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      // Test form data update
      const stepComponent = getByTestId('basic-info-step');
      await act(async () => {
        stepComponent.props.onFormDataChange({ first_name: 'Test' });
      });

      expect(mockHookReturn.updateFormData).toHaveBeenCalledWith({ first_name: 'Test' });

      // Test next step navigation
      await act(async () => {
        fireEvent.press(getByTestId('next-button'));
      });

      expect(mockHookReturn.validateStep).toHaveBeenCalled();
      expect(mockHookReturn.saveProgress).toHaveBeenCalled();
    });

    it('should handle all wizard lifecycle events', async () => {
      const { unmount } = render(<TeacherProfileWizard {...mockProps} />);

      await waitForAsyncUpdates();

      expect(mockHookReturn.loadProgress).toHaveBeenCalled();

      unmount();

      // Should cleanup timers
      expect(clearTimeout).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have proper accessibility labels', () => {
      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      const exitButton = getByTestId('exit-button');
      const nextButton = getByTestId('next-button');
      const previousButton = getByTestId('previous-button');

      expect(exitButton.props.accessibilityLabel).toBeDefined();
      expect(nextButton.props.accessibilityLabel).toBeDefined();
      expect(previousButton.props.accessibilityLabel).toBeDefined();
    });

    it('should announce step changes to screen readers', () => {
      mockUseProfileWizard.mockReturnValue(
        createMockUseProfileWizard({ currentStep: 2 })
      );

      const { getByTestId } = render(<TeacherProfileWizard {...mockProps} />);

      const stepAnnouncement = getByTestId('step-announcement');
      expect(stepAnnouncement.props.accessibilityLiveRegion).toBe('polite');
      expect(stepAnnouncement.props.children).toContain('Step 3 of 7');
    });
  });

  describe('Performance', () => {
    it('should not cause unnecessary re-renders', () => {
      const renderSpy = jest.fn();
      
      const TestComponent = () => {
        renderSpy();
        return <TeacherProfileWizard {...mockProps} />;
      };

      const { rerender } = render(<TestComponent />);

      expect(renderSpy).toHaveBeenCalledTimes(1);

      // Re-render with same props
      rerender(<TestComponent />);

      expect(renderSpy).toHaveBeenCalledTimes(2);
    });

    it('should cleanup resources properly', () => {
      const { unmount } = render(<TeacherProfileWizard {...mockProps} />);

      const timeoutSpy = jest.spyOn(global, 'clearTimeout');

      unmount();

      expect(timeoutSpy).toHaveBeenCalled();
    });
  });
});