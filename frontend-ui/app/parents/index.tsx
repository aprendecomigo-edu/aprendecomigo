import Link from '@unitools/link';
import { CreditCard, Clock, Users, CheckCircle2 } from 'lucide-react-native';
import React from 'react';

import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { LinkText } from '@/components/ui/link';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

export default function LandingPage() {
  const handleStripeCheckout = (productType: 'subscription' | 'package') => {
    // TODO: Implement Stripe Checkout integration
    // This will be implemented as part of the Stripe integration
    console.log(`Selected product: ${productType}`);
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
            <Text size="lg" className="text-center text-typography-600 max-w-80">
              Premium tutoring hours for quality education
            </Text>
          </VStack>

          {/* Product Cards */}
          <VStack space="lg" className="mt-8">
            {/* Monthly Subscription */}
            <Card className="p-6 border-outline-200">
              <VStack space="md">
                <HStack space="sm" className="items-center">
                  <Icon as={Clock} size="lg" className="text-primary-600" />
                  <Heading size="lg" className="text-typography-900">
                    Monthly Subscription
                  </Heading>
                </HStack>

                <Text className="text-typography-600">5 hours per month of premium tutoring</Text>

                <VStack space="xs" className="mt-2">
                  <HStack space="xs" className="items-center">
                    <Icon as={CheckCircle2} size="sm" className="text-success-600" />
                    <Text size="sm" className="text-typography-600">
                      Recurring monthly access
                    </Text>
                  </HStack>
                  <HStack space="xs" className="items-center">
                    <Icon as={CheckCircle2} size="sm" className="text-success-600" />
                    <Text size="sm" className="text-typography-600">
                      Best value for regular learners
                    </Text>
                  </HStack>
                  <HStack space="xs" className="items-center">
                    <Icon as={CheckCircle2} size="sm" className="text-success-600" />
                    <Text size="sm" className="text-typography-600">
                      Cancel anytime
                    </Text>
                  </HStack>
                </VStack>

                <Button
                  action="primary"
                  variant="solid"
                  size="lg"
                  className="mt-4"
                  onPress={() => handleStripeCheckout('subscription')}
                >
                  <ButtonIcon as={CreditCard} />
                  <ButtonText>Choose Monthly Plan</ButtonText>
                </Button>
              </VStack>
            </Card>

            {/* One-time Package */}
            <Card className="p-6 border-outline-200">
              <VStack space="md">
                <HStack space="sm" className="items-center">
                  <Icon as={Users} size="lg" className="text-secondary-600" />
                  <Heading size="lg" className="text-typography-900">
                    One-time Package
                  </Heading>
                </HStack>

                <Text className="text-typography-600">10 hours usable within 3 months</Text>

                <VStack space="xs" className="mt-2">
                  <HStack space="xs" className="items-center">
                    <Icon as={CheckCircle2} size="sm" className="text-success-600" />
                    <Text size="sm" className="text-typography-600">
                      Flexible scheduling
                    </Text>
                  </HStack>
                  <HStack space="xs" className="items-center">
                    <Icon as={CheckCircle2} size="sm" className="text-success-600" />
                    <Text size="sm" className="text-typography-600">
                      No recurring charges
                    </Text>
                  </HStack>
                  <HStack space="xs" className="items-center">
                    <Icon as={CheckCircle2} size="sm" className="text-success-600" />
                    <Text size="sm" className="text-typography-600">
                      3-month validity
                    </Text>
                  </HStack>
                </VStack>

                <Button
                  action="secondary"
                  variant="solid"
                  size="lg"
                  className="mt-4"
                  onPress={() => handleStripeCheckout('package')}
                >
                  <ButtonIcon as={CreditCard} />
                  <ButtonText>Buy One-time Package</ButtonText>
                </Button>
              </VStack>
            </Card>
          </VStack>

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
