import React from 'react';

import { Button, ButtonText } from '@/components/ui/button';
import { Modal, ModalBackdrop, ModalContent, ModalHeader, ModalBody } from '@/components/ui/modal';
import { Text } from '@/components/ui/text';

interface BulkActionModalProps {
  selectedTransactions: any[];
  action: string;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (action: string, options: any) => void;
  loading: boolean;
}

const BulkActionModal: React.FC<BulkActionModalProps> = ({
  selectedTransactions,
  action,
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
          <Text className="font-semibold">Bulk Action</Text>
        </ModalHeader>
        <ModalBody>
          <Text className="text-gray-600 text-center">
            Bulk Action Modal - Component placeholder
          </Text>
          <Button onPress={onClose} className="mt-4">
            <ButtonText>Close</ButtonText>
          </Button>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default BulkActionModal;
