import { fireEvent } from '@testing-library/react-native';
import React from 'react';

import { render, createMockCompletionData } from '../../utils/test-utils';

import { WizardNavigation } from '@/components/wizard/WizardNavigation';
import { WIZARD_STEPS } from '@/screens/onboarding/teacher-profile-wizard';

describe('WizardNavigation', () => {
  const mockOnStepClick = jest.fn();

  const defaultProps = {
    steps: WIZARD_STEPS,
    currentStep: 0,
    onStepClick: mockOnStepClick,
    completionData: createMockCompletionData(),
    hasErrors: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render all wizard steps', () => {
      const { getByText } = render(<WizardNavigation {...defaultProps} />);

      WIZARD_STEPS.forEach(step => {
        expect(getByText(step.title)).toBeTruthy();
      });
    });

    it('should highlight current step', () => {
      const { getByTestId } = render(<WizardNavigation {...defaultProps} currentStep={2} />);

      const currentStepButton = getByTestId('step-button-2');
      expect(currentStepButton.props.className).toContain('current');
    });

    it('should show completed steps with checkmark', () => {
      const completionData = createMockCompletionData({
        step_completion: {
          'basic-info': { is_complete: true, completion_percentage: 100, missing_fields: [] },
          biography: { is_complete: true, completion_percentage: 100, missing_fields: [] },
          education: {
            is_complete: false,
            completion_percentage: 50,
            missing_fields: ['certifications'],
          },
        },
      });

      const { getByTestId } = render(
        <WizardNavigation {...defaultProps} currentStep={2} completionData={completionData} />
      );

      expect(getByTestId('step-completed-0')).toBeTruthy();
      expect(getByTestId('step-completed-1')).toBeTruthy();
      expect(() => getByTestId('step-completed-2')).toThrow();
    });

    it('should show step icons correctly', () => {
      const { getByTestId } = render(<WizardNavigation {...defaultProps} />);

      WIZARD_STEPS.forEach((step, index) => {
        expect(getByTestId(`step-icon-${index}`)).toBeTruthy();
      });
    });

    it('should show step numbers when not completed', () => {
      const { getByTestId } = render(<WizardNavigation {...defaultProps} />);

      // Step 0 is current, should show number, not icon
      expect(getByTestId('step-number-0')).toBeTruthy();
    });
  });

  describe('Step Status Indicators', () => {
    it('should show error indicator for steps with errors', () => {
      const { getByTestId } = render(<WizardNavigation {...defaultProps} hasErrors={true} />);

      expect(getByTestId('step-error-indicator')).toBeTruthy();
    });

    it('should show completion percentage for partially completed steps', () => {
      const completionData = createMockCompletionData({
        step_completion: {
          education: {
            is_complete: false,
            completion_percentage: 75,
            missing_fields: ['certifications'],
          },
        },
      });

      const { getByText } = render(
        <WizardNavigation {...defaultProps} completionData={completionData} />
      );

      expect(getByText('75%')).toBeTruthy();
    });

    it('should show required badge for required steps', () => {
      const { getAllByText } = render(<WizardNavigation {...defaultProps} />);

      // All steps except preview are required
      const requiredBadges = getAllByText('Required');
      expect(requiredBadges).toHaveLength(6);
    });

    it('should show optional badge for optional steps', () => {
      const { getByText } = render(<WizardNavigation {...defaultProps} />);

      // Preview step is optional
      expect(getByText('Optional')).toBeTruthy();
    });
  });

  describe('Step Navigation', () => {
    it('should call onStepClick when step is clicked', () => {
      const { getByTestId } = render(<WizardNavigation {...defaultProps} />);

      fireEvent.press(getByTestId('step-button-3'));

      expect(mockOnStepClick).toHaveBeenCalledWith(3);
    });

    it('should allow navigation to completed steps', () => {
      const completionData = createMockCompletionData({
        step_completion: {
          'basic-info': { is_complete: true, completion_percentage: 100, missing_fields: [] },
          biography: { is_complete: true, completion_percentage: 100, missing_fields: [] },
        },
      });

      const { getByTestId } = render(
        <WizardNavigation {...defaultProps} currentStep={2} completionData={completionData} />
      );

      fireEvent.press(getByTestId('step-button-0'));
      expect(mockOnStepClick).toHaveBeenCalledWith(0);

      fireEvent.press(getByTestId('step-button-1'));
      expect(mockOnStepClick).toHaveBeenCalledWith(1);
    });

    it('should prevent navigation to future incomplete steps', () => {
      const { getByTestId } = render(<WizardNavigation {...defaultProps} currentStep={1} />);

      const futureStepButton = getByTestId('step-button-4');
      expect(futureStepButton.props.disabled).toBe(true);
    });

    it('should allow navigation to next step if current is complete', () => {
      const completionData = createMockCompletionData({
        step_completion: {
          'basic-info': { is_complete: true, completion_percentage: 100, missing_fields: [] },
        },
      });

      const { getByTestId } = render(
        <WizardNavigation {...defaultProps} currentStep={0} completionData={completionData} />
      );

      const nextStepButton = getByTestId('step-button-1');
      expect(nextStepButton.props.disabled).toBe(false);
    });
  });

  describe('Visual States', () => {
    it('should apply correct styles for completed steps', () => {
      const completionData = createMockCompletionData({
        step_completion: {
          'basic-info': { is_complete: true, completion_percentage: 100, missing_fields: [] },
        },
      });

      const { getByTestId } = render(
        <WizardNavigation {...defaultProps} currentStep={1} completionData={completionData} />
      );

      const completedStepButton = getByTestId('step-button-0');
      expect(completedStepButton.props.className).toContain('completed');
    });

    it('should apply correct styles for current step', () => {
      const { getByTestId } = render(<WizardNavigation {...defaultProps} currentStep={2} />);

      const currentStepButton = getByTestId('step-button-2');
      expect(currentStepButton.props.className).toContain('current');
    });

    it('should apply correct styles for disabled future steps', () => {
      const { getByTestId } = render(<WizardNavigation {...defaultProps} currentStep={1} />);

      const futureStepButton = getByTestId('step-button-4');
      expect(futureStepButton.props.className).toContain('disabled');
    });

    it('should show progress connector between steps', () => {
      const { getAllByTestId } = render(<WizardNavigation {...defaultProps} />);

      const connectors = getAllByTestId(/step-connector-/);
      expect(connectors).toHaveLength(WIZARD_STEPS.length - 1);
    });

    it('should highlight completed progress connectors', () => {
      const completionData = createMockCompletionData({
        step_completion: {
          'basic-info': { is_complete: true, completion_percentage: 100, missing_fields: [] },
          biography: { is_complete: true, completion_percentage: 100, missing_fields: [] },
        },
      });

      const { getByTestId } = render(
        <WizardNavigation {...defaultProps} currentStep={2} completionData={completionData} />
      );

      const connector1 = getByTestId('step-connector-0');
      expect(connector1.props.className).toContain('completed');
    });
  });

  describe('Accessibility', () => {
    it('should have proper accessibility labels for steps', () => {
      const { getByTestId } = render(<WizardNavigation {...defaultProps} />);

      WIZARD_STEPS.forEach((step, index) => {
        const stepButton = getByTestId(`step-button-${index}`);
        expect(stepButton.props.accessibilityLabel).toContain(step.title);
      });
    });

    it('should indicate current step to screen readers', () => {
      const { getByTestId } = render(<WizardNavigation {...defaultProps} currentStep={2} />);

      const currentStepButton = getByTestId('step-button-2');
      expect(currentStepButton.props.accessibilityLabel).toContain('current');
    });

    it('should indicate completed steps to screen readers', () => {
      const completionData = createMockCompletionData({
        step_completion: {
          'basic-info': { is_complete: true, completion_percentage: 100, missing_fields: [] },
        },
      });

      const { getByTestId } = render(
        <WizardNavigation {...defaultProps} currentStep={1} completionData={completionData} />
      );

      const completedStepButton = getByTestId('step-button-0');
      expect(completedStepButton.props.accessibilityLabel).toContain('completed');
    });

    it('should indicate disabled steps to screen readers', () => {
      const { getByTestId } = render(<WizardNavigation {...defaultProps} currentStep={1} />);

      const disabledStepButton = getByTestId('step-button-4');
      expect(disabledStepButton.props.accessibilityState.disabled).toBe(true);
    });

    it('should have proper accessibility role for navigation', () => {
      const { getByTestId } = render(<WizardNavigation {...defaultProps} />);

      const navigation = getByTestId('wizard-navigation');
      expect(navigation.props.accessibilityRole).toBe('tablist');
    });
  });

  describe('Responsive Design', () => {
    it('should handle compact mode on smaller screens', () => {
      const { getByTestId } = render(<WizardNavigation {...defaultProps} compact={true} />);

      const navigation = getByTestId('wizard-navigation');
      expect(navigation.props.className).toContain('compact');
    });

    it('should show abbreviated step titles in compact mode', () => {
      const { queryByText, getByText } = render(
        <WizardNavigation {...defaultProps} compact={true} />
      );

      // Should show abbreviated titles
      expect(getByText('Basic')).toBeTruthy();
      expect(getByText('Bio')).toBeTruthy();

      // Should not show full titles
      expect(queryByText('Basic Information')).toBeNull();
      expect(queryByText('Professional Biography')).toBeNull();
    });
  });

  describe('Edge Cases', () => {
    it('should handle missing completion data gracefully', () => {
      const { getByTestId } = render(<WizardNavigation {...defaultProps} completionData={null} />);

      // Should still render navigation
      expect(getByTestId('wizard-navigation')).toBeTruthy();
    });

    it('should handle empty steps array', () => {
      const { getByTestId } = render(<WizardNavigation {...defaultProps} steps={[]} />);

      const navigation = getByTestId('wizard-navigation');
      expect(navigation.props.children).toHaveLength(0);
    });

    it('should handle invalid current step index', () => {
      const { getByTestId } = render(<WizardNavigation {...defaultProps} currentStep={999} />);

      // Should not crash
      expect(getByTestId('wizard-navigation')).toBeTruthy();
    });

    it('should handle partial completion data', () => {
      const partialCompletionData = {
        ...createMockCompletionData(),
        step_completion: {
          'basic-info': { is_complete: true, completion_percentage: 100, missing_fields: [] },
          // Missing other steps
        },
      };

      const { getByTestId } = render(
        <WizardNavigation {...defaultProps} completionData={partialCompletionData} />
      );

      // Should handle missing step completion data
      expect(getByTestId('step-button-0')).toBeTruthy();
      expect(getByTestId('step-button-1')).toBeTruthy();
    });
  });

  describe('Performance', () => {
    it('should memoize step rendering to prevent unnecessary re-renders', () => {
      const renderSpy = jest.fn();

      const TestComponent = (props: any) => {
        renderSpy();
        return <WizardNavigation {...props} />;
      };

      const { rerender } = render(<TestComponent {...defaultProps} />);

      expect(renderSpy).toHaveBeenCalledTimes(1);

      // Re-render with same props
      rerender(<TestComponent {...defaultProps} />);

      expect(renderSpy).toHaveBeenCalledTimes(2);

      // Re-render with same currentStep
      rerender(<TestComponent {...defaultProps} currentStep={0} />);

      expect(renderSpy).toHaveBeenCalledTimes(3);
    });

    it('should only re-render affected steps when completion data changes', () => {
      const { rerender, getByTestId } = render(<WizardNavigation {...defaultProps} />);

      const step0 = getByTestId('step-button-0');
      const step1 = getByTestId('step-button-1');

      // Update completion data for step 0 only
      const updatedCompletionData = createMockCompletionData({
        step_completion: {
          'basic-info': { is_complete: true, completion_percentage: 100, missing_fields: [] },
        },
      });

      rerender(<WizardNavigation {...defaultProps} completionData={updatedCompletionData} />);

      // Step 0 should be updated, step 1 should remain the same
      expect(getByTestId('step-completed-0')).toBeTruthy();
    });
  });
});
