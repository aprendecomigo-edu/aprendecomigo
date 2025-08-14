/**
 * Add Payment Method Modal - Common Logic and Types
 *
 * Shared business logic, types, and utilities for payment method management
 * across web and native platforms.
 */

import { CreditCard, Plus, Lock, AlertCircle } from 'lucide-react-native';
import React from 'react';

import { Alert } from '@/components/ui/alert';
import { Button, ButtonText } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import {
  Modal,
  ModalBackdrop,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from '@/components/ui/modal';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Shared types and interfaces
export interface AddPaymentMethodModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

// Shared modal header component
export function PaymentMethodModalHeader({ onClose }: { onClose: () => void }) {
  return (
    <ModalHeader className="pb-4">
      <VStack space="xs" className="flex-1">
        <HStack space="sm" className="items-center">
          <Icon as={CreditCard} size="sm" className="text-primary-600" />
          <Heading size="lg">Add Payment Method</Heading>
        </HStack>
        <Text className="text-sm text-typography-600">
          Add a new credit or debit card to your account
        </Text>
      </VStack>
      <ModalCloseButton />
    </ModalHeader>
  );
}

// Shared platform not supported content
export function PlatformNotSupportedContent() {
  return (
    <VStack space="md" className="items-center py-8">
      <Icon as={AlertCircle} size="xl" className="text-warning-500" />
      <VStack space="sm" className="items-center">
        <Heading size="md" className="text-typography-900">
          Web Only Feature
        </Heading>
        <Text className="text-typography-600 text-center">
          Payment method management is currently available on the web version only. Please visit our
          website to manage your payment methods.
        </Text>
      </VStack>
    </VStack>
  );
}

// Shared loading content
export function LoadingContent() {
  return (
    <VStack space="md" className="items-center py-8">
      <Spinner size="large" />
      <Text className="text-typography-600">Loading payment form...</Text>
    </VStack>
  );
}

// Shared error content
export function ErrorContent({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <VStack space="md" className="py-4">
      <Alert action="error" variant="solid">
        <Icon as={AlertCircle} className="text-error-600" />
        <VStack space="sm" className="flex-1">
          <Heading size="sm" className="text-error-900">
            Setup Error
          </Heading>
          <Text className="text-error-800 text-sm">{error}</Text>
        </VStack>
      </Alert>
      <Button action="secondary" variant="outline" size="sm" onPress={onRetry}>
        <ButtonText>Try Again</ButtonText>
      </Button>
    </VStack>
  );
}

// Shared close button footer
export function CloseButtonFooter({ onClose }: { onClose: () => void }) {
  return (
    <ModalFooter className="pt-4">
      <Button action="secondary" variant="outline" size="md" onPress={onClose} className="w-full">
        <ButtonText>Close</ButtonText>
      </Button>
    </ModalFooter>
  );
}

// Shared security notice
export function SecurityNotice() {
  return (
    <HStack space="xs" className="items-center justify-center p-3 bg-success-50 rounded-lg">
      <Icon as={Lock} size="sm" className="text-success-600" />
      <Text className="text-sm text-success-800">
        Your payment information is secure and encrypted
      </Text>
    </HStack>
  );
}

// Shared terms notice
export function TermsNotice() {
  return (
    <Text className="text-xs text-typography-500 text-center">
      By adding a payment method, you agree to our Terms of Service. Your payment information is
      processed securely by Stripe.
    </Text>
  );
}
