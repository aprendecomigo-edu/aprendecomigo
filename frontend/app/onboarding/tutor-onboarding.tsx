import { useRouter } from 'expo-router';
import React, { useEffect, useState } from 'react';

import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Save,
  AlertCircle,
  Clock,
  Lightbulb,
  Target,
  TrendingUp,
  ExternalLink,
} from '@/components/ui/icons';
import { Platform, Dimensions } from 'react-native';

import { TutorSchoolCreationModal } from '@/components/modals/TutorSchoolCreationModal';
import { CourseSelectionManager } from '@/components/onboarding/CourseSelectionManager';
import { EducationalSystemSelector } from '@/components/onboarding/EducationalSystemSelector';
import { AvailabilityStep } from '@/components/profile-wizard/AvailabilityStep';
import { BasicInfoStep } from '@/components/profile-wizard/BasicInfoStep';
import { BiographyStep } from '@/components/profile-wizard/BiographyStep';
import { EducationStep } from '@/components/profile-wizard/EducationStep';
import { ProfilePreviewStep } from '@/components/profile-wizard/ProfilePreviewStep';
import {
  AlertDialog,
  AlertDialogBackdrop,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogBody,
  AlertDialogFooter,
} from '@/components/ui/alert-dialog';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Progress, ProgressFilledTrack } from '@/components/ui/progress';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useTutorOnboarding, TUTOR_ONBOARDING_STEPS } from '@/hooks/useTutorOnboarding';

const { width: screenWidth } = Dimensions.get('window');
const isMobile = Platform.OS !== 'web' || screenWidth < 768;

interface StepProgressIndicatorProps {
  steps: typeof TUTOR_ONBOARDING_STEPS;
  currentStep: number;
  completedSteps: Set<string>;
  onStepClick?: (index: number) => void;
}

const StepProgressIndicator: React.FC<StepProgressIndicatorProps> = ({
  steps,
  currentStep,
  completedSteps,
  onStepClick,
}) => {
  if (isMobile) {
    // Mobile: Show minimal progress bar
    const progressPercentage = ((currentStep + 1) / steps.length) * 100;

    return (
      <VStack space="xs">
        <HStack className="items-center justify-between">
          <Text className="text-sm font-medium text-gray-700">
            Step {currentStep + 1} of {steps.length}
          </Text>
          <Text className="text-sm text-gray-500">{Math.round(progressPercentage)}% Complete</Text>
        </HStack>
        <Progress value={progressPercentage} className="h-2">
          <ProgressFilledTrack className="bg-blue-600" />
        </Progress>
      </VStack>
    );
  }

  // Desktop: Show detailed step navigator
  return (
    <VStack space="sm">
      {steps.map((step, index) => {
        const isCompleted = completedSteps.has(step.id);
        const isCurrent = index === currentStep;
        const canNavigate = index <= currentStep || isCompleted;

        return (
          <Button
            key={step.id}
            variant="ghost"
            onPress={() => canNavigate && onStepClick?.(index)}
            disabled={!canNavigate}
            className={`
              justify-start h-auto py-3 px-4 border rounded-lg
              ${
                isCurrent
                  ? 'border-blue-500 bg-blue-50'
                  : isCompleted
                    ? 'border-green-200 bg-green-50'
                    : 'border-gray-200 bg-white'
              }
              ${canNavigate ? 'hover:bg-gray-50' : 'opacity-50'}
            `}
          >
            <HStack space="sm" className="items-center w-full">
              <Box
                className={`
                  w-8 h-8 rounded-full items-center justify-center
                  ${isCompleted ? 'bg-green-600' : isCurrent ? 'bg-blue-600' : 'bg-gray-300'}
                `}
              >
                {isCompleted ? (
                  <Icon as={CheckCircle2} className="text-white" size="sm" />
                ) : (
                  <Text
                    className={`text-sm font-semibold ${
                      isCurrent ? 'text-white' : 'text-gray-600'
                    }`}
                  >
                    {index + 1}
                  </Text>
                )}
              </Box>

              <VStack className="flex-1" space="xs">
                <Text
                  className={`text-sm font-medium text-left ${
                    isCurrent ? 'text-blue-900' : 'text-gray-900'
                  }`}
                >
                  {step.title}
                </Text>
                <Text
                  className={`text-xs text-left ${isCurrent ? 'text-blue-700' : 'text-gray-600'}`}
                >
                  {step.description}
                </Text>
              </VStack>

              <VStack space="xs" className="items-end">
                {step.isRequired && (
                  <Badge className="bg-red-100">
                    <BadgeText className="text-red-700 text-xs">Required</BadgeText>
                  </Badge>
                )}
                <HStack space="xs" className="items-center">
                  <Icon as={Clock} className="text-gray-400" size="xs" />
                  <Text className="text-gray-500 text-xs">{step.estimatedMinutes}min</Text>
                </HStack>
              </VStack>
            </HStack>
          </Button>
        );
      })}
    </VStack>
  );
};

