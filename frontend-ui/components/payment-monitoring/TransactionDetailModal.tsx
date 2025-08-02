import React from 'react';

import { Button, ButtonText } from '@/components/ui/button';
import { Modal, ModalBackdrop, ModalContent, ModalHeader, ModalBody } from '@/components/ui/modal';
import { Text } from '@/components/ui/text';

interface TransactionDetailModalProps {
  transaction: any;
  isOpen: boolean;
  onClose: () => void;
  onRefund: (transaction: any) => void;
  onRetry: (transaction: any) => void;
}

const TransactionDetailModal: React.FC<TransactionDetailModalProps> = ({
  transaction,
  isOpen,
  onClose,
  onRefund,
  onRetry,
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalBackdrop />
      <ModalContent>
        <ModalHeader>
          <Text className="font-semibold">Transaction Details</Text>
        </ModalHeader>
        <ModalBody>
          <Text className="text-gray-600 text-center">
            Transaction Detail Modal - Component placeholder
          </Text>
          <Button onPress={onClose} className="mt-4">
            <ButtonText>Close</ButtonText>
          </Button>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default TransactionDetailModal;
