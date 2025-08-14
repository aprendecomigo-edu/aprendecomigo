import useRouter from '@unitools/router';
import { useLocalSearchParams } from 'expo-router';
import {
  CheckCircle2,
  ExternalLink,
  ArrowRight,
  Share2,
  Users,
  Calendar,
  DollarSign,
} from 'lucide-react-native';
import React, { useEffect } from 'react';

import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface NextStep {
  title: string;
  description: string;
  action_url?: string;
  icon: any;
  priority: 'high' | 'medium' | 'low';
}

const TUTOR_NEXT_STEPS: NextStep[] = [
  {
    title: 'Attract Your First Students',
    description:
      'Share your profile link with potential students and start building your tutoring business.',
    icon: Users,
    priority: 'high',
  },
  {
    title: 'Set Your Availability',
    description: 'Fine-tune your weekly schedule and booking preferences to match your lifestyle.',
    action_url: '/settings/availability',
    icon: Calendar,
    priority: 'high',
  },
  {
    title: 'Review Your Rates',
    description: 'Adjust your pricing strategy based on market insights and your experience level.',
    action_url: '/settings/rates',
    icon: DollarSign,
    priority: 'medium',
  },
];

const SCHOOL_NEXT_STEPS: NextStep[] = [
  {
    title: 'Invite Teachers',
    description:
      'Start building your teaching team by inviting qualified educators to join your school.',
    action_url: '/admin/invitations',
    icon: Users,
    priority: 'high',
  },
  {
    title: 'Add Students',
    description: 'Begin enrolling students and organizing them into classes.',
    action_url: '/admin/students',
    icon: Users,
    priority: 'high',
  },
];

