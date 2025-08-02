import useRouter from '@unitools/router';
import {
  User,
  FileText,
  GraduationCap,
  BookOpen,
  DollarSign,
  Calendar,
  Eye,
  ArrowLeft,
  ArrowRight,
  Save,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react-native';
import React, { useState, useEffect, useRef } from 'react';
import { Platform, Dimensions } from 'react-native';

import { AvailabilityStep } from '@/components/profile-wizard/availability-step';
import { BasicInfoStep } from '@/components/profile-wizard/basic-info-step';
import { BiographyStep } from '@/components/profile-wizard/biography-step';
import { EducationStep } from '@/components/profile-wizard/education-step';
import { ProfileCompletionTracker } from '@/components/profile-wizard/profile-completion-tracker';
import { ProfilePreviewStep } from '@/components/profile-wizard/profile-preview-step';
import { RatesStep } from '@/components/profile-wizard/rates-step';
import { SubjectsStep } from '@/components/profile-wizard/subjects-step';
import {
  AlertDialog,
  AlertDialogBackdrop,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogBody,
} from '@/components/ui/alert-dialog';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Progress, ProgressFilledTrack } from '@/components/ui/progress';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { WizardNavigation } from '@/components/wizard/wizard-navigation';
import WizardErrorBoundary from '@/components/wizard/wizard-error-boundary';
import { useProfileWizard } from '@/hooks/useProfileWizard';

const { width: screenWidth } = Dimensions.get('window');
const isMobile = Platform.OS !== 'web' || screenWidth < 768;

// Wizard step configuration
export const WIZARD_STEPS = [
  {
    id: 'basic-info',
    title: 'Basic Information',
    description: 'Profile photo, name, title, and contact details',
    icon: User,
    component: BasicInfoStep,
    isRequired: true,
  },
  {
    id: 'biography',
    title: 'Professional Biography',
    description: 'Tell students about your teaching approach and experience',
    icon: FileText,
    component: BiographyStep,
    isRequired: true,
  },
  {
    id: 'education',
    title: 'Education Background',
    description: 'Degrees, certifications, and qualifications',
    icon: GraduationCap,
    component: EducationStep,
    isRequired: true,
  },
  {
    id: 'subjects',
    title: 'Teaching Subjects',
    description: 'Subjects you teach and grade levels you work with',
    icon: BookOpen,
    component: SubjectsStep,
    isRequired: true,
  },
  {
    id: 'rates',
    title: 'Rates & Pricing',
    description: 'Set your hourly rates and package options',
    icon: DollarSign,
    component: RatesStep,
    isRequired: true,
  },
  {
    id: 'availability',
    title: 'Availability',
    description: 'Weekly schedule and booking preferences',
    icon: Calendar,
    component: AvailabilityStep,
    isRequired: true,
  },
  {
    id: 'preview',
    title: 'Profile Preview',
    description: 'Review how your profile appears to students',
    icon: Eye,
    component: ProfilePreviewStep,
    isRequired: false,
  },
];

interface TeacherProfileWizardProps {
  onComplete?: () => void;
  onExit?: () => void;
  resumeFromStep?: number;
}