const OnboardingGuidancePanel: React.FC<{
  guidance?: any;
  currentStepTitle: string;
}> = ({ guidance, currentStepTitle }) => {
  if (!guidance || isMobile) return null;

  return (
    <Card className="border-l-4 border-l-blue-500">
      <CardHeader className="pb-3">
        <HStack space="sm" className="items-center">
          <Icon as={Lightbulb} className="text-blue-600" size="lg" />
          <Heading size="md" className="text-gray-900">
            {currentStepTitle} Tips
          </Heading>
        </HStack>
      </CardHeader>

      <CardContent className="pt-0">
        <VStack space="md">
          {guidance.tips?.length > 0 && (
            <VStack space="sm">
              <Text className="text-gray-700 font-medium text-sm">Key Tips:</Text>
              <VStack space="xs">
                {guidance.tips.slice(0, 3).map((tip: any, index: number) => (
                  <HStack key={index} space="xs" className="items-start">
                    <Icon
                      as={tip.priority === 'high' ? Target : TrendingUp}
                      className={`${
                        tip.priority === 'high' ? 'text-red-500' : 'text-blue-500'
                      } mt-0.5`}
                      size="xs"
                    />
                    <VStack className="flex-1" space="xs">
                      <Text className="text-gray-900 text-sm font-medium">{tip.title}</Text>
                      <Text className="text-gray-600 text-xs">{tip.description}</Text>
                    </VStack>
                  </HStack>
                ))}
              </VStack>
            </VStack>
          )}

          {guidance.recommendations?.length > 0 && (
            <VStack space="sm">
              <Text className="text-gray-700 font-medium text-sm">Recommendations:</Text>
              <VStack space="xs">
                {guidance.recommendations.slice(0, 2).map((rec: any, index: number) => (
                  <HStack key={index} space="xs" className="items-start">
                    <Text className="text-blue-600 text-sm">→</Text>
                    <Text className="text-gray-600 text-sm flex-1">{rec.text}</Text>
                    {rec.url && <Icon as={ExternalLink} className="text-blue-500" size="xs" />}
                  </HStack>
                ))}
              </VStack>
            </VStack>
          )}

          {guidance.estimated_time && (
            <HStack space="xs" className="items-center p-2 bg-blue-50 rounded-md">
              <Icon as={Clock} className="text-blue-600" size="sm" />
              <Text className="text-blue-700 text-sm">
                Estimated time: {guidance.estimated_time} minutes
              </Text>
            </HStack>
          )}
        </VStack>
      </CardContent>
    </Card>
  );
};

