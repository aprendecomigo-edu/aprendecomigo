/**
 * Custom hook for fetching and managing pricing plans.
 *
 * Provides reactive access to pricing plan data with loading states,
 * error handling, and automatic retries.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';

import { PurchaseApiClient } from '@/api/purchaseApi';
import type { PricingPlan, UsePricingPlansResult } from '@/types/purchase';

/**
 * Hook for fetching and managing pricing plans data.
 *
 * @returns Object containing plans data, loading state, error info, and refetch function
 */
export function usePricingPlans(): UsePricingPlansResult {
  const [plans, setPlans] = useState<PricingPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPlans = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const startTime = performance.now();
      const plansData = await PurchaseApiClient.getPricingPlans();
      const fetchTime = performance.now() - startTime;

      // Log performance in development
      if (__DEV__) {
        console.log(`Pricing plans fetched in ${fetchTime.toFixed(2)}ms`);
      }

      // Sort plans by display_order, then by price
      const sortedPlans = plansData.sort((a, b) => {
        // First sort by display_order
        if (a.display_order !== b.display_order) {
          return a.display_order - b.display_order;
        }

        // Then sort by price (ascending)
        const priceA = parseFloat(a.price_eur);
        const priceB = parseFloat(b.price_eur);
        return priceA - priceB;
      });

      setPlans(sortedPlans);
    } catch (error: any) {
      console.error('Error fetching pricing plans:', error);
      setError(error.message || 'Failed to load pricing plans');
    } finally {
      setLoading(false);
    }
  }, []);

  const refetch = useCallback(async () => {
    await fetchPlans();
  }, [fetchPlans]);

  // Initial fetch on mount
  useEffect(() => {
    fetchPlans();
  }, [fetchPlans]);

  return {
    plans,
    loading,
    error,
    refetch,
  };
}
