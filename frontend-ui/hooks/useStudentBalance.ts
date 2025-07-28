/**
 * Custom hook for fetching and managing student balance information.
 * 
 * Provides reactive access to student balance data including hours,
 * package status, and expiration information.
 */

import { useState, useEffect, useCallback } from 'react';
import { PurchaseApiClient } from '@/api/purchaseApi';
import type { StudentBalanceResponse, UseStudentBalanceResult } from '@/types/purchase';

/**
 * Hook for fetching and managing student balance data.
 * 
 * @param email Optional email parameter for admin access to other students' data
 * @returns Object containing balance data, loading state, error info, and refetch function
 */
export function useStudentBalance(email?: string): UseStudentBalanceResult {
  const [balance, setBalance] = useState<StudentBalanceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBalance = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const balanceData = await PurchaseApiClient.getStudentBalance(email);
      setBalance(balanceData);
    } catch (error: any) {
      console.error('Error fetching student balance:', error);
      setError(error.message || 'Failed to load balance information');
      setBalance(null);
    } finally {
      setLoading(false);
    }
  }, [email]);

  const refetch = useCallback(async () => {
    await fetchBalance();
  }, [fetchBalance]);

  // Initial fetch on mount or when email changes
  useEffect(() => {
    fetchBalance();
  }, [fetchBalance]);

  return {
    balance,
    loading,
    error,
    refetch,
  };
}