import { useLocalSearchParams } from 'expo-router';
import React from 'react';

import MainLayout from '@/components/layouts/MainLayout';
import { Box } from '@/components/ui/box';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

export default function ChatRoomScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();

  return (
    <MainLayout _title="Chat">
      <Box className="flex-1">
        <VStack className="p-6" space="md">
          <Text className="text-xl font-bold text-gray-900">Chat Room {id}</Text>
          <Text className="text-gray-600">Sistema de chat em tempo real disponível em breve.</Text>
        </VStack>
      </Box>
    </MainLayout>
  );
}
