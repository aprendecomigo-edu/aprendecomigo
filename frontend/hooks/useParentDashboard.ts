/**
 * Parent Dashboard Hook
 *
 * Custom hook for managing parent dashboard state including
 * child accounts, family metrics, and purchase approvals.
 */

import { useState, useEffect, useCallback } from 'react';

import {
  getParentApprovalDashboard,
  getFamilyMetrics,
  getChildrenProfiles,
  ParentApprovalDashboard,
  FamilyMetrics,
  ChildProfile,
  PurchaseApprovalRequest,
  approvePurchaseRequest,
  rejectPurchaseRequest,
} from '@/api/parentApi';

interface UseParentDashboardState {
  dashboardData: ParentApprovalDashboard | null;
  familyMetrics: FamilyMetrics | null;
  children: ChildProfile[];
  selectedChildId: string | null;
  isLoading: boolean;
  error: string | null;
  isRefreshing: boolean;
}

interface UseParentDashboardActions {
  refreshDashboard: () => Promise<void>;
  selectChild: (childId: string | null) => void;
  approvePurchase: (requestId: string, notes?: string) => Promise<void>;
  rejectPurchase: (requestId: string, notes?: string) => Promise<void>;
  setTimeframe: (timeframe: 'week' | 'month' | 'quarter') => void;
}

export const useParentDashboard = () => {
  const [state, setState] = useState<UseParentDashboardState>({
    dashboardData: null,
    familyMetrics: null,
    children: [],
    selectedChildId: null,
    isLoading: true,
    error: null,
    isRefreshing: false,
  });

  const [timeframe, setTimeframe] = useState<'week' | 'month' | 'quarter'>('month');

  // Load dashboard data
  const loadDashboardData = useCallback(
    async (isRefresh = false) => {
      try {
        setState(prev => ({
          ...prev,
          isLoading: !isRefresh,
          isRefreshing: isRefresh,
          error: null,
        }));

        // Load all data in parallel
        const [dashboardData, familyMetrics, children] = await Promise.all([
          getParentApprovalDashboard(),
          getFamilyMetrics(timeframe),
          getChildrenProfiles(),
        ]);

        setState(prev => ({
          ...prev,
          dashboardData,
          familyMetrics,
          children,
          isLoading: false,
          isRefreshing: false,
        }));
      } catch (error) {
        console.error('Error loading parent dashboard data:', error);
        setState(prev => ({
          ...prev,
          error: error instanceof Error ? error.message : 'Failed to load dashboard data',
          isLoading: false,
          isRefreshing: false,
        }));
      }
    },
    [timeframe]
  );

  // Initial data load
  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Refresh dashboard
  const refreshDashboard = useCallback(async () => {
    await loadDashboardData(true);
  }, [loadDashboardData]);

  // Select child account
  const selectChild = useCallback((childId: string | null) => {
    setState(prev => ({ ...prev, selectedChildId: childId }));
  }, []);

  // Approve purchase request
  const approvePurchase = useCallback(
    async (requestId: string, notes?: string) => {
      try {
        setState(prev => ({ ...prev, error: null }));

        const updatedRequest = await approvePurchaseRequest(requestId, notes);

        // Update local state
        setState(prev => ({
          ...prev,
          dashboardData: prev.dashboardData
            ? {
                ...prev.dashboardData,
                pending_requests: prev.dashboardData.pending_requests.filter(
                  req => req.id !== parseInt(requestId)
                ),
                recent_approvals: [updatedRequest, ...prev.dashboardData.recent_approvals].slice(
                  0,
                  10
                ),
              }
            : null,
        }));

        // Refresh metrics to get updated data
        const updatedMetrics = await getFamilyMetrics(timeframe);
        setState(prev => ({ ...prev, familyMetrics: updatedMetrics }));
      } catch (error) {
        console.error('Error approving purchase:', error);
        setState(prev => ({
          ...prev,
          error: error instanceof Error ? error.message : 'Failed to approve purchase',
        }));
        throw error;
      }
    },
    [timeframe]
  );

  // Reject purchase request
  const rejectPurchase = useCallback(async (requestId: string, notes?: string) => {
    try {
      setState(prev => ({ ...prev, error: null }));

      const updatedRequest = await rejectPurchaseRequest(requestId, notes);

      // Update local state
      setState(prev => ({
        ...prev,
        dashboardData: prev.dashboardData
          ? {
              ...prev.dashboardData,
              pending_requests: prev.dashboardData.pending_requests.filter(
                req => req.id !== parseInt(requestId)
              ),
              recent_approvals: [updatedRequest, ...prev.dashboardData.recent_approvals].slice(
                0,
                10
              ),
            }
          : null,
      }));
    } catch (error) {
      console.error('Error rejecting purchase:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to reject purchase',
      }));
      throw error;
    }
  }, []);

  // Set timeframe and reload metrics
  const setTimeframeAndReload = useCallback((newTimeframe: 'week' | 'month' | 'quarter') => {
    setTimeframe(newTimeframe);
  }, []);

  const actions: UseParentDashboardActions = {
    refreshDashboard,
    selectChild,
    approvePurchase,
    rejectPurchase,
    setTimeframe: setTimeframeAndReload,
  };

  // Derived state
  const selectedChild =
    state.children.find(child => child.id.toString() === state.selectedChildId) || null;
  const pendingApprovals = state.dashboardData?.pending_requests || [];
  const recentApprovals = state.dashboardData?.recent_approvals || [];

  return {
    ...state,
    selectedChild,
    pendingApprovals,
    recentApprovals,
    timeframe,
    actions,
  };
};
