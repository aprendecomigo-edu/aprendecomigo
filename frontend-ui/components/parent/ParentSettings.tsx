/**
 * ParentSettings Component
 * 
 * Parent account settings including notification preferences,
 * family budget controls, and account management options.
 */

import React from 'react';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { Heading } from '@/components/ui/heading';

export const ParentSettings: React.FC = () => {
  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <VStack className="flex-1 justify-center items-center p-6">
        <Heading size="xl" className="text-gray-900 mb-4">
          Parent Settings
        </Heading>
        <Text className="text-gray-600 text-center">
          Parent settings panel coming soon.
        </Text>
      </VStack>
    </SafeAreaView>
  );
};