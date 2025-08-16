import React, { lazy, Suspense } from 'react';

import LoadingScreen from '@/components/ui/loading-screen';

// Lazy load the PurchaseFlow component
const PurchaseFlow = lazy(() => import('./PurchaseFlow'));

interface LazyPurchaseFlowProps {
  onPurchaseComplete: (transactionId: number) => void;
  onCancel: () => void;
  className?: string;
}

/**
 * Lazy-loaded wrapper for PurchaseFlow component
 * Reduces initial bundle size by loading payment components only when needed
 */
export function LazyPurchaseFlow(props: LazyPurchaseFlowProps) {
  return (
    <Suspense fallback={<LoadingScreen message="Loading payment system..." />}>
      <PurchaseFlow {...props} />
    </Suspense>
  );
}

export default LazyPurchaseFlow;
