/**
 * Add Payment Method Modal Component - Fallback Implementation
 *
 * Main entry point with Platform.OS fallback.
 * Platform-specific files should override this implementation.
 */

import React from 'react';
import { Platform } from 'react-native';

import {
  AddPaymentMethodModalProps,
  PaymentMethodModalHeader,
  PlatformNotSupportedContent,
  CloseButtonFooter,
  LoadingContent,
} from './add-payment-method-common';

import { Modal, ModalBackdrop, ModalBody, ModalContent } from '@/components/ui/modal';

// Export types for external usage
export type { AddPaymentMethodModalProps };

/**
 * Fallback Add Payment Method Modal Component.
 * Platform-specific implementations should override this.
 */
export function AddPaymentMethodModal({ isOpen, onClose }: AddPaymentMethodModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalBackdrop />
      <ModalContent className="max-w-lg mx-auto">
        <PaymentMethodModalHeader onClose={onClose} />

        <ModalBody>
          {Platform.OS === 'web' ? <LoadingContent /> : <PlatformNotSupportedContent />}
        </ModalBody>

        {Platform.OS !== 'web' && <CloseButtonFooter onClose={onClose} />}
      </ModalContent>
    </Modal>
  );
}
