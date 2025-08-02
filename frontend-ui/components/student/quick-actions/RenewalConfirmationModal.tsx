/**
 * Renewal Confirmation Modal Component
 * 
 * Confirmation dialog with transaction details for subscription renewals
 * and quick top-up purchases before processing payment.
 */

import React, { useState } from 'react';
import { X, RotateCcw, Zap, CreditCard, Calendar, Clock, Euro, Shield, CheckCircle, AlertCircle } from 'lucide-react-native';

import { 
  Modal, 
  ModalBackdrop, 
  ModalContent, 
  ModalHeader, 
  ModalCloseButton, 
  ModalBody, 
  ModalFooter 
} from '@/components/ui/modal';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { Divider } from '@/components/ui/divider';
import { Alert, AlertIcon, AlertText } from '@/components/ui/alert';

import type { 
  PaymentMethod, 
  PackageInfo, 
  TopUpPackage,
  RenewalRequest,
  QuickTopUpRequest 
} from '@/types/purchase';

interface RenewalConfirmationModalProps {
  /** Whether modal is open */
  isOpen: boolean;
  /** Close modal callback */
  onClose: () => void;
  /** Type of transaction */
  transactionType: 'renewal' | 'topup';
  /** Package/plan being renewed (for renewals) */
  expiredPackage?: PackageInfo;
  /** Top-up package being purchased (for top-ups) */
  topUpPackage?: TopUpPackage;
  /** Selected payment method */
  paymentMethod: PaymentMethod;
  /** Callback when confirmation is accepted */
  onConfirm: (request: RenewalRequest | QuickTopUpRequest) => Promise<void>;
  /** Whether transaction is processing */
  isProcessing?: boolean;
  /** Error message to display */
  error?: string;
  /** Enable biometric authentication */
  enableBiometricAuth?: boolean;
}

/**
 * Renewal Confirmation Modal Component
 * 
 * Shows transaction details and confirms renewal or top-up purchases.
 */
