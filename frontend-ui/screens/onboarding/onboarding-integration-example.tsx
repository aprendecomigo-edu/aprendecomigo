import React, { useState, useEffect } from 'react';
import useRouter from '@unitools/router';

import { 
  OnboardingProgress, 
  OnboardingChecklist, 
  ContextualHelp,
  useOnboarding,
  useContextualHelp,
  ONBOARDING_HELP_TIPS,
  OnboardingTutorial
} from '@/screens/onboarding';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { VStack } from '@/components/ui/vstack';
import { Text } from '@/components/ui/text';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Icon } from '@/components/ui/icon';
import { Rocket, Settings, ChevronRight } from 'lucide-react-native';

/**
 * Example: How to integrate onboarding into the school admin dashboard
 * 
 * This component demonstrates how to:
 * 1. Show onboarding progress in the dashboard
 * 2. Provide contextual help
 * 3. Control tutorial access
 * 4. Handle onboarding completion states
 */
export const SchoolAdminDashboardWithOnboarding: React.FC = () => {
  const router = useRouter();
  const { 
    progress, 
    shouldShowOnboarding, 
    isCompleted, 
    completionPercentage,
    isLoading 
  } = useOnboarding();
  
  const { tips, addTip } = useContextualHelp('dashboard');
  const [showOnboardingPanel, setShowOnboardingPanel] = useState(false);

  // Add contextual help tips when component mounts
  useEffect(() => {
    if (shouldShowOnboarding && !isCompleted) {
      ONBOARDING_HELP_TIPS.welcome.forEach(tip => addTip(tip));
    }
  }, [shouldShowOnboarding, isCompleted, addTip]);

  // Auto-show onboarding panel for new users
  useEffect(() => {
    if (shouldShowOnboarding && completionPercentage < 25) {
      setShowOnboardingPanel(true);
    }
  }, [shouldShowOnboarding, completionPercentage]);

  if (isLoading) {
    return (
      <Box className="flex-1 bg-gray-50 p-4">
        <Text>Loading dashboard...</Text>
      </Box>
    );
  }

  return (
    <Box className="flex-1 bg-gray-50">
      <VStack space="lg" className="p-4 max-w-6xl mx-auto">
        
        {/* Header with onboarding status */}
        <HStack className="items-center justify-between">
          <VStack>
            <Heading size="2xl" className="text-gray-900">
              School Dashboard
            </Heading>
            {shouldShowOnboarding && !isCompleted && (
              <HStack space="sm" className="items-center">
                <Badge className="bg-blue-100">
                  <BadgeText className="text-blue-700">
                    Setup: {Math.round(completionPercentage)}% complete
                  </BadgeText>
                </Badge>
                <Button
                  variant="link"
                  size="sm"
                  onPress={() => setShowOnboardingPanel(!showOnboardingPanel)}
                >
                  <ButtonText className="text-blue-600">
                    {showOnboardingPanel ? 'Hide' : 'Show'} Setup
                  </ButtonText>
                </Button>
              </HStack>
            )}
          </VStack>

          <HStack space="sm">
            {/* Contextual Help */}
            <ContextualHelp 
              tips={tips}
              showBadge={true}
              maxTips={3}
            />

            {/* Settings */}
            <Button variant="outline" size="sm">
              <ButtonIcon as={Settings} className="text-gray-600" />
            </Button>
          </HStack>
        </HStack>

        {/* Onboarding Panel (collapsible) */}
        {shouldShowOnboarding && !isCompleted && showOnboardingPanel && (
          <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
            <VStack space="lg" className="p-6">
              <HStack space="sm" className="items-center">
                <Icon as={Rocket} size={24} className="text-blue-600" />
                <VStack className="flex-1">
                  <Heading size="lg" className="text-gray-900">
                    Complete Your School Setup
                  </Heading>
                  <Text className="text-gray-600">
                    A few more steps to unlock all platform features
                  </Text>
                </VStack>
              </HStack>

              <OnboardingProgress
                completedSteps={progress?.completed_steps || []}
                skippedSteps={progress?.skipped_steps || []}
                completionPercentage={completionPercentage}
                compact={true}
              />

              <HStack space="sm">
                <Button
                  size="sm"
                  onPress={() => router.push('/onboarding/checklist')}
                  className="bg-blue-600"
                >
                  <ButtonText className="text-white">Continue Setup</ButtonText>
                  <ButtonIcon as={ChevronRight} className="text-white ml-1" />
                </Button>
                
                <Button
                  variant="outline"
                  size="sm"
                  onPress={() => setShowOnboardingPanel(false)}
                >
                  <ButtonText>Later</ButtonText>
                </Button>
              </HStack>
            </VStack>
          </Card>
        )}

        {/* Main Dashboard Content */}
        <VStack space="md">
          {/* Dashboard metrics and content would go here */}
          <Card>
            <VStack space="md" className="p-6">
              <Heading size="lg">School Overview</Heading>
              <Text className="text-gray-600">
                Your main dashboard content goes here...
              </Text>
            </VStack>
          </Card>

          {/* Quick Actions with onboarding integration */}
          <Card>
            <VStack space="md" className="p-6">
              <Heading size="lg">Quick Actions</Heading>
              <VStack space="sm">
                
                {/* Show setup actions for incomplete onboarding */}
                {shouldShowOnboarding && !isCompleted && (
                  <>
                    <Button
                      variant="outline"
                      onPress={() => router.push('/onboarding/checklist')}
                      className="justify-start"
                      testID="complete-setup-action"
                    >
                      <ButtonIcon as={Rocket} className="text-blue-600 mr-2" />
                      <ButtonText className="text-blue-600">
                        Complete School Setup ({Math.round(completionPercentage)}%)
                      </ButtonText>
                      <Badge className="bg-red-500 ml-auto">
                        <BadgeText className="text-white text-xs">
                          {progress?.total_steps - progress?.completed_steps.length || 0}
                        </BadgeText>
                      </Badge>
                    </Button>
                  </>
                )}

                {/* Regular dashboard actions */}
                <Button variant="outline" className="justify-start">
                  <ButtonText>Invite Teachers</ButtonText>
                </Button>
                <Button variant="outline" className="justify-start">
                  <ButtonText>Add Students</ButtonText>
                </Button>
                <Button variant="outline" className="justify-start">
                  <ButtonText>View Reports</ButtonText>
                </Button>
              </VStack>
            </VStack>
          </Card>
        </VStack>

        {/* Tutorial Controller */}
        <OnboardingTutorial
          autoStart={false}
          userType="admin"
          onComplete={() => {
            console.log('Dashboard tutorial completed');
          }}
          onSkip={() => {
            console.log('Dashboard tutorial skipped');
          }}
        />
      </VStack>
    </Box>
  );
};

