/**
 * Webhook Monitoring Screen - GitHub Issue #117
 *
 * Administrative interface for monitoring webhook health, viewing event logs,
 * and managing webhook configurations.
 */

import React from 'react';

import { Box } from '@/components/ui/box';
import { Heading } from '@/components/ui/heading';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

export default function WebhookMonitoring() {
  return (
    <VStack flex={1} className="p-6">
      <Heading size="xl" className="text-typography-900 mb-4">
        Webhook Monitoring
      </Heading>
      <Box className="p-6 bg-background-50 rounded-lg border border-border-200">
        <Text className="text-typography-600">Webhook monitoring interface coming soon...</Text>
      </Box>
    </VStack>
  );
}
