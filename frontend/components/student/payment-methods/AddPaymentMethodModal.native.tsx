/**
 * Add Payment Method Modal - Native Implementation
 *
 * Native-specific implementation that shows platform not supported message
 * and directs users to the web version for payment method management.
 * Future enhancement: Could integrate with native payment sheets.
 */

import React from 'react';

import {
  AddPaymentMethodModalProps,
  PaymentMethodModalHeader,
  PlatformNotSupportedContent,
  CloseButtonFooter,
} from './add-payment-method-common';

import { Modal, ModalBackdrop, ModalBody, ModalContent } from '@/components/ui/modal';

/**
 * Add Payment Method Modal Component - Native Implementation
 */
export function AddPaymentMethodModal({ isOpen, onClose }: AddPaymentMethodModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalBackdrop />
      <ModalContent className="max-w-lg mx-auto">
        <PaymentMethodModalHeader onClose={onClose} />

        <ModalBody>
          <PlatformNotSupportedContent />
        </ModalBody>

        <CloseButtonFooter onClose={onClose} />
      </ModalContent>
    </Modal>
  );
}