export default function TutorOnboardingScreen() {
  const router = useRouter();
  const [showExitDialog, setShowExitDialog] = useState(false);
  const [showSchoolCreationModal, setShowSchoolCreationModal] = useState(false);

  const {
    currentStep,
    onboardingId,
    progress,
    formData,
    selectedEducationalSystem,
    selectedCourses,
    customSubjects,
    availableSystems,
    availableCourses,
    isLoading,
    isSaving,
    isSubmitting,
    error,
    validationErrors,
    stepData,
    completedSteps,
    guidance,
    setCurrentStep,
    nextStep,
    previousStep,
    goToStep,
    updateFormData,
    setSelectedEducationalSystem,
    setSelectedCourses,
    initializeOnboarding,
    saveProgress,
    validateCurrentStep,
    submitOnboarding,
    resetOnboarding,
  } = useTutorOnboarding();

  // Initialize onboarding on mount
  useEffect(() => {
    initializeOnboarding();
  }, [initializeOnboarding]);

  const currentStepConfig = TUTOR_ONBOARDING_STEPS[currentStep];
  const totalSteps = TUTOR_ONBOARDING_STEPS.length;
  const progressPercentage = ((currentStep + 1) / totalSteps) * 100;

  // Handle school creation for tutors
  const handleSchoolCreation = async (data: any) => {
    try {
      updateFormData('school-creation', data);
      setShowSchoolCreationModal(false);

      // Move to next step
      await nextStep();
    } catch (error) {
      if (__DEV__) {
        console.error('Error creating tutor school:', error); // TODO: Review for sensitive data
      }
    }
  };

  // Handle step navigation
  const handleNextStep = async () => {
    if (currentStepConfig.id === 'school-creation') {
      setShowSchoolCreationModal(true);
      return;
    }

    const success = await nextStep();
    if (!success) {
      if (__DEV__) {
        console.error('Failed to move to next step'); // TODO: Review for sensitive data
      }
    }
  };

  const handlePreviousStep = () => {
    previousStep();
  };

  const handleStepClick = (stepIndex: number) => {
    setCurrentStep(stepIndex);
  };

  // Handle completion
  const handleComplete = async () => {
    try {
      const publishingOptions = {
        make_discoverable: true,
        auto_accept_bookings: false,
        notification_preferences: {
          email_notifications: true,
          sms_notifications: false,
          booking_confirmations: true,
          student_messages: true,
        },
        marketing_consent: {
          promotional_emails: true,
          feature_updates: true,
          educational_content: true,
        },
      };

      const result = await submitOnboarding(publishingOptions);

      // Navigate to success screen or dashboard
      router.push({
        pathname: '/onboarding/success',
        query: { type: 'tutor', profileUrl: result.profile_url },
      });
    } catch (error) {
      if (__DEV__) {
        console.error('Error completing onboarding:', error); // TODO: Review for sensitive data
      }
    }
  };

  // Handle exit
  const handleExit = () => {
    if (isSaving || Object.keys(stepData).length > 0) {
      setShowExitDialog(true);
    } else {
      router.back();
    }
  };

  const confirmExit = () => {
    resetOnboarding();
    router.back();
  };

  const saveAndExit = async () => {
    try {
      await saveProgress();
      router.back();
    } catch (error) {
      if (__DEV__) {
        console.error('Error saving before exit:', error); // TODO: Review for sensitive data
      }
    }
  };

  // Render step content
  const renderStepContent = () => {
    if (isLoading) {
      return (
        <VStack className="flex-1 items-center justify-center" space="md">
          <Spinner size="large" />
          <Text className="text-gray-600">Loading...</Text>
        </VStack>
      );
    }

    switch (currentStepConfig.id) {
      case 'school-creation':
        return (
          <VStack className="flex-1 items-center justify-center p-8" space="md">
            <Icon as={CheckCircle2} className="text-blue-600" size="xl" />
            <VStack space="sm" className="items-center">
              <Heading size="lg" className="text-gray-900 text-center">
                Ready to Create Your Practice
              </Heading>
              <Text className="text-gray-600 text-center max-w-md">
                Let's set up your tutoring business profile. This will help organize your services
                and make it easier for students to find you.
              </Text>
            </VStack>
            <Button onPress={() => setShowSchoolCreationModal(true)} className="bg-blue-600">
              <ButtonText className="text-white">Create My Practice</ButtonText>
            </Button>
          </VStack>
        );

      case 'educational-system':
        return (
          <EducationalSystemSelector
            selectedSystemId={selectedEducationalSystem?.id}
            onSystemSelect={setSelectedEducationalSystem}
            onContinue={handleNextStep}
            isLoading={isSaving}
            showContinueButton={false}
          />
        );

      case 'course-selection':
        return (
          <CourseSelectionManager
            selectedCourses={selectedCourses}
            customSubjects={customSubjects}
            onSelectionChange={setSelectedCourses}
            availableCourses={availableCourses}
            isLoadingCourses={isLoading}
            educationalSystemId={selectedEducationalSystem?.id}
            educationalSystemName={selectedEducationalSystem?.name}
            onContinue={handleNextStep}
            showContinueButton={false}
          />
        );

      case 'basic-info':
        return (
          <BasicInfoStep
            formData={stepData['basic-info'] || formData.personal_info || {}}
            onFormDataChange={data => updateFormData('basic-info', { personal_info: data })}
            validationErrors={validationErrors}
            isLoading={isSaving}
          />
        );

      case 'biography':
        return (
          <BiographyStep
            formData={stepData['biography'] || formData.business_profile || {}}
            onFormDataChange={data => updateFormData('biography', { business_profile: data })}
            validationErrors={validationErrors}
            isLoading={isSaving}
          />
        );

      case 'education':
        return (
          <EducationStep
            formData={stepData['education'] || formData.education || {}}
            onFormDataChange={data => updateFormData('education', { education: data })}
            validationErrors={validationErrors}
            isLoading={isSaving}
          />
        );

      case 'availability':
        return (
          <AvailabilityStep
            formData={stepData['availability'] || formData.availability || {}}
            onFormDataChange={data => updateFormData('availability', { availability: data })}
            validationErrors={validationErrors}
            isLoading={isSaving}
          />
        );

      case 'preview':
        return (
          <ProfilePreviewStep
            formData={formData}
            onFormDataChange={data => updateFormData('preview', data)}
            validationErrors={validationErrors}
            isLoading={isSaving}
          />
        );

      default:
        return (
          <VStack className="flex-1 items-center justify-center" space="md">
            <Text className="text-gray-600">Step content not implemented yet</Text>
            <Text className="text-gray-500 text-sm">Current step: {currentStepConfig.id}</Text>
          </VStack>
        );
    }
  };

  if (!currentStepConfig) {
    return (
      <VStack className="flex-1 items-center justify-center" space="md">
        <Spinner size="large" />
        <Text className="text-gray-600">Loading onboarding...</Text>
      </VStack>
    );
  }

  return (
    <Box className="flex-1 bg-gray-50">
      {/* Header */}
      <Box className="bg-white border-b border-gray-200 px-4 py-4">
        <VStack space="md">
          {/* Top Navigation */}
          <HStack className="items-center justify-between">
            <Button
              variant="outline"
              size="sm"
              onPress={handleExit}
              className="flex-row items-center"
            >
              <ButtonIcon as={ArrowLeft} className="text-gray-600 mr-1" />
              <ButtonText className="text-gray-600">Exit</ButtonText>
            </Button>

            <HStack space="sm" className="items-center">
              {/* Save Status */}
              {isSaving && (
                <HStack space="xs" className="items-center">
                  <Spinner size="small" />
                  <Text className="text-gray-500 text-sm">Saving...</Text>
                </HStack>
              )}

              <Button
                variant="outline"
                size="sm"
                onPress={saveProgress}
                disabled={isSaving}
                className="flex-row items-center"
              >
                <ButtonIcon as={Save} className="text-blue-600 mr-1" />
                <ButtonText className="text-blue-600">Save Progress</ButtonText>
              </Button>
            </HStack>
          </HStack>

          {/* Progress */}
          <StepProgressIndicator
            steps={TUTOR_ONBOARDING_STEPS}
            currentStep={currentStep}
            completedSteps={completedSteps}
            onStepClick={handleStepClick}
          />

          {/* Current Step Info */}
          <VStack space="xs">
            <HStack space="sm" className="items-center">
              <Heading size="lg" className="text-gray-900">
                {currentStepConfig.title}
              </Heading>
              {currentStepConfig.isRequired && (
                <Badge className="bg-red-100">
                  <BadgeText className="text-red-700 text-xs">Required</BadgeText>
                </Badge>
              )}
            </HStack>
            <Text className="text-gray-600">{currentStepConfig.description}</Text>
          </VStack>
        </VStack>
      </Box>

      {/* Content Area */}
      <HStack className="flex-1">
        {/* Main Content */}
        <Box className="flex-1">
          {error && (
            <Box className="bg-red-50 border-l-4 border-red-400 p-4 m-4">
              <HStack space="sm" className="items-center">
                <Icon as={AlertCircle} size={20} className="text-red-500" />
                <Text className="text-red-700">{error}</Text>
              </HStack>
            </Box>
          )}

          {renderStepContent()}
        </Box>

        {/* Guidance Panel (Desktop only) */}
        {!isMobile && (
          <Box className="w-80 border-l border-gray-200 bg-white p-6">
            <OnboardingGuidancePanel
              guidance={guidance}
              currentStepTitle={currentStepConfig.title}
            />
          </Box>
        )}
      </HStack>

      {/* Footer Navigation */}
      <Box className="bg-white border-t border-gray-200 px-4 py-4">
        <HStack className="items-center justify-between">
          <Button
            variant="outline"
            onPress={handlePreviousStep}
            disabled={currentStep === 0 || isSaving}
            className="flex-row items-center"
          >
            <ButtonIcon as={ArrowLeft} className="text-gray-600 mr-1" />
            <ButtonText className="text-gray-600">Previous</ButtonText>
          </Button>

          <HStack space="sm">
            {currentStep < totalSteps - 1 ? (
              <Button
                onPress={handleNextStep}
                disabled={isSaving || isSubmitting}
                className="bg-blue-600 hover:bg-blue-700 flex-row items-center"
              >
                <ButtonText className="text-white">Next Step</ButtonText>
                <ButtonIcon as={ArrowRight} className="text-white ml-1" />
              </Button>
            ) : (
              <Button
                onPress={handleComplete}
                disabled={isSaving || isSubmitting}
                className="bg-green-600 hover:bg-green-700 flex-row items-center"
              >
                {isSubmitting ? (
                  <Spinner size="small" color="white" />
                ) : (
                  <>
                    <ButtonIcon as={CheckCircle2} className="text-white mr-1" />
                    <ButtonText className="text-white">Complete Setup</ButtonText>
                  </>
                )}
              </Button>
            )}
          </HStack>
        </HStack>
      </Box>

      {/* School Creation Modal */}
      <TutorSchoolCreationModal
        isOpen={showSchoolCreationModal}
        onClose={() => setShowSchoolCreationModal(false)}
        onSubmit={handleSchoolCreation}
        userName={formData.personal_info?.first_name || 'Your'}
        isLoading={isSaving}
      />

      {/* Exit Confirmation Dialog */}
      <AlertDialog isOpen={showExitDialog} onClose={() => setShowExitDialog(false)}>
        <AlertDialogBackdrop />
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <Heading size="lg" className="text-gray-900">
              Save Your Progress?
            </Heading>
          </AlertDialogHeader>
          <AlertDialogBody>
            <VStack space="sm">
              <Text className="text-gray-600">
                You have made progress on your profile. Would you like to save your progress before
                leaving?
              </Text>
              <Text className="text-gray-500 text-sm">
                You can return to complete your profile setup later.
              </Text>
            </VStack>
          </AlertDialogBody>
          <AlertDialogFooter>
            <HStack space="sm" className="w-full">
              <Button variant="outline" onPress={confirmExit} className="flex-1">
                <ButtonText>Exit Without Saving</ButtonText>
              </Button>
              <Button onPress={saveAndExit} className="flex-1 bg-blue-600">
                <ButtonText>Save & Exit</ButtonText>
              </Button>
            </HStack>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Box>
  );
}
