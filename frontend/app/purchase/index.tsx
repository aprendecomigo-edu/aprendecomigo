/**
 * Purchase Page
 *
 * Dedicated page for the purchase flow with clean URL routing.
 * Provides a focused experience for students to purchase tutoring hours.
 */

import useRouter from '@unitools/router';
import React, { lazy, Suspense } from 'react';

import LoadingScreen from '@/components/ui/loading-screen';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { ScrollView } from '@/components/ui/scroll-view';
import { useToast } from '@/components/ui/toast';

// Lazy load the PurchaseFlow component
const PurchaseFlow = lazy(() => import('@/components/purchase').then(module => ({ default: module.PurchaseFlow })));

export default function PurchasePage() {
  const router = useRouter();
  const { showToast } = useToast();

  const handlePurchaseComplete = (transactionId: number) => {
    showToast(
      'success',
      `Payment successful! Transaction ID: ${transactionId}. Redirecting to your dashboard...`,
      6000
    );

    // Navigate to success page or dashboard after a brief delay
    setTimeout(() => {
      router.push('/home');
    }, 3000);
  };

  const handleCancel = () => {
    router.push('/');
  };

  return (
    <SafeAreaView className="flex-1 bg-background-50">
      <ScrollView className="flex-1">
        <Suspense fallback={<LoadingScreen message="Loading purchase flow..." />}>
          <PurchaseFlow
            onPurchaseComplete={handlePurchaseComplete}
            onCancel={handleCancel}
            className="px-4 py-6"
          />
        </Suspense>
      </ScrollView>
    </SafeAreaView>
  );
}
