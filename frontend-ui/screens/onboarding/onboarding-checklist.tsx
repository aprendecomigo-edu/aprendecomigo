import { 
  CheckCircle, 
  Circle, 
  Building2, 
  UserPlus, 
  GraduationCap, 
  CreditCard, 
  Calendar,
  ArrowRight,
  Skip,
  HelpCircle,
  ExternalLink
} from 'lucide-react-native';
import React, { useState } from 'react';
import { Platform, Dimensions } from 'react-native';
import useRouter from '@unitools/router';

import { useOnboarding, ONBOARDING_STEPS } from '@/hooks/useOnboarding';
import { OnboardingProgress } from './onboarding-progress';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Divider } from '@/components/ui/divider';
import {
  AlertDialog,
  AlertDialogBackdrop,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogCloseButton,
  AlertDialogFooter,
  AlertDialogBody,
} from '@/components/ui/alert-dialog';

const { width: screenWidth } = Dimensions.get('window');
const isMobile = Platform.OS !== 'web' || screenWidth < 768;

// Map step IDs to icons
const stepIcons: Record<string, any> = {
  complete_school_profile: Building2,
  invite_first_teacher: UserPlus,
  add_first_student: GraduationCap,
  setup_billing: CreditCard,
  create_first_schedule: Calendar,
};

interface OnboardingChecklistProps {
  onStepAction?: (stepId: string, action: 'start' | 'skip') => void;
  showProgress?: boolean;
  className?: string;
}

