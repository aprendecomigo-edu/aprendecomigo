/**
 * Payment Method Card Component
 *
 * Displays individual payment method information with actions
 * for setting as default and removal.
 */

import { CreditCard, Check, MoreVertical, Trash2, Star, AlertTriangle } from 'lucide-react-native';
import React, { useState } from 'react';

import type { PaymentMethod } from '@/api/paymentMethodApi';
import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Menu, MenuItem, MenuItemLabel, MenuSeparator } from '@/components/ui/menu';
import {
  Modal,
  ModalBackdrop,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from '@/components/ui/modal';
import { Pressable } from '@/components/ui/pressable';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface PaymentMethodCardProps {
  paymentMethod: PaymentMethod;
  onSetDefault: (id: string) => Promise<void>;
  onRemove: (id: string) => Promise<void>;
  isSettingDefault: boolean;
  isRemoving: boolean;
  canRemove: boolean; // false if it's the only/default payment method
}

/**
 * Get card brand icon and styling
 */
function getCardBrandInfo(brand: string) {
  const brandLower = brand.toLowerCase();

  switch (brandLower) {
    case 'visa':
      return { color: 'text-blue-600', bgColor: 'bg-blue-50' };
    case 'mastercard':
      return { color: 'text-red-600', bgColor: 'bg-red-50' };
    case 'amex':
    case 'american_express':
      return { color: 'text-green-600', bgColor: 'bg-green-50' };
    case 'discover':
      return { color: 'text-orange-600', bgColor: 'bg-orange-50' };
    default:
      return { color: 'text-gray-600', bgColor: 'bg-gray-50' };
  }
}

/**
 * Confirmation modal for payment method removal
 */
function RemovalConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  paymentMethod,
  isRemoving,
}: {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  paymentMethod: PaymentMethod;
  isRemoving: boolean;
}) {
  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalBackdrop />
      <ModalContent className="max-w-md mx-auto">
        <ModalHeader>
          <VStack space="xs">
            <HStack space="sm" className="items-center">
              <Icon as={AlertTriangle} size="sm" className="text-warning-500" />
              <Heading size="md">Remove Payment Method</Heading>
            </HStack>
          </VStack>
          <ModalCloseButton />
        </ModalHeader>

        <ModalBody>
          <VStack space="md">
            <Text className="text-typography-700">
              Are you sure you want to remove this payment method?
            </Text>

            <Card className="p-3 bg-background-50">
              <HStack space="sm" className="items-center">
                <Icon as={CreditCard} size="sm" className="text-typography-600" />
                <VStack space="0">
                  <Text className="font-medium text-typography-900">
                    {paymentMethod.card.brand.toUpperCase()} •••• {paymentMethod.card.last4}
                  </Text>
                  <Text className="text-xs text-typography-600">
                    Expires {paymentMethod.card.exp_month.toString().padStart(2, '0')}/
                    {paymentMethod.card.exp_year}
                  </Text>
                </VStack>
              </HStack>
            </Card>

            <Text className="text-sm text-typography-600">
              This action cannot be undone. You can add the payment method again later if needed.
            </Text>
          </VStack>
        </ModalBody>

        <ModalFooter>
          <HStack space="md" className="w-full">
            <Button
              action="secondary"
              variant="outline"
              size="md"
              onPress={onClose}
              disabled={isRemoving}
              className="flex-1"
            >
              <ButtonText>Cancel</ButtonText>
            </Button>
            <Button
              action="negative"
              variant="solid"
              size="md"
              onPress={onConfirm}
              disabled={isRemoving}
              className="flex-1"
            >
              {isRemoving ? (
                <>
                  <Spinner size="sm" />
                  <ButtonText className="ml-2">Removing...</ButtonText>
                </>
              ) : (
                <>
                  <ButtonIcon as={Trash2} />
                  <ButtonText>Remove</ButtonText>
                </>
              )}
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}

/**
 * Payment Method Card Component
 */
