/**
 * Child Account Hook
 *
 * Custom hook for managing individual child account data
 * from a parent's perspective including balance, history, and settings.
 */

import { useState, useEffect, useCallback } from 'react';

import {
  getChildProfile,
  getChildAccountBalance,
  getChildTransactionHistory,
  getChildPurchaseHistory,
  getBudgetControlForChild,
  updateBudgetControl,
  createBudgetControl,
  ChildProfile,
  FamilyBudgetControl,
} from '@/api/parentApi';

interface ChildAccountData {
  profile: ChildProfile | null;
  balance: any | null; // Using the same structure as student balance
  transactionHistory: any[];
  purchaseHistory: any[];
  budgetControl: FamilyBudgetControl | null;
}

interface UseChildAccountState {
  childData: ChildAccountData;
  isLoading: boolean;
  error: string | null;
  isRefreshing: boolean;
}

interface UseChildAccountActions {
  refreshChildData: () => Promise<void>;
  updateChildBudget: (budgetData: Partial<FamilyBudgetControl>) => Promise<void>;
  loadTransactionHistory: (page?: number) => Promise<void>;
  loadPurchaseHistory: (page?: number) => Promise<void>;
}

export const useChildAccount = (childId: string) => {
  const [state, setState] = useState<UseChildAccountState>({
    childData: {
      profile: null,
      balance: null,
      transactionHistory: [],
      purchaseHistory: [],
      budgetControl: null,
    },
    isLoading: true,
    error: null,
    isRefreshing: false,
  });

  // Load child account data
  const loadChildData = useCallback(
    async (isRefresh = false) => {
      try {
        setState(prev => ({
          ...prev,
          isLoading: !isRefresh,
          isRefreshing: isRefresh,
          error: null,
        }));

        // Load all child data in parallel
        const [profile, balance, budgetControl] = await Promise.all([
          getChildProfile(childId),
          getChildAccountBalance(childId),
          getBudgetControlForChild(childId).catch(() => null), // Budget control might not exist
        ]);

        // Load initial transaction and purchase history
        const [transactionHistory, purchaseHistory] = await Promise.all([
          getChildTransactionHistory(childId, { limit: 20 }),
          getChildPurchaseHistory(childId, { limit: 20 }),
        ]);

        setState(prev => ({
          ...prev,
          childData: {
            profile,
            balance,
            transactionHistory: transactionHistory.results || transactionHistory,
            purchaseHistory: purchaseHistory.results || purchaseHistory,
            budgetControl,
          },
          isLoading: false,
          isRefreshing: false,
        }));
      } catch (error) {
        console.error('Error loading child account data:', error);
        setState(prev => ({
          ...prev,
          error: error instanceof Error ? error.message : 'Failed to load child account data',
          isLoading: false,
          isRefreshing: false,
        }));
      }
    },
    [childId]
  );

  // Initial data load
  useEffect(() => {
    if (childId) {
      loadChildData();
    }
  }, [childId, loadChildData]);

  // Refresh child data
  const refreshChildData = useCallback(async () => {
    await loadChildData(true);
  }, [loadChildData]);

  // Update child budget control
  const updateChildBudget = useCallback(
    async (budgetData: Partial<FamilyBudgetControl>) => {
      try {
        setState(prev => ({ ...prev, error: null }));

        let updatedBudgetControl: FamilyBudgetControl;

        if (state.childData.budgetControl) {
          // Update existing budget control
          updatedBudgetControl = await updateBudgetControl(
            state.childData.budgetControl.id.toString(),
            budgetData
          );
        } else {
          // Create new budget control
          updatedBudgetControl = await createBudgetControl({
            child_profile: parseInt(childId),
            requires_approval_above: '50.00', // Default approval threshold
            ...budgetData,
          });
        }

        setState(prev => ({
          ...prev,
          childData: {
            ...prev.childData,
            budgetControl: updatedBudgetControl,
          },
        }));
      } catch (error) {
        console.error('Error updating child budget:', error);
        setState(prev => ({
          ...prev,
          error: error instanceof Error ? error.message : 'Failed to update budget settings',
        }));
        throw error;
      }
    },
    [childId, state.childData.budgetControl]
  );

  // Load more transaction history
  const loadTransactionHistory = useCallback(
    async (page = 1) => {
      try {
        const additionalHistory = await getChildTransactionHistory(childId, {
          page,
          limit: 20,
        });

        setState(prev => ({
          ...prev,
          childData: {
            ...prev.childData,
            transactionHistory:
              page === 1
                ? additionalHistory.results || additionalHistory
                : [
                    ...prev.childData.transactionHistory,
                    ...(additionalHistory.results || additionalHistory),
                  ],
          },
        }));
      } catch (error) {
        console.error('Error loading transaction history:', error);
        setState(prev => ({
          ...prev,
          error: error instanceof Error ? error.message : 'Failed to load transaction history',
        }));
      }
    },
    [childId]
  );

  // Load more purchase history
  const loadPurchaseHistory = useCallback(
    async (page = 1) => {
      try {
        const additionalHistory = await getChildPurchaseHistory(childId, {
          page,
          limit: 20,
        });

        setState(prev => ({
          ...prev,
          childData: {
            ...prev.childData,
            purchaseHistory:
              page === 1
                ? additionalHistory.results || additionalHistory
                : [
                    ...prev.childData.purchaseHistory,
                    ...(additionalHistory.results || additionalHistory),
                  ],
          },
        }));
      } catch (error) {
        console.error('Error loading purchase history:', error);
        setState(prev => ({
          ...prev,
          error: error instanceof Error ? error.message : 'Failed to load purchase history',
        }));
      }
    },
    [childId]
  );

  const actions: UseChildAccountActions = {
    refreshChildData,
    updateChildBudget,
    loadTransactionHistory,
    loadPurchaseHistory,
  };

  return {
    ...state,
    actions,
  };
};
