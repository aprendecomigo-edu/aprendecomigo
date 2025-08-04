import React from 'react';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface OnboardingChecklistProps {
  onStepAction?: (stepId: string, action: 'start' | 'skip') => void;
  showProgress?: boolean;
}

export const OnboardingChecklist: React.FC<OnboardingChecklistProps> = ({ 
  onStepAction, 
  showProgress 
}) => {
  const handleStepAction = (stepId: string, action: 'start' | 'skip') => {
    onStepAction?.(stepId, action);
  };

  return (
    <VStack space="lg" className="p-6">
      <Heading size="xl" className="text-gray-900">
        Complete Your Setup
      </Heading>
      
      <Text className="text-gray-600">
        Follow these steps to get your school ready for tutoring sessions.
      </Text>
      
      <VStack space="md">
        <Box className="bg-white rounded-lg border border-gray-200 p-4">
          <VStack space="sm">
            <Text className="font-medium text-gray-900">Invite First Teacher</Text>
            <Text className="text-gray-600 text-sm">
              Add your first teacher to start organizing classes.
            </Text>
            <Button
              size="sm"
              onPress={() => handleStepAction('invite_first_teacher', 'start')}
            >
              <ButtonText>Start</ButtonText>
            </Button>
          </VStack>
        </Box>
        
        <Box className="bg-white rounded-lg border border-gray-200 p-4">
          <VStack space="sm">
            <Text className="font-medium text-gray-900">Add First Student</Text>
            <Text className="text-gray-600 text-sm">
              Register your first student to begin scheduling sessions.
            </Text>
            <Button
              size="sm"
              onPress={() => handleStepAction('add_first_student', 'start')}
            >
              <ButtonText>Start</ButtonText>
            </Button>
          </VStack>
        </Box>
        
        <Box className="bg-white rounded-lg border border-gray-200 p-4">
          <VStack space="sm">
            <Text className="font-medium text-gray-900">Complete School Profile</Text>
            <Text className="text-gray-600 text-sm">
              Fill out your school's information and preferences.
            </Text>
            <Button
              size="sm"
              onPress={() => handleStepAction('complete_school_profile', 'start')}
            >
              <ButtonText>Start</ButtonText>
            </Button>
          </VStack>
        </Box>
      </VStack>
    </VStack>
  );
};