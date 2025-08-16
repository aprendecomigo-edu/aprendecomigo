/**
 * useStudentDashboard Hook Tests
 *
 * Comprehensive test suite for the student dashboard hook.
 * Tests tab management, data coordination, filtering, and search functionality.
 */

import { renderHook, waitFor, act } from '@testing-library/react-native';

import {
  createMockStudentBalance,
  createMockTransactionHistory,
  createMockPurchaseHistory,
  createMockDashboardState,
  mockStudentApiCalls,
  mockSuccessfulStudentApi,
  mockFailedStudentApi,
  cleanupStudentMocks,
} from '@/__tests__/utils/student-test-utils';
import { useStudentDashboard } from '@/hooks/useStudentDashboard';

// Mock the PurchaseApiClient
jest.mock('@/api/purchaseApi', () => ({
  PurchaseApiClient: {
    getStudentBalance: jest.fn(),
    getTransactionHistory: jest.fn(),
    getPurchaseHistory: jest.fn(),
  },
}));

// Mock timers for debounced search
jest.useFakeTimers();

describe('useStudentDashboard Hook', () => {
  beforeEach(() => {
    cleanupStudentMocks();
    jest.clearAllTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
    jest.useFakeTimers();
  });

  describe('Initial State', () => {
    it('initializes with correct default state', () => {
      mockSuccessfulStudentApi();

      const { result } = renderHook(() => useStudentDashboard());

      expect(result.current.state).toEqual({
        activeTab: 'overview',
        transactionFilters: {},
        purchaseFilters: { include_consumption: true },
        searchQuery: '',
      });
    });

    it('starts with loading balance data', () => {
      mockStudentApiCalls.getStudentBalance.mockImplementation(
        () => new Promise(() => {}), // Never resolves
      );

      const { result } = renderHook(() => useStudentDashboard());

      expect(result.current.balanceLoading).toBe(true);
      expect(result.current.balance).toBeNull();
      expect(result.current.balanceError).toBeNull();
    });

    it('initializes transactions and purchases as not loading', () => {
      mockSuccessfulStudentApi();

      const { result } = renderHook(() => useStudentDashboard());

      expect(result.current.transactionsLoading).toBe(false);
      expect(result.current.purchasesLoading).toBe(false);
      expect(result.current.transactions).toBeNull();
      expect(result.current.purchases).toBeNull();
    });
  });

  describe('Balance Data Management', () => {
    it('loads balance data on mount', async () => {
      const mockBalance = createMockStudentBalance();
      mockStudentApiCalls.getStudentBalance.mockResolvedValue(mockBalance);

      const { result } = renderHook(() => useStudentDashboard());

      await waitFor(() => {
        expect(result.current.balanceLoading).toBe(false);
      });

      expect(result.current.balance).toEqual(mockBalance);
      expect(result.current.balanceError).toBeNull();
      expect(mockStudentApiCalls.getStudentBalance).toHaveBeenCalledWith(undefined);
    });

    it('loads balance data with email parameter', async () => {
      const mockBalance = createMockStudentBalance();
      const testEmail = 'student@test.com';
      mockStudentApiCalls.getStudentBalance.mockResolvedValue(mockBalance);

      const { result } = renderHook(() => useStudentDashboard(testEmail));

      await waitFor(() => {
        expect(result.current.balanceLoading).toBe(false);
      });

      expect(result.current.balance).toEqual(mockBalance);
      expect(mockStudentApiCalls.getStudentBalance).toHaveBeenCalledWith(testEmail);
    });

    it('handles balance loading error', async () => {
      const errorMessage = 'Failed to load balance';
      mockStudentApiCalls.getStudentBalance.mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useStudentDashboard());

      await waitFor(() => {
        expect(result.current.balanceLoading).toBe(false);
      });

      expect(result.current.balance).toBeNull();
      expect(result.current.balanceError).toBe(errorMessage);
    });

    it('refreshes balance data when refreshBalance is called', async () => {
      const initialBalance = createMockStudentBalance({
        balance_summary: { remaining_hours: '10.0' } as any,
      });
      const updatedBalance = createMockStudentBalance({
        balance_summary: { remaining_hours: '8.0' } as any,
      });

      mockStudentApiCalls.getStudentBalance
        .mockResolvedValueOnce(initialBalance)
        .mockResolvedValueOnce(updatedBalance);

      const { result } = renderHook(() => useStudentDashboard());

      await waitFor(() => {
        expect(result.current.balance).toEqual(initialBalance);
      });

      await act(async () => {
        await result.current.actions.refreshBalance();
      });

      expect(result.current.balance).toEqual(updatedBalance);
    });
  });

  describe('Tab Management', () => {
    it('changes active tab correctly', () => {
      mockSuccessfulStudentApi();

      const { result } = renderHook(() => useStudentDashboard());

      act(() => {
        result.current.actions.setActiveTab('transactions');
      });

      expect(result.current.state.activeTab).toBe('transactions');
    });

    it('loads transaction data when switching to transactions tab', async () => {
      const mockTransactions = createMockTransactionHistory();
      mockSuccessfulStudentApi();
      mockStudentApiCalls.getTransactionHistory.mockResolvedValue(mockTransactions);

      const { result } = renderHook(() => useStudentDashboard());

      await waitFor(() => {
        expect(result.current.balanceLoading).toBe(false);
      });

      act(() => {
        result.current.actions.setActiveTab('transactions');
      });

      // Advance timers to trigger debounced search
      act(() => {
        jest.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(result.current.transactions).toEqual(mockTransactions);
      });

      expect(mockStudentApiCalls.getTransactionHistory).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        email: undefined,
      });
    });

    it('loads purchase data when switching to purchases tab', async () => {
      const mockPurchases = createMockPurchaseHistory();
      mockSuccessfulStudentApi();
      mockStudentApiCalls.getPurchaseHistory.mockResolvedValue(mockPurchases);

      const { result } = renderHook(() => useStudentDashboard());

      await waitFor(() => {
        expect(result.current.balanceLoading).toBe(false);
      });

      act(() => {
        result.current.actions.setActiveTab('purchases');
      });

      // Advance timers to trigger debounced search
      act(() => {
        jest.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(result.current.purchases).toEqual(mockPurchases);
      });

      expect(mockStudentApiCalls.getPurchaseHistory).toHaveBeenCalledWith({
        include_consumption: true,
        page: 1,
        page_size: 20,
        email: undefined,
      });
    });
  });

  describe('Transaction History Management', () => {
    it('refreshes transaction data correctly', async () => {
      const mockTransactions = createMockTransactionHistory();
      mockSuccessfulStudentApi();
      mockStudentApiCalls.getTransactionHistory.mockResolvedValue(mockTransactions);

      const { result } = renderHook(() => useStudentDashboard());

      await act(async () => {
        await result.current.actions.refreshTransactions(1);
      });

      expect(result.current.transactions).toEqual(mockTransactions);
      expect(mockStudentApiCalls.getTransactionHistory).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        email: undefined,
      });
    });

    it('handles transaction loading error', async () => {
      const errorMessage = 'Failed to load transactions';
      mockSuccessfulStudentApi();
      mockStudentApiCalls.getTransactionHistory.mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useStudentDashboard());

      await act(async () => {
        await result.current.actions.refreshTransactions(1);
      });

      expect(result.current.transactions).toBeNull();
      expect(result.current.transactionsError).toBe(errorMessage);
    });

    it('loads more transactions for pagination', async () => {
      const page1Transactions = createMockTransactionHistory({
        results: [{ id: 'txn_1' } as any],
        next: 'http://api.example.com/transactions?page=2',
      });

      const page2Transactions = createMockTransactionHistory({
        results: [{ id: 'txn_2' } as any],
        next: null,
      });

      mockSuccessfulStudentApi();
      mockStudentApiCalls.getTransactionHistory
        .mockResolvedValueOnce(page1Transactions)
        .mockResolvedValueOnce(page2Transactions);

      const { result } = renderHook(() => useStudentDashboard());

      // Load first page
      await act(async () => {
        await result.current.actions.refreshTransactions(1);
      });

      expect(result.current.transactions).toEqual(page1Transactions);

      // Load more
      await act(async () => {
        await result.current.actions.loadMoreTransactions();
      });

      expect(result.current.transactions?.results).toHaveLength(2);
      expect(result.current.transactions?.results[0].id).toBe('txn_1');
      expect(result.current.transactions?.results[1].id).toBe('txn_2');
    });

    it('does not load more when no next page exists', async () => {
      const mockTransactions = createMockTransactionHistory({ next: null });
      mockSuccessfulStudentApi();
      mockStudentApiCalls.getTransactionHistory.mockResolvedValue(mockTransactions);

      const { result } = renderHook(() => useStudentDashboard());

      await act(async () => {
        await result.current.actions.refreshTransactions(1);
      });

      const callCount = mockStudentApiCalls.getTransactionHistory.mock.calls.length;

      await act(async () => {
        await result.current.actions.loadMoreTransactions();
      });

      // Should not make additional API call
      expect(mockStudentApiCalls.getTransactionHistory.mock.calls.length).toBe(callCount);
    });

    it('does not load more when already loading', async () => {
      const mockTransactions = createMockTransactionHistory({
        next: 'http://api.example.com/transactions?page=2',
      });
      mockSuccessfulStudentApi();

      // Mock slow API call
      let resolveTransactions: (value: any) => void;
      const transactionPromise = new Promise(resolve => {
        resolveTransactions = resolve;
      });
      mockStudentApiCalls.getTransactionHistory.mockImplementation(() => transactionPromise);

      const { result } = renderHook(() => useStudentDashboard());

      // Start loading
      act(() => {
        result.current.actions.refreshTransactions(1);
      });

      expect(result.current.transactionsLoading).toBe(true);

      const callCount = mockStudentApiCalls.getTransactionHistory.mock.calls.length;

      // Try to load more while loading
      await act(async () => {
        await result.current.actions.loadMoreTransactions();
      });

      // Should not make additional API call
      expect(mockStudentApiCalls.getTransactionHistory.mock.calls.length).toBe(callCount);

      // Complete the initial call
      act(() => {
        resolveTransactions!(mockTransactions);
      });
    });
  });

  describe('Purchase History Management', () => {
    it('refreshes purchase data correctly', async () => {
      const mockPurchases = createMockPurchaseHistory();
      mockSuccessfulStudentApi();
      mockStudentApiCalls.getPurchaseHistory.mockResolvedValue(mockPurchases);

      const { result } = renderHook(() => useStudentDashboard());

      await act(async () => {
        await result.current.actions.refreshPurchases(1);
      });

      expect(result.current.purchases).toEqual(mockPurchases);
      expect(mockStudentApiCalls.getPurchaseHistory).toHaveBeenCalledWith({
        include_consumption: true,
        page: 1,
        page_size: 20,
        email: undefined,
      });
    });

    it('handles purchase loading error', async () => {
      const errorMessage = 'Failed to load purchases';
      mockSuccessfulStudentApi();
      mockStudentApiCalls.getPurchaseHistory.mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useStudentDashboard());

      await act(async () => {
        await result.current.actions.refreshPurchases(1);
      });

      expect(result.current.purchases).toBeNull();
      expect(result.current.purchasesError).toBe(errorMessage);
    });

    it('loads more purchases for pagination', async () => {
      const page1Purchases = createMockPurchaseHistory({
        results: [{ id: 1 } as any],
        next: 'http://api.example.com/purchases?page=2',
      });

      const page2Purchases = createMockPurchaseHistory({
        results: [{ id: 2 } as any],
        next: null,
      });

      mockSuccessfulStudentApi();
      mockStudentApiCalls.getPurchaseHistory
        .mockResolvedValueOnce(page1Purchases)
        .mockResolvedValueOnce(page2Purchases);

      const { result } = renderHook(() => useStudentDashboard());

      // Load first page
      await act(async () => {
        await result.current.actions.refreshPurchases(1);
      });

      expect(result.current.purchases).toEqual(page1Purchases);

      // Load more
      await act(async () => {
        await result.current.actions.loadMorePurchases();
      });

      expect(result.current.purchases?.results).toHaveLength(2);
      expect(result.current.purchases?.results[0].id).toBe(1);
      expect(result.current.purchases?.results[1].id).toBe(2);
    });
  });

  describe('Filter Management', () => {
    it('updates transaction filters correctly', () => {
      mockSuccessfulStudentApi();

      const { result } = renderHook(() => useStudentDashboard());

      act(() => {
        result.current.actions.setTransactionFilters({
          payment_status: 'succeeded',
          transaction_type: 'purchase',
        });
      });

      expect(result.current.state.transactionFilters).toEqual({
        payment_status: 'succeeded',
        transaction_type: 'purchase',
      });
    });

    it('updates purchase filters correctly', () => {
      mockSuccessfulStudentApi();

      const { result } = renderHook(() => useStudentDashboard());

      act(() => {
        result.current.actions.setPurchaseFilters({
          status: 'active',
          date_from: '2024-01-01',
        });
      });

      expect(result.current.state.purchaseFilters).toEqual({
        include_consumption: true,
        status: 'active',
        date_from: '2024-01-01',
      });
    });

    it('refreshes data when transaction filters change', async () => {
      const mockTransactions = createMockTransactionHistory();
      mockSuccessfulStudentApi();
      mockStudentApiCalls.getTransactionHistory.mockResolvedValue(mockTransactions);

      const { result } = renderHook(() => useStudentDashboard());

      // Switch to transactions tab first
      act(() => {
        result.current.actions.setActiveTab('transactions');
      });

      // Change filters
      act(() => {
        result.current.actions.setTransactionFilters({
          payment_status: 'succeeded',
        });
      });

      // Advance timers to trigger debounced search
      act(() => {
        jest.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(mockStudentApiCalls.getTransactionHistory).toHaveBeenCalledWith({
          payment_status: 'succeeded',
          page: 1,
          page_size: 20,
          email: undefined,
        });
      });
    });

    it('refreshes data when purchase filters change', async () => {
      const mockPurchases = createMockPurchaseHistory();
      mockSuccessfulStudentApi();
      mockStudentApiCalls.getPurchaseHistory.mockResolvedValue(mockPurchases);

      const { result } = renderHook(() => useStudentDashboard());

      // Switch to purchases tab first
      act(() => {
        result.current.actions.setActiveTab('purchases');
      });

      // Change filters
      act(() => {
        result.current.actions.setPurchaseFilters({
          status: 'active',
        });
      });

      // Advance timers to trigger debounced search
      act(() => {
        jest.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(mockStudentApiCalls.getPurchaseHistory).toHaveBeenCalledWith({
          include_consumption: true,
          status: 'active',
          page: 1,
          page_size: 20,
          email: undefined,
        });
      });
    });
  });

  describe('Search Functionality', () => {
    it('updates search query correctly', () => {
      mockSuccessfulStudentApi();

      const { result } = renderHook(() => useStudentDashboard());

      act(() => {
        result.current.actions.setSearchQuery('test search');
      });

      expect(result.current.state.searchQuery).toBe('test search');
    });

    it('debounces search query updates', async () => {
      const mockTransactions = createMockTransactionHistory();
      mockSuccessfulStudentApi();
      mockStudentApiCalls.getTransactionHistory.mockResolvedValue(mockTransactions);

      const { result } = renderHook(() => useStudentDashboard());

      // Switch to transactions tab
      act(() => {
        result.current.actions.setActiveTab('transactions');
      });

      // Rapid search query changes
      act(() => {
        result.current.actions.setSearchQuery('test');
      });

      act(() => {
        result.current.actions.setSearchQuery('test search');
      });

      // Should not trigger API call yet
      expect(mockStudentApiCalls.getTransactionHistory).not.toHaveBeenCalledWith(
        expect.objectContaining({ search: 'test search' }),
      );

      // Advance timers to trigger debounced search
      act(() => {
        jest.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(mockStudentApiCalls.getTransactionHistory).toHaveBeenCalledWith({
          page: 1,
          page_size: 20,
          email: undefined,
          search: 'test search',
        });
      });
    });

    it('includes search in API calls for transactions', async () => {
      const mockTransactions = createMockTransactionHistory();
      mockSuccessfulStudentApi();
      mockStudentApiCalls.getTransactionHistory.mockResolvedValue(mockTransactions);

      const { result } = renderHook(() => useStudentDashboard());

      // Set search query and switch to transactions tab
      act(() => {
        result.current.actions.setSearchQuery('mathematics');
        result.current.actions.setActiveTab('transactions');
      });

      // Advance timers to trigger debounced search
      act(() => {
        jest.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(mockStudentApiCalls.getTransactionHistory).toHaveBeenCalledWith({
          page: 1,
          page_size: 20,
          email: undefined,
          search: 'mathematics',
        });
      });
    });

    it('includes search in API calls for purchases', async () => {
      const mockPurchases = createMockPurchaseHistory();
      mockSuccessfulStudentApi();
      mockStudentApiCalls.getPurchaseHistory.mockResolvedValue(mockPurchases);

      const { result } = renderHook(() => useStudentDashboard());

      // Set search query and switch to purchases tab
      act(() => {
        result.current.actions.setSearchQuery('premium');
        result.current.actions.setActiveTab('purchases');
      });

      // Advance timers to trigger debounced search
      act(() => {
        jest.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(mockStudentApiCalls.getPurchaseHistory).toHaveBeenCalledWith({
          include_consumption: true,
          page: 1,
          page_size: 20,
          email: undefined,
          search: 'premium',
        });
      });
    });

    it('trims whitespace from search query', async () => {
      const mockTransactions = createMockTransactionHistory();
      mockSuccessfulStudentApi();
      mockStudentApiCalls.getTransactionHistory.mockResolvedValue(mockTransactions);

      const { result } = renderHook(() => useStudentDashboard());

      act(() => {
        result.current.actions.setSearchQuery('  test search  ');
        result.current.actions.setActiveTab('transactions');
      });

      // Advance timers to trigger debounced search
      act(() => {
        jest.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(mockStudentApiCalls.getTransactionHistory).toHaveBeenCalledWith({
          page: 1,
          page_size: 20,
          email: undefined,
          search: 'test search',
        });
      });
    });

    it('does not include search parameter when query is empty', async () => {
      const mockTransactions = createMockTransactionHistory();
      mockSuccessfulStudentApi();
      mockStudentApiCalls.getTransactionHistory.mockResolvedValue(mockTransactions);

      const { result } = renderHook(() => useStudentDashboard());

      act(() => {
        result.current.actions.setSearchQuery('');
        result.current.actions.setActiveTab('transactions');
      });

      // Advance timers to trigger debounced search
      act(() => {
        jest.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(mockStudentApiCalls.getTransactionHistory).toHaveBeenCalledWith({
          page: 1,
          page_size: 20,
          email: undefined,
        });
      });

      // Should not have search parameter
      const lastCall = mockStudentApiCalls.getTransactionHistory.mock.calls.slice(-1)[0];
      expect(lastCall[0]).not.toHaveProperty('search');
    });
  });

  describe('Refresh All Functionality', () => {
    it('refreshes all data sources', async () => {
      const mockBalance = createMockStudentBalance();
      const mockTransactions = createMockTransactionHistory();
      const mockPurchases = createMockPurchaseHistory();

      mockStudentApiCalls.getStudentBalance.mockResolvedValue(mockBalance);
      mockStudentApiCalls.getTransactionHistory.mockResolvedValue(mockTransactions);
      mockStudentApiCalls.getPurchaseHistory.mockResolvedValue(mockPurchases);

      const { result } = renderHook(() => useStudentDashboard());

      await act(async () => {
        await result.current.actions.refreshAll();
      });

      expect(mockStudentApiCalls.getStudentBalance).toHaveBeenCalled();
      expect(mockStudentApiCalls.getTransactionHistory).toHaveBeenCalled();
      expect(mockStudentApiCalls.getPurchaseHistory).toHaveBeenCalled();
    });

    it('handles partial failures in refresh all', async () => {
      const mockBalance = createMockStudentBalance();
      mockStudentApiCalls.getStudentBalance.mockResolvedValue(mockBalance);
      mockStudentApiCalls.getTransactionHistory.mockRejectedValue(new Error('Transaction error'));
      mockStudentApiCalls.getPurchaseHistory.mockRejectedValue(new Error('Purchase error'));

      const { result } = renderHook(() => useStudentDashboard());

      // Should not throw even if some calls fail
      await act(async () => {
        await result.current.actions.refreshAll();
      });

      expect(result.current.balance).toEqual(mockBalance);
      expect(result.current.transactionsError).toBe('Transaction error');
      expect(result.current.purchasesError).toBe('Purchase error');
    });
  });

  describe('Performance', () => {
    it('executes hook quickly', () => {
      mockSuccessfulStudentApi();

      const start = performance.now();
      renderHook(() => useStudentDashboard());
      const end = performance.now();

      expect(end - start).toBeLessThan(50);
    });

    it('handles rapid state changes efficiently', () => {
      mockSuccessfulStudentApi();

      const { result } = renderHook(() => useStudentDashboard());

      const start = performance.now();

      // Rapid state changes
      act(() => {
        result.current.actions.setActiveTab('transactions');
        result.current.actions.setSearchQuery('test');
        result.current.actions.setTransactionFilters({ payment_status: 'succeeded' });
        result.current.actions.setActiveTab('purchases');
      });

      const end = performance.now();

      expect(end - start).toBeLessThan(50);
    });
  });

  describe('Memory Management', () => {
    it('cleans up properly when unmounted', async () => {
      mockSuccessfulStudentApi();

      const { unmount } = renderHook(() => useStudentDashboard());

      // Unmount should not cause any warnings or errors
      expect(() => unmount()).not.toThrow();
    });

    it('handles unmount during pending API calls', () => {
      mockStudentApiCalls.getStudentBalance.mockImplementation(
        () => new Promise(() => {}), // Never resolves
      );

      const { unmount } = renderHook(() => useStudentDashboard());

      // Unmount before API calls complete
      expect(() => unmount()).not.toThrow();
    });
  });

  describe('Edge Cases', () => {
    it('handles empty API responses gracefully', async () => {
      mockStudentApiCalls.getStudentBalance.mockResolvedValue(null as any);
      mockStudentApiCalls.getTransactionHistory.mockResolvedValue({ results: [], count: 0 } as any);
      mockStudentApiCalls.getPurchaseHistory.mockResolvedValue({ results: [], count: 0 } as any);

      const { result } = renderHook(() => useStudentDashboard());

      await waitFor(() => {
        expect(result.current.balanceLoading).toBe(false);
      });

      // Should handle null balance gracefully
      expect(result.current.balance).toBeNull();
      expect(result.current.balanceError).toBe('Failed to load balance information');
    });

    it('handles API timeout scenarios', async () => {
      const timeoutError = new Error('Request timeout');
      timeoutError.name = 'TimeoutError';
      mockStudentApiCalls.getStudentBalance.mockRejectedValue(timeoutError);

      const { result } = renderHook(() => useStudentDashboard());

      await waitFor(() => {
        expect(result.current.balanceLoading).toBe(false);
      });

      expect(result.current.balanceError).toBe('Request timeout');
    });

    it('handles extremely large data sets', async () => {
      const largeTransactionHistory = createMockTransactionHistory({
        results: Array.from({ length: 1000 }, (_, i) => ({ id: `txn_${i}` }) as any),
        count: 10000,
      });

      mockSuccessfulStudentApi();
      mockStudentApiCalls.getTransactionHistory.mockResolvedValue(largeTransactionHistory);

      const { result } = renderHook(() => useStudentDashboard());

      await act(async () => {
        await result.current.actions.refreshTransactions(1);
      });

      expect(result.current.transactions?.results).toHaveLength(1000);
    });
  });
});