export default function OnboardingSuccessScreen() {
  const router = useRouter();
  const { type, profileUrl, discoveryUrl, bookingUrl } = useLocalSearchParams<{
    type: string;
    profileUrl: string;
    discoveryUrl: string;
    bookingUrl: string;
  }>();

  const isTutor = type === 'tutor';
  const nextSteps = isTutor ? TUTOR_NEXT_STEPS : SCHOOL_NEXT_STEPS;

  // Auto-redirect after a delay if no interaction
  useEffect(() => {
    const timer = setTimeout(() => {
      if (isTutor) {
        router.replace('/(school-admin)/dashboard');
      } else {
        router.replace('/(school-admin)/dashboard');
      }
    }, 30000); // 30 seconds

    return () => clearTimeout(timer);
  }, [router, isTutor]);

  const handleShare = async () => {
    if (!profileUrl) return;

    try {
      if (navigator.share) {
        await navigator.share({
          title: `My ${isTutor ? 'Tutoring' : 'School'} Profile - Aprende Comigo`,
          text: `Check out my ${isTutor ? 'tutoring services' : 'school'} on Aprende Comigo!`,
          url: profileUrl,
        });
      } else {
        // Fallback: copy to clipboard
        await navigator.clipboard.writeText(profileUrl);
        // You could show a toast here
        console.log('Profile URL copied to clipboard');
      }
    } catch (error) {
      console.error('Error sharing:', error);
    }
  };

  const handleNextStepAction = (step: NextStep) => {
    if (step.action_url) {
      router.push(step.action_url);
    }
  };

  const handleGoToDashboard = () => {
    if (isTutor) {
      router.replace('/(school-admin)/dashboard');
    } else {
      router.replace('/(school-admin)/dashboard');
    }
  };

  return (
    <Box className="flex-1 bg-gray-50 p-6">
      <VStack className="flex-1 max-w-2xl mx-auto" space="lg">
        {/* Success Header */}
        <VStack className="items-center text-center" space="lg">
          <Box className="w-20 h-20 rounded-full bg-green-100 items-center justify-center">
            <Icon as={CheckCircle2} className="text-green-600" size="xl" />
          </Box>

          <VStack space="sm">
            <Heading size="2xl" className="text-gray-900 text-center">
              {isTutor ? 'Your Tutoring Profile is Live!' : 'School Registration Complete!'}
            </Heading>
            <Text className="text-gray-600 text-center text-lg max-w-md">
              {isTutor
                ? 'Congratulations! Your professional tutoring profile is now active and ready to attract students.'
                : 'Your school has been successfully registered and is ready to manage teachers and students.'}
            </Text>
          </VStack>

          {/* Profile Links for Tutors */}
          {isTutor && (profileUrl || discoveryUrl || bookingUrl) && (
            <VStack space="sm" className="w-full">
              <Text className="text-gray-700 font-medium">Your Profile Links:</Text>
              <VStack space="sm" className="w-full">
                {profileUrl && (
                  <HStack
                    space="sm"
                    className="items-center justify-between p-3 bg-white rounded-lg border"
                  >
                    <VStack className="flex-1" space="xs">
                      <Text className="text-gray-900 font-medium text-sm">Profile Page</Text>
                      <Text className="text-gray-600 text-xs" numberOfLines={1}>
                        {profileUrl}
                      </Text>
                    </VStack>
                    <HStack space="xs">
                      <Pressable onPress={handleShare} className="p-2">
                        <Icon as={Share2} className="text-blue-600" size="sm" />
                      </Pressable>
                      <Pressable onPress={() => window.open(profileUrl, '_blank')} className="p-2">
                        <Icon as={ExternalLink} className="text-blue-600" size="sm" />
                      </Pressable>
                    </HStack>
                  </HStack>
                )}

                {bookingUrl && (
                  <HStack
                    space="sm"
                    className="items-center justify-between p-3 bg-white rounded-lg border"
                  >
                    <VStack className="flex-1" space="xs">
                      <Text className="text-gray-900 font-medium text-sm">Booking Page</Text>
                      <Text className="text-gray-600 text-xs" numberOfLines={1}>
                        {bookingUrl}
                      </Text>
                    </VStack>
                    <Pressable onPress={() => window.open(bookingUrl, '_blank')} className="p-2">
                      <Icon as={ExternalLink} className="text-blue-600" size="sm" />
                    </Pressable>
                  </HStack>
                )}
              </VStack>
            </VStack>
          )}
        </VStack>

        {/* Next Steps */}
        <VStack space="md">
          <Heading size="lg" className="text-gray-900">
            Recommended Next Steps
          </Heading>

          <VStack space="sm">
            {nextSteps.map((step, index) => (
              <Card key={index} className="border shadow-sm">
                <CardContent className="p-4">
                  <HStack space="md" className="items-start">
                    <Box
                      className={`w-10 h-10 rounded-full items-center justify-center ${
                        step.priority === 'high'
                          ? 'bg-blue-100'
                          : step.priority === 'medium'
                          ? 'bg-yellow-100'
                          : 'bg-gray-100'
                      }`}
                    >
                      <Icon
                        as={step.icon}
                        className={
                          step.priority === 'high'
                            ? 'text-blue-600'
                            : step.priority === 'medium'
                            ? 'text-yellow-600'
                            : 'text-gray-600'
                        }
                        size="lg"
                      />
                    </Box>

                    <VStack className="flex-1" space="xs">
                      <HStack className="items-center justify-between">
                        <Heading size="sm" className="text-gray-900">
                          {step.title}
                        </Heading>
                        {step.priority === 'high' && (
                          <Badge className="bg-blue-100">
                            <BadgeText className="text-blue-700 text-xs">Priority</BadgeText>
                          </Badge>
                        )}
                      </HStack>
                      <Text className="text-gray-600 text-sm">{step.description}</Text>

                      {step.action_url && (
                        <Button
                          variant="outline"
                          size="sm"
                          onPress={() => handleNextStepAction(step)}
                          className="self-start mt-2"
                        >
                          <ButtonText className="text-blue-600">Take Action</ButtonText>
                          <ButtonIcon as={ArrowRight} className="text-blue-600 ml-1" />
                        </Button>
                      )}
                    </VStack>
                  </HStack>
                </CardContent>
              </Card>
            ))}
          </VStack>
        </VStack>

        {/* Action Buttons */}
        <VStack space="sm" className="mt-auto">
          <Button onPress={handleGoToDashboard} className="w-full bg-blue-600 hover:bg-blue-700">
            <ButtonText className="text-white font-medium">Go to Dashboard</ButtonText>
            <ButtonIcon as={ArrowRight} className="text-white ml-2" />
          </Button>

          {isTutor && profileUrl && (
            <Button
              variant="outline"
              onPress={() => window.open(profileUrl, '_blank')}
              className="w-full"
            >
              <ButtonText className="text-blue-600">View My Profile</ButtonText>
              <ButtonIcon as={ExternalLink} className="text-blue-600 ml-2" />
            </Button>
          )}
        </VStack>
      </VStack>
    </Box>
  );
}
