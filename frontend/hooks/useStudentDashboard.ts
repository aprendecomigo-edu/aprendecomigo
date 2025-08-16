/**
 * Custom hook for managing student dashboard data and state.
 *
 * Provides centralized state management for dashboard tabs, filters,
 * search functionality, and data fetching across all dashboard sections.
 */

import { useState, useCallback, useEffect, useMemo } from 'react';

import { PurchaseApiClient } from '@/api/purchaseApi';
import type {
  DashboardState,
  TransactionFilterOptions,
  PurchaseFilterOptions,
  PaginatedTransactionHistory,
  PaginatedPurchaseHistory,
  StudentBalanceResponse,
} from '@/types/purchase';

interface UseStudentDashboardResult {
  // Dashboard state
  state: DashboardState;

  // Balance data
  balance: StudentBalanceResponse | null;
  balanceLoading: boolean;
  balanceError: string | null;

  // Transaction history
  transactions: PaginatedTransactionHistory | null;
  transactionsLoading: boolean;
  transactionsError: string | null;

  // Purchase history
  purchases: PaginatedPurchaseHistory | null;
  purchasesLoading: boolean;
  purchasesError: string | null;

  // Actions
  actions: {
    setActiveTab: (tab: DashboardState['activeTab']) => void;
    setTransactionFilters: (filters: Partial<TransactionFilterOptions>) => void;
    setPurchaseFilters: (filters: Partial<PurchaseFilterOptions>) => void;
    setSearchQuery: (query: string) => void;
    refreshBalance: () => Promise<void>;
    refreshTransactions: (page?: number) => Promise<void>;
    refreshPurchases: (page?: number) => Promise<void>;
    refreshAll: () => Promise<void>;
    loadMoreTransactions: () => Promise<void>;
    loadMorePurchases: () => Promise<void>;
  };
}

/**
 * Hook for managing student dashboard data and state.
 */