export function PaymentMethodCard({
  paymentMethod,
  onSetDefault,
  onRemove,
  isSettingDefault,
  isRemoving,
  canRemove,
}: PaymentMethodCardProps) {
  const [showRemovalModal, setShowRemovalModal] = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  const brandInfo = getCardBrandInfo(paymentMethod.card.brand);

  const handleSetDefault = async () => {
    if (!paymentMethod.is_default) {
      await onSetDefault(paymentMethod.id);
    }
  };

  const handleRemove = async () => {
    try {
      await onRemove(paymentMethod.id);
      setShowRemovalModal(false);
    } catch (error) {
      // Error is handled by parent component
    }
  };

  return (
    <>
      <Card className={`p-4 ${paymentMethod.is_default ? 'border-primary-300 bg-primary-50' : ''}`}>
        <VStack space="sm">
          {/* Header with card info and actions */}
          <HStack className="items-center justify-between">
            <HStack space="sm" className="items-center flex-1">
              {/* Card Icon */}
              <div className={`p-2 rounded-md ${brandInfo.bgColor}`}>
                <Icon as={CreditCard} size="sm" className={brandInfo.color} />
              </div>

              {/* Card Details */}
              <VStack space="0" className="flex-1">
                <HStack space="sm" className="items-center">
                  <Text className="font-semibold text-typography-900">
                    {paymentMethod.card.brand.toUpperCase()} •••• {paymentMethod.card.last4}
                  </Text>
                  {paymentMethod.is_default && (
                    <Badge variant="solid" action="primary" size="sm">
                      <Icon as={Star} size="xs" />
                      <Text className="text-xs ml-1">Default</Text>
                    </Badge>
                  )}
                </HStack>
                <Text className="text-sm text-typography-600">
                  Expires {paymentMethod.card.exp_month.toString().padStart(2, '0')}/
                  {paymentMethod.card.exp_year}
                </Text>
              </VStack>
            </HStack>

            {/* Actions Menu */}
            <Menu
              isOpen={showMenu}
              onClose={() => setShowMenu(false)}
              onOpen={() => setShowMenu(true)}
              trigger={({ ...triggerProps }) => (
                <Pressable {...triggerProps}>
                  <Icon as={MoreVertical} size="sm" className="text-typography-400" />
                </Pressable>
              )}
            >
              {!paymentMethod.is_default && (
                <MenuItem key="set-default" onPress={handleSetDefault}>
                  <Icon as={Star} size="sm" />
                  <MenuItemLabel>
                    {isSettingDefault ? 'Setting as Default...' : 'Set as Default'}
                  </MenuItemLabel>
                </MenuItem>
              )}

              {!paymentMethod.is_default && canRemove && (
                <>
                  <MenuSeparator />
                  <MenuItem key="remove" onPress={() => setShowRemovalModal(true)}>
                    <Icon as={Trash2} size="sm" className="text-error-500" />
                    <MenuItemLabel className="text-error-700">Remove</MenuItemLabel>
                  </MenuItem>
                </>
              )}
            </Menu>
          </HStack>

          {/* Card Funding Type */}
          {paymentMethod.card.funding && (
            <HStack className="items-center">
              <Text className="text-xs text-typography-500">
                {paymentMethod.card.funding.charAt(0).toUpperCase() +
                  paymentMethod.card.funding.slice(1)}{' '}
                Card
              </Text>
            </HStack>
          )}

          {/* Billing Details */}
          {paymentMethod.billing_details.name && (
            <VStack space="xs">
              <Text className="text-xs font-medium text-typography-700">Billing Information</Text>
              <Text className="text-xs text-typography-600">
                {paymentMethod.billing_details.name}
              </Text>
              {paymentMethod.billing_details.address && (
                <Text className="text-xs text-typography-600">
                  {[
                    paymentMethod.billing_details.address.line1,
                    paymentMethod.billing_details.address.city,
                    paymentMethod.billing_details.address.state,
                    paymentMethod.billing_details.address.postal_code,
                  ]
                    .filter(Boolean)
                    .join(', ')}
                </Text>
              )}
            </VStack>
          )}

          {/* Footer */}
          <HStack className="items-center justify-between">
            <Text className="text-xs text-typography-500">
              Added {new Date(paymentMethod.created_at).toLocaleDateString()}
            </Text>

            {paymentMethod.is_default && (
              <HStack space="xs" className="items-center">
                <Icon as={Check} size="xs" className="text-success-500" />
                <Text className="text-xs text-success-600">Default payment method</Text>
              </HStack>
            )}
          </HStack>

          {/* Loading States */}
          {(isSettingDefault || isRemoving) && (
            <HStack
              space="xs"
              className="items-center justify-center p-2 bg-background-100 rounded-md"
            >
              <Spinner size="sm" />
              <Text className="text-xs text-typography-600">
                {isSettingDefault ? 'Setting as default...' : 'Removing...'}
              </Text>
            </HStack>
          )}
        </VStack>
      </Card>

      {/* Removal Confirmation Modal */}
      <RemovalConfirmationModal
        isOpen={showRemovalModal}
        onClose={() => setShowRemovalModal(false)}
        onConfirm={handleRemove}
        paymentMethod={paymentMethod}
        isRemoving={isRemoving}
      />
    </>
  );
}
