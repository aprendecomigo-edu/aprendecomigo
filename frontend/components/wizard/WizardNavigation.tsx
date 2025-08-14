import { CheckCircle2, Circle, AlertCircle } from 'lucide-react-native';
import React from 'react';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface WizardStep {
  id: string;
  title: string;
  description: string;
  icon: any;
  component: any;
  isRequired: boolean;
}

interface CompletionData {
  completion_percentage: number;
  missing_critical: string[];
  missing_optional: string[];
  is_complete: boolean;
  step_completion: Record<
    string,
    {
      is_complete: boolean;
      completion_percentage: number;
      missing_fields: string[];
    }
  >;
}

interface WizardNavigationProps {
  steps: WizardStep[];
  currentStep: number;
  onStepClick: (stepIndex: number) => void;
  completionData?: CompletionData;
  className?: string;
  hasErrors?: boolean;
  onErrorRecovery?: () => void;
}

export const WizardNavigation: React.FC<WizardNavigationProps> = ({
  steps,
  currentStep,
  onStepClick,
  completionData,
  className = '',
  hasErrors = false,
  onErrorRecovery,
}) => {
  const getStepStatus = (stepIndex: number) => {
    const step = steps[stepIndex];
    const stepCompletion = completionData?.step_completion?.[step.id];

    if (stepCompletion?.is_complete) {
      return 'completed';
    }

    if (stepIndex < currentStep) {
      return 'visited';
    }

    if (stepIndex === currentStep) {
      return 'current';
    }

    if (stepCompletion && stepCompletion.completion_percentage > 0) {
      return 'in-progress';
    }

    return 'pending';
  };

  const getStepIcon = (stepIndex: number) => {
    const status = getStepStatus(stepIndex);
    const step = steps[stepIndex];

    switch (status) {
      case 'completed':
        return <Icon as={CheckCircle2} size={20} className="text-green-600" />;
      case 'current':
        return <Icon as={step.icon} size={20} className="text-blue-600" />;
      case 'in-progress':
        return <Icon as={AlertCircle} size={20} className="text-yellow-600" />;
      case 'visited':
        return <Icon as={step.icon} size={20} className="text-gray-600" />;
      default:
        return <Icon as={Circle} size={20} className="text-gray-400" />;
    }
  };

  const getStepStyles = (stepIndex: number) => {
    const status = getStepStatus(stepIndex);

    switch (status) {
      case 'completed':
        return {
          container: 'bg-green-50 border-green-200 hover:bg-green-100',
          title: 'text-green-900',
          description: 'text-green-700',
        };
      case 'current':
        return {
          container: 'bg-blue-50 border-blue-300 ring-2 ring-blue-200',
          title: 'text-blue-900',
          description: 'text-blue-700',
        };
      case 'in-progress':
        return {
          container: 'bg-yellow-50 border-yellow-200 hover:bg-yellow-100',
          title: 'text-yellow-900',
          description: 'text-yellow-700',
        };
      case 'visited':
        return {
          container: 'bg-gray-50 border-gray-200 hover:bg-gray-100',
          title: 'text-gray-900',
          description: 'text-gray-600',
        };
      default:
        return {
          container: 'bg-white border-gray-200 hover:bg-gray-50',
          title: 'text-gray-700',
          description: 'text-gray-500',
        };
    }
  };

  const isStepClickable = (stepIndex: number) => {
    // Can navigate to current step or any previous step
    // But prevent navigation if there are critical errors
    const isWithinAllowedRange = stepIndex <= currentStep;
    const notBlocked = !hasErrors;
    return isWithinAllowedRange && notBlocked;
  };

  const getStepCompletionPercentage = (stepIndex: number) => {
    const step = steps[stepIndex];
    const stepCompletion = completionData?.step_completion?.[step.id];
    return stepCompletion?.completion_percentage || 0;
  };

  return (
    <Box className={`bg-white border-r border-gray-200 ${className}`}>
      <VStack space="xs" className="p-4 max-w-xs">
        <Text className="text-sm font-semibold text-gray-900 mb-2">Profile Setup Progress</Text>

        {steps.map((step, index) => {
          const styles = getStepStyles(index);
          const isClickable = isStepClickable(index);
          const completionPercentage = getStepCompletionPercentage(index);

          return (
            <Box key={step.id}>
              <Button
                variant="ghost"
                className={`${styles.container} p-3 w-full transition-all duration-200 ${
                  !isClickable ? 'opacity-60 cursor-not-allowed' : ''
                }`}
                onPress={() => isClickable && onStepClick(index)}
                isDisabled={!isClickable}
              >
                <HStack space="sm" className="items-start w-full">
                  {/* Step Icon */}
                  <Box className="mt-0.5">{getStepIcon(index)}</Box>

                  {/* Step Content */}
                  <VStack className="flex-1" space="xs">
                    <HStack className="items-center justify-between w-full">
                      <Text className={`text-sm font-medium ${styles.title}`}>{step.title}</Text>
                      {step.isRequired && <Box className="w-2 h-2 bg-red-400 rounded-full" />}
                    </HStack>

                    <Text className={`text-xs ${styles.description}`}>{step.description}</Text>

                    {/* Progress Bar for In-Progress Steps */}
                    {completionPercentage > 0 && completionPercentage < 100 && (
                      <Box className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                        <Box
                          className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${completionPercentage}%` }}
                        />
                      </Box>
                    )}
                  </VStack>
                </HStack>
              </Button>

              {/* Connector Line */}
              {index < steps.length - 1 && (
                <Box className="ml-8 my-1">
                  <Divider
                    orientation="vertical"
                    className={`h-6 w-px ${
                      getStepStatus(index) === 'completed' ? 'bg-green-300' : 'bg-gray-300'
                    }`}
                  />
                </Box>
              )}
            </Box>
          );
        })}

        {/* Overall Progress Summary */}
        {completionData && (
          <Box className="mt-4 p-3 bg-gray-50 rounded-lg">
            <VStack space="xs">
              <HStack className="items-center justify-between">
                <Text className="text-sm font-medium text-gray-900">Overall Progress</Text>
                <Text className="text-sm text-gray-600">
                  {Math.round(completionData.completion_percentage)}%
                </Text>
              </HStack>

              <Box className="w-full bg-gray-200 rounded-full h-2">
                <Box
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${completionData.completion_percentage}%` }}
                />
              </Box>

              {completionData.missing_critical.length > 0 && (
                <VStack space="xs" className="mt-2">
                  <Text className="text-xs font-medium text-red-700">Missing Required Fields:</Text>
                  {completionData.missing_critical.slice(0, 3).map((field, index) => (
                    <Text key={index} className="text-xs text-red-600">
                      • {field}
                    </Text>
                  ))}
                  {completionData.missing_critical.length > 3 && (
                    <Text className="text-xs text-red-600">
                      ... and {completionData.missing_critical.length - 3} more
                    </Text>
                  )}
                </VStack>
              )}
            </VStack>
          </Box>
        )}
      </VStack>
    </Box>
  );
};