export function useStudentDashboard(email?: string): UseStudentDashboardResult {
  // Dashboard state
  const [state, setState] = useState<DashboardState>({
    activeTab: 'overview',
    transactionFilters: {},
    purchaseFilters: { include_consumption: true },
    searchQuery: '',
  });

  // Balance state
  const [balance, setBalance] = useState<StudentBalanceResponse | null>(null);
  const [balanceLoading, setBalanceLoading] = useState(true);
  const [balanceError, setBalanceError] = useState<string | null>(null);

  // Transaction history state
  const [transactions, setTransactions] = useState<PaginatedTransactionHistory | null>(null);
  const [transactionsLoading, setTransactionsLoading] = useState(false);
  const [transactionsError, setTransactionsError] = useState<string | null>(null);

  // Purchase history state
  const [purchases, setPurchases] = useState<PaginatedPurchaseHistory | null>(null);
  const [purchasesLoading, setPurchasesLoading] = useState(false);
  const [purchasesError, setPurchasesError] = useState<string | null>(null);

  // Actions
  const setActiveTab = useCallback((tab: DashboardState['activeTab']) => {
    setState(prev => ({ ...prev, activeTab: tab }));
  }, []);

  const setTransactionFilters = useCallback((filters: Partial<TransactionFilterOptions>) => {
    setState(prev => ({
      ...prev,
      transactionFilters: { ...prev.transactionFilters, ...filters },
    }));
  }, []);

  const setPurchaseFilters = useCallback((filters: Partial<PurchaseFilterOptions>) => {
    setState(prev => ({
      ...prev,
      purchaseFilters: { ...prev.purchaseFilters, ...filters },
    }));
  }, []);

  const setSearchQuery = useCallback((query: string) => {
    setState(prev => ({ ...prev, searchQuery: query }));
  }, []);

  // Debounced search query for API calls
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState(state.searchQuery);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchQuery(state.searchQuery);
    }, 300);

    return () => clearTimeout(timer);
  }, [state.searchQuery]);

  // Fetch balance data
  const refreshBalance = useCallback(async () => {
    setBalanceLoading(true);
    setBalanceError(null);

    try {
      const balanceData = await PurchaseApiClient.getStudentBalance(email);
      setBalance(balanceData);
    } catch (error: any) {
      console.error('Error fetching balance:', error);
      setBalanceError(error.message || 'Failed to load balance information');
      setBalance(null);
    } finally {
      setBalanceLoading(false);
    }
  }, [email]);

  // Fetch transaction history
  const refreshTransactions = useCallback(
    async (page = 1) => {
      setTransactionsLoading(true);
      setTransactionsError(null);

      try {
        const options = {
          ...state.transactionFilters,
          page,
          page_size: 20,
          email,
        };

        // Add search to filters if present
        if (debouncedSearchQuery.trim()) {
          options.search = debouncedSearchQuery.trim();
        }

        const transactionData = await PurchaseApiClient.getTransactionHistory(options);

        if (page === 1) {
          setTransactions(transactionData);
        } else {
          // Append to existing data for pagination
          setTransactions(prev =>
            prev
              ? {
                  ...transactionData,
                  results: [...prev.results, ...transactionData.results],
                }
              : transactionData,
          );
        }
      } catch (error: any) {
        console.error('Error fetching transactions:', error);
        setTransactionsError(error.message || 'Failed to load transaction history');
        if (page === 1) {
          setTransactions(null);
        }
      } finally {
        setTransactionsLoading(false);
      }
    },
    [state.transactionFilters, debouncedSearchQuery, email],
  );

  // Fetch purchase history
  const refreshPurchases = useCallback(
    async (page = 1) => {
      setPurchasesLoading(true);
      setPurchasesError(null);

      try {
        const options = {
          ...state.purchaseFilters,
          page,
          page_size: 20,
          email,
        };

        // Add search to filters if present
        if (debouncedSearchQuery.trim()) {
          options.search = debouncedSearchQuery.trim();
        }

        const purchaseData = await PurchaseApiClient.getPurchaseHistory(options);

        if (page === 1) {
          setPurchases(purchaseData);
        } else {
          // Append to existing data for pagination
          setPurchases(prev =>
            prev
              ? {
                  ...purchaseData,
                  results: [...prev.results, ...purchaseData.results],
                }
              : purchaseData,
          );
        }
      } catch (error: any) {
        console.error('Error fetching purchases:', error);
        setPurchasesError(error.message || 'Failed to load purchase history');
        if (page === 1) {
          setPurchases(null);
        }
      } finally {
        setPurchasesLoading(false);
      }
    },
    [state.purchaseFilters, debouncedSearchQuery, email],
  );

  // Refresh all data with graceful degradation
  const refreshAll = useCallback(async () => {
    const results = await Promise.allSettled([
      refreshBalance(),
      refreshTransactions(1),
      refreshPurchases(1),
    ]);

    // Log any failures for monitoring
    const operations = ['balance', 'transactions', 'purchases'];
    results.forEach((result, index) => {
      if (result.status === 'rejected') {
        console.error(`Failed to refresh ${operations[index]}:`, result.reason);
      }
    });

    // All operations are independent, so we continue even if some fail
    // Individual error states are handled by the respective functions
  }, [refreshBalance, refreshTransactions, refreshPurchases]);

  // Load more data for pagination
  const loadMoreTransactions = useCallback(async () => {
    if (!transactions?.next || transactionsLoading) return;

    // Calculate next page from URL or increment current page
    const currentPage = Math.ceil(transactions.results.length / 20);
    await refreshTransactions(currentPage + 1);
  }, [transactions, transactionsLoading, refreshTransactions]);

  const loadMorePurchases = useCallback(async () => {
    if (!purchases?.next || purchasesLoading) return;

    // Calculate next page from URL or increment current page
    const currentPage = Math.ceil(purchases.results.length / 20);
    await refreshPurchases(currentPage + 1);
  }, [purchases, purchasesLoading, refreshPurchases]);

  // Initial data fetch
  useEffect(() => {
    refreshBalance();
  }, [refreshBalance]);

  // Refresh transactions when filters change
  useEffect(() => {
    if (state.activeTab === 'transactions') {
      refreshTransactions(1);
    }
  }, [state.activeTab, state.transactionFilters, debouncedSearchQuery, refreshTransactions]);

  // Refresh purchases when filters change
  useEffect(() => {
    if (state.activeTab === 'purchases') {
      refreshPurchases(1);
    }
  }, [state.activeTab, state.purchaseFilters, debouncedSearchQuery, refreshPurchases]);

  return {
    state,
    balance,
    balanceLoading,
    balanceError,
    transactions,
    transactionsLoading,
    transactionsError,
    purchases,
    purchasesLoading,
    purchasesError,
    actions: {
      setActiveTab,
      setTransactionFilters,
      setPurchaseFilters,
      setSearchQuery,
      refreshBalance,
      refreshTransactions,
      refreshPurchases,
      refreshAll,
      loadMoreTransactions,
      loadMorePurchases,
    },
  };
}
