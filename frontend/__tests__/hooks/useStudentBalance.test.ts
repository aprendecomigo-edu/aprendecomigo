/**
 * useStudentBalance Hook Tests
 *
 * Comprehensive test suite for the student balance hook.
 * Tests API calls, loading states, error handling, and refetch functionality.
 */

import { renderHook, waitFor, act } from '@testing-library/react-native';

import {
  createMockStudentBalance,
  createMockLowBalanceStudent,
  createMockCriticalBalanceStudent,
  createMockEmptyBalanceStudent,
  mockStudentApiCalls,
  mockSuccessfulStudentApi,
  mockFailedStudentApi,
  cleanupStudentMocks,
} from '@/__tests__/utils/student-test-utils';
import { useStudentBalance } from '@/hooks/useStudentBalance';

// Mock the PurchaseApiClient
jest.mock('@/api/purchaseApi', () => ({
  PurchaseApiClient: {
    getStudentBalance: jest.fn(),
  },
}));

describe('useStudentBalance Hook', () => {
  beforeEach(() => {
    cleanupStudentMocks();
  });

  describe('Initial Load', () => {
    it('starts with loading state', () => {
      mockStudentApiCalls.getStudentBalance.mockImplementation(
        () => new Promise(() => {}), // Never resolves
      );

      const { result } = renderHook(() => useStudentBalance());

      expect(result.current.loading).toBe(true);
      expect(result.current.balance).toBeNull();
      expect(result.current.error).toBeNull();
    });

    it('loads balance data successfully', async () => {
      const mockBalance = createMockStudentBalance();
      mockStudentApiCalls.getStudentBalance.mockResolvedValue(mockBalance);

      const { result } = renderHook(() => useStudentBalance());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.balance).toEqual(mockBalance);
      expect(result.current.error).toBeNull();
      expect(mockStudentApiCalls.getStudentBalance).toHaveBeenCalledWith(undefined);
    });

    it('loads balance data with email parameter', async () => {
      const mockBalance = createMockStudentBalance();
      const testEmail = 'student@test.com';
      mockStudentApiCalls.getStudentBalance.mockResolvedValue(mockBalance);

      const { result } = renderHook(() => useStudentBalance(testEmail));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.balance).toEqual(mockBalance);
      expect(mockStudentApiCalls.getStudentBalance).toHaveBeenCalledWith(testEmail);
    });

    it('handles API error on initial load', async () => {
      const errorMessage = 'Failed to load balance information';
      mockStudentApiCalls.getStudentBalance.mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useStudentBalance());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.balance).toBeNull();
      expect(result.current.error).toBe(errorMessage);
    });

    it('handles API error with custom message', async () => {
      const customError = new Error('Network connection failed');
      mockStudentApiCalls.getStudentBalance.mockRejectedValue(customError);

      const { result } = renderHook(() => useStudentBalance());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Network connection failed');
    });

    it('handles API error without message', async () => {
      mockStudentApiCalls.getStudentBalance.mockRejectedValue(new Error());

      const { result } = renderHook(() => useStudentBalance());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Failed to load balance information');
    });
  });

  describe('Email Parameter Changes', () => {
    it('refetches data when email parameter changes', async () => {
      const mockBalance1 = createMockStudentBalance({
        student_info: { id: 1, name: 'Student 1', email: 'student1@test.com' },
      });
      const mockBalance2 = createMockStudentBalance({
        student_info: { id: 2, name: 'Student 2', email: 'student2@test.com' },
      });

      mockStudentApiCalls.getStudentBalance
        .mockResolvedValueOnce(mockBalance1)
        .mockResolvedValueOnce(mockBalance2);

      const { result, rerender } = renderHook(({ email }) => useStudentBalance(email), {
        initialProps: { email: 'student1@test.com' },
      });

      // Wait for initial load
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.balance).toEqual(mockBalance1);
      expect(mockStudentApiCalls.getStudentBalance).toHaveBeenCalledWith('student1@test.com');

      // Change email parameter
      rerender({ email: 'student2@test.com' });

      await waitFor(() => {
        expect(result.current.balance).toEqual(mockBalance2);
      });

      expect(mockStudentApiCalls.getStudentBalance).toHaveBeenCalledWith('student2@test.com');
      expect(mockStudentApiCalls.getStudentBalance).toHaveBeenCalledTimes(2);
    });

    it('handles email parameter changing from undefined to defined', async () => {
      const mockBalance = createMockStudentBalance();
      mockStudentApiCalls.getStudentBalance.mockResolvedValue(mockBalance);

      const { result, rerender } = renderHook(({ email }) => useStudentBalance(email), {
        initialProps: { email: undefined },
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(mockStudentApiCalls.getStudentBalance).toHaveBeenCalledWith(undefined);

      // Change from undefined to defined email
      rerender({ email: 'student@test.com' });

      await waitFor(() => {
        expect(result.current.balance).toEqual(mockBalance);
      });

      expect(mockStudentApiCalls.getStudentBalance).toHaveBeenCalledWith('student@test.com');
    });

    it('handles email parameter changing from defined to undefined', async () => {
      const mockBalance = createMockStudentBalance();
      mockStudentApiCalls.getStudentBalance.mockResolvedValue(mockBalance);

      const { result, rerender } = renderHook(({ email }) => useStudentBalance(email), {
        initialProps: { email: 'student@test.com' },
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(mockStudentApiCalls.getStudentBalance).toHaveBeenCalledWith('student@test.com');

      // Change from defined email to undefined
      rerender({ email: undefined });

      await waitFor(() => {
        expect(result.current.balance).toEqual(mockBalance);
      });

      expect(mockStudentApiCalls.getStudentBalance).toHaveBeenCalledWith(undefined);
    });
  });

  describe('Refetch Functionality', () => {
    it('refetches data successfully', async () => {
      const initialBalance = createMockStudentBalance({
        balance_summary: { remaining_hours: '10.0' } as any,
      });
      const updatedBalance = createMockStudentBalance({
        balance_summary: { remaining_hours: '8.0' } as any,
      });

      mockStudentApiCalls.getStudentBalance
        .mockResolvedValueOnce(initialBalance)
        .mockResolvedValueOnce(updatedBalance);

      const { result } = renderHook(() => useStudentBalance());

      // Wait for initial load
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.balance).toEqual(initialBalance);

      // Trigger refetch
      await act(async () => {
        await result.current.refetch();
      });

      expect(result.current.balance).toEqual(updatedBalance);
      expect(mockStudentApiCalls.getStudentBalance).toHaveBeenCalledTimes(2);
    });

    it('handles refetch error', async () => {
      const initialBalance = createMockStudentBalance();
      mockStudentApiCalls.getStudentBalance
        .mockResolvedValueOnce(initialBalance)
        .mockRejectedValueOnce(new Error('Refetch failed'));

      const { result } = renderHook(() => useStudentBalance());

      // Wait for initial load
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.balance).toEqual(initialBalance);
      expect(result.current.error).toBeNull();

      // Trigger refetch with error
      await act(async () => {
        await result.current.refetch();
      });

      expect(result.current.balance).toBeNull();
      expect(result.current.error).toBe('Refetch failed');
    });

    it('shows loading state during refetch', async () => {
      const initialBalance = createMockStudentBalance();
      let resolveRefetch: (value: any) => void;
      const refetchPromise = new Promise(resolve => {
        resolveRefetch = resolve;
      });

      mockStudentApiCalls.getStudentBalance
        .mockResolvedValueOnce(initialBalance)
        .mockImplementationOnce(() => refetchPromise);

      const { result } = renderHook(() => useStudentBalance());

      // Wait for initial load
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Trigger refetch
      act(() => {
        result.current.refetch();
      });

      // Should show loading during refetch
      expect(result.current.loading).toBe(true);

      // Resolve refetch
      act(() => {
        resolveRefetch!(createMockStudentBalance());
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });

    it('clears error on successful refetch', async () => {
      mockStudentApiCalls.getStudentBalance
        .mockRejectedValueOnce(new Error('Initial error'))
        .mockResolvedValueOnce(createMockStudentBalance());

      const { result } = renderHook(() => useStudentBalance());

      // Wait for initial error
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Initial error');

      // Trigger successful refetch
      await act(async () => {
        await result.current.refetch();
      });

      expect(result.current.error).toBeNull();
      expect(result.current.balance).toBeTruthy();
    });
  });

  describe('Different Balance Scenarios', () => {
    it('handles low balance scenario', async () => {
      const lowBalance = createMockLowBalanceStudent();
      mockStudentApiCalls.getStudentBalance.mockResolvedValue(lowBalance);

      const { result } = renderHook(() => useStudentBalance());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.balance).toEqual(lowBalance);
      expect(parseFloat(result.current.balance!.balance_summary.remaining_hours)).toBe(1.5);
    });

    it('handles critical balance scenario', async () => {
      const criticalBalance = createMockCriticalBalanceStudent();
      mockStudentApiCalls.getStudentBalance.mockResolvedValue(criticalBalance);

      const { result } = renderHook(() => useStudentBalance());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.balance).toEqual(criticalBalance);
      expect(parseFloat(result.current.balance!.balance_summary.remaining_hours)).toBe(0.2);
    });

    it('handles empty balance scenario', async () => {
      const emptyBalance = createMockEmptyBalanceStudent();
      mockStudentApiCalls.getStudentBalance.mockResolvedValue(emptyBalance);

      const { result } = renderHook(() => useStudentBalance());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.balance).toEqual(emptyBalance);
      expect(parseFloat(result.current.balance!.balance_summary.remaining_hours)).toBe(0);
      expect(result.current.balance!.package_status.active_packages).toHaveLength(0);
    });

    it('handles balance with multiple active packages', async () => {
      const multiPackageBalance = createMockStudentBalance({
        package_status: {
          active_packages: [
            {
              transaction_id: 1,
              plan_name: 'Package A',
              hours_included: '10.0',
              hours_consumed: '3.0',
              hours_remaining: '7.0',
              expires_at: '2024-04-01T00:00:00Z',
              days_until_expiry: 30,
              is_expired: false,
            },
            {
              transaction_id: 2,
              plan_name: 'Package B',
              hours_included: '5.0',
              hours_consumed: '1.0',
              hours_remaining: '4.0',
              expires_at: '2024-05-01T00:00:00Z',
              days_until_expiry: 60,
              is_expired: false,
            },
          ],
          expired_packages: [],
        },
      });

      mockStudentApiCalls.getStudentBalance.mockResolvedValue(multiPackageBalance);

      const { result } = renderHook(() => useStudentBalance());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.balance).toEqual(multiPackageBalance);
      expect(result.current.balance!.package_status.active_packages).toHaveLength(2);
    });
  });

  describe('Performance', () => {
    it('executes hook quickly', async () => {
      mockStudentApiCalls.getStudentBalance.mockResolvedValue(createMockStudentBalance());

      const start = performance.now();
      const { result } = renderHook(() => useStudentBalance());
      const end = performance.now();

      expect(end - start).toBeLessThan(50);

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });

    it('handles multiple rapid refetches gracefully', async () => {
      const mockBalance = createMockStudentBalance();
      mockStudentApiCalls.getStudentBalance.mockResolvedValue(mockBalance);

      const { result } = renderHook(() => useStudentBalance());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Trigger multiple rapid refetches
      const promises = [];
      for (let i = 0; i < 5; i++) {
        promises.push(result.current.refetch());
      }

      await act(async () => {
        await Promise.all(promises);
      });

      expect(result.current.balance).toEqual(mockBalance);
      expect(result.current.error).toBeNull();
    });
  });

  describe('Memory Management', () => {
    it('cleans up properly when unmounted', async () => {
      mockStudentApiCalls.getStudentBalance.mockResolvedValue(createMockStudentBalance());

      const { result, unmount } = renderHook(() => useStudentBalance());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Unmount should not cause any warnings or errors
      expect(() => unmount()).not.toThrow();
    });

    it('handles unmount during pending API call', async () => {
      // Mock a slow API call
      mockStudentApiCalls.getStudentBalance.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 1000)),
      );

      const { unmount } = renderHook(() => useStudentBalance());

      // Unmount before API call completes
      expect(() => unmount()).not.toThrow();
    });
  });

  describe('Edge Cases', () => {
    it('handles malformed API response gracefully', async () => {
      // Mock malformed response
      mockStudentApiCalls.getStudentBalance.mockResolvedValue({
        // Missing required fields
        student_info: null,
      });

      const { result } = renderHook(() => useStudentBalance());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Should still set the balance even if malformed
      expect(result.current.balance).toBeTruthy();
      expect(result.current.error).toBeNull();
    });

    it('handles API timeout scenario', async () => {
      const timeoutError = new Error('Request timeout');
      timeoutError.name = 'TimeoutError';
      mockStudentApiCalls.getStudentBalance.mockRejectedValue(timeoutError);

      const { result } = renderHook(() => useStudentBalance());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Request timeout');
      expect(result.current.balance).toBeNull();
    });

    it('handles network error scenario', async () => {
      const networkError = new Error('Network Error');
      networkError.name = 'NetworkError';
      mockStudentApiCalls.getStudentBalance.mockRejectedValue(networkError);

      const { result } = renderHook(() => useStudentBalance());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Network Error');
    });

    it('handles extremely large balance numbers', async () => {
      const largeBalance = createMockStudentBalance({
        balance_summary: {
          hours_purchased: '999999.99',
          hours_consumed: '500000.50',
          remaining_hours: '499999.49',
          balance_amount: '9999999.99',
        },
      });

      mockStudentApiCalls.getStudentBalance.mockResolvedValue(largeBalance);

      const { result } = renderHook(() => useStudentBalance());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.balance).toEqual(largeBalance);
      expect(parseFloat(result.current.balance!.balance_summary.remaining_hours)).toBe(499999.49);
    });
  });
});
