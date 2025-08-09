import React from 'react';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Modal, ModalBackdrop, ModalBody, ModalContent, ModalHeader } from '@/components/ui/modal';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface FlowProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
}

export const AddFirstTeacherFlow: React.FC<FlowProps> = ({ isOpen, onClose, onComplete }) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalBackdrop />
      <ModalContent>
        <ModalHeader>
          <Text className="font-bold">Add First Teacher</Text>
        </ModalHeader>
        <ModalBody>
          <VStack space="md">
            <Text>Teacher invitation flow will be implemented here.</Text>
            <Button onPress={onComplete}>
              <ButtonText>Complete</ButtonText>
            </Button>
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export const AddFirstStudentFlow: React.FC<FlowProps> = ({ isOpen, onClose, onComplete }) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalBackdrop />
      <ModalContent>
        <ModalHeader>
          <Text className="font-bold">Add First Student</Text>
        </ModalHeader>
        <ModalBody>
          <VStack space="md">
            <Text>Student registration flow will be implemented here.</Text>
            <Button onPress={onComplete}>
              <ButtonText>Complete</ButtonText>
            </Button>
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export const SchoolProfileFlow: React.FC<FlowProps> = ({ isOpen, onClose, onComplete }) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalBackdrop />
      <ModalContent>
        <ModalHeader>
          <Text className="font-bold">Complete School Profile</Text>
        </ModalHeader>
        <ModalBody>
          <VStack space="md">
            <Text>School profile completion flow will be implemented here.</Text>
            <Button onPress={onComplete}>
              <ButtonText>Complete</ButtonText>
            </Button>
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};