export const TeacherProfileWizard: React.FC<TeacherProfileWizardProps> = ({
  onComplete,
  onExit,
  resumeFromStep = 0,
}) => {
  const router = useRouter();
  const autoSaveInterval = useRef<NodeJS.Timeout | null>(null);

  const {
    currentStep,
    formData,
    completionData,
    isLoading,
    isSaving,
    error,
    validationErrors,
    setCurrentStep,
    updateFormData,
    validateStep,
    saveProgress,
    submitProfile,
    loadProgress,
  } = useProfileWizard();

  const [showExitDialog, setShowExitDialog] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Computed state values
  const isAutoSaving = isSaving && hasUnsavedChanges;
  const hasCriticalErrors = error !== null && !isLoading;

  // Initialize wizard
  useEffect(() => {
    const initializeWizard = async () => {
      try {
        await loadProgress();
        if (resumeFromStep > 0) {
          setCurrentStep(resumeFromStep);
        }
      } catch (error) {
        console.error('Error initializing wizard:', error);
      }
    };

    initializeWizard();
  }, [loadProgress, resumeFromStep, setCurrentStep]);

  // Auto-save functionality
  useEffect(() => {
    if (hasUnsavedChanges && !isSaving) {
      // Clear existing timeout
      if (autoSaveInterval.current) {
        clearTimeout(autoSaveInterval.current);
      }

      // Set new timeout for auto-save
      autoSaveInterval.current = setTimeout(async () => {
        try {
          await saveProgress();
          setHasUnsavedChanges(false);
        } catch (error) {
          console.error('Auto-save failed:', error);
        }
      }, 30000); // Auto-save every 30 seconds
    }

    return () => {
      if (autoSaveInterval.current) {
        clearTimeout(autoSaveInterval.current);
      }
    };
  }, [hasUnsavedChanges, isSaving, saveProgress]);

  // Handle form data changes
  const handleFormDataChange = (stepData: any) => {
    updateFormData(stepData);
    setHasUnsavedChanges(true);
  };

  // Handle next step
  const handleNextStep = async () => {
    try {
      const isValid = await validateStep(currentStep);
      if (!isValid) {
        return;
      }

      // Save progress before moving to next step
      await saveProgress();
      setHasUnsavedChanges(false);

      if (currentStep < WIZARD_STEPS.length - 1) {
        setCurrentStep(currentStep + 1);
      } else {
        // Final step - submit profile
        await handleComplete();
      }
    } catch (error) {
      console.error('Error moving to next step:', error);
    }
  };

  // Handle previous step
  const handlePreviousStep = async () => {
    if (hasUnsavedChanges) {
      await saveProgress();
      setHasUnsavedChanges(false);
    }

    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  // Handle manual save
  const handleSaveProgress = async () => {
    try {
      await saveProgress();
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error('Error saving progress:', error);
    }
  };

  // Handle wizard completion
  const handleComplete = async () => {
    try {
      await submitProfile();

      if (onComplete) {
        onComplete();
      } else {
        // Default navigation to dashboard
        router.push('/(school-admin)/dashboard');
      }
    } catch (error) {
      console.error('Error completing profile wizard:', error);
    }
  };

  // Handle exit wizard
  const handleExitWizard = () => {
    if (hasUnsavedChanges) {
      setShowExitDialog(true);
    } else {
      if (onExit) {
        onExit();
      } else {
        router.back();
      }
    }
  };

  // Confirm exit without saving
  const confirmExit = () => {
    setShowExitDialog(false);
    if (onExit) {
      onExit();
    } else {
      router.back();
    }
  };

  // Save and exit
  const saveAndExit = async () => {
    try {
      await saveProgress();
      setShowExitDialog(false);
      if (onExit) {
        onExit();
      } else {
        router.back();
      }
    } catch (error) {
      console.error('Error saving before exit:', error);
    }
  };

  // Error boundary handlers
  const handleErrorBoundaryReset = () => {
    // Clear local state and try to reload from the hook
    setHasUnsavedChanges(false);
    setShowExitDialog(false);
    loadProgress().catch(console.error);
  };

  const handleErrorBoundarySaveAndExit = async () => {
    try {
      // Attempt to save current progress before exiting
      await saveProgress();
    } catch (error) {
      console.error('Failed to save progress during error recovery:', error);
    } finally {
      // Exit regardless of save success
      if (onExit) {
        onExit();
      } else {
        router.back();
      }
    }
  };

  const handleErrorBoundaryGoToDashboard = () => {
    // Navigate to dashboard without saving
    router.push('/(school-admin)/dashboard');
  };

  const currentStepConfig = WIZARD_STEPS[currentStep];
  const StepComponent = currentStepConfig?.component;
  const progressPercentage = ((currentStep + 1) / WIZARD_STEPS.length) * 100;

  if (isLoading) {
    return (
      <Box className="flex-1 items-center justify-center p-8">
        <VStack space="md" className="items-center">
          <Spinner size="large" />
          <Text className="text-gray-600">Loading your profile...</Text>
        </VStack>
      </Box>
    );
  }

  return (
    <WizardErrorBoundary
      onReset={handleErrorBoundaryReset}
      onSaveAndExit={handleErrorBoundarySaveAndExit}
      onGoToDashboard={handleErrorBoundaryGoToDashboard}
      maxRetries={3}
    >
      <Box className="flex-1 bg-gray-50">
        {/* Header */}
        <Box className="bg-white border-b border-gray-200 px-4 py-4">
          <VStack space="md">
            {/* Top Navigation */}
            <HStack className="items-center justify-between">
              <Button
                variant="outline"
                size="sm"
                onPress={handleExitWizard}
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

                {hasUnsavedChanges && !isSaving && (
                  <Button
                    variant="outline"
                    size="sm"
                    onPress={handleSaveProgress}
                    className="flex-row items-center"
                  >
                    <ButtonIcon as={Save} className="text-blue-600 mr-1" />
                    <ButtonText className="text-blue-600">Save</ButtonText>
                  </Button>
                )}

                {/* Profile Completion */}
                <ProfileCompletionTracker
                  completionData={completionData || undefined}
                  compact={isMobile}
                />
              </HStack>
            </HStack>

            {/* Progress Bar */}
            <VStack space="xs">
              <HStack className="items-center justify-between">
                <Text className="text-sm font-medium text-gray-700">
                  Step {currentStep + 1} of {WIZARD_STEPS.length}
                </Text>
                <Text className="text-sm text-gray-500">
                  {Math.round(progressPercentage)}% Complete
                </Text>
              </HStack>
              <Progress value={progressPercentage} className="h-2">
                <ProgressFilledTrack className="bg-blue-600" />
              </Progress>
            </VStack>

            {/* Current Step Info */}
            <VStack space="xs">
              <HStack space="sm" className="items-center">
                <Icon as={currentStepConfig.icon} size={20} className="text-blue-600" />
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

        {/* Wizard Navigation - Desktop */}
        {!isMobile && (
          <WizardNavigation
            steps={WIZARD_STEPS}
            currentStep={currentStep}
            onStepClick={setCurrentStep}
            completionData={completionData || undefined}
            hasErrors={hasCriticalErrors}
          />
        )}

        {/* Step Content */}
        <Box className="flex-1">
          {error && (
            <Box className="bg-red-50 border-l-4 border-red-400 p-4 mx-4 mt-4">
              <HStack space="sm" className="items-center">
                <Icon as={AlertCircle} size={20} className="text-red-500" />
                <Text className="text-red-700">{error}</Text>
              </HStack>
            </Box>
          )}

          {StepComponent && (
            <StepComponent
              formData={formData}
              onFormDataChange={handleFormDataChange}
              validationErrors={validationErrors}
              isLoading={isSaving}
            />
          )}
        </Box>

        {/* Footer Navigation */}
        <Box className="bg-white border-t border-gray-200 px-4 py-4">
          <HStack className="items-center justify-between">
            <Button
              variant="outline"
              onPress={handlePreviousStep}
              isDisabled={currentStep === 0 || isSaving}
              className="flex-row items-center"
            >
              <ButtonIcon as={ArrowLeft} className="text-gray-600 mr-1" />
              <ButtonText className="text-gray-600">Previous</ButtonText>
            </Button>

            <HStack space="sm">
              {currentStep < WIZARD_STEPS.length - 1 ? (
                <Button
                  onPress={handleNextStep}
                  isDisabled={isSaving || isAutoSaving || hasCriticalErrors}
                  className="bg-blue-600 hover:bg-blue-700 flex-row items-center"
                >
                  <ButtonText className="text-white">Next Step</ButtonText>
                  <ButtonIcon as={ArrowRight} className="text-white ml-1" />
                </Button>
              ) : (
                <Button
                  onPress={handleComplete}
                  isDisabled={isSaving || isAutoSaving || hasCriticalErrors}
                  className="bg-green-600 hover:bg-green-700 flex-row items-center"
                >
                  {isSaving || isAutoSaving ? (
                    <Spinner size="small" color="white" />
                  ) : (
                    <>
                      <ButtonIcon as={CheckCircle2} className="text-white mr-1" />
                      <ButtonText className="text-white">Complete Profile</ButtonText>
                    </>
                  )}
                </Button>
              )}
            </HStack>
          </HStack>
        </Box>

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
                  You have unsaved changes to your profile. Would you like to save your progress
                  before leaving?
                </Text>
                <Text className="text-gray-500 text-sm">
                  You can return to complete your profile later.
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
    </WizardErrorBoundary>
  );
};
