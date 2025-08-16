import { Check } from 'lucide-react-native';
import React from 'react';

import { Box } from '@/components/ui/box';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface StepIndicatorProps {
  currentStep: number;
  totalSteps: number;
  completedSteps: number[];
}

const StepIndicator: React.FC<StepIndicatorProps> = ({
  currentStep,
  totalSteps,
  completedSteps = [],
}) => {
  const stepLabels = [
    'Informações',
    'Matérias',
    'Níveis',
    'Disponibilidade',
    'Taxas',
    'Credenciais',
    'Marketing',
    'Revisão',
  ];

  const getStepStatus = (stepNumber: number) => {
    if (completedSteps.includes(stepNumber)) {
      return 'completed';
    } else if (stepNumber === currentStep) {
      return 'current';
    } else if (stepNumber < currentStep) {
      return 'completed';
    } else {
      return 'upcoming';
    }
  };

  const getStepColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500 border-green-500';
      case 'current':
        return 'bg-blue-500 border-blue-500';
      case 'upcoming':
        return 'bg-gray-200 border-gray-300';
      default:
        return 'bg-gray-200 border-gray-300';
    }
  };

  const getTextColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600';
      case 'current':
        return 'text-blue-600';
      case 'upcoming':
        return 'text-gray-500';
      default:
        return 'text-gray-500';
    }
  };

  return (
    <Box className="py-4">
      <HStack className="justify-between items-start" space="xs">
        {Array.from({ length: totalSteps }, (_, index) => {
          const stepNumber = index + 1;
          const status = getStepStatus(stepNumber);
          const isCompleted = status === 'completed';
          const isCurrent = status === 'current';

          return (
            <VStack key={stepNumber} className="items-center flex-1" space="xs">
              {/* Step Circle */}
              <Box
                className={`w-8 h-8 rounded-full border-2 items-center justify-center ${getStepColor(
                  status,
                )}`}
              >
                {isCompleted ? (
                  <Icon as={Check} size="sm" className="text-white" />
                ) : (
                  <Text
                    className={`text-xs font-medium ${isCurrent ? 'text-white' : 'text-gray-600'}`}
                  >
                    {stepNumber}
                  </Text>
                )}
              </Box>

              {/* Step Label */}
              <Text
                className={`text-xs text-center ${getTextColor(status)} font-medium`}
                numberOfLines={2}
              >
                {stepLabels[index]}
              </Text>

              {/* Connection Line */}
              {index < totalSteps - 1 && (
                <Box
                  className={`absolute top-4 left-1/2 w-full h-0.5 ${
                    stepNumber < currentStep || completedSteps.includes(stepNumber + 1)
                      ? 'bg-green-300'
                      : 'bg-gray-300'
                  }`}
                  style={{
                    transform: [{ translateX: '50%' }],
                    zIndex: -1,
                  }}
                />
              )}
            </VStack>
          );
        })}
      </HStack>
    </Box>
  );
};

export default StepIndicator;
