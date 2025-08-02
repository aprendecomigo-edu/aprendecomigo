import { useLocalSearchParams } from 'expo-router';
import React from 'react';

import MainLayout from '@/components/layouts/main-layout';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

const AcceptInvitationMinimal = () => {
  const { token } = useLocalSearchParams<{ token: string }>();

  return (
    <MainLayout>
      <VStack space="md" className="p-6">
        <Text>Minimal Invitation Test</Text>
        <Text>Token: {token}</Text>
        <Text>If you can see this, the basic page structure works.</Text>
      </VStack>
    </MainLayout>
  );
};

export default AcceptInvitationMinimal;
