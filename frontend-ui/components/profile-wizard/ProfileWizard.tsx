import React, { useState } from 'react';
import { Alert } from 'react-native';
import { useRouter } from 'expo-router';

import { useInvitationProfileWizard } from '@/hooks/useInvitationProfileWizard';
import { useInvitationActions } from '@/hooks/useInvitations';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { VStack } from '@/components/ui/vstack';
import { HStack } from '@/components/ui/hstack';
import { Text } from '@/components/ui/text';
import { Heading } from '@/components/ui/heading';
import { Spinner } from '@/components/ui/spinner';

import StepIndicator from './StepIndicator';
import BasicInformationStep from './steps/BasicInformationStep';
import TeachingSubjectsStep from './steps/TeachingSubjectsStep';
import GradeLevelStep from './steps/GradeLevelStep';
import AvailabilityStep from './steps/AvailabilityStep';
import RatesCompensationStep from './steps/RatesCompensationStep';
import CredentialsStep from './steps/CredentialsStep';
import ProfileMarketingStep from './steps/ProfileMarketingStep';
import PreviewSubmitStep from './steps/PreviewSubmitStep';

interface ProfileWizardProps {
  invitationToken: string;
  invitationData: any;
  onSuccess: () => void;
  onCancel?: () => void;
}

