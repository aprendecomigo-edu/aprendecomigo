import React from 'react';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import MainLayout from '@/components/layouts/MainLayout';

interface TeacherProfileWizardProps {
  onComplete?: () => void;
  onExit?: () => void;
}

export const TeacherProfileWizard: React.FC<TeacherProfileWizardProps> = ({ 
  onComplete, 
  onExit 
}) => {
  return (
    <MainLayout _title="Teacher Profile Setup">
      <Box className="flex-1">
        <VStack className="p-6 flex-1 justify-center" space="lg">
          <VStack space="md" className="items-center">
            <Heading size="xl" className="text-center text-gray-900">
              Complete Your Teacher Profile
            </Heading>
            <Text className="text-center text-gray-600">
              Help us create the perfect teaching environment for you.
            </Text>
          </VStack>
          
          <VStack space="md" className="mt-8">
            <Button
              size="lg"
              onPress={onComplete}
              className="w-full"
            >
              <ButtonText>Complete Setup</ButtonText>
            </Button>
            
            <Button
              variant="outline"
              size="lg"
              onPress={onExit}
              className="w-full"
            >
              <ButtonText>Exit for Now</ButtonText>
            </Button>
          </VStack>
        </VStack>
      </Box>
    </MainLayout>
  );
};