export const OnboardingChecklist: React.FC<OnboardingChecklistProps> = ({
  onStepAction,
  showProgress = true,
  className = '',
}) => {
  const router = useRouter();
  const { 
    progress, 
    completeStep, 
    skipStep, 
    createOnboardingTask,
    isLoading 
  } = useOnboarding();
  
  const [selectedStep, setSelectedStep] = useState<string | null>(null);
  const [showSkipDialog, setShowSkipDialog] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const completedSteps = progress?.completed_steps || [];
  const skippedSteps = progress?.skipped_steps || [];
  const completionPercentage = progress?.completion_percentage || 0;

  const getStepStatus = (stepId: string) => {
    if (completedSteps.includes(stepId)) return 'completed';
    if (skippedSteps.includes(stepId)) return 'skipped';
    return 'pending';
  };

  const handleStepStart = async (stepId: string) => {
    if (actionLoading) return;

    setActionLoading(stepId);
    
    try {
      // Create task for this step
      const step = ONBOARDING_STEPS.find(s => s.id === stepId);
      if (step) {
        await createOnboardingTask({
          title: step.taskTitle,
          description: step.taskDescription,
          priority: 'high',
          task_type: 'onboarding',
          due_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days from now
        });
      }

      // Handle step-specific navigation
      switch (stepId) {
        case 'complete_school_profile':
          router.push('/settings');
          break;
        case 'invite_first_teacher':
          // This will be handled by the AddFirstTeacherFlow component
          if (onStepAction) {
            onStepAction(stepId, 'start');
          }
          break;
        case 'add_first_student':
          // This will be handled by the AddFirstStudentFlow component
          if (onStepAction) {
            onStepAction(stepId, 'start');
          }
          break;
        case 'setup_billing':
          router.push('/purchase');
          break;
        case 'create_first_schedule':
          router.push('/calendar');
          break;
        default:
          if (onStepAction) {
            onStepAction(stepId, 'start');
          }
      }
    } catch (error) {
      console.error('Error starting step:', error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleStepSkip = (stepId: string) => {
    setSelectedStep(stepId);
    setShowSkipDialog(true);
  };

  const confirmSkipStep = async () => {
    if (!selectedStep || actionLoading) return;

    setActionLoading(selectedStep);
    
    try {
      await skipStep(selectedStep);
      
      if (onStepAction) {
        onStepAction(selectedStep, 'skip');
      }
    } catch (error) {
      console.error('Error skipping step:', error);
    } finally {
      setActionLoading(null);
      setShowSkipDialog(false);
      setSelectedStep(null);
    }
  };

  const getStepIcon = (stepId: string) => {
    const status = getStepStatus(stepId);
    const IconComponent = stepIcons[stepId] || HelpCircle;

    if (status === 'completed') {
      return <Icon as={CheckCircle} size={24} className="text-green-500" />;
    }

    return (
      <Icon 
        as={IconComponent} 
        size={24} 
        className={
          status === 'skipped' ? 'text-gray-400' :
          'text-blue-600'
        } 
      />
    );
  };

  const getStepCardStyle = (stepId: string) => {
    const status = getStepStatus(stepId);
    
    switch (status) {
      case 'completed':
        return 'bg-green-50 border-green-200';
      case 'skipped':
        return 'bg-gray-50 border-gray-200';
      default:
        return 'bg-white border-gray-200 hover:border-blue-300 hover:shadow-md';
    }
  };

  if (isLoading) {
    return (
      <Box className={`flex items-center justify-center p-8 ${className}`}>
        <VStack space="md" className="items-center">
          <Spinner size="large" />
          <Text className="text-gray-600">Loading onboarding checklist...</Text>
        </VStack>
      </Box>
    );
  }

  return (
    <VStack space="lg" className={className}>
      {/* Progress Section */}
      {showProgress && (
        <OnboardingProgress
          completedSteps={completedSteps}
          skippedSteps={skippedSteps}
          completionPercentage={completionPercentage}
          compact={isMobile}
        />
      )}

      {/* Checklist Header */}
      <VStack space="sm">
        <Heading size={isMobile ? "lg" : "xl"} className="text-gray-900">
          Setup Checklist
        </Heading>
        <Text className="text-gray-600">
          Follow these steps to configure your school and start using the platform effectively
        </Text>
      </VStack>

      {/* Steps List */}
      <VStack space="md">
        {ONBOARDING_STEPS.map((step, index) => {
          const status = getStepStatus(step.id);
          const isLoading = actionLoading === step.id;
          
          return (
            <Card 
              key={step.id}
              className={`${getStepCardStyle(step.id)} transition-all duration-200`}
            >
              <VStack space="md" className="p-6">
                {/* Step Header */}
                <HStack space="md" className="items-start">
                  <Box className="mt-1">
                    {getStepIcon(step.id)}
                  </Box>
                  
                  <VStack className="flex-1" space="xs">
                    <HStack className="items-center justify-between">
                      <Heading size="md" className="text-gray-900">
                        {step.name}
                      </Heading>
                      
                      {status === 'completed' && (
                        <Badge className="bg-green-100">
                          <BadgeText className="text-green-700">
                            Completed
                          </BadgeText>
                        </Badge>
                      )}
                      
                      {status === 'skipped' && (
                        <Badge className="bg-gray-100">
                          <BadgeText className="text-gray-600">
                            Skipped
                          </BadgeText>
                        </Badge>
                      )}
                    </HStack>
                    
                    <Text className="text-gray-600">
                      {step.description}
                    </Text>
                  </VStack>
                </HStack>

                {/* Step Actions */}
                {status === 'pending' && (
                  <>
                    <Divider className="my-2" />
                    <HStack space="sm" className={isMobile ? 'flex-col space-y-2' : ''}>
                      <Button
                        size={isMobile ? "md" : "sm"}
                        onPress={() => handleStepStart(step.id)}
                        isDisabled={isLoading}
                        className={`bg-blue-600 hover:bg-blue-700 ${isMobile ? 'flex-1' : ''}`}
                        testID={`start-step-${step.id}`}
                      >
                        {isLoading ? (
                          <Spinner size="small" color="white" />
                        ) : (
                          <>
                            <ButtonText className="text-white">
                              Start Step
                            </ButtonText>
                            <ButtonIcon as={ArrowRight} className="text-white ml-1" />
                          </>
                        )}
                      </Button>
                      
                      <Button
                        variant="outline"
                        size={isMobile ? "md" : "sm"}
                        onPress={() => handleStepSkip(step.id)}
                        isDisabled={isLoading}
                        className={`border-gray-300 ${isMobile ? 'flex-1' : ''}`}
                        testID={`skip-step-${step.id}`}
                      >
                        <ButtonIcon as={Skip} className="text-gray-600 mr-1" />
                        <ButtonText className="text-gray-600">
                          Skip
                        </ButtonText>
                      </Button>
                    </HStack>
                  </>
                )}

                {/* Completed Step Actions */}
                {status === 'completed' && (
                  <>
                    <Divider className="my-2" />
                    <HStack>
                      <Button
                        variant="outline"
                        size="sm"
                        onPress={() => handleStepStart(step.id)}
                        className="border-green-300"
                      >
                        <ButtonIcon as={ExternalLink} className="text-green-600 mr-1" />
                        <ButtonText className="text-green-600">
                          Review
                        </ButtonText>
                      </Button>
                    </HStack>
                  </>
                )}

                {/* Skipped Step Actions */}
                {status === 'skipped' && (
                  <>
                    <Divider className="my-2" />
                    <HStack>
                      <Button
                        variant="outline"
                        size="sm"
                        onPress={() => handleStepStart(step.id)}
                        className="border-gray-300"
                      >
                        <ButtonText className="text-gray-600">
                          Complete Now
                        </ButtonText>
                      </Button>
                    </HStack>
                  </>
                )}
              </VStack>
            </Card>
          );
        })}
      </VStack>

      {/* Completion Message */}
      {completionPercentage >= 100 && (
        <Card className="bg-gradient-to-r from-green-50 to-blue-50 border-green-200">
          <VStack space="md" className="p-6 text-center">
            <Icon as={CheckCircle} size={48} className="text-green-500 mx-auto" />
            <VStack space="sm">
              <Heading size="lg" className="text-gray-900">
                Congratulations! 🎉
              </Heading>
              <Text className="text-gray-700">
                You've completed all the onboarding steps. Your school is fully set up and ready to use!
              </Text>
            </VStack>
            <Button
              onPress={() => router.push('/(school-admin)/dashboard')}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <ButtonText className="text-white">
                Go to Dashboard
              </ButtonText>
              <ButtonIcon as={ArrowRight} className="text-white ml-2" />
            </Button>
          </VStack>
        </Card>
      )}

      {/* Skip Step Confirmation Dialog */}
      <AlertDialog isOpen={showSkipDialog} onClose={() => setShowSkipDialog(false)}>
        <AlertDialogBackdrop />
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <Heading size="lg" className="text-gray-900">
              Skip This Step?
            </Heading>
          </AlertDialogHeader>
          <AlertDialogBody>
            {selectedStep && (
              <VStack space="sm">
                <Text className="text-gray-600">
                  Are you sure you want to skip "{ONBOARDING_STEPS.find(s => s.id === selectedStep)?.name}"?
                </Text>
                <Text className="text-gray-500 text-sm">
                  You can always complete this step later from your dashboard.
                </Text>
              </VStack>
            )}
          </AlertDialogBody>
          <AlertDialogFooter>
            <HStack space="sm" className="w-full">
              <Button
                variant="outline"
                onPress={() => setShowSkipDialog(false)}
                className="flex-1"
              >
                <ButtonText>Cancel</ButtonText>
              </Button>
              <Button
                onPress={confirmSkipStep}
                isDisabled={!!actionLoading}
                className="flex-1 bg-gray-600"
              >
                <ButtonText>
                  {actionLoading ? 'Skipping...' : 'Skip Step'}
                </ButtonText>
              </Button>
            </HStack>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </VStack>
  );
};