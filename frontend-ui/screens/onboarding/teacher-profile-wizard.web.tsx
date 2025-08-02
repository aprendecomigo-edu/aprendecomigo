import React from 'react';

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
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Progress, ProgressFilledTrack } from '@/components/ui/progress';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { WizardNavigation } from '@/components/wizard/WizardNavigation';
import WizardErrorBoundary from '@/components/wizard/WizardErrorBoundary';

import {
  TeacherProfileWizardProps,
  useTeacherProfileWizard,
  WIZARD_STEPS,
  WizardIcons,
} from './teacher-profile-wizard-common';

const { ArrowLeft, ArrowRight, Save, AlertCircle, CheckCircle2 } = WizardIcons;

export const TeacherProfileWizard: React.FC<TeacherProfileWizardProps> = ({
  onComplete,
  onExit,
  resumeFromStep = 0,
}) => {
  const {
    currentStep,
    formData,
    completionData,
    isLoading,
    isSaving,
    error,
    validationErrors,
    showExitDialog,
    setShowExitDialog,
    hasUnsavedChanges,
    isAutoSaving,
    hasCriticalErrors,
    currentStepConfig,
    StepComponent,
    progressPercentage,
    handleFormDataChange,
    handleNextStep,
    handlePreviousStep,
    handleSaveProgress,
    handleComplete,
    handleExitWizard,
    confirmExit,
    saveAndExit,
    handleErrorBoundaryReset,
    handleErrorBoundarySaveAndExit,
    handleErrorBoundaryGoToDashboard,
    setCurrentStep,
  } = useTeacherProfileWizard({ onComplete, onExit, resumeFromStep });

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
        {/* Header - Desktop Layout */}
        <Box className="bg-white border-b border-gray-200 px-6 py-6">
          <VStack space="lg">
            {/* Top Navigation */}
            <HStack className="items-center justify-between">
              <Button
                variant="outline"
                size="md"
                onPress={handleExitWizard}
                className="flex-row items-center"
              >
                <ButtonIcon as={ArrowLeft} className="text-gray-600 mr-2" />
                <ButtonText className="text-gray-600">Exit Wizard</ButtonText>
              </Button>

              <HStack space="lg" className="items-center">
                {/* Save Status */}
                {isSaving && (
                  <HStack space="sm" className="items-center">
                    <Spinner size="small" />
                    <Text className="text-gray-500">Auto-saving...</Text>
                  </HStack>
                )}

                {hasUnsavedChanges && !isSaving && (
                  <Button
                    variant="outline"
                    size="md"
                    onPress={handleSaveProgress}
                    className="flex-row items-center"
                  >
                    <ButtonIcon as={Save} className="text-blue-600 mr-2" />
                    <ButtonText className="text-blue-600">Save Progress</ButtonText>
                  </Button>
                )}

                {/* Profile Completion - More detailed on desktop */}
                <Box className="bg-gray-50 rounded-lg p-3">
                  <Text className="text-sm font-medium text-gray-700 mb-1">Profile Completion</Text>
                  <Text className="text-xs text-gray-500">
                    {Math.round(progressPercentage)}% Complete
                  </Text>
                </Box>
              </HStack>
            </HStack>

            {/* Progress Bar */}
            <VStack space="sm">
              <HStack className="items-center justify-between">
                <Text className="text-lg font-semibold text-gray-800">
                  Step {currentStep + 1} of {WIZARD_STEPS.length}
                </Text>
                <Text className="text-sm text-gray-500">
                  {Math.round(progressPercentage)}% Complete
                </Text>
              </HStack>
              <Progress value={progressPercentage} className="h-3">
                <ProgressFilledTrack className="bg-blue-600" />
              </Progress>
            </VStack>

            {/* Current Step Info */}
            <VStack space="sm">
              <HStack space="md" className="items-center">
                <Box className="bg-blue-100 rounded-lg p-3">
                  <Icon as={currentStepConfig.icon} size={24} className="text-blue-600" />
                </Box>
                <VStack className="flex-1">
                  <HStack space="sm" className="items-center">
                    <Heading size="xl" className="text-gray-900">
                      {currentStepConfig.title}
                    </Heading>
                    {currentStepConfig.isRequired && (
                      <Badge className="bg-red-100">
                        <BadgeText className="text-red-700 text-xs">Required</BadgeText>
                      </Badge>
                    )}
                  </HStack>
                  <Text className="text-gray-600 text-base">{currentStepConfig.description}</Text>
                </VStack>
              </HStack>
            </VStack>
          </VStack>
        </Box>

        {/* Main Content Area with Sidebar Navigation */}
        <HStack className="flex-1">
          {/* Desktop Wizard Navigation Sidebar */}
          <Box className="w-80 bg-white border-r border-gray-200">
            <WizardNavigation
              steps={WIZARD_STEPS}
              currentStep={currentStep}
              onStepClick={setCurrentStep}
              completionData={completionData || undefined}
              hasErrors={hasCriticalErrors}
            />
          </Box>

          {/* Step Content */}
          <VStack className="flex-1">
            {error && (
              <Box className="bg-red-50 border-l-4 border-red-400 p-4 mx-6 mt-6">
                <HStack space="sm" className="items-center">
                  <Icon as={AlertCircle} size={20} className="text-red-500" />
                  <Text className="text-red-700">{error}</Text>
                </HStack>
              </Box>
            )}

            <Box className="flex-1 p-6">
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
            <Box className="bg-white border-t border-gray-200 px-6 py-4">
              <HStack className="items-center justify-between">
                <Button
                  variant="outline"
                  size="lg"
                  onPress={handlePreviousStep}
                  isDisabled={currentStep === 0 || isSaving}
                  className="flex-row items-center"
                >
                  <ButtonIcon as={ArrowLeft} className="text-gray-600 mr-2" />
                  <ButtonText className="text-gray-600">Previous Step</ButtonText>
                </Button>

                <HStack space="md">
                  {currentStep < WIZARD_STEPS.length - 1 ? (
                    <Button
                      size="lg"
                      onPress={handleNextStep}
                      isDisabled={isSaving || isAutoSaving || hasCriticalErrors}
                      className="bg-blue-600 hover:bg-blue-700 flex-row items-center px-8"
                    >
                      <ButtonText className="text-white font-medium">Continue</ButtonText>
                      <ButtonIcon as={ArrowRight} className="text-white ml-2" />
                    </Button>
                  ) : (
                    <Button
                      size="lg"
                      onPress={handleComplete}
                      isDisabled={isSaving || isAutoSaving || hasCriticalErrors}
                      className="bg-green-600 hover:bg-green-700 flex-row items-center px-8"
                    >
                      {isSaving || isAutoSaving ? (
                        <Spinner size="small" color="white" />
                      ) : (
                        <>
                          <ButtonIcon as={CheckCircle2} className="text-white mr-2" />
                          <ButtonText className="text-white font-medium">Complete Profile</ButtonText>
                        </>
                      )}
                    </Button>
                  )}
                </HStack>
              </HStack>
            </Box>
          </VStack>
        </HStack>

        {/* Exit Confirmation Dialog */}
        <AlertDialog isOpen={showExitDialog} onClose={() => setShowExitDialog(false)}>
          <AlertDialogBackdrop />
          <AlertDialogContent className="max-w-lg">
            <AlertDialogHeader>
              <Heading size="xl" className="text-gray-900">
                Save Your Progress?
              </Heading>
            </AlertDialogHeader>
            <AlertDialogBody>
              <VStack space="md">
                <Text className="text-gray-600 text-base">
                  You have unsaved changes to your profile. Would you like to save your progress
                  before leaving the wizard?
                </Text>
                <Text className="text-gray-500 text-sm">
                  You can return to complete your profile later from your dashboard.
                </Text>
              </VStack>
            </AlertDialogBody>
            <AlertDialogFooter>
              <HStack space="md" className="w-full">
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