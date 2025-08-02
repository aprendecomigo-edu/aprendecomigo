import { CheckCircle, Circle } from 'lucide-react-native';
import React from 'react';
import { Platform, Dimensions } from 'react-native';

import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon, ArrowRightIcon } from '@/components/ui/icon';
import { Progress, ProgressFilledTrack } from '@/components/ui/progress';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { ONBOARDING_STEPS } from '@/hooks/useOnboarding';

const { width: screenWidth } = Dimensions.get('window');
const isMobile = Platform.OS !== 'web' || screenWidth < 768;

interface OnboardingProgressProps {
  completedSteps: string[];
  skippedSteps: string[];
  completionPercentage: number;
  currentStep?: number;
  showStepDetails?: boolean;
  compact?: boolean;
  className?: string;
}

export const OnboardingProgress: React.FC<OnboardingProgressProps> = ({
  completedSteps = [],
  skippedSteps = [],
  completionPercentage = 0,
  currentStep = 0,
  showStepDetails = true,
  compact = false,
  className = '',
}) => {
  const totalSteps = ONBOARDING_STEPS.length;
  const completedCount = completedSteps.length;
  const skippedCount = skippedSteps.length;
  const remainingCount = totalSteps - completedCount - skippedCount;

  const getStepStatus = (stepId: string) => {
    if (completedSteps.includes(stepId)) return 'completed';
    if (skippedSteps.includes(stepId)) return 'skipped';
    return 'pending';
  };

  const getStepIcon = (stepId: string, index: number) => {
    const status = getStepStatus(stepId);
    const isActive = index === currentStep;

    switch (status) {
      case 'completed':
        return <Icon as={CheckCircle} size={compact ? 16 : 20} className="text-green-500" />;
      case 'skipped':
        return <Icon as={ArrowRightIcon} size={compact ? 16 : 20} className="text-gray-400" />;
      default:
        return (
          <Icon
            as={Circle}
            size={compact ? 16 : 20}
            className={isActive ? 'text-blue-500' : 'text-gray-300'}
          />
        );
    }
  };

  const getStepColor = (stepId: string, index: number) => {
    const status = getStepStatus(stepId);
    const isActive = index === currentStep;

    if (status === 'completed') return 'text-green-700';
    if (status === 'skipped') return 'text-gray-500';
    if (isActive) return 'text-blue-700';
    return 'text-gray-600';
  };

  if (compact) {
    return (
      <Box className={`bg-white rounded-lg p-4 shadow-sm ${className}`}>
        <VStack space="sm">
          <HStack className="items-center justify-between">
            <Text size="sm" className="font-medium text-gray-700">
              Setup Progress
            </Text>
            <Badge className="bg-blue-100">
              <BadgeText className="text-blue-700 text-xs">
                {completedCount}/{totalSteps}
              </BadgeText>
            </Badge>
          </HStack>

          <Progress value={completionPercentage} className="h-2">
            <ProgressFilledTrack className="bg-blue-500" />
          </Progress>

          <HStack className="items-center justify-between">
            <Text size="xs" className="text-gray-500">
              {completionPercentage}% complete
            </Text>
            {skippedCount > 0 && (
              <Text size="xs" className="text-gray-400">
                {skippedCount} skipped
              </Text>
            )}
          </HStack>
        </VStack>
      </Box>
    );
  }

  return (
    <Box className={`bg-white rounded-lg p-6 shadow-sm ${className}`}>
      <VStack space="lg">
        {/* Header */}
        <VStack space="sm">
          <HStack className="items-center justify-between">
            <Heading size={isMobile ? 'lg' : 'xl'} className="text-gray-900">
              Setup Progress
            </Heading>
            <Badge className="bg-blue-100">
              <BadgeText className="text-blue-700">
                {completedCount} of {totalSteps} completed
              </BadgeText>
            </Badge>
          </HStack>

          <Text className="text-gray-600">
            Complete these steps to get the most out of your platform
          </Text>
        </VStack>

        {/* Progress Bar */}
        <VStack space="sm">
          <Progress value={completionPercentage} className="h-3">
            <ProgressFilledTrack className="bg-gradient-to-r from-blue-500 to-blue-600" />
          </Progress>

          <HStack className="items-center justify-between">
            <Text size="sm" className="text-gray-700 font-medium">
              {completionPercentage}% complete
            </Text>
            <HStack space="md">
              {completedCount > 0 && (
                <Text size="sm" className="text-green-600">
                  {completedCount} completed
                </Text>
              )}
              {skippedCount > 0 && (
                <Text size="sm" className="text-gray-500">
                  {skippedCount} skipped
                </Text>
              )}
              {remainingCount > 0 && (
                <Text size="sm" className="text-blue-600">
                  {remainingCount} remaining
                </Text>
              )}
            </HStack>
          </HStack>
        </VStack>

        {/* Step Details */}
        {showStepDetails && (
          <VStack space="sm">
            <Heading size="md" className="text-gray-800 mb-2">
              Steps Overview
            </Heading>

            <VStack space="xs">
              {ONBOARDING_STEPS.map((step, index) => {
                const status = getStepStatus(step.id);
                const isActive = index === currentStep;

                return (
                  <HStack
                    key={step.id}
                    space="sm"
                    className={`items-center p-3 rounded-lg ${
                      isActive
                        ? 'bg-blue-50 border border-blue-200'
                        : status === 'completed'
                        ? 'bg-green-50'
                        : status === 'skipped'
                        ? 'bg-gray-50'
                        : 'bg-gray-25'
                    }`}
                  >
                    {getStepIcon(step.id, index)}

                    <VStack className="flex-1" space="xs">
                      <Text size="sm" className={`font-medium ${getStepColor(step.id, index)}`}>
                        {step.name}
                      </Text>
                      {!isMobile && (
                        <Text
                          size="xs"
                          className={`${
                            status === 'completed'
                              ? 'text-green-600'
                              : status === 'skipped'
                              ? 'text-gray-500'
                              : isActive
                              ? 'text-blue-600'
                              : 'text-gray-500'
                          }`}
                        >
                          {step.description}
                        </Text>
                      )}
                    </VStack>

                    {status === 'completed' && (
                      <Badge className="bg-green-100">
                        <BadgeText className="text-green-700 text-xs">Done</BadgeText>
                      </Badge>
                    )}

                    {status === 'skipped' && (
                      <Badge className="bg-gray-100">
                        <BadgeText className="text-gray-600 text-xs">Skipped</BadgeText>
                      </Badge>
                    )}

                    {isActive && status === 'pending' && (
                      <Badge className="bg-blue-100">
                        <BadgeText className="text-blue-700 text-xs">Current</BadgeText>
                      </Badge>
                    )}
                  </HStack>
                );
              })}
            </VStack>
          </VStack>
        )}

        {/* Completion Message */}
        {completionPercentage >= 100 && (
          <Box className="bg-green-50 border border-green-200 rounded-lg p-4">
            <HStack space="sm" className="items-center">
              <Icon as={CheckCircle} size={20} className="text-green-500" />
              <VStack className="flex-1">
                <Text className="font-medium text-green-800">Congratulations! 🎉</Text>
                <Text size="sm" className="text-green-700">
                  You've completed the onboarding process. Your school is ready to go!
                </Text>
              </VStack>
            </HStack>
          </Box>
        )}
      </VStack>
    </Box>
  );
};
