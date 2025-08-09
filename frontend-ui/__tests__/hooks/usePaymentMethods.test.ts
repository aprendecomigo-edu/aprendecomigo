/**
 * usePaymentMethods Hook Tests
 *
 * Comprehensive test suite for the payment methods management hook.
 * Tests CRUD operations, error handling, loading states, and API integration.
 */

import { renderHook, act, waitFor } from '@testing-library/react-native';

import {
  createMockPaymentMethods,
  createMockPaymentMethod,
  mockSuccessfulPurchaseApi,
  mockFailedPurchaseApi,
} from '@/__tests__/utils/payment-test-utils';
import { PaymentMethodApiClient } from '@/api/paymentMethodApi';
import { usePaymentMethods } from '@/hooks/usePaymentMethods';

// Mock the API client
jest.mock('@/api/paymentMethodApi');
const mockPaymentMethodApiClient = PaymentMethodApiClient as jest.Mocked<
  typeof PaymentMethodApiClient
>;

// Mock React Native Alert
jest.mock('react-native', () => ({
  Alert: {
    alert: jest.fn(),
  },
}));

describe('usePaymentMethods Hook', () => {
  const mockEmail = 'test@example.com';
  const mockPaymentMethods = createMockPaymentMethods();

  beforeEach(() => {
    jest.clearAllMocks();
    // Setup default successful API responses
    mockPaymentMethodApiClient.getPaymentMethods.mockResolvedValue(mockPaymentMethods);
    mockPaymentMethodApiClient.removePaymentMethod.mockResolvedValue({ success: true });
    mockPaymentMethodApiClient.setDefaultPaymentMethod.mockResolvedValue({ success: true });
  });

  describe('Initial State', () => {
    it('initializes with correct default state', () => {
      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      expect(result.current.paymentMethods).toEqual([]);
      expect(result.current.loading).toBe(true);
      expect(result.current.error).toBeNull();
      expect(result.current.removing).toBe(false);
      expect(result.current.settingDefault).toBe(false);
      expect(result.current.operationError).toBeNull();
      expect(result.current.hasPaymentMethods).toBe(false);
    });

    it('loads payment methods on mount with email', async () => {
      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(mockPaymentMethodApiClient.getPaymentMethods).toHaveBeenCalledWith(mockEmail);
      expect(result.current.paymentMethods).toEqual(mockPaymentMethods);
      expect(result.current.hasPaymentMethods).toBe(true);
      expect(result.current.error).toBeNull();
    });

    it('does not load payment methods when email is not provided', async () => {
      const { result } = renderHook(() => usePaymentMethods());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(mockPaymentMethodApiClient.getPaymentMethods).not.toHaveBeenCalled();
      expect(result.current.paymentMethods).toEqual([]);
      expect(result.current.hasPaymentMethods).toBe(false);
    });

    it('handles API error during initial load', async () => {
      const error = new Error('Failed to load payment methods');
      mockPaymentMethodApiClient.getPaymentMethods.mockRejectedValue(error);

      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Failed to load payment methods');
      expect(result.current.paymentMethods).toEqual([]);
      expect(result.current.hasPaymentMethods).toBe(false);
    });
  });

  describe('Payment Methods Loading', () => {
    it('shows loading state during initial fetch', async () => {
      // Make the API call hang to test loading state
      let resolvePromise: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolvePromise = resolve;
      });
      mockPaymentMethodApiClient.getPaymentMethods.mockReturnValue(pendingPromise);

      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      expect(result.current.loading).toBe(true);
      expect(result.current.paymentMethods).toEqual([]);

      // Resolve the promise
      await act(async () => {
        resolvePromise!(mockPaymentMethods);
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });

    it('updates hasPaymentMethods correctly', async () => {
      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.hasPaymentMethods).toBe(true);
      });

      // Test with empty array
      mockPaymentMethodApiClient.getPaymentMethods.mockResolvedValue([]);

      await act(async () => {
        await result.current.refreshPaymentMethods();
      });

      expect(result.current.hasPaymentMethods).toBe(false);
    });

    it('handles network errors gracefully', async () => {
      const networkError = new Error('Network request failed');
      networkError.name = 'NetworkError';
      mockPaymentMethodApiClient.getPaymentMethods.mockRejectedValue(networkError);

      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.error).toBe('Network request failed');
      });
    });
  });

  describe('Refresh Payment Methods', () => {
    it('refreshes payment methods successfully', async () => {
      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Prepare new data for refresh
      const newMethods = [createMockPaymentMethod({ id: 'pm_new' })];
      mockPaymentMethodApiClient.getPaymentMethods.mockResolvedValue(newMethods);

      await act(async () => {
        await result.current.refreshPaymentMethods();
      });

      expect(result.current.paymentMethods).toEqual(newMethods);
      expect(mockPaymentMethodApiClient.getPaymentMethods).toHaveBeenCalledTimes(2);
    });

    it('shows loading state during refresh', async () => {
      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Make refresh hang
      let resolveRefresh: (value: any) => void;
      const pendingRefresh = new Promise(resolve => {
        resolveRefresh = resolve;
      });
      mockPaymentMethodApiClient.getPaymentMethods.mockReturnValue(pendingRefresh);

      act(() => {
        result.current.refreshPaymentMethods();
      });

      expect(result.current.loading).toBe(true);

      // Resolve the refresh
      await act(async () => {
        resolveRefresh!(mockPaymentMethods);
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });

    it('handles refresh errors correctly', async () => {
      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Make refresh fail
      mockPaymentMethodApiClient.getPaymentMethods.mockRejectedValue(new Error('Refresh failed'));

      await act(async () => {
        await result.current.refreshPaymentMethods();
      });

      expect(result.current.error).toBe('Refresh failed');
      expect(result.current.paymentMethods).toEqual([]); // Data is cleared on error per hook implementation
    });

    it('does not refresh when email is not provided', async () => {
      const { result } = renderHook(() => usePaymentMethods());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await act(async () => {
        await result.current.refreshPaymentMethods();
      });

      expect(mockPaymentMethodApiClient.getPaymentMethods).not.toHaveBeenCalled();
    });
  });

  describe('Remove Payment Method', () => {
    it('removes payment method successfully', async () => {
      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const methodIdToRemove = mockPaymentMethods[1].id; // Non-default method

      await act(async () => {
        await result.current.removePaymentMethod(methodIdToRemove);
      });

      expect(mockPaymentMethodApiClient.removePaymentMethod).toHaveBeenCalledWith(
        methodIdToRemove,
        mockEmail
      );
      expect(result.current.operationError).toBeNull();

      // Should refresh payment methods after removal
      expect(mockPaymentMethodApiClient.getPaymentMethods).toHaveBeenCalledTimes(2);
    });

    it('shows removing state during removal', async () => {
      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Make removal hang
      let resolveRemoval: (value: any) => void;
      const pendingRemoval = new Promise(resolve => {
        resolveRemoval = resolve;
      });
      mockPaymentMethodApiClient.removePaymentMethod.mockReturnValue(pendingRemoval);

      act(() => {
        result.current.removePaymentMethod('pm_test_456');
      });

      expect(result.current.removing).toBe(true);

      // Resolve the removal
      await act(async () => {
        resolveRemoval!({ success: true });
      });

      await waitFor(() => {
        expect(result.current.removing).toBe(false);
      });
    });

    it('handles removal errors correctly', async () => {
      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const errorMessage = 'Cannot remove default payment method';
      mockPaymentMethodApiClient.removePaymentMethod.mockRejectedValue(new Error(errorMessage));

      await act(async () => {
        try {
          await result.current.removePaymentMethod('pm_test_123');
        } catch (error) {
          // Expected to throw since the hook re-throws errors
        }
      });

      expect(result.current.operationError).toBe(errorMessage);
      expect(result.current.removing).toBe(false);
    });

    it('handles API response with success: false', async () => {
      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      mockPaymentMethodApiClient.removePaymentMethod.mockResolvedValue({
        success: false,
        message: 'Payment method is being used in a pending transaction',
      });

      await act(async () => {
        try {
          await result.current.removePaymentMethod('pm_test_123');
        } catch (error) {
          // Expected to throw since the hook re-throws errors
        }
      });

      expect(result.current.operationError).toBe(
        'Payment method is being used in a pending transaction'
      );
    });

    it('prevents removal when email is not provided', async () => {
      const { result } = renderHook(() => usePaymentMethods());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await act(async () => {
        await result.current.removePaymentMethod('pm_test_123');
      });

      expect(mockPaymentMethodApiClient.removePaymentMethod).not.toHaveBeenCalled();
      expect(result.current.operationError).toBe('Email is required');
    });
  });

  describe('Set Default Payment Method', () => {
    it('sets default payment method successfully', async () => {
      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const methodIdToSetDefault = mockPaymentMethods[1].id; // Non-default method

      await act(async () => {
        await result.current.setDefaultPaymentMethod(methodIdToSetDefault);
      });

      expect(mockPaymentMethodApiClient.setDefaultPaymentMethod).toHaveBeenCalledWith(
        methodIdToSetDefault,
        mockEmail
      );
      expect(result.current.operationError).toBeNull();

      // Should refresh payment methods after setting default
      expect(mockPaymentMethodApiClient.getPaymentMethods).toHaveBeenCalledTimes(2);
    });

    it('shows setting default state during operation', async () => {
      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Make setting default hang
      let resolveSetDefault: (value: any) => void;
      const pendingSetDefault = new Promise(resolve => {
        resolveSetDefault = resolve;
      });
      mockPaymentMethodApiClient.setDefaultPaymentMethod.mockReturnValue(pendingSetDefault);

      act(() => {
        result.current.setDefaultPaymentMethod('pm_test_456');
      });

      expect(result.current.settingDefault).toBe(true);

      // Resolve the operation
      await act(async () => {
        resolveSetDefault!({ success: true });
      });

      await waitFor(() => {
        expect(result.current.settingDefault).toBe(false);
      });
    });

    it('handles set default errors correctly', async () => {
      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const errorMessage = 'Payment method not found';
      mockPaymentMethodApiClient.setDefaultPaymentMethod.mockRejectedValue(new Error(errorMessage));

      await act(async () => {
        try {
          await result.current.setDefaultPaymentMethod('pm_nonexistent');
        } catch (error) {
          // Expected to throw since the hook re-throws errors
        }
      });

      expect(result.current.operationError).toBe(errorMessage);
      expect(result.current.settingDefault).toBe(false);
    });

    it('handles API response with success: false', async () => {
      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      mockPaymentMethodApiClient.setDefaultPaymentMethod.mockResolvedValue({
        success: false,
        message: 'Cannot set expired payment method as default',
      });

      await act(async () => {
        try {
          await result.current.setDefaultPaymentMethod('pm_test_123');
        } catch (error) {
          // Expected to throw since the hook re-throws errors
        }
      });

      expect(result.current.operationError).toBe('Cannot set expired payment method as default');
    });

    it('prevents setting default when email is not provided', async () => {
      const { result } = renderHook(() => usePaymentMethods());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await act(async () => {
        await result.current.setDefaultPaymentMethod('pm_test_123');
      });

      expect(mockPaymentMethodApiClient.setDefaultPaymentMethod).not.toHaveBeenCalled();
      expect(result.current.operationError).toBe('Email is required');
    });
  });

  describe('Error Management', () => {
    it('clears errors correctly', async () => {
      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Set an error
      mockPaymentMethodApiClient.removePaymentMethod.mockRejectedValue(new Error('Test error'));

      await act(async () => {
        try {
          await result.current.removePaymentMethod('pm_test_123');
        } catch (error) {
          // Expected to throw since the hook re-throws errors
        }
      });

      expect(result.current.operationError).toBe('Test error');

      // Clear errors
      await act(async () => {
        result.current.clearErrors();
      });

      expect(result.current.operationError).toBeNull();
    });

    it('clears both loading and operation errors', async () => {
      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      // Wait for initial load to complete
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Create a loading error by making refresh fail
      mockPaymentMethodApiClient.getPaymentMethods.mockRejectedValue(new Error('Loading error'));

      await act(async () => {
        await result.current.refreshPaymentMethods();
      });

      expect(result.current.error).toBe('Loading error');

      // Simulate operation error
      mockPaymentMethodApiClient.removePaymentMethod.mockRejectedValue(
        new Error('Operation error')
      );
      await act(async () => {
        try {
          await result.current.removePaymentMethod('pm_test_123');
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.operationError).toBe('Operation error');

      // Clear all errors
      await act(async () => {
        result.current.clearErrors();
      });

      expect(result.current.error).toBeNull();
      expect(result.current.operationError).toBeNull();
    });
  });

  describe('Edge Cases', () => {
    it('handles empty payment methods array', async () => {
      mockPaymentMethodApiClient.getPaymentMethods.mockResolvedValue([]);

      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.paymentMethods).toEqual([]);
      expect(result.current.hasPaymentMethods).toBe(false);
    });

    it('handles null/undefined email gracefully', async () => {
      const { result: resultNull } = renderHook(() => usePaymentMethods(null as any));
      const { result: resultUndefined } = renderHook(() => usePaymentMethods(undefined));

      await waitFor(() => {
        expect(resultNull.current.loading).toBe(false);
        expect(resultUndefined.current.loading).toBe(false);
      });

      expect(mockPaymentMethodApiClient.getPaymentMethods).not.toHaveBeenCalled();
    });

    it('handles malformed API responses', async () => {
      mockPaymentMethodApiClient.getPaymentMethods.mockResolvedValue(null as any);

      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.paymentMethods).toEqual([]);
      expect(result.current.hasPaymentMethods).toBe(false);
    });

    it('handles very large number of payment methods', async () => {
      const manyMethods = Array.from({ length: 100 }, (_, i) =>
        createMockPaymentMethod({ id: `pm_${i}` })
      );
      mockPaymentMethodApiClient.getPaymentMethods.mockResolvedValue(manyMethods);

      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.paymentMethods).toHaveLength(100);
      expect(result.current.hasPaymentMethods).toBe(true);
    });

    it('handles concurrent operations gracefully', async () => {
      const { result } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Start multiple operations simultaneously
      await act(async () => {
        const promises = [
          result.current.removePaymentMethod('pm_test_456'),
          result.current.setDefaultPaymentMethod('pm_test_456'),
          result.current.refreshPaymentMethods(),
        ];

        await Promise.allSettled(promises);
      });

      // Should handle all operations and end in stable state
      expect(result.current.removing).toBe(false);
      expect(result.current.settingDefault).toBe(false);
      expect(result.current.loading).toBe(false);
    });
  });

  describe('Email Changes', () => {
    it('reloads payment methods when email changes', async () => {
      const { result, rerender } = renderHook(({ email }) => usePaymentMethods(email), {
        initialProps: { email: 'user1@example.com' },
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(mockPaymentMethodApiClient.getPaymentMethods).toHaveBeenCalledWith(
        'user1@example.com'
      );

      // Change email
      rerender({ email: 'user2@example.com' });

      await waitFor(() => {
        expect(mockPaymentMethodApiClient.getPaymentMethods).toHaveBeenCalledWith(
          'user2@example.com'
        );
      });

      expect(mockPaymentMethodApiClient.getPaymentMethods).toHaveBeenCalledTimes(2);
    });

    it('clears data when email becomes undefined', async () => {
      const { result, rerender } = renderHook(({ email }) => usePaymentMethods(email), {
        initialProps: { email: 'user@example.com' },
      });

      await waitFor(() => {
        expect(result.current.hasPaymentMethods).toBe(true);
      });

      // Remove email - this will trigger refreshPaymentMethods with undefined email
      rerender({ email: undefined });

      await waitFor(() => {
        expect(result.current.paymentMethods).toEqual([]);
        expect(result.current.hasPaymentMethods).toBe(false);
        expect(result.current.error).toBeNull();
        expect(result.current.loading).toBe(false);
      });
    });
  });

  describe('Performance', () => {
    it('initializes quickly', () => {
      const start = performance.now();
      renderHook(() => usePaymentMethods(mockEmail));
      const end = performance.now();

      expect(end - start).toBeLessThan(50);
    });

    it('handles re-renders efficiently', async () => {
      const { result, rerender } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const start = performance.now();
      rerender();
      const end = performance.now();

      expect(end - start).toBeLessThan(25);
    });
  });

  describe('Memory Management', () => {
    it('cleans up properly when unmounted', async () => {
      const { result, unmount } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Unmount should not cause any errors
      expect(() => unmount()).not.toThrow();
    });

    it('handles unmounting during async operations', async () => {
      const { result, unmount } = renderHook(() => usePaymentMethods(mockEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Start an async operation
      let resolveOperation: (value: any) => void;
      const pendingOperation = new Promise(resolve => {
        resolveOperation = resolve;
      });
      mockPaymentMethodApiClient.removePaymentMethod.mockReturnValue(pendingOperation);

      act(() => {
        result.current.removePaymentMethod('pm_test_123');
      });

      // Unmount while operation is pending
      unmount();

      // Resolve operation after unmount - should not cause errors
      await act(async () => {
        resolveOperation!({ success: true });
      });
    });
  });
});
