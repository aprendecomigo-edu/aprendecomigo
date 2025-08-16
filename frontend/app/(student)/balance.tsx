import { useRouter } from 'expo-router';
import { RefreshCw, Plus, BarChart3 } from 'lucide-react-native';
import React from 'react';

import { StudentBalanceCard } from '@/components/purchase';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

export default function StudentBalancePage() {
  const router = useRouter();

  const handlePurchaseMore = () => {
    router.push('/purchase');
  };

  const handleScheduleSession = () => {
    router.push('/calendar');
  };

  const handleViewDashboard = () => {
    router.push('/(student)/dashboard');
  };

  return (
    <SafeAreaView className="flex-1 bg-background-50">
      <ScrollView className="flex-1">
        <VStack className="flex-1 px-6 py-8 max-w-4xl mx-auto w-full" space="lg">
          {/* Header */}
          <VStack space="sm">
            <Heading size="3xl" className="text-typography-900">
              Your Balance
            </Heading>
            <Text className="text-lg text-typography-600">
              Manage your tutoring hours and track your progress
            </Text>
          </VStack>

          {/* Balance Card */}
          <StudentBalanceCard />

          {/* Quick Actions */}
          <VStack space="md">
            <Heading size="lg" className="text-typography-900">
              Quick Actions
            </Heading>

            <HStack space="md" className="flex-wrap">
              <Button
                action="primary"
                variant="solid"
                size="lg"
                onPress={handleScheduleSession}
                className="flex-1 min-w-40"
              >
                <ButtonIcon as={RefreshCw} />
                <ButtonText>Schedule Session</ButtonText>
              </Button>

              <Button
                action="secondary"
                variant="outline"
                size="lg"
                onPress={handlePurchaseMore}
                className="flex-1 min-w-40"
              >
                <ButtonIcon as={Plus} />
                <ButtonText>Purchase More Hours</ButtonText>
              </Button>

              <Button
                action="secondary"
                variant="solid"
                size="lg"
                onPress={handleViewDashboard}
                className="flex-1 min-w-40"
              >
                <ButtonIcon as={BarChart3} />
                <ButtonText>Full Dashboard</ButtonText>
              </Button>
            </HStack>
          </VStack>
        </VStack>
      </ScrollView>
    </SafeAreaView>
  );
}