export function RenewalConfirmationModal({
  isOpen,
  onClose,
  transactionType,
  expiredPackage,
  topUpPackage,
  paymentMethod,
  onConfirm,
  isProcessing = false,
  error,
  enableBiometricAuth = false,
}: RenewalConfirmationModalProps) {
  const [biometricAuthCompleted, setBiometricAuthCompleted] = useState(false);

  // Reset state when modal opens/closes
  React.useEffect(() => {
    if (!isOpen) {
      setBiometricAuthCompleted(false);
    }
  }, [isOpen]);

  // Handle biometric authentication
  const handleBiometricAuth = async () => {
    // In a real implementation, this would trigger the device's biometric authentication
    try {
      // Simulate biometric auth
      await new Promise(resolve => setTimeout(resolve, 1000));
      setBiometricAuthCompleted(true);
    } catch (error) {
      console.error('Biometric authentication failed:', error);
    }
  };

  // Handle confirmation
  const handleConfirm = async () => {
    if (enableBiometricAuth && !biometricAuthCompleted) {
      await handleBiometricAuth();
      return;
    }

    try {
      if (transactionType === 'renewal') {
        const request: RenewalRequest = {
          payment_method_id: paymentMethod.id,
          confirm_immediately: true,
        };
        await onConfirm(request);
      } else {
        const request: QuickTopUpRequest = {
          package_id: topUpPackage!.id,
          payment_method_id: paymentMethod.id,
          confirm_immediately: true,
        };
        await onConfirm(request);
      }
    } catch (error) {
      // Error handling is managed by parent component
    }
  };

  // Get transaction details
  const getTransactionDetails = () => {
    if (transactionType === 'renewal' && expiredPackage) {
      return {
        title: 'Renew Subscription',
        icon: RotateCcw,
        iconColor: 'text-primary-600',
        bgColor: 'bg-primary-50',
        borderColor: 'border-primary-200',
        item: expiredPackage.plan_name,
        hours: expiredPackage.hours_included,
        // For renewal, we'd need to get the current plan price
        // This would typically come from the backend
        price: '€29.99', // Placeholder
        description: 'Renew your expired subscription to continue accessing tutoring hours',
        validity: '30 days',
      };
    } else if (transactionType === 'topup' && topUpPackage) {
      return {
        title: 'Purchase Hours',
        icon: Zap,
        iconColor: 'text-warning-600',
        bgColor: 'bg-warning-50',
        borderColor: 'border-warning-200',
        item: topUpPackage.name,
        hours: topUpPackage.hours.toString(),
        price: `€${topUpPackage.price_eur}`,
        description: 'Add hours to your account for immediate use',
        validity: 'No expiration',
      };
    }
    return null;
  };

  const details = getTransactionDetails();
  if (!details) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalBackdrop />
      <ModalContent>
        <ModalHeader>
          <VStack space="xs">
            <HStack className="items-center justify-between">
              <HStack space="sm" className="items-center">
                <Icon as={details.icon} size="sm" className={details.iconColor} />
                <Heading size="lg">{details.title}</Heading>
              </HStack>
              <ModalCloseButton>
                <Icon as={X} />
              </ModalCloseButton>
            </HStack>
            <Text className="text-sm text-typography-600">
              Please review the transaction details before confirming
            </Text>
          </VStack>
        </ModalHeader>

        <ModalBody>
          <VStack space="lg">
            {/* Error Display */}
            {error && (
              <Alert action="error" variant="outline">
                <AlertIcon as={AlertCircle} />
                <AlertText>{error}</AlertText>
              </Alert>
            )}

            {/* Transaction Summary */}
            <Card className={`p-4 ${details.bgColor} border ${details.borderColor}`}>
              <VStack space="md">
                <HStack className="items-center justify-between">
                  <VStack space="xs">
                    <Text className="font-semibold text-typography-900">
                      {details.item}
                    </Text>
                    <Text className="text-sm text-typography-600">
                      {details.description}
                    </Text>
                  </VStack>
                  <VStack className="items-end">
                    <Text className="text-2xl font-bold text-typography-900">
                      {details.price}
                    </Text>
                  </VStack>
                </HStack>

                <Divider />

                <VStack space="sm">
                  <HStack className="items-center justify-between">
                    <HStack space="xs" className="items-center">
                      <Icon as={Clock} size="sm" className="text-typography-500" />
                      <Text className="text-sm text-typography-700">Hours</Text>
                    </HStack>
                    <Text className="text-sm font-medium text-typography-900">
                      {details.hours}
                    </Text>
                  </HStack>

                  <HStack className="items-center justify-between">
                    <HStack space="xs" className="items-center">
                      <Icon as={Calendar} size="sm" className="text-typography-500" />
                      <Text className="text-sm text-typography-700">Validity</Text>
                    </HStack>
                    <Text className="text-sm font-medium text-typography-900">
                      {details.validity}
                    </Text>
                  </HStack>

                  <HStack className="items-center justify-between">
                    <HStack space="xs" className="items-center">
                      <Icon as={Euro} size="sm" className="text-typography-500" />
                      <Text className="text-sm text-typography-700">Total Amount</Text>
                    </HStack>
                    <Text className="text-sm font-bold text-typography-900">
                      {details.price}
                    </Text>
                  </HStack>
                </VStack>
              </VStack>
            </Card>

            {/* Payment Method */}
            <VStack space="sm">
              <Text className="font-medium text-typography-700">Payment Method</Text>
              <Card className="p-4 border border-outline-200">
                <HStack space="md" className="items-center">
                  <Icon as={CreditCard} size="md" className="text-typography-600" />
                  <VStack space="xs">
                    <Text className="font-medium text-typography-900">
                      {paymentMethod.card.brand.toUpperCase()} ••••{paymentMethod.card.last4}
                    </Text>
                    <Text className="text-xs text-typography-600">
                      Expires {paymentMethod.card.exp_month.toString().padStart(2, '0')}/{paymentMethod.card.exp_year}
                    </Text>
                    {paymentMethod.billing_details?.name && (
                      <Text className="text-xs text-typography-600">
                        {paymentMethod.billing_details.name}
                      </Text>
                    )}
                  </VStack>
                </HStack>
              </Card>
            </VStack>

            {/* Biometric Authentication Status */}
            {enableBiometricAuth && (
              <Card className={`p-4 ${biometricAuthCompleted ? 'bg-success-50 border-success-200' : 'bg-warning-50 border-warning-200'}`}>
                <HStack space="sm" className="items-center">
                  <Icon 
                    as={biometricAuthCompleted ? CheckCircle : Shield} 
                    size="sm" 
                    className={biometricAuthCompleted ? 'text-success-600' : 'text-warning-600'} 
                  />
                  <VStack space="xs" className="flex-1">
                    <Text className={`text-sm font-medium ${biometricAuthCompleted ? 'text-success-800' : 'text-warning-800'}`}>
                      {biometricAuthCompleted ? 'Authentication Completed' : 'Biometric Authentication Required'}
                    </Text>
                    <Text className={`text-xs ${biometricAuthCompleted ? 'text-success-700' : 'text-warning-700'}`}>
                      {biometricAuthCompleted 
                        ? 'Your identity has been verified successfully'
                        : 'Please authenticate to confirm this transaction'
                      }
                    </Text>
                  </VStack>
                </HStack>
              </Card>
            )}

            {/* Security Notice */}
            <Card className="p-3 bg-info-50 border-info-200">
              <HStack space="sm" className="items-center">
                <Icon as={Shield} size="sm" className="text-info-600" />
                <VStack space="xs" className="flex-1">
                  <Text className="text-xs font-medium text-info-800">
                    Secure Transaction
                  </Text>
                  <Text className="text-xs text-info-700">
                    This transaction is processed securely by Stripe. You will receive a receipt via email.
                  </Text>
                </VStack>
              </HStack>
            </Card>
          </VStack>
        </ModalBody>

        <ModalFooter>
          <HStack space="sm" className="w-full">
            <Button
              action="secondary"
              variant="outline"
              size="md"
              onPress={onClose}
              disabled={isProcessing}
              className="flex-1"
            >
              <ButtonText>Cancel</ButtonText>
            </Button>
            
            <Button
              action="primary"
              variant="solid"
              size="md"
              onPress={handleConfirm}
              disabled={isProcessing || (enableBiometricAuth && !biometricAuthCompleted)}
              className="flex-1"
            >
              {isProcessing ? (
                <>
                  <Spinner size="sm" />
                  <ButtonText className="ml-2">Processing...</ButtonText>
                </>
              ) : enableBiometricAuth && !biometricAuthCompleted ? (
                <>
                  <ButtonIcon as={Shield} />
                  <ButtonText>Authenticate</ButtonText>
                </>
              ) : (
                <>
                  <ButtonIcon as={details.icon} />
                  <ButtonText>Confirm {transactionType === 'renewal' ? 'Renewal' : 'Purchase'}</ButtonText>
                </>
              )}
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}