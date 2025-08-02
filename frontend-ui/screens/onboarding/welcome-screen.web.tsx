import React from 'react';

import {
  AlertDialog,
  AlertDialogBackdrop,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogCloseButton,
  AlertDialogFooter,
  AlertDialogBody,
} from '@/components/ui/alert-dialog';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

import {
  WelcomeScreenProps,
  useWelcomeScreen,
  platformCapabilities,
  WelcomeScreenIcons,
} from './welcome-screen-common';

const { CheckCircle, ArrowRight, SkipForward } = WelcomeScreenIcons;

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onGetStarted, onSkip }) => {
  const {
    userProfile,
    isLoading,
    showSkipDialog,
    setShowSkipDialog,
    isSkipping,
    handleGetStarted,
    handleSkipConfirm,
  } = useWelcomeScreen({ onGetStarted, onSkip });

  if (isLoading) {
    return (
      <Center className="flex-1 bg-white">
        <VStack space="md" className="items-center">
          <Spinner size="large" />
          <Text className="text-gray-600">Loading welcome screen...</Text>
        </VStack>
      </Center>
    );
  }

  return (
    <Box className="flex-1 bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header Section - Desktop optimized */}
      <Box className="px-8 pt-16 pb-8">
        <Center>
          <VStack space="lg" className="items-center max-w-3xl">
            {/* Welcome Icon/Logo */}
            <Box className="bg-white rounded-full p-8 shadow-lg">
              <Icon as={CheckCircle} size={64} className="text-green-500" />
            </Box>

            {/* Personalized Greeting */}
            <VStack space="sm" className="items-center">
              <Heading size="4xl" className="text-center text-gray-900 font-bold">
                Welcome to Aprende Comigo!
              </Heading>
              {userProfile?.name && (
                <Text size="xl" className="text-center text-gray-700">
                  Hello, {userProfile.name} 👋
                </Text>
              )}
            </VStack>

            {/* Welcome Message */}
            <Text size="lg" className="text-center text-gray-600 leading-relaxed max-w-2xl">
              Thank you for joining our educational platform! You're now ready to transform how your
              school manages tutoring sessions, teacher coordination, and student success.
            </Text>
          </VStack>
        </Center>
      </Box>

      {/* Platform Capabilities Section - Desktop layout */}
      <Box className="px-8 pb-8">
        <VStack space="lg">
          <Heading size="2xl" className="text-center text-gray-800 mb-6">
            What you can accomplish:
          </Heading>

          {/* Grid layout for desktop */}
          <HStack space="lg" className="justify-center">
            {platformCapabilities.map((capability, index) => (
              <Card key={index} className="bg-white border-0 shadow-sm max-w-sm flex-1">
                <VStack space="md" className="items-center p-6 text-center">
                  <Box className="bg-blue-100 rounded-xl p-4">
                    <Icon as={capability.icon} size={32} className="text-blue-600" />
                  </Box>
                  <VStack space="xs" className="items-center">
                    <Text size="lg" className="font-semibold text-gray-900">
                      {capability.title}
                    </Text>
                    <Text size="md" className="text-gray-600 text-center">
                      {capability.description}
                    </Text>
                  </VStack>
                </VStack>
              </Card>
            ))}
          </HStack>
        </VStack>
      </Box>

      {/* Action Buttons - Desktop layout */}
      <Box className="px-8 pb-8 mt-auto">
        <Center>
          <VStack space="lg" className="max-w-lg">
            <HStack space="md" className="w-full">
              <Button
                size="lg"
                onPress={handleGetStarted}
                className="bg-blue-600 hover:bg-blue-700 flex-1"
                testID="get-started-button"
              >
                <ButtonText className="text-white font-semibold">Get Started</ButtonText>
                <ButtonIcon as={ArrowRight} className="text-white ml-2" />
              </Button>

              <Button
                variant="outline"
                size="lg"
                onPress={() => setShowSkipDialog(true)}
                className="border-gray-300"
                testID="skip-onboarding-button"
              >
                <ButtonIcon as={SkipForward} className="text-gray-600 mr-2" />
                <ButtonText className="text-gray-600">Skip Onboarding</ButtonText>
              </Button>
            </HStack>

            <Text size="sm" className="text-center text-gray-500">
              You can always access this setup later from your dashboard settings
            </Text>
          </VStack>
        </Center>
      </Box>

      {/* Skip Confirmation Dialog */}
      <AlertDialog isOpen={showSkipDialog} onClose={() => setShowSkipDialog(false)}>
        <AlertDialogBackdrop />
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <Heading size="lg" className="text-gray-900">
              Skip Onboarding?
            </Heading>
          </AlertDialogHeader>
          <AlertDialogBody>
            <Text className="text-gray-600">
              Are you sure you want to skip the onboarding process? This will help you set up your
              school and get the most out of the platform.
            </Text>
            <Text className="text-gray-500 mt-3 text-sm">
              You can always return to complete these steps later from your dashboard.
            </Text>
          </AlertDialogBody>
          <AlertDialogFooter>
            <HStack space="sm" className="w-full">
              <Button variant="outline" onPress={() => setShowSkipDialog(false)} className="flex-1">
                <ButtonText>Cancel</ButtonText>
              </Button>
              <Button
                onPress={handleSkipConfirm}
                isDisabled={isSkipping}
                className="flex-1 bg-gray-600"
              >
                <ButtonText>{isSkipping ? 'Skipping...' : 'Skip for Now'}</ButtonText>
              </Button>
            </HStack>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Box>
  );
};