import useRouter from '@unitools/router';
import {
  CheckCircle,
  ArrowRight,
  SkipForward,
  Building2,
  Users,
  GraduationCap,
} from 'lucide-react-native';
import React, { useState, useEffect } from 'react';
import { Platform, Dimensions } from 'react-native';

import { useAuth } from '@/api/authContext';
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
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Image } from '@/components/ui/image';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useOnboarding } from '@/hooks/useOnboarding';

const { width: screenWidth } = Dimensions.get('window');
const isTablet = screenWidth >= 768;
const isMobile = Platform.OS !== 'web' || screenWidth < 768;

interface WelcomeScreenProps {
  onGetStarted?: () => void;
  onSkip?: () => void;
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onGetStarted, onSkip }) => {
  const router = useRouter();
  const { userProfile } = useAuth();
  const { skipOnboarding, createOnboardingTask, isLoading } = useOnboarding();
  const [showSkipDialog, setShowSkipDialog] = useState(false);
  const [isSkipping, setIsSkipping] = useState(false);

  // Create initial onboarding tasks when component mounts
  useEffect(() => {
    const createInitialTasks = async () => {
      if (!userProfile?.is_admin) return;

      try {
        // Create the first essential task
        await createOnboardingTask({
          title: 'Complete your school profile',
          description:
            'Add school information, logo, and contact details to personalize your account',
          priority: 'high',
          task_type: 'onboarding',
          due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days from now
        });
      } catch (error) {
        console.error('Error creating initial tasks:', error);
      }
    };

    createInitialTasks();
  }, [userProfile, createOnboardingTask]);

  const handleGetStarted = () => {
    if (onGetStarted) {
      onGetStarted();
    } else {
      router.push('/(school-admin)/dashboard');
    }
  };

  const handleSkipConfirm = async () => {
    try {
      setIsSkipping(true);
      await skipOnboarding();

      if (onSkip) {
        onSkip();
      } else {
        router.replace('/(school-admin)/dashboard');
      }
    } catch (error) {
      console.error('Error skipping onboarding:', error);
    } finally {
      setIsSkipping(false);
      setShowSkipDialog(false);
    }
  };

  const platformCapabilities = [
    {
      icon: Building2,
      title: 'School Management',
      description: 'Manage school information, settings, and organizational structure',
    },
    {
      icon: Users,
      title: 'Teacher Coordination',
      description: 'Invite teachers, manage schedules, and track performance',
    },
    {
      icon: GraduationCap,
      title: 'Student Enrollment',
      description: 'Add students, manage enrollments, and track academic progress',
    },
  ];

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
      {/* Header Section */}
      <Box className={`${isMobile ? 'px-4 pt-12' : 'px-8 pt-16'} pb-8`}>
        <Center>
          <VStack space="lg" className="items-center max-w-2xl">
            {/* Welcome Icon/Logo */}
            <Box className="bg-white rounded-full p-6 shadow-lg">
              <Icon as={CheckCircle} size={isMobile ? 48 : 64} className="text-green-500" />
            </Box>

            {/* Personalized Greeting */}
            <VStack space="sm" className="items-center">
              <Heading
                size={isMobile ? '2xl' : '3xl'}
                className="text-center text-gray-900 font-bold"
              >
                Welcome to Aprende Comigo!
              </Heading>
              {userProfile?.name && (
                <Text size={isMobile ? 'lg' : 'xl'} className="text-center text-gray-700">
                  Hello, {userProfile.name} 👋
                </Text>
              )}
            </VStack>

            {/* Welcome Message */}
            <Text
              size={isMobile ? 'md' : 'lg'}
              className="text-center text-gray-600 leading-relaxed"
            >
              Thank you for joining our educational platform! You're now ready to transform how your
              school manages tutoring sessions, teacher coordination, and student success.
            </Text>
          </VStack>
        </Center>
      </Box>

      {/* Platform Capabilities Section */}
      <Box className={`${isMobile ? 'px-4' : 'px-8'} pb-8`}>
        <VStack space="md">
          <Heading size={isMobile ? 'lg' : 'xl'} className="text-center text-gray-800 mb-4">
            What you can accomplish:
          </Heading>

          <VStack space="sm">
            {platformCapabilities.map((capability, index) => (
              <Card key={index} className="bg-white border-0 shadow-sm">
                <HStack space="md" className="items-center p-4">
                  <Box className="bg-blue-100 rounded-lg p-3">
                    <Icon
                      as={capability.icon}
                      size={isMobile ? 20 : 24}
                      className="text-blue-600"
                    />
                  </Box>
                  <VStack className="flex-1" space="xs">
                    <Text size={isMobile ? 'md' : 'lg'} className="font-semibold text-gray-900">
                      {capability.title}
                    </Text>
                    <Text size={isMobile ? 'sm' : 'md'} className="text-gray-600">
                      {capability.description}
                    </Text>
                  </VStack>
                </HStack>
              </Card>
            ))}
          </VStack>
        </VStack>
      </Box>

      {/* Action Buttons */}
      <Box className={`${isMobile ? 'px-4' : 'px-8'} pb-8 mt-auto`}>
        <VStack space="md" className="max-w-md mx-auto">
          <Button
            size={isMobile ? 'md' : 'lg'}
            onPress={handleGetStarted}
            className="bg-blue-600 hover:bg-blue-700"
            testID="get-started-button"
          >
            <ButtonText className="text-white font-semibold">Get Started</ButtonText>
            <ButtonIcon as={ArrowRight} className="text-white ml-2" />
          </Button>

          <Button
            variant="outline"
            size={isMobile ? 'sm' : 'md'}
            onPress={() => setShowSkipDialog(true)}
            className="border-gray-300"
            testID="skip-onboarding-button"
          >
            <ButtonIcon as={SkipForward} className="text-gray-600 mr-2" />
            <ButtonText className="text-gray-600">Skip Onboarding</ButtonText>
          </Button>

          <Text size="sm" className="text-center text-gray-500 mt-2">
            You can always access this setup later from your dashboard settings
          </Text>
        </VStack>
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
