/**
 * Purchase Page
 * 
 * Dedicated page for the purchase flow with clean URL routing.
 * Provides a focused experience for students to purchase tutoring hours.
 */

import useRouter from '@unitools/router';
import React from 'react';

import { SafeAreaView } from '@/components/ui/safe-area-view';
import { ScrollView } from '@/components/ui/scroll-view';
import { PurchaseFlow } from '@/components/purchase';

export default function PurchasePage() {
  const router = useRouter();

  const handlePurchaseComplete = (transactionId: number) => {
    console.log(`Purchase completed with transaction ID: ${transactionId}`);
    
    // Navigate to success page or dashboard after a brief delay
    setTimeout(() => {
      router.push('/dashboard');
    }, 3000);
  };

  const handleCancel = () => {
    router.push('/');
  };

  return (
    <SafeAreaView className="flex-1 bg-background-50">
      <ScrollView className="flex-1">
        <PurchaseFlow 
          onPurchaseComplete={handlePurchaseComplete}
          onCancel={handleCancel}
          className="px-4 py-6"
        />
      </ScrollView>
    </SafeAreaView>
  );
}