// Example of how to add onboarding to an existing dashboard component
export const withOnboarding = <T extends object>(
  WrappedComponent: React.ComponentType<T>
) => {
  return (props: T) => {
    const { shouldShowOnboarding, isCompleted, progress } = useOnboarding();

    return (
      <VStack space="md" className="flex-1">
        {/* Onboarding banner for incomplete setup */}
        {shouldShowOnboarding && !isCompleted && progress && progress.completion_percentage < 50 && (
          <Card className="bg-yellow-50 border-yellow-200 mx-4 mt-4">
            <HStack space="sm" className="p-4 items-center">
              <Icon as={Rocket} size={20} className="text-yellow-600" />
              <VStack className="flex-1">
                <Text className="font-medium text-yellow-800">
                  Complete your school setup
                </Text>
                <Text className="text-yellow-700 text-sm">
                  {progress.total_steps - progress.completed_steps.length} steps remaining
                </Text>
              </VStack>
              <Button 
                size="sm" 
                className="bg-yellow-600"
                onPress={() => {
                  // Navigation handled by individual components
                }}
              >
                <ButtonText className="text-white">Continue</ButtonText>
              </Button>
            </HStack>
          </Card>
        )}

        {/* Original component */}
        <WrappedComponent {...props} />
      </VStack>
    );
  };
};