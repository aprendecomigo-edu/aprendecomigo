/**
 * FamilyOverview Component
 * 
 * Comprehensive family-wide view showing aggregate metrics,
 * spending summaries, and overall family account status.
 */

import React from 'react';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { Heading } from '@/components/ui/heading';

export const FamilyOverview: React.FC = () => {
  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <VStack className="flex-1 justify-center items-center p-6">
        <Heading size="xl" className="text-gray-900 mb-4">
          Family Overview
        </Heading>
        <Text className="text-gray-600 text-center">
          Comprehensive family dashboard coming soon.
        </Text>
      </VStack>
    </SafeAreaView>
  );
};