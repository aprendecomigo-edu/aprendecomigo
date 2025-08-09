import React from 'react';

import MainLayout from '@/components/layouts/MainLayout';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface WelcomeScreenProps {
  onGetStarted?: () => void;
  onSkip?: () => void;
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onGetStarted, onSkip }) => {
  return (
    <MainLayout _title="Welcome">
      <Box className="flex-1">
        <VStack className="p-6 flex-1 justify-center" space="lg">
          <VStack space="md" className="items-center">
            <Heading size="3xl" className="text-center text-gray-900">
              Welcome to Aprende Comigo!
            </Heading>
            <Text className="text-center text-gray-600 text-lg">
              Transform how your school manages tutoring sessions, teacher coordination, and student
              success.
            </Text>
          </VStack>

          <VStack space="md" className="mt-8">
            <Button size="lg" onPress={onGetStarted} className="w-full">
              <ButtonText>Get Started</ButtonText>
            </Button>

            <Button variant="outline" size="lg" onPress={onSkip} className="w-full">
              <ButtonText>Skip for Now</ButtonText>
            </Button>
          </VStack>
        </VStack>
      </Box>
    </MainLayout>
  );
};
