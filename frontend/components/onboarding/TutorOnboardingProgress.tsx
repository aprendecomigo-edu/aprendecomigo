import {
  Check,
  ChevronRight,
  Clock,
  User,
  School,
  BookOpen,
  DollarSign,
  FileText,
  Star,
  AlertCircle,
} from 'lucide-react-native';
import React from 'react';

import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Progress, ProgressFilledTrack } from '@/components/ui/progress';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Onboarding step configuration for individual tutors
export interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<any>;
  isRequired: boolean;
  estimatedTime: number; // in minutes
  isCompleted: boolean;
  canAccess: boolean;
  completedAt?: Date;
}

export interface TutorOnboardingData {
  steps: OnboardingStep[];
  currentStepId: string;
  overallProgress: number;
  completedSteps: number;
  totalSteps: number;
  estimatedTimeRemaining: number;
  startedAt?: Date;
  completedAt?: Date;
}

// Default onboarding steps for individual tutors
export const DEFAULT_TUTOR_ONBOARDING_STEPS: Omit<OnboardingStep, 'isCompleted' | 'canAccess'>[] = [
  {
    id: 'account-creation',
    title: 'Account Created',
    description: 'Basic account setup and email verification',
    icon: User,
    isRequired: true,
    estimatedTime: 5,
  },
  {
    id: 'school-setup',
    title: 'Practice Setup',
    description: 'Create your tutoring practice profile',
    icon: School,
    isRequired: true,
    estimatedTime: 3,
  },
  {
    id: 'educational-system',
    title: 'Educational System',
    description: 'Choose the education system you teach within',
    icon: BookOpen,
    isRequired: true,
    estimatedTime: 2,
  },
  {
    id: 'subject-selection',
    title: 'Teaching Subjects',
    description: 'Select the courses and subjects you teach',
    icon: BookOpen,
    isRequired: true,
    estimatedTime: 10,
  },
  {
    id: 'rate-configuration',
    title: 'Pricing Setup',
    description: 'Set your hourly rates for each subject',
    icon: DollarSign,
    isRequired: true,
    estimatedTime: 8,
  },
  {
    id: 'teacher-profile',
    title: 'Teacher Profile',
    description: 'Complete your professional teaching profile',
    icon: FileText,
    isRequired: true,
    estimatedTime: 15,
  },
  {
    id: 'profile-review',
    title: 'Profile Review',
    description: 'Review and publish your tutor profile',
    icon: Star,
    isRequired: true,
    estimatedTime: 5,
  },
];

interface TutorOnboardingProgressProps {
  onboarding: TutorOnboardingData;
  onStepClick?: (stepId: string) => void;
  onContinue?: () => void;
  onSkipToNext?: () => void;
  showTimeEstimates?: boolean;
  compact?: boolean;
  className?: string;
}