const ProfileWizard: React.FC<ProfileWizardProps> = ({
  invitationToken,
  invitationData,
  onSuccess,
  onCancel,
}) => {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const {
    currentStep,
    totalSteps,
    profileData,
    validationErrors,
    loading,
    hasUnsavedChanges,
    nextStep,
    previousStep,
    goToStep,
    updateProfileData,
    validateStep,
    getCurrentStepErrors,
    isStepCompleted,
    getProgress,
    canGoNext,
    canGoPrevious,
    isLastStep,
    clearSavedData,
    // Helper functions
    addTeachingSubject,
    removeTeachingSubject,
    addEducationEntry,
    removeEducationEntry,
    addExperienceEntry,
    removeExperienceEntry,
    addCertification,
    removeCertification,
  } = useInvitationProfileWizard(invitationToken);

  const { acceptInvitation } = useInvitationActions();

  const handleNext = () => {
    if (nextStep()) {
      // Successfully moved to next step
    } else {
      // Show validation errors
      const errors = getCurrentStepErrors();
      const errorMessages = Object.values(errors);
      if (errorMessages.length > 0) {
        Alert.alert('Campos obrigatórios', errorMessages[0]);
      }
    }
  };

  const handlePrevious = () => {
    if (hasUnsavedChanges) {
      Alert.alert(
        'Alterações não salvas',
        'Você tem alterações não salvas. Deseja continuar?',
        [
          { text: 'Cancelar', style: 'cancel' },
          { text: 'Continuar', onPress: previousStep },
        ]
      );
    } else {
      previousStep();
    }
  };

  const handleCancel = () => {
    if (hasUnsavedChanges) {
      Alert.alert(
        'Cancelar configuração do perfil?',
        'Você perderá todas as informações inseridas.',
        [
          { text: 'Continuar editando', style: 'cancel' },
          { 
            text: 'Cancelar', 
            style: 'destructive',
            onPress: () => {
              clearSavedData();
              onCancel?.();
            }
          },
        ]
      );
    } else {
      onCancel?.();
    }
  };

  const handleSubmit = async () => {
    // Validate all steps
    let allValid = true;
    for (let i = 1; i <= totalSteps - 1; i++) {
      if (!validateStep(i)) {
        allValid = false;
        break;
      }
    }

    if (!allValid) {
      Alert.alert(
        'Perfil incompleto',
        'Por favor, complete todos os campos obrigatórios antes de enviar.'
      );
      return;
    }

    try {
      setIsSubmitting(true);
      
      // Accept invitation with comprehensive profile data
      const result = await acceptInvitation(invitationToken, profileData);
      
      // Clear saved wizard data
      await clearSavedData();
      
      Alert.alert(
        'Sucesso!',
        'Seu perfil foi configurado e o convite foi aceito com sucesso!',
        [
          {
            text: 'Ir para Dashboard',
            onPress: onSuccess,
          }
        ]
      );
      
    } catch (error: any) {
      console.error('Failed to submit profile:', error);
      Alert.alert(
        'Erro',
        error.message || 'Falha ao enviar perfil. Tente novamente.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderCurrentStep = () => {
    const stepProps = {
      profileData,
      updateProfileData,
      validationErrors: getCurrentStepErrors(),
      invitationData,
    };

    switch (currentStep) {
      case 1:
        return <BasicInformationStep {...stepProps} />;
      case 2:
        return (
          <TeachingSubjectsStep 
            {...stepProps}
            onAddSubject={addTeachingSubject}
            onRemoveSubject={removeTeachingSubject}
          />
        );
      case 3:
        return <GradeLevelStep {...stepProps} />;
      case 4:
        return <AvailabilityStep {...stepProps} />;
      case 5:
        return <RatesCompensationStep {...stepProps} />;
      case 6:
        return (
          <CredentialsStep 
            {...stepProps}
            onAddEducation={addEducationEntry}
            onRemoveEducation={removeEducationEntry}
            onAddExperience={addExperienceEntry}
            onRemoveExperience={removeExperienceEntry}
            onAddCertification={addCertification}
            onRemoveCertification={removeCertification}
          />
        );
      case 7:
        return <ProfileMarketingStep {...stepProps} />;
      case 8:
        return (
          <PreviewSubmitStep 
            {...stepProps}
            onEditStep={goToStep}
            onSubmit={handleSubmit}
            isSubmitting={isSubmitting}
          />
        );
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <Box className="flex-1 justify-center items-center p-6">
        <VStack space="md" className="items-center">
          <Spinner size="large" />
          <Text className="text-gray-600">Carregando configuração do perfil...</Text>
        </VStack>
      </Box>
    );
  }

  return (
    <Box className="flex-1 bg-gray-50">
      {/* Header */}
      <Box className="bg-white border-b border-gray-200 px-6 py-4">
        <VStack space="sm">
          <HStack className="justify-between items-center">
            <VStack>
              <Heading size="lg" className="text-gray-900">
                Configuração do Perfil
              </Heading>
              <Text className="text-sm text-gray-600">
                Escola: {invitationData?.invitation?.school?.name}
              </Text>
            </VStack>
            <Text className="text-sm text-gray-500">
              {Math.round(getProgress())}% completo
            </Text>
          </HStack>
          
          <StepIndicator
            currentStep={currentStep}
            totalSteps={totalSteps}
            completedSteps={Array.from({ length: totalSteps }, (_, i) => i + 1)
              .filter(step => step < currentStep && isStepCompleted(step))}
          />
        </VStack>
      </Box>

      {/* Step Content */}
      <Box className="flex-1 p-6">
        {renderCurrentStep()}
      </Box>

      {/* Footer Navigation */}
      <Box className="bg-white border-t border-gray-200 px-6 py-4">
        <HStack className="justify-between items-center">
          <Button
            variant="outline"
            onPress={canGoPrevious ? handlePrevious : handleCancel}
            disabled={isSubmitting}
          >
            <ButtonText>
              {canGoPrevious ? 'Anterior' : 'Cancelar'}
            </ButtonText>
          </Button>

          <HStack space="sm">
            {hasUnsavedChanges && (
              <Text className="text-xs text-amber-600 self-center">
                Alterações não salvas
              </Text>
            )}
            
            {isLastStep ? (
              <Button
                onPress={handleSubmit}
                disabled={isSubmitting}
                className="bg-green-600"
              >
                {isSubmitting ? (
                  <HStack space="xs" className="items-center">
                    <Spinner size="small" />
                    <ButtonText className="text-white">Enviando...</ButtonText>
                  </HStack>
                ) : (
                  <ButtonText className="text-white">
                    Finalizar Perfil
                  </ButtonText>
                )}
              </Button>
            ) : (
              <Button
                onPress={handleNext}
                disabled={!canGoNext || isSubmitting}
              >
                <ButtonText>Próximo</ButtonText>
              </Button>
            )}
          </HStack>
        </HStack>
      </Box>
    </Box>
  );
};

export default ProfileWizard;