import { X, ChevronLeft, ChevronRight, Play } from 'lucide-react-native';
import React from 'react';
import { Dimensions, Platform } from 'react-native';

import { useTutorial } from './TutorialContext';

import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonIcon, ButtonText } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import {
  Modal,
  ModalBackdrop,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
} from '@/components/ui/modal';
import { Pressable } from '@/components/ui/pressable';
import { Progress, ProgressFilledTrack } from '@/components/ui/progress';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

export const TutorialOverlay: React.FC = () => {
  const { state, nextStep, prevStep, skipTutorial, completeTutorial } = useTutorial();

  if (!state.isActive || !state.config) {
    return null;
  }

  const currentStep = state.config.steps[state.currentStep];
  const progress = ((state.currentStep + 1) / state.config.steps.length) * 100;
  const isLastStep = state.currentStep === state.config.steps.length - 1;
  const isFirstStep = state.currentStep === 0;

  const handleNext = () => {
    if (currentStep.action) {
      currentStep.action.onPress();
    }
    if (isLastStep) {
      completeTutorial();
    } else {
      nextStep();
    }
  };

  const handleSkip = () => {
    skipTutorial();
  };

  return (
    <Modal isOpen={state.isActive} onClose={handleSkip}>
      <ModalBackdrop />
      <ModalContent
        className="w-[90%] max-w-md bg-white rounded-2xl shadow-2xl"
        style={{
          marginTop: Platform.OS === 'web' ? 'auto' : screenHeight * 0.15,
          marginBottom: 'auto',
        }}
      >
        <ModalHeader className="px-6 py-4 border-b border-gray-100">
          <HStack className="items-center justify-between w-full">
            <VStack className="flex-1">
              <Heading className="text-lg font-bold text-gray-900">{currentStep.title}</Heading>
              {state.config.showProgress !== false && (
                <HStack className="items-center mt-2" space="sm">
                  <Progress value={progress} className="flex-1 h-2 bg-gray-200 rounded-full">
                    <ProgressFilledTrack className="bg-blue-600 rounded-full" />
                  </Progress>
                  <Badge variant="outline" className="border-gray-300">
                    <BadgeText className="text-xs text-gray-600">
                      {state.currentStep + 1} / {state.config.steps.length}
                    </BadgeText>
                  </Badge>
                </HStack>
              )}
            </VStack>
            {state.config.canSkip !== false && (
              <Pressable onPress={handleSkip} className="ml-4 p-2">
                <Icon as={X} size="sm" className="text-gray-500" />
              </Pressable>
            )}
          </HStack>
        </ModalHeader>

        <ModalBody className="px-6 py-4">
          <VStack space="md">
            <Text className="text-gray-700 text-base leading-relaxed">{currentStep.content}</Text>

            {currentStep.highlight && (
              <Box className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <HStack className="items-center" space="sm">
                  <Icon as={Play} size="sm" className="text-blue-600" />
                  <Text className="text-blue-800 font-medium text-sm">Destaque interativo</Text>
                </HStack>
              </Box>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter className="px-6 py-4 border-t border-gray-100">
          <HStack className="items-center justify-between w-full" space="sm">
            <Button
              variant="outline"
              size="sm"
              onPress={prevStep}
              disabled={isFirstStep}
              className={`${isFirstStep ? 'opacity-50' : ''}`}
            >
              <ButtonIcon as={ChevronLeft} size="sm" />
              <ButtonText>Anterior</ButtonText>
            </Button>

            <HStack space="sm">
              {state.config.canSkip !== false && (
                <Button
                  variant="outline"
                  size="sm"
                  onPress={handleSkip}
                  className="border-gray-300"
                >
                  <ButtonText className="text-gray-600">Pular</ButtonText>
                </Button>
              )}

              <Button
                variant="solid"
                size="sm"
                onPress={handleNext}
                className="bg-blue-600 min-w-[100px]"
              >
                <ButtonText className="text-white">
                  {isLastStep ? 'Concluir' : currentStep.action?.label || 'Próximo'}
                </ButtonText>
                {!isLastStep && <ButtonIcon as={ChevronRight} size="sm" />}
              </Button>
            </HStack>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
