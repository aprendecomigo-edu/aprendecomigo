import Link from '@unitools/link';
import React from 'react';

import { PurchaseFlow } from '@/components/purchase';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { LinkText } from '@/components/ui/link';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { useToast } from '@/components/ui/toast';
import { VStack } from '@/components/ui/vstack';

export default function LandingPage() {
  const { showToast } = useToast();

  const handlePurchaseComplete = (transactionId: number) => {
    showToast(
      'success',
      `Payment successful! Transaction ID: ${transactionId}. You can now access your tutoring hours.`,
      6000
    );
  };

  return (
    <SafeAreaView className="flex-1 bg-background-50">
      <ScrollView className="flex-1">
        <VStack className="flex-1 px-6 py-8" space="xl">
          {/* Header */}
          <VStack space="md" className="items-center">
            <Heading size="3xl" className="text-center text-typography-900">
              Aprende Comigo
            </Heading>
            <Text className="text-lg text-center text-typography-600 max-w-80">
              Premium tutoring hours for quality education
            </Text>
          </VStack>

          {/* Purchase Flow */}
          <PurchaseFlow onPurchaseComplete={handlePurchaseComplete} className="mt-8" />

          {/* Authentication Links */}
          <VStack space="md" className="items-center mt-8">
            <Text className="text-typography-600 text-center">
              Already have an account or want to create one?
            </Text>
            <HStack space="md" className="items-center">
              <Link href="/auth/signin">
                <LinkText className="text-primary-600 font-semibold">Sign In</LinkText>
              </Link>
              <Text className="text-typography-400">•</Text>
              <Link href="/auth/signup">
                <LinkText className="text-primary-600 font-semibold">Sign Up</LinkText>
              </Link>
            </HStack>
          </VStack>
        </VStack>
      </ScrollView>
    </SafeAreaView>
  );
}
