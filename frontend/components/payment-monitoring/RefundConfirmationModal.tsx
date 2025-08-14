import React from 'react';

import { Button, ButtonText } from '@/components/ui/button';
import { Modal, ModalBackdrop, ModalContent, ModalHeader, ModalBody } from '@/components/ui/modal';
import { Text } from '@/components/ui/text';

interface RefundConfirmationModalProps {
  transaction: any;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (request: any) => void;
  loading: boolean;
}

const RefundConfirmationModal: React.FC<RefundConfirmationModalProps> = ({
  transaction,
  isOpen,
  onClose,
  onConfirm,
  loading,
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalBackdrop />
      <ModalContent>
        <ModalHeader>
          <Text className="font-semibold">Confirm Refund</Text>
        </ModalHeader>
        <ModalBody>
          <Text className="text-gray-600 text-center">
            Refund Confirmation Modal - Component placeholder
          </Text>
          <Button onPress={onClose} className="mt-4">
            <ButtonText>Close</ButtonText>
          </Button>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default RefundConfirmationModal;
