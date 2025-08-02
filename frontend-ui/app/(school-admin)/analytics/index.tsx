import React from 'react';

import { Box } from '@/components/ui/box';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

export default function SchoolAnalyticsPage() {
  return (
    <Box className="flex-1 p-6">
      <VStack space="lg">
        <Text className="text-2xl font-bold text-typography-900">
          School Analytics
        </Text>
        
        <Box className="bg-background-50 p-4 rounded-lg">
          <Text className="text-lg text-typography-700">
            Analytics dashboard coming soon...
          </Text>
          <Text className="text-sm text-typography-500 mt-2">
            This page will display comprehensive analytics for your school including:
          </Text>
          <VStack space="xs" className="mt-3 ml-4">
            <Text className="text-sm text-typography-600">• Student performance metrics</Text>
            <Text className="text-sm text-typography-600">• Teacher activity statistics</Text>
            <Text className="text-sm text-typography-600">• Revenue and payment analytics</Text>
            <Text className="text-sm text-typography-600">• Usage trends and insights</Text>
          </VStack>
        </Box>
      </VStack>
    </Box>
  );
}