const StepCard: React.FC<{
  step: OnboardingStep;
  isActive: boolean;
  isCurrent: boolean;
  onClick?: (stepId: string) => void;
  showTimeEstimate?: boolean;
  compact?: boolean;
}> = ({ step, isActive, isCurrent, onClick, showTimeEstimate = true, compact = false }) => {
  const getStepStatus = () => {
    if (step.isCompleted) return 'completed';
    if (isCurrent) return 'current';
    if (step.canAccess) return 'available';
    return 'locked';
  };

  const status = getStepStatus();

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return {
          bg: 'bg-green-100',
          text: 'text-green-600',
          border: 'border-green-200',
          iconBg: 'bg-green-600',
          iconText: 'text-white',
        };
      case 'current':
        return {
          bg: 'bg-blue-100',
          text: 'text-blue-600',
          border: 'border-blue-500',
          iconBg: 'bg-blue-600',
          iconText: 'text-white',
        };
      case 'available':
        return {
          bg: 'bg-gray-50',
          text: 'text-gray-700',
          border: 'border-gray-200',
          iconBg: 'bg-white',
          iconText: 'text-gray-600',
        };
      default:
        return {
          bg: 'bg-gray-50',
          text: 'text-gray-400',
          border: 'border-gray-200',
          iconBg: 'bg-gray-100',
          iconText: 'text-gray-400',
        };
    }
  };

  const colors = getStatusColor();
  const StepIcon = step.icon;

  const handleClick = () => {
    if (onClick && step.canAccess) {
      onClick(step.id);
    }
  };

  if (compact) {
    return (
      <Pressable
        onPress={handleClick}
        disabled={!step.canAccess}
        className="flex-1"
        accessibilityRole="button"
        accessibilityLabel={`${step.title} - ${status}`}
        accessibilityHint={step.description}
      >
        <HStack space="xs" className="items-center">
          <Box className={`w-8 h-8 rounded-full items-center justify-center ${colors.iconBg}`}>
            {step.isCompleted ? (
              <Icon as={Check} className="text-white" size="sm" />
            ) : (
              <Icon as={StepIcon} className={colors.iconText} size="sm" />
            )}
          </Box>
          <VStack className="flex-1">
            <Text className={`text-sm font-medium ${colors.text}`}>{step.title}</Text>
            {isCurrent && <Text className="text-blue-600 text-xs">Current step</Text>}
          </VStack>
          {step.canAccess && !step.isCompleted && (
            <Icon as={ChevronRight} className="text-gray-400" size="sm" />
          )}
        </HStack>
      </Pressable>
    );
  }

  return (
    <Pressable
      onPress={handleClick}
      disabled={!step.canAccess}
      className="w-full"
      accessibilityRole="button"
      accessibilityLabel={`${step.title} - ${status}`}
      accessibilityHint={step.description}
    >
      <Card
        className={`
          border-2 transition-all duration-200
          ${colors.border} ${colors.bg}
          ${isCurrent ? 'shadow-md' : 'shadow-sm'}
          ${step.canAccess ? 'hover:shadow-md' : ''}
        `}
      >
        <CardContent className="p-4">
          <HStack className="items-start justify-between">
            <HStack space="md" className="items-start flex-1">
              <Box
                className={`w-12 h-12 rounded-full items-center justify-center ${colors.iconBg}`}
              >
                {step.isCompleted ? (
                  <Icon as={Check} className="text-white" size="lg" />
                ) : (
                  <Icon as={StepIcon} className={colors.iconText} size="lg" />
                )}
              </Box>

              <VStack className="flex-1" space="xs">
                <VStack space="xs">
                  <HStack className="items-center justify-between">
                    <Heading size="sm" className={`${colors.text} font-medium`}>
                      {step.title}
                    </Heading>
                    {step.isRequired && (
                      <Badge className="bg-red-100">
                        <BadgeText className="text-red-700 text-xs">Required</BadgeText>
                      </Badge>
                    )}
                  </HStack>

                  <Text className={`text-sm ${colors.text} opacity-80`}>{step.description}</Text>
                </VStack>

                <HStack space="md" className="items-center">
                  {showTimeEstimate && (
                    <HStack space="xs" className="items-center">
                      <Icon as={Clock} className={colors.text} size="xs" />
                      <Text className={`text-xs ${colors.text}`}>~{step.estimatedTime} min</Text>
                    </HStack>
                  )}

                  {step.completedAt && (
                    <Text className="text-green-600 text-xs">
                      Completed {step.completedAt.toLocaleDateString()}
                    </Text>
                  )}

                  {isCurrent && (
                    <Badge className="bg-blue-600">
                      <BadgeText className="text-white text-xs">Current</BadgeText>
                    </Badge>
                  )}
                </HStack>
              </VStack>
            </HStack>

            {step.canAccess && !step.isCompleted && (
              <Icon as={ChevronRight} className="text-gray-400 ml-2" size="md" />
            )}
          </HStack>
        </CardContent>
      </Card>
    </Pressable>
  );
};

export const TutorOnboardingProgress: React.FC<TutorOnboardingProgressProps> = ({
  onboarding,
  onStepClick,
  onContinue,
  onSkipToNext,
  showTimeEstimates = true,
  compact = false,
  className = '',
}) => {
  const currentStep = onboarding.steps.find(step => step.id === onboarding.currentStepId);
  const nextStep = onboarding.steps.find(
    step => !step.isCompleted && step.canAccess && step.id !== onboarding.currentStepId,
  );

  const isCompleted = onboarding.overallProgress >= 100;

  return (
    <VStack className={`w-full ${className}`} space="lg">
      {/* Header */}
      <VStack space="md">
        <VStack className="items-center text-center" space="sm">
          <Box className="w-16 h-16 rounded-full bg-blue-100 items-center justify-center">
            <Icon as={Star} className="text-blue-600" size="xl" />
          </Box>
          <VStack space="xs">
            <Heading size="xl" className="text-gray-900">
              {isCompleted ? 'Onboarding Complete!' : 'Complete Your Tutor Setup'}
            </Heading>
            <Text className="text-gray-600 text-center">
              {isCompleted
                ? 'Your tutoring profile is ready to attract students'
                : 'Set up your professional tutoring profile to start teaching'}
            </Text>
          </VStack>
        </VStack>

        {/* Progress Overview */}
        <VStack space="md" className="bg-white p-4 rounded-lg border border-gray-200">
          <HStack className="items-center justify-between">
            <Text className="text-gray-700 font-medium">Overall Progress</Text>
            <Text className="text-blue-600 font-bold">
              {Math.round(onboarding.overallProgress)}%
            </Text>
          </HStack>

          <Progress value={onboarding.overallProgress} className="h-3">
            <ProgressFilledTrack className="bg-blue-600" />
          </Progress>

          <HStack className="items-center justify-between text-sm">
            <Text className="text-gray-600">
              {onboarding.completedSteps} of {onboarding.totalSteps} steps completed
            </Text>
            {onboarding.estimatedTimeRemaining > 0 && (
              <HStack space="xs" className="items-center">
                <Icon as={Clock} className="text-gray-500" size="xs" />
                <Text className="text-gray-600">
                  ~{onboarding.estimatedTimeRemaining} min remaining
                </Text>
              </HStack>
            )}
          </HStack>
        </VStack>
      </VStack>

      {/* Current Step Highlight */}
      {currentStep && !isCompleted && (
        <Box className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
          <VStack space="sm">
            <HStack className="items-center justify-between">
              <Text className="text-blue-900 font-medium">Current Step: {currentStep.title}</Text>
              <Badge className="bg-blue-600">
                <BadgeText className="text-white text-xs">Active</BadgeText>
              </Badge>
            </HStack>
            <Text className="text-blue-800 text-sm">{currentStep.description}</Text>
            {showTimeEstimates && (
              <HStack space="xs" className="items-center">
                <Icon as={Clock} className="text-blue-600" size="xs" />
                <Text className="text-blue-700 text-sm">
                  Estimated time: {currentStep.estimatedTime} minutes
                </Text>
              </HStack>
            )}
          </VStack>
        </Box>
      )}

      {/* Steps List */}
      <VStack space={compact ? 'sm' : 'md'}>
        {onboarding.steps.map(step => (
          <StepCard
            key={step.id}
            step={step}
            isActive={step.canAccess}
            isCurrent={step.id === onboarding.currentStepId}
            onClick={onStepClick}
            showTimeEstimate={showTimeEstimates}
            compact={compact}
          />
        ))}
      </VStack>

      {/* Action Buttons */}
      {!isCompleted && (
        <VStack space="sm">
          {onContinue && currentStep && (
            <Button onPress={onContinue} className="w-full bg-blue-600 hover:bg-blue-700">
              <ButtonText className="text-white font-medium">
                Continue: {currentStep.title}
              </ButtonText>
              <ButtonIcon as={ChevronRight} className="text-white ml-2" />
            </Button>
          )}

          {onSkipToNext && nextStep && nextStep.id !== onboarding.currentStepId && (
            <Button variant="outline" onPress={onSkipToNext} className="w-full">
              <ButtonText className="text-gray-700">Skip to: {nextStep.title}</ButtonText>
            </Button>
          )}
        </VStack>
      )}

      {/* Completion Message */}
      {isCompleted && onboarding.completedAt && (
        <Box className="bg-green-50 border border-green-200 p-4 rounded-lg">
          <HStack space="sm" className="items-start">
            <Icon as={Check} className="text-green-600 mt-0.5" size="sm" />
            <VStack space="xs" className="flex-1">
              <Text className="text-green-900 font-medium">Profile Setup Complete!</Text>
              <Text className="text-green-800 text-sm">
                Your tutoring profile was completed on {onboarding.completedAt.toLocaleDateString()}
                . You're ready to start teaching and accepting students.
              </Text>
            </VStack>
          </HStack>
        </Box>
      )}

      {/* Help Text */}
      <Box className="bg-gray-50 p-4 rounded-lg">
        <HStack space="sm" className="items-start">
          <Icon as={AlertCircle} className="text-gray-500 mt-0.5" size="sm" />
          <VStack space="xs" className="flex-1">
            <Text className="text-gray-700 font-medium text-sm">Need Help?</Text>
            <Text className="text-gray-600 text-sm">
              You can complete these steps in any order, but all required steps must be finished
              before your profile goes live. You can always return to modify your settings later.
            </Text>
          </VStack>
        </HStack>
      </Box>
    </VStack>
  );
};
