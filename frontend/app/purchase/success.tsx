/**
 * Purchase Success Page
 *
 * Thank you page shown after successful purchase completion.
 * Provides confirmation details and next steps for students.
 */

import { useRouter } from 'expo-router';
import { CheckCircle, Calendar, BookOpen, ArrowRight } from 'lucide-react-native';
import React, { useEffect } from 'react';

import { StudentBalanceCard } from '@/components/purchase';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

export default function PurchaseSuccessPage() {
  const router = useRouter();

  // Auto-redirect after 30 seconds if user doesn't take action
  useEffect(() => {
    const timer = setTimeout(() => {
      router.push('/home');
    }, 30000);

    return () => clearTimeout(timer);
  }, [router]);

  const handleViewDashboard = () => {
    router.push('/home');
  };

  const handleScheduleSession = () => {
    router.push('/calendar');
  };

  const handleViewBalance = () => {
    router.push('/student');
  };

  return (
    <SafeAreaView className="flex-1 bg-background-50">
      <ScrollView className="flex-1">
        <VStack className="flex-1 px-6 py-8 max-w-4xl mx-auto w-full" space="xl">
          {/* Success Header */}
          <Card className="p-8 bg-success-50 border border-success-200">
            <VStack space="lg" className="items-center text-center">
              <Icon as={CheckCircle} size="xl" className="text-success-600" />

              <VStack space="sm" className="items-center">
                <Heading size="3xl" className="text-success-900">
                  Purchase Successful!
                </Heading>
                <Text className="text-lg text-success-800 max-w-2xl">
                  Thank you for choosing Aprende Comigo! Your tutoring hours have been added to your
                  account and are ready to use.
                </Text>
              </VStack>
            </VStack>
          </Card>

          {/* Next Steps */}
          <VStack space="lg">
            <Heading size="xl" className="text-typography-900 text-center">
              What's Next?
            </Heading>

            <VStack space="md">
              {/* Schedule Session Card */}
              <Card className="p-6 hover:shadow-lg transition-shadow">
                <HStack space="md" className="items-center">
                  <Icon as={Calendar} size="xl" className="text-primary-600" />
                  <VStack space="sm" className="flex-1">
                    <Heading size="md" className="text-typography-900">
                      Schedule Your First Session
                    </Heading>
                    <Text className="text-typography-600">
                      Browse available tutors and book your first tutoring session.
                    </Text>
                  </VStack>
                  <Button action="primary" variant="solid" onPress={handleScheduleSession}>
                    <ButtonIcon as={ArrowRight} />
                    <ButtonText>Schedule</ButtonText>
                  </Button>
                </HStack>
              </Card>

              {/* View Balance Card */}
              <Card className="p-6 hover:shadow-lg transition-shadow">
                <HStack space="md" className="items-center">
                  <Icon as={BookOpen} size="xl" className="text-secondary-600" />
                  <VStack space="sm" className="flex-1">
                    <Heading size="md" className="text-typography-900">
                      View Your Balance
                    </Heading>
                    <Text className="text-typography-600">
                      Check your available hours and track your learning progress.
                    </Text>
                  </VStack>
                  <Button action="secondary" variant="outline" onPress={handleViewBalance}>
                    <ButtonIcon as={ArrowRight} />
                    <ButtonText>View Balance</ButtonText>
                  </Button>
                </HStack>
              </Card>
            </VStack>
          </VStack>

          {/* Student Balance Display */}
          <VStack space="md">
            <Heading size="lg" className="text-typography-900">
              Your Account Balance
            </Heading>
            <StudentBalanceCard showStudentInfo={false} />
          </VStack>

          {/* Dashboard Button */}
          <VStack space="sm" className="items-center">
            <Button
              action="primary"
              variant="solid"
              size="lg"
              onPress={handleViewDashboard}
              className="w-full max-w-md"
            >
              <ButtonText>Go to Dashboard</ButtonText>
            </Button>

            <Text className="text-sm text-typography-500 text-center">
              You'll be automatically redirected to your dashboard in a few moments.
            </Text>
          </VStack>

          {/* Help Information */}
          <Card className="p-6 bg-info-50 border border-info-200">
            <VStack space="sm">
              <Heading size="md" className="text-info-900">
                Need Help Getting Started?
              </Heading>
              <Text className="text-info-800">
                Check your email for a welcome message with detailed instructions on how to make the
                most of your tutoring hours. Our support team is also available if you have any
                questions.
              </Text>
            </VStack>
          </Card>
        </VStack>
      </ScrollView>
    </SafeAreaView>
  );
}
