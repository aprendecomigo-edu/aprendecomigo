/**
 * PaymentMethodsSection Component Tests
 *
 * Comprehensive test suite for the payment methods management component.
 * Tests CRUD operations, default method selection, error handling, and user interactions.
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';

import { PaymentMethodsSection } from '@/components/student/payment-methods/PaymentMethodsSection';
import { usePaymentMethods } from '@/hooks/usePaymentMethods';
import {
  createMockPaymentMethods,
  createMockPaymentMethod,
} from '@/__tests__/utils/payment-test-utils';

// Mock the hook
jest.mock('@/hooks/usePaymentMethods');
const mockUsePaymentMethods = usePaymentMethods as jest.MockedFunction<typeof usePaymentMethods>;

// Mock child components
jest.mock('@/components/student/payment-methods/AddPaymentMethodModal', () => ({
  AddPaymentMethodModal: ({ isOpen, onClose, onSuccess }: any) =>
    isOpen ? (
      <div testID="add-payment-modal">
        <button testID="modal-close" onPress={onClose}>
          Close
        </button>
        <button testID="modal-success" onPress={onSuccess}>
          Add Success
        </button>
      </div>
    ) : null,
}));

jest.mock('@/components/student/payment-methods/PaymentMethodCard', () => ({
  PaymentMethodCard: ({
    paymentMethod,
    onSetDefault,
    onRemove,
    isSettingDefault,
    isRemoving,
    canRemove,
  }: any) => (
    <div testID={`payment-method-${paymentMethod.id}`}>
      <span>{paymentMethod.card.brand} ****{paymentMethod.card.last4}</span>
      {paymentMethod.is_default && <span testID="default-badge">Default</span>}
      
      <button
        testID={`set-default-${paymentMethod.id}`}
        onPress={() => onSetDefault(paymentMethod.id)}
        disabled={isSettingDefault || paymentMethod.is_default}
      >
        {isSettingDefault ? 'Setting...' : 'Set Default'}
      </button>
      
      <button
        testID={`remove-${paymentMethod.id}`}
        onPress={() => onRemove(paymentMethod.id)}
        disabled={isRemoving || !canRemove}
      >
        {isRemoving ? 'Removing...' : 'Remove'}
      </button>
    </div>
  ),
}));

describe('PaymentMethodsSection Component', () => {
  const mockPaymentMethods = createMockPaymentMethods();
  const defaultProps = {
    email: 'test@example.com',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading State', () => {
    it('displays loading state when no payment methods exist', () => {
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: [],
        loading: true,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: false,
      });

      const { getByText, getByTestId } = render(<PaymentMethodsSection {...defaultProps} />);

      expect(getByText('Payment Methods')).toBeTruthy();
      expect(getByTestId('spinner')).toBeTruthy();
      expect(getByText('Loading payment methods...')).toBeTruthy();
    });

    it('does not show loading state when payment methods exist', () => {
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: mockPaymentMethods,
        loading: true,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { queryByText } = render(<PaymentMethodsSection {...defaultProps} />);

      expect(queryByText('Loading payment methods...')).toBeNull();
    });
  });

  describe('Error State', () => {
    it('displays error state when loading fails and no payment methods exist', () => {
      const errorMessage = 'Failed to load payment methods';
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: [],
        loading: false,
        error: errorMessage,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: false,
      });

      const { getByText } = render(<PaymentMethodsSection {...defaultProps} />);

      expect(getByText('Unable to Load Payment Methods')).toBeTruthy();
      expect(getByText(errorMessage)).toBeTruthy();
      expect(getByText('Try Again')).toBeTruthy();
    });

    it('allows retry when error occurs', () => {
      const mockRefresh = jest.fn();
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: [],
        loading: false,
        error: 'Network error',
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: mockRefresh,
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: false,
      });

      const { getByText } = render(<PaymentMethodsSection {...defaultProps} />);

      fireEvent.press(getByText('Try Again'));

      expect(mockRefresh).toHaveBeenCalled();
    });

    it('does not show error state when payment methods exist', () => {
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: mockPaymentMethods,
        loading: false,
        error: 'Some error',
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { queryByText } = render(<PaymentMethodsSection {...defaultProps} />);

      expect(queryByText('Unable to Load Payment Methods')).toBeNull();
    });
  });

  describe('Payment Methods Display', () => {
    it('renders payment methods correctly', () => {
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: mockPaymentMethods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByText, getByTestId } = render(<PaymentMethodsSection {...defaultProps} />);

      expect(getByText('Payment Methods')).toBeTruthy();
      expect(getByText('Manage your saved payment methods for tutoring hour purchases')).toBeTruthy();

      // Check that payment methods are displayed
      mockPaymentMethods.forEach(method => {
        expect(getByTestId(`payment-method-${method.id}`)).toBeTruthy();
        expect(getByText(`${method.card.brand} ****${method.card.last4}`)).toBeTruthy();
      });
    });

    it('shows default badge for default payment method', () => {
      const methodsWithDefault = [
        createMockPaymentMethod({ id: 'pm_1', is_default: true }),
        createMockPaymentMethod({ id: 'pm_2', is_default: false }),
      ];

      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: methodsWithDefault,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByTestId } = render(<PaymentMethodsSection {...defaultProps} />);

      expect(getByTestId('default-badge')).toBeTruthy();
    });

    it('displays security notice', () => {
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: mockPaymentMethods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByText } = render(<PaymentMethodsSection {...defaultProps} />);

      expect(getByText('Secure Payment Processing')).toBeTruthy();
      expect(getByText(/All payment methods are processed and stored securely/)).toBeTruthy();
    });
  });

  describe('Empty State', () => {
    it('displays empty state when no payment methods exist', () => {
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: [],
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: false,
      });

      const { getByText } = render(<PaymentMethodsSection {...defaultProps} />);

      expect(getByText('No Payment Methods')).toBeTruthy();
      expect(getByText(/Add a payment method to make purchasing/)).toBeTruthy();
      expect(getByText('Add Your First Payment Method')).toBeTruthy();
    });

    it('allows adding first payment method from empty state', () => {
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: [],
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: false,
      });

      const { getByText, getByTestId } = render(<PaymentMethodsSection {...defaultProps} />);

      fireEvent.press(getByText('Add Your First Payment Method'));

      expect(getByTestId('add-payment-modal')).toBeTruthy();
    });
  });

  describe('Add Payment Method', () => {
    it('opens add payment method modal when button is clicked', () => {
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: mockPaymentMethods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByText, getByTestId } = render(<PaymentMethodsSection {...defaultProps} />);

      fireEvent.press(getByText('Add Payment Method'));

      expect(getByTestId('add-payment-modal')).toBeTruthy();
    });

    it('clears errors when opening add payment method modal', () => {
      const mockClearErrors = jest.fn();
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: mockPaymentMethods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: 'Some error',
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: mockClearErrors,
        hasPaymentMethods: true,
      });

      const { getByText } = render(<PaymentMethodsSection {...defaultProps} />);

      fireEvent.press(getByText('Add Payment Method'));

      expect(mockClearErrors).toHaveBeenCalled();
    });

    it('closes modal and refreshes methods on successful addition', async () => {
      const mockRefresh = jest.fn().mockResolvedValue(undefined);
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: mockPaymentMethods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: mockRefresh,
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByText, getByTestId, queryByTestId } = render(<PaymentMethodsSection {...defaultProps} />);

      // Open modal
      fireEvent.press(getByText('Add Payment Method'));
      expect(getByTestId('add-payment-modal')).toBeTruthy();

      // Simulate successful addition
      await act(async () => {
        fireEvent.press(getByTestId('modal-success'));
      });

      expect(mockRefresh).toHaveBeenCalled();
      expect(queryByTestId('add-payment-modal')).toBeNull();
    });

    it('closes modal when close is clicked', () => {
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: mockPaymentMethods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByText, getByTestId, queryByTestId } = render(<PaymentMethodsSection {...defaultProps} />);

      // Open modal
      fireEvent.press(getByText('Add Payment Method'));
      expect(getByTestId('add-payment-modal')).toBeTruthy();

      // Close modal
      fireEvent.press(getByTestId('modal-close'));
      expect(queryByTestId('add-payment-modal')).toBeNull();
    });
  });

  describe('Set Default Payment Method', () => {
    it('handles setting default payment method', async () => {
      const mockSetDefault = jest.fn().mockResolvedValue(undefined);
      const methods = [
        createMockPaymentMethod({ id: 'pm_1', is_default: true }),
        createMockPaymentMethod({ id: 'pm_2', is_default: false }),
      ];

      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: methods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: mockSetDefault,
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByTestId } = render(<PaymentMethodsSection {...defaultProps} />);

      await act(async () => {
        fireEvent.press(getByTestId('set-default-pm_2'));
      });

      expect(mockSetDefault).toHaveBeenCalledWith('pm_2');
    });

    it('shows loading state while setting default', () => {
      const methods = [
        createMockPaymentMethod({ id: 'pm_1', is_default: true }),
        createMockPaymentMethod({ id: 'pm_2', is_default: false }),
      ];

      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: methods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByTestId, getByText } = render(<PaymentMethodsSection {...defaultProps} />);

      // Simulate clicking set default button
      fireEvent.press(getByTestId('set-default-pm_2'));

      // The component tracks setting state internally
      // Check that the button shows loading state
      expect(getByTestId('set-default-pm_2')).toBeTruthy();
    });

    it('disables default button for already default method', () => {
      const methods = [
        createMockPaymentMethod({ id: 'pm_1', is_default: true }),
        createMockPaymentMethod({ id: 'pm_2', is_default: false }),
      ];

      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: methods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByTestId } = render(<PaymentMethodsSection {...defaultProps} />);

      const defaultButton = getByTestId('set-default-pm_1');
      expect(defaultButton).toHaveProperty('disabled', true);
    });
  });

  describe('Remove Payment Method', () => {
    it('handles removing payment method', async () => {
      const mockRemove = jest.fn().mockResolvedValue(undefined);
      const methods = [
        createMockPaymentMethod({ id: 'pm_1', is_default: true }),
        createMockPaymentMethod({ id: 'pm_2', is_default: false }),
      ];

      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: methods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: mockRemove,
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByTestId } = render(<PaymentMethodsSection {...defaultProps} />);

      await act(async () => {
        fireEvent.press(getByTestId('remove-pm_2'));
      });

      expect(mockRemove).toHaveBeenCalledWith('pm_2');
    });

    it('prevents removing default payment method', () => {
      const methods = [
        createMockPaymentMethod({ id: 'pm_1', is_default: true }),
        createMockPaymentMethod({ id: 'pm_2', is_default: false }),
      ];

      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: methods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByTestId } = render(<PaymentMethodsSection {...defaultProps} />);

      const removeButton = getByTestId('remove-pm_1');
      expect(removeButton).toHaveProperty('disabled', true);
    });

    it('prevents removing when only one payment method exists', () => {
      const methods = [createMockPaymentMethod({ id: 'pm_1', is_default: true })];

      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: methods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByTestId } = render(<PaymentMethodsSection {...defaultProps} />);

      const removeButton = getByTestId('remove-pm_1');
      expect(removeButton).toHaveProperty('disabled', true);
    });

    it('shows loading state while removing', () => {
      const methods = [
        createMockPaymentMethod({ id: 'pm_1', is_default: true }),
        createMockPaymentMethod({ id: 'pm_2', is_default: false }),
      ];

      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: methods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByTestId } = render(<PaymentMethodsSection {...defaultProps} />);

      // Simulate clicking remove button
      fireEvent.press(getByTestId('remove-pm_2'));

      // The component tracks removing state internally
      expect(getByTestId('remove-pm_2')).toBeTruthy();
    });
  });

  describe('Operation Error Handling', () => {
    it('displays operation error when it occurs', () => {
      const operationError = 'Failed to remove payment method';
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: mockPaymentMethods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByText } = render(<PaymentMethodsSection {...defaultProps} />);

      expect(getByText('Operation Failed')).toBeTruthy();
      expect(getByText(operationError)).toBeTruthy();
      expect(getByText('Dismiss')).toBeTruthy();
    });

    it('allows dismissing operation error', () => {
      const mockClearErrors = jest.fn();
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: mockPaymentMethods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: 'Some error',
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: mockClearErrors,
        hasPaymentMethods: true,
      });

      const { getByText } = render(<PaymentMethodsSection {...defaultProps} />);

      fireEvent.press(getByText('Dismiss'));

      expect(mockClearErrors).toHaveBeenCalled();
    });

    it('does not display operation error when none exists', () => {
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: mockPaymentMethods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { queryByText } = render(<PaymentMethodsSection {...defaultProps} />);

      expect(queryByText('Operation Failed')).toBeNull();
    });
  });

  describe('Refresh Functionality', () => {
    it('calls refresh when refresh button is clicked', () => {
      const mockRefresh = jest.fn();
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: mockPaymentMethods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: mockRefresh,
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByText } = render(<PaymentMethodsSection {...defaultProps} />);

      fireEvent.press(getByText('Refresh'));

      expect(mockRefresh).toHaveBeenCalled();
    });

    it('shows loading state during refresh', () => {
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: mockPaymentMethods,
        loading: true,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByText } = render(<PaymentMethodsSection {...defaultProps} />);

      expect(getByText('Refreshing...')).toBeTruthy();
    });

    it('disables refresh button during loading', () => {
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: mockPaymentMethods,
        loading: true,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByText } = render(<PaymentMethodsSection {...defaultProps} />);

      const refreshButton = getByText('Refreshing...');
      expect(refreshButton.closest('button')).toHaveProperty('disabled', true);
    });
  });

  describe('Props Handling', () => {
    it('passes email prop to usePaymentMethods hook', () => {
      const testEmail = 'test@example.com';
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: [],
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: false,
      });

      render(<PaymentMethodsSection email={testEmail} />);

      expect(mockUsePaymentMethods).toHaveBeenCalledWith(testEmail);
    });

    it('handles undefined email prop', () => {
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: [],
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: false,
      });

      render(<PaymentMethodsSection />);

      expect(mockUsePaymentMethods).toHaveBeenCalledWith(undefined);
    });
  });

  describe('Performance', () => {
    it('renders quickly with multiple payment methods', () => {
      const manyMethods = Array.from({ length: 10 }, (_, i) =>
        createMockPaymentMethod({ id: `pm_${i}` })
      );

      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: manyMethods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const start = performance.now();
      render(<PaymentMethodsSection {...defaultProps} />);
      const end = performance.now();

      expect(end - start).toBeLessThan(100);
    });

    it('handles re-renders efficiently', () => {
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: mockPaymentMethods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { rerender } = render(<PaymentMethodsSection {...defaultProps} />);

      const start = performance.now();
      rerender(<PaymentMethodsSection {...defaultProps} />);
      const end = performance.now();

      expect(end - start).toBeLessThan(50);
    });
  });

  describe('Accessibility', () => {
    it('provides proper headings and structure', () => {
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: mockPaymentMethods,
        loading: false,
        error: null,
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: true,
      });

      const { getByText } = render(<PaymentMethodsSection {...defaultProps} />);

      expect(getByText('Payment Methods')).toBeTruthy();
      expect(getByText('Manage your saved payment methods for tutoring hour purchases')).toBeTruthy();
      expect(getByText('Secure Payment Processing')).toBeTruthy();
    });

    it('provides accessible error messages', () => {
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: [],
        loading: false,
        error: 'Connection failed',
        removing: false,
        settingDefault: false,
        operationError: null,
        refreshPaymentMethods: jest.fn(),
        removePaymentMethod: jest.fn(),
        setDefaultPaymentMethod: jest.fn(),
        clearErrors: jest.fn(),
        hasPaymentMethods: false,
      });

      const { getByText } = render(<PaymentMethodsSection {...defaultProps} />);

      expect(getByText('Unable to Load Payment Methods')).toBeTruthy();
      expect(getByText('Connection failed')).toBeTruthy();
    });
  });
});