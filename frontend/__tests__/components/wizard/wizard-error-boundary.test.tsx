import { fireEvent } from '@testing-library/react-native';
import React from 'react';
import { View, Text, Pressable } from 'react-native';

import { render, throwError, expectErrorBoundary } from '../../utils/test-utils';

import WizardErrorBoundary from '@/components/wizard/WizardErrorBoundary';

// Test component that throws errors
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return (
    <View testID="success-component">
      <Text>No error</Text>
    </View>
  );
};

describe('WizardErrorBoundary', () => {
  const mockOnReset = jest.fn();
  const mockOnSaveAndExit = jest.fn();
  const mockOnGoToDashboard = jest.fn();

  const defaultProps = {
    onReset: mockOnReset,
    onSaveAndExit: mockOnSaveAndExit,
    onGoToDashboard: mockOnGoToDashboard,
    maxRetries: 3,
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Suppress console.error for error boundary tests
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    (console.error as jest.Mock).mockRestore();
  });

  describe('Normal Operation', () => {
    it('should render children when no error occurs', () => {
      const { getByTestId } = render(
        <WizardErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={false} />
        </WizardErrorBoundary>,
      );

      expect(getByTestId('success-component')).toBeTruthy();
    });

    it('should not interfere with normal component behavior', () => {
      const TestComponent = () => {
        const [count, setCount] = React.useState(0);

        return (
          <View>
            <Text testID="counter">{count}</Text>
            <Pressable testID="increment" onPress={() => setCount(c => c + 1)}>
              <Text>Increment</Text>
            </Pressable>
          </View>
        );
      };

      const { getByTestId } = render(
        <WizardErrorBoundary {...defaultProps}>
          <TestComponent />
        </WizardErrorBoundary>,
      );

      expect(getByTestId('counter')).toHaveTextContent('0');

      fireEvent.press(getByTestId('increment'));

      expect(getByTestId('counter')).toHaveTextContent('1');
    });
  });

  describe('Error Handling', () => {
    it('should catch and display error when child component throws', () => {
      const { getByText, getByTestId } = render(
        <WizardErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      expect(getByTestId('error-boundary-container')).toBeTruthy();
      expect(getByText('Something went wrong')).toBeTruthy();
      expect(getByText(/We encountered an unexpected error/)).toBeTruthy();
    });

    it('should show error details in development mode', () => {
      // Mock development environment
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';

      const { getByText } = render(
        <WizardErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      expect(getByText('Test error')).toBeTruthy();
      expect(getByTestId('error-details')).toBeTruthy();

      process.env.NODE_ENV = originalEnv;
    });

    it('should hide error details in production mode', () => {
      // Mock production environment
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';

      const { queryByTestId } = render(
        <WizardErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      expect(queryByTestId('error-details')).toBeNull();

      process.env.NODE_ENV = originalEnv;
    });

    it('should track retry attempts correctly', () => {
      const { getByTestId, rerender } = render(
        <WizardErrorBoundary {...defaultProps} maxRetries={2}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      // First error
      expect(getByTestId('retry-button')).toBeTruthy();

      // Reset and trigger error again
      fireEvent.press(getByTestId('retry-button'));

      rerender(
        <WizardErrorBoundary {...defaultProps} maxRetries={2}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      // Second error - should still show retry
      expect(getByTestId('retry-button')).toBeTruthy();

      // Reset and trigger error third time
      fireEvent.press(getByTestId('retry-button'));

      rerender(
        <WizardErrorBoundary {...defaultProps} maxRetries={2}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      // Third error - should not show retry (exceeded maxRetries)
      expect(() => getByTestId('retry-button')).toThrow();
    });

    it('should disable retry when max retries exceeded', () => {
      const { getByTestId, getByText } = render(
        <WizardErrorBoundary {...defaultProps} maxRetries={0}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      expect(() => getByTestId('retry-button')).toThrow();
      expect(getByText('Maximum retry attempts exceeded')).toBeTruthy();
    });
  });

  describe('Recovery Actions', () => {
    it('should call onReset when retry button is pressed', () => {
      const { getByTestId } = render(
        <WizardErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      fireEvent.press(getByTestId('retry-button'));

      expect(mockOnReset).toHaveBeenCalled();
    });

    it('should call onSaveAndExit when save and exit button is pressed', () => {
      const { getByTestId } = render(
        <WizardErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      fireEvent.press(getByTestId('save-exit-button'));

      expect(mockOnSaveAndExit).toHaveBeenCalled();
    });

    it('should call onGoToDashboard when dashboard button is pressed', () => {
      const { getByTestId } = render(
        <WizardErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      fireEvent.press(getByTestId('dashboard-button'));

      expect(mockOnGoToDashboard).toHaveBeenCalled();
    });

    it('should reset error state when retry is successful', () => {
      const ErrorComponent = ({ shouldThrow }: { shouldThrow: boolean }) => {
        if (shouldThrow) {
          throw new Error('Test error');
        }
        return (
          <View testID="success-after-retry">
            <Text>Recovered!</Text>
          </View>
        );
      };

      const TestWrapper = () => {
        const [shouldThrow, setShouldThrow] = React.useState(true);

        return (
          <WizardErrorBoundary {...defaultProps} onReset={() => setShouldThrow(false)}>
            <ErrorComponent shouldThrow={shouldThrow} />
          </WizardErrorBoundary>
        );
      };

      const { getByTestId, queryByTestId } = render(<TestWrapper />);

      // Should show error initially
      expect(getByTestId('error-boundary-container')).toBeTruthy();

      // Retry should recover
      fireEvent.press(getByTestId('retry-button'));

      expect(getByTestId('success-after-retry')).toBeTruthy();
      expect(queryByTestId('error-boundary-container')).toBeNull();
    });
  });

  describe('Error Information Display', () => {
    it('should display user-friendly error message', () => {
      const { getByText } = render(
        <WizardErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      expect(getByText('Something went wrong')).toBeTruthy();
      expect(
        getByText(/We encountered an unexpected error while processing your profile/),
      ).toBeTruthy();
    });

    it('should show helpful suggestions for recovery', () => {
      const { getByText } = render(
        <WizardErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      expect(getByText(/You can try the following options/)).toBeTruthy();
      expect(getByText(/Try Again/)).toBeTruthy();
      expect(getByText(/Save & Exit/)).toBeTruthy();
      expect(getByText(/Go to Dashboard/)).toBeTruthy();
    });

    it('should display retry count information', () => {
      const { getByText } = render(
        <WizardErrorBoundary {...defaultProps} maxRetries={3}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      expect(getByText(/Attempts remaining: 3/)).toBeTruthy();
    });

    it('should show different message when retries are exhausted', () => {
      const { getByText } = render(
        <WizardErrorBoundary {...defaultProps} maxRetries={0}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      expect(getByText('Maximum retry attempts exceeded')).toBeTruthy();
      expect(getByText(/Please save your progress and try again later/)).toBeTruthy();
    });
  });

  describe('Accessibility', () => {
    it('should have proper accessibility labels for recovery actions', () => {
      const { getByTestId } = render(
        <WizardErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      const retryButton = getByTestId('retry-button');
      const saveExitButton = getByTestId('save-exit-button');
      const dashboardButton = getByTestId('dashboard-button');

      expect(retryButton.props.accessibilityLabel).toContain('Try again');
      expect(saveExitButton.props.accessibilityLabel).toContain('Save progress and exit');
      expect(dashboardButton.props.accessibilityLabel).toContain('Go to dashboard');
    });

    it('should announce error to screen readers', () => {
      const { getByTestId } = render(
        <WizardErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      const errorAnnouncement = getByTestId('error-announcement');
      expect(errorAnnouncement.props.accessibilityLiveRegion).toBe('assertive');
      expect(errorAnnouncement.props.children).toContain('Error occurred');
    });

    it('should have proper heading hierarchy', () => {
      const { getByTestId } = render(
        <WizardErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      const errorHeading = getByTestId('error-heading');
      expect(errorHeading.props.accessibilityRole).toBe('heading');
      expect(errorHeading.props.accessibilityLevel).toBe(1);
    });
  });

  describe('Error Logging and Reporting', () => {
    it('should log error details for debugging', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      render(
        <WizardErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      expect(consoleSpy).toHaveBeenCalledWith(
        'WizardErrorBoundary caught an error:',
        expect.any(Error),
        expect.any(Object), // Error info
      );

      consoleSpy.mockRestore();
    });

    it('should provide error context information', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      render(
        <WizardErrorBoundary {...defaultProps}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      expect(consoleSpy).toHaveBeenCalledWith(
        'WizardErrorBoundary caught an error:',
        expect.any(Error),
        expect.objectContaining({
          componentStack: expect.any(String),
        }),
      );

      consoleSpy.mockRestore();
    });
  });

  describe('Edge Cases', () => {
    it('should handle missing callback props gracefully', () => {
      const { getByTestId } = render(
        <WizardErrorBoundary>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      // Should still render error UI
      expect(getByTestId('error-boundary-container')).toBeTruthy();

      // Buttons should be disabled or hidden when callbacks are missing
      const retryButton = getByTestId('retry-button');
      expect(retryButton.props.disabled).toBe(true);
    });

    it('should handle errors in error boundary itself', () => {
      const BuggyErrorBoundary = ({ children }: { children: React.ReactNode }) => {
        const [hasError, setHasError] = React.useState(false);

        if (hasError) {
          // Simulate error in error boundary
          throw new Error('Error boundary error');
        }

        return (
          <WizardErrorBoundary
            {...defaultProps}
            onReset={() => setHasError(true)} // This will cause error
          >
            {children}
          </WizardErrorBoundary>
        );
      };

      const { getByTestId } = render(
        <BuggyErrorBoundary>
          <ThrowError shouldThrow={true} />
        </BuggyErrorBoundary>,
      );

      // Should catch the initial error
      expect(getByTestId('error-boundary-container')).toBeTruthy();

      // Pressing retry should not crash the app
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      fireEvent.press(getByTestId('retry-button'));

      // Should have logged the error but not crashed
      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
    });

    it('should handle async errors in child components', async () => {
      const AsyncErrorComponent = () => {
        React.useEffect(() => {
          // Simulate async error (but catch it to avoid unhandled rejection)
          setTimeout(() => {
            try {
              throw new Error('Async error');
            } catch (error) {
              // This error would normally be unhandled, but error boundaries don't catch async errors
              if (__DEV__) {
                console.log('Async error caught in test:', error.message);
              }
            }
          }, 100);
        }, []);

        return (
          <View testID="async-component">
            <Text>Async component</Text>
          </View>
        );
      };

      const { getByTestId } = render(
        <WizardErrorBoundary {...defaultProps}>
          <AsyncErrorComponent />
        </WizardErrorBoundary>,
      );

      // Initially should render normally
      expect(getByTestId('async-component')).toBeTruthy();

      // Note: Error boundaries don't catch async errors by default
      // This test documents the current behavior
    });
  });

  describe('Performance', () => {
    it('should not impact performance when no errors occur', () => {
      const renderSpy = jest.fn();

      const TestComponent = () => {
        renderSpy();
        return (
          <View testID="test">
            <Text>Test</Text>
          </View>
        );
      };

      const { rerender } = render(
        <WizardErrorBoundary {...defaultProps}>
          <TestComponent />
        </WizardErrorBoundary>,
      );

      expect(renderSpy).toHaveBeenCalledTimes(1);

      // Re-render should not cause unnecessary renders
      rerender(
        <WizardErrorBoundary {...defaultProps}>
          <TestComponent />
        </WizardErrorBoundary>,
      );

      expect(renderSpy).toHaveBeenCalledTimes(2); // Only one additional render
    });

    it('should cleanup resources when unmounted', () => {
      const { unmount } = render(
        <WizardErrorBoundary {...defaultProps}>
          <View>
            <Text>Test</Text>
          </View>
        </WizardErrorBoundary>,
      );

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      unmount();

      // Should not cause any errors or memory leaks
      expect(consoleSpy).not.toHaveBeenCalled();

      consoleSpy.mockRestore();
    });
  });

  describe('Custom Error Messages', () => {
    it('should allow custom error messages', () => {
      const customProps = {
        ...defaultProps,
        fallbackMessage: 'Custom error message',
        fallbackDescription: 'Custom error description',
      };

      const { getByText } = render(
        <WizardErrorBoundary {...customProps}>
          <ThrowError shouldThrow={true} />
        </WizardErrorBoundary>,
      );

      expect(getByText('Custom error message')).toBeTruthy();
      expect(getByText('Custom error description')).toBeTruthy();
    });

    it('should support error message customization based on error type', () => {
      const CustomErrorBoundary = (props: any) => {
        const getCustomMessage = (error: Error) => {
          if (error.message.includes('Network')) {
            return 'Network connection error';
          }
          if (error.message.includes('Validation')) {
            return 'Data validation error';
          }
          return 'Unexpected error occurred';
        };

        return <WizardErrorBoundary {...props} getCustomMessage={getCustomMessage} />;
      };

      const NetworkError = () => {
        throw new Error('Network timeout');
      };

      const { getByText } = render(
        <CustomErrorBoundary {...defaultProps}>
          <NetworkError />
        </CustomErrorBoundary>,
      );

      expect(getByText('Network connection error')).toBeTruthy();
    });
  });
});
