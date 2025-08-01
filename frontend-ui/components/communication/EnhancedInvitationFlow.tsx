import React, { useState, useEffect, useCallback } from 'react';
import { Alert } from 'react-native';
import { 
  UserIcon, 
  CheckCircleIcon, 
  HelpCircleIcon,
  ArrowRightIcon,
  StarIcon,
  GiftIcon,
  HeartIcon
} from 'lucide-react-native';
import { router } from 'expo-router';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { Badge } from '@/components/ui/badge';

import { useTeacherOnboarding, useFAQSystem, useContextualHelp, useOnboardingCelebrations } from '@/hooks/useTeacherOnboarding';
import ProfileWizard from '@/components/profile-wizard/ProfileWizard';

interface EnhancedInvitationFlowProps {
  invitationToken: string;
  invitationData: any;
  onSuccess: () => void;
  onCancel?: () => void;
}

const EnhancedInvitationFlow: React.FC<EnhancedInvitationFlowProps> = ({
  invitationToken,
  invitationData,
  onSuccess,
  onCancel,
}) => {
  const [currentView, setCurrentView] = useState<'welcome' | 'wizard' | 'help'>('welcome');
  const [showFAQs, setShowFAQs] = useState(false);

  const { 
    progress, 
    markMilestoneAchieved, 
    progressPercentage 
  } = useTeacherOnboarding();

  const { 
    faqs, 
    searchFAQs, 
    markFAQHelpful 
  } = useFAQSystem();

  const { 
    contextualFAQs, 
    getContextualHelp 
  } = useContextualHelp();

  const {
    showCelebration,
    celebrationData,
    celebrateMilestone,
    closeCelebration,
  } = useOnboardingCelebrations();

  // Load contextual help for invitation acceptance
  useEffect(() => {
    getContextualHelp('invitation_acceptance');
  }, [getContextualHelp]);

  const handleStartWizard = useCallback(() => {
    setCurrentView('wizard');
    markMilestoneAchieved('invitation_accepted');
    celebrateMilestone('Invitation Accepted');
  }, [markMilestoneAchieved, celebrateMilestone]);

  const handleShowHelp = useCallback(() => {
    setShowFAQs(true);
  }, []);

  const handleWizardSuccess = useCallback(() => {
    celebrateMilestone('Profile Setup Complete');
    onSuccess();
  }, [celebrateMilestone, onSuccess]);

  const renderWelcomeScreen = () => (
    <ScrollView className="flex-1" contentContainerStyle={{ flexGrow: 1 }}>
      <VStack className="flex-1 p-6" space="lg">
        {/* Hero Section */}
        <Card className="p-8 bg-gradient-to-br from-blue-50 to-purple-50 border-2 border-blue-100">
          <VStack space="lg" className="items-center text-center">
            <Box className="p-6 bg-white rounded-full shadow-lg">
              <Icon as={GiftIcon} size="xl" className="text-blue-600" />
            </Box>
            
            <VStack space="md" className="items-center">
              <Heading size="xl" className="text-gray-900 text-center">
                Welcome to {invitationData?.invitation?.school?.name}! 🎉
              </Heading>
              
              <Text className="text-gray-600 text-center text-lg">
                You've been invited to join our teaching community. 
                Let's set up your profile and get you started!
              </Text>
            </VStack>

            <VStack space="sm" className="items-center">
              <Badge className="bg-green-100 text-green-800 px-4 py-2">
                <Text className="font-semibold">Exclusive Teacher Invitation</Text>
              </Badge>
              
              <Text className="text-sm text-gray-500">
                Invited by: {invitationData?.invitation?.inviter_name || 'School Administrator'}
              </Text>
            </VStack>
          </VStack>
        </Card>

        {/* School Information */}
        <Card className="p-6">
          <VStack space="md">
            <HStack space="sm" className="items-center">
              <Icon as={UserIcon} size="sm" className="text-blue-600" />
              <Heading size="md" className="text-gray-900">
                About {invitationData?.invitation?.school?.name}
              </Heading>
            </HStack>
            
            <Text className="text-gray-600">
              {invitationData?.invitation?.school?.description || 
               'Join our innovative educational community dedicated to student success and teacher excellence.'}
            </Text>

            {invitationData?.invitation?.custom_message && (
              <Card className="p-4 bg-blue-50 border border-blue-200">
                <VStack space="xs">
                  <Text className="font-semibold text-blue-900">
                    Personal Message
                  </Text>
                  <Text className="text-blue-800">
                    "{invitationData.invitation.custom_message}"
                  </Text>
                </VStack>
              </Card>
            )}
          </VStack>
        </Card>

        {/* What to Expect */}
        <Card className="p-6">
          <VStack space="md">
            <HStack space="sm" className="items-center">
              <Icon as={StarIcon} size="sm" className="text-purple-600" />
              <Heading size="md" className="text-gray-900">
                What to Expect
              </Heading>
            </HStack>
            
            <VStack space="sm">
              {[
                'Quick 5-minute profile setup',
                'Choose your teaching subjects and grade levels',
                'Set your availability and rates',
                'Upload credentials and create your bio',
                'Start connecting with students right away'
              ].map((item, index) => (
                <HStack key={index} space="sm" className="items-center">
                  <Icon as={CheckCircleIcon} size="xs" className="text-green-600" />
                  <Text className="text-gray-700 flex-1">{item}</Text>
                </HStack>
              ))}
            </VStack>
          </VStack>
        </Card>

        {/* Contextual FAQ */}
        {contextualFAQs.length > 0 && (
          <Card className="p-6">
            <VStack space="md">
              <HStack space="sm" className="items-center">
                <Icon as={HelpCircleIcon} size="sm" className="text-orange-600" />
                <Heading size="md" className="text-gray-900">
                  Common Questions
                </Heading>
              </HStack>
              
              <VStack space="sm">
                {contextualFAQs.slice(0, 3).map((faq) => (
                  <Pressable
                    key={faq.id}
                    onPress={() => {
                      Alert.alert(faq.question, faq.answer);
                      markFAQHelpful(faq.id, true);
                    }}
                    className="p-3 bg-gray-50 rounded-lg border hover:bg-gray-100"
                  >
                    <Text className="text-gray-700 font-medium">
                      {faq.question}
                    </Text>
                  </Pressable>
                ))}
              </VStack>
              
              <Button variant="link" onPress={handleShowHelp}>
                <ButtonText>View All FAQs</ButtonText>
              </Button>
            </VStack>
          </Card>
        )}

        {/* Progress Indicator */}
        {progress && (
          <Card className="p-6">
            <VStack space="md">
              <HStack className="justify-between items-center">
                <Text className="font-semibold text-gray-900">
                  Profile Completion
                </Text>
                <Text className="text-sm text-gray-600">
                  {Math.round(progressPercentage)}% Complete
                </Text>
              </HStack>
              
              <Box className="w-full bg-gray-200 rounded-full h-2">
                <Box 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progressPercentage}%` }}
                />
              </Box>
              
              <Text className="text-xs text-gray-500 text-center">
                Complete your profile to start teaching
              </Text>
            </VStack>
          </Card>
        )}

        {/* Action Buttons */}
        <VStack space="md" className="mt-auto">
          <Button 
            onPress={handleStartWizard}
            className="bg-blue-600 py-4"
            size="lg"
          >
            <HStack space="sm" className="items-center">
              <ButtonText className="text-white font-semibold text-lg">
                Get Started
              </ButtonText>
              <Icon as={ArrowRightIcon} size="sm" className="text-white" />
            </HStack>
          </Button>
          
          <HStack space="md" className="justify-center">
            <Button variant="link" onPress={handleShowHelp}>
              <ButtonText>Need Help?</ButtonText>
            </Button>
            
            {onCancel && (
              <Button variant="link" onPress={onCancel}>
                <ButtonText>Maybe Later</ButtonText>
              </Button>
            )}
          </HStack>
        </VStack>
      </VStack>

      {/* Celebration Modal */}
      {showCelebration && celebrationData && (
        <Box className="absolute inset-0 bg-black/50 justify-center items-center">
          <Card className="mx-6 p-8 max-w-sm w-full">
            <VStack space="lg" className="items-center text-center">
              <Icon as={HeartIcon} size="xl" className="text-red-500" />
              
              <VStack space="sm" className="items-center">
                <Heading size="lg" className="text-gray-900">
                  {celebrationData.title}
                </Heading>
                <Text className="text-gray-600">
                  {celebrationData.message}
                </Text>
              </VStack>
              
              <Button onPress={closeCelebration} className="bg-blue-600">
                <ButtonText className="text-white">Continue</ButtonText>
              </Button>
            </VStack>
          </Card>
        </Box>
      )}
    </ScrollView>
  );

  const renderFAQScreen = () => (
    <ScrollView className="flex-1" contentContainerStyle={{ flexGrow: 1 }}>
      <VStack className="flex-1 p-6" space="lg">
        <HStack className="justify-between items-center">
          <Heading size="xl" className="text-gray-900">
            Frequently Asked Questions
          </Heading>
          <Button variant="outline" onPress={() => setShowFAQs(false)}>
            <ButtonText>Back</ButtonText>
          </Button>
        </HStack>

        <VStack space="md">
          {faqs.map((faq) => (
            <Card key={faq.id} className="p-4">
              <VStack space="sm">
                <Text className="font-semibold text-gray-900">
                  {faq.question}
                </Text>
                <Text className="text-gray-600">
                  {faq.answer}
                </Text>
                <HStack space="sm">
                  <Button 
                    size="sm" 
                    variant="outline"
                    onPress={() => markFAQHelpful(faq.id, true)}
                  >
                    <ButtonText>Helpful</ButtonText>
                  </Button>
                </HStack>
              </VStack>
            </Card>
          ))}
        </VStack>
      </VStack>
    </ScrollView>
  );

  if (currentView === 'help' || showFAQs) {
    return renderFAQScreen();
  }

  if (currentView === 'wizard') {
    return (
      <ProfileWizard
        invitationToken={invitationToken}
        invitationData={invitationData}
        onSuccess={handleWizardSuccess}
        onCancel={() => setCurrentView('welcome')}
      />
    );
  }

  return renderWelcomeScreen();
};

export default EnhancedInvitationFlow;