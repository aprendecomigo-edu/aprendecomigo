/**
 * Custom hook for managing quick action operations (renewal and top-up).
 * 
 * Provides state management for top-up packages, quick renewal,
 * and orchestrates the quick action flows.
 */

import { useState, useCallback, useEffect } from 'react';
import { PurchaseApiClient } from '@/api/purchaseApi';
import type { 
  TopUpPackage,
  QuickActionState,
  RenewalRequest,
  QuickTopUpRequest,
  RenewalResponse,
  QuickTopUpResponse,
  PackageInfo,
  PaymentMethod
} from '@/types/purchase';

interface UseQuickActionsResult {
  // Top-up packages
  topUpPackages: TopUpPackage[];
  packagesLoading: boolean;
  packagesError: string | null;
  
  // Quick action state
  actionState: QuickActionState;
  
  // Actions
  loadTopUpPackages: () => Promise<void>;
  setActionType: (actionType: 'renewal' | 'topup' | null) => void;
  selectPackage: (pkg: TopUpPackage) => void;
  selectPaymentMethod: (method: PaymentMethod) => void;
  processRenewal: (request: RenewalRequest) => Promise<RenewalResponse>;
  processQuickTopUp: (request: QuickTopUpRequest) => Promise<QuickTopUpResponse>;
  setError: (error: string | null) => void;
  resetState: () => void;
  
  // Computed values
  canRenew: (expiredPackage: PackageInfo | null, defaultPaymentMethod: PaymentMethod | null) => boolean;
  canTopUp: (selectedPackage: TopUpPackage | null, defaultPaymentMethod: PaymentMethod | null) => boolean;
}

/**
 * Hook for managing quick action operations.
 */
export function useQuickActions(email?: string): UseQuickActionsResult {
  // Top-up packages state
  const [topUpPackages, setTopUpPackages] = useState<TopUpPackage[]>([]);
  const [packagesLoading, setPackagesLoading] = useState(false);
  const [packagesError, setPackagesError] = useState<string | null>(null);

  // Quick action state
  const [actionState, setActionState] = useState<QuickActionState>({
    isVisible: false,
    actionType: null,
    isProcessing: false,
    error: null,
    selectedPackage: undefined,
    selectedPaymentMethod: undefined,
    confirmationStep: 'select',
  });

  // Load top-up packages
  const loadTopUpPackages = useCallback(async () => {
    setPackagesLoading(true);
    setPackagesError(null);

    try {
      const packages = await PurchaseApiClient.getTopUpPackages(email);
      setTopUpPackages(packages.sort((a, b) => a.display_order - b.display_order));
    } catch (error: any) {
      console.error('Error loading top-up packages:', error);
      setPackagesError(error.message || 'Failed to load top-up packages');
      setTopUpPackages([]);
    } finally {
      setPackagesLoading(false);
    }
  }, [email]);

  // Set action type
  const setActionType = useCallback((actionType: 'renewal' | 'topup' | null) => {
    setActionState(prev => ({
      ...prev,
      actionType,
      confirmationStep: 'select',
      error: null,
      selectedPackage: undefined,
      selectedPaymentMethod: undefined,
    }));
  }, []);

  // Select package for top-up
  const selectPackage = useCallback((pkg: TopUpPackage) => {
    setActionState(prev => ({
      ...prev,
      selectedPackage: pkg,
    }));
  }, []);

  // Select payment method
  const selectPaymentMethod = useCallback((method: PaymentMethod) => {
    setActionState(prev => ({
      ...prev,
      selectedPaymentMethod: method,
      confirmationStep: 'confirm',
    }));
  }, []);

  // Process renewal
  const processRenewal = useCallback(async (request: RenewalRequest): Promise<RenewalResponse> => {
    setActionState(prev => ({
      ...prev,
      isProcessing: true,
      error: null,
      confirmationStep: 'processing',
    }));

    try {
      const response = await PurchaseApiClient.renewSubscription(request, email);
      
      if (response.success) {
        setActionState(prev => ({
          ...prev,
          confirmationStep: 'success',
        }));
      } else {
        setActionState(prev => ({
          ...prev,
          error: response.message || 'Renewal failed',
          confirmationStep: 'error',
        }));
      }
      
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to process renewal';
      setActionState(prev => ({
        ...prev,
        error: errorMessage,
        confirmationStep: 'error',
      }));
      throw error;
    } finally {
      setActionState(prev => ({
        ...prev,
        isProcessing: false,
      }));
    }
  }, [email]);

  // Process quick top-up
  const processQuickTopUp = useCallback(async (request: QuickTopUpRequest): Promise<QuickTopUpResponse> => {
    setActionState(prev => ({
      ...prev,
      isProcessing: true,
      error: null,
      confirmationStep: 'processing',
    }));

    try {
      const response = await PurchaseApiClient.quickTopUp(request, email);
      
      if (response.success) {
        setActionState(prev => ({
          ...prev,
          confirmationStep: 'success',
        }));
      } else {
        setActionState(prev => ({
          ...prev,
          error: response.message || 'Top-up failed',
          confirmationStep: 'error',
        }));
      }
      
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to process top-up';
      setActionState(prev => ({
        ...prev,
        error: errorMessage,
        confirmationStep: 'error',
      }));
      throw error;
    } finally {
      setActionState(prev => ({
        ...prev,
        isProcessing: false,
      }));
    }
  }, [email]);

  // Set error
  const setError = useCallback((error: string | null) => {
    setActionState(prev => ({
      ...prev,
      error,
      confirmationStep: error ? 'error' : prev.confirmationStep,
    }));
  }, []);

  // Reset state
  const resetState = useCallback(() => {
    setActionState({
      isVisible: false,
      actionType: null,
      isProcessing: false,
      error: null,
      selectedPackage: undefined,
      selectedPaymentMethod: undefined,
      confirmationStep: 'select',
    });
  }, []);

  // Check if renewal is possible
  const canRenew = useCallback((
    expiredPackage: PackageInfo | null, 
    defaultPaymentMethod: PaymentMethod | null
  ): boolean => {
    return !!(
      expiredPackage && 
      defaultPaymentMethod && 
      !actionState.isProcessing
    );
  }, [actionState.isProcessing]);

  // Check if top-up is possible
  const canTopUp = useCallback((
    selectedPackage: TopUpPackage | null, 
    defaultPaymentMethod: PaymentMethod | null
  ): boolean => {
    return !!(
      selectedPackage && 
      defaultPaymentMethod && 
      !actionState.isProcessing
    );
  }, [actionState.isProcessing]);

  // Load top-up packages on mount
  useEffect(() => {
    loadTopUpPackages();
  }, [loadTopUpPackages]);

  return {
    topUpPackages,
    packagesLoading,
    packagesError,
    actionState,
    loadTopUpPackages,
    setActionType,
    selectPackage,
    selectPaymentMethod,
    processRenewal,
    processQuickTopUp,
    setError,
    resetState,
    canRenew,
    canTopUp,
  };
}