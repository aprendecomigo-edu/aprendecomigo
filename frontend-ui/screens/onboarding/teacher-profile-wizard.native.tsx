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
import WizardErrorBoundary from '@/components/wizard/wizard-error-boundary';

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
        {/* Mobile Header */}
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

                {/* Compact completion indicator */}
                <Box className="bg-gray-100 rounded-full px-3 py-1">
                  <Text className="text-xs font-medium text-gray-600">
                    {Math.round(progressPercentage)}%
                  </Text>
                </Box>
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
              <Text className="text-gray-600 text-sm">{currentStepConfig.description}</Text>
            </VStack>
          </VStack>
        </Box>

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

        {/* Mobile Footer Navigation */}
        <Box className="bg-white border-t border-gray-200 px-4 py-4">
          <VStack space="sm">
            {/* Step indicators for mobile */}
            <HStack className="justify-center" space="xs">
              {WIZARD_STEPS.map((_, index) => (
                <Box
                  key={index}
                  className={`w-2 h-2 rounded-full ${
                    index === currentStep
                      ? 'bg-blue-600'
                      : index < currentStep
                      ? 'bg-green-500'
                      : 'bg-gray-300'
                  }`}
                />
              ))}
            </HStack>

            {/* Navigation buttons */}
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
                    <ButtonText className="text-white">Next</ButtonText>
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
                        <ButtonText className="text-white">Complete</ButtonText>
                      </>
                    )}
                  </Button>
                )}
              </HStack>
            </HStack>
          </VStack>
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