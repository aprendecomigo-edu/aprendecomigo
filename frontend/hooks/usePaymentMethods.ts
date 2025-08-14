/**
 * Custom hook for managing payment method data and operations.
 *
 * Provides state management for payment method listing, adding, removing,
 * and setting default payment methods.
 */

import { useState, useCallback, useEffect } from 'react';

import {
  PaymentMethodApiClient,
  type PaymentMethod,
  type AddPaymentMethodRequest,
  type AddPaymentMethodResponse,
} from '@/api/paymentMethodApi';

interface UsePaymentMethodsResult {
  // Data state
  paymentMethods: PaymentMethod[];
  loading: boolean;
  error: string | null;

  // Operation states
  adding: boolean;
  removing: boolean;
  settingDefault: boolean;
  operationError: string | null;

  // Actions
  refreshPaymentMethods: () => Promise<void>;
  addPaymentMethod: (request: AddPaymentMethodRequest) => Promise<AddPaymentMethodResponse | null>;
  removePaymentMethod: (paymentMethodId: string) => Promise<void>;
  setDefaultPaymentMethod: (paymentMethodId: string) => Promise<void>;
  clearErrors: () => void;

  // Computed values
  defaultPaymentMethod: PaymentMethod | null;
  hasPaymentMethods: boolean;
}

/**
 * Hook for managing payment method data and operations.
 */
export function usePaymentMethods(email?: string): UsePaymentMethodsResult {
  // Payment method data state
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Operation states
  const [adding, setAdding] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [settingDefault, setSettingDefault] = useState(false);
  const [operationError, setOperationError] = useState<string | null>(null);

  // Refresh payment methods data
  const refreshPaymentMethods = useCallback(async () => {
    if (!email) {
      setLoading(false);
      setPaymentMethods([]);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const methodsData = await PaymentMethodApiClient.getPaymentMethods(email);
      setPaymentMethods(Array.isArray(methodsData) ? methodsData : []);
    } catch (error: any) {
      console.error('Error fetching payment methods:', error);
      setError(error.message || 'Failed to load payment methods');
      setPaymentMethods([]);
    } finally {
      setLoading(false);
    }
  }, [email]);

  // Add new payment method
  const addPaymentMethod = useCallback(
    async (request: AddPaymentMethodRequest): Promise<AddPaymentMethodResponse | null> => {
      setAdding(true);
      setOperationError(null);

      try {
        const result = await PaymentMethodApiClient.addPaymentMethod(request, email);

        // Refresh payment methods to get the updated list
        await refreshPaymentMethods();

        return result;
      } catch (error: any) {
        console.error('Error adding payment method:', error);
        setOperationError(error.message || 'Failed to add payment method');
        return null;
      } finally {
        setAdding(false);
      }
    },
    [email, refreshPaymentMethods]
  );

  // Remove payment method
  const removePaymentMethod = useCallback(
    async (paymentMethodId: string): Promise<void> => {
      if (!email) {
        setOperationError('Email is required');
        return;
      }

      setRemoving(true);
      setOperationError(null);

      try {
        const result = await PaymentMethodApiClient.removePaymentMethod(paymentMethodId, email);

        // Handle API responses that return success/failure objects
        if (result && typeof result === 'object' && 'success' in result && !result.success) {
          const errorMessage = (result as any).message || 'Failed to remove payment method';
          setOperationError(errorMessage);
          throw new Error(errorMessage);
        }

        // Refresh payment methods to get the updated list
        await refreshPaymentMethods();
      } catch (error: any) {
        console.error('Error removing payment method:', error);
        setOperationError(error.message || 'Failed to remove payment method');
        throw error; // Re-throw to allow component to handle
      } finally {
        setRemoving(false);
      }
    },
    [email, refreshPaymentMethods]
  );

  // Set default payment method
  const setDefaultPaymentMethod = useCallback(
    async (paymentMethodId: string): Promise<void> => {
      if (!email) {
        setOperationError('Email is required');
        return;
      }

      setSettingDefault(true);
      setOperationError(null);

      try {
        const result = await PaymentMethodApiClient.setDefaultPaymentMethod(paymentMethodId, email);

        // Handle API responses that return success/failure objects
        if (result && typeof result === 'object' && 'success' in result && !result.success) {
          const errorMessage = (result as any).message || 'Failed to set default payment method';
          setOperationError(errorMessage);
          throw new Error(errorMessage);
        }

        // Refresh payment methods to get the updated default status
        await refreshPaymentMethods();
      } catch (error: any) {
        console.error('Error setting default payment method:', error);
        setOperationError(error.message || 'Failed to set default payment method');
        throw error; // Re-throw to allow component to handle
      } finally {
        setSettingDefault(false);
      }
    },
    [email, refreshPaymentMethods]
  );

  // Clear all errors
  const clearErrors = useCallback(() => {
    setError(null);
    setOperationError(null);
  }, []);

  // Computed values
  const defaultPaymentMethod = paymentMethods.find(method => method.is_default) || null;
  const hasPaymentMethods = paymentMethods.length > 0;

  // Initial data fetch
  useEffect(() => {
    refreshPaymentMethods();
  }, [refreshPaymentMethods]);

  return {
    paymentMethods,
    loading,
    error,
    adding,
    removing,
    settingDefault,
    operationError,
    refreshPaymentMethods,
    addPaymentMethod,
    removePaymentMethod,
    setDefaultPaymentMethod,
    clearErrors,
    defaultPaymentMethod,
    hasPaymentMethods,
  };
}
