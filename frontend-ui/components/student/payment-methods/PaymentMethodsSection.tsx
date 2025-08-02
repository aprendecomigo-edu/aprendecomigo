/**
 * Payment Methods Section Component
 *
 * Displays and manages payment methods in the Account Settings tab.
 * Provides functionality to add, remove, and set default payment methods.
 */

import { CreditCard, Plus, AlertTriangle, RefreshCw } from 'lucide-react-native';
import React, { useState } from 'react';

import { AddPaymentMethodModal } from './AddPaymentMethodModal';
import { PaymentMethodCard } from './PaymentMethodCard';

import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { usePaymentMethods } from '@/hooks/usePaymentMethods';

interface PaymentMethodsSectionProps {
  email?: string;
}

/**
 * Payment Methods Section Component
 */
export function PaymentMethodsSection({ email }: PaymentMethodsSectionProps) {
  const {
    paymentMethods,
    loading,
    error,
    removing,
    settingDefault,
    operationError,
    refreshPaymentMethods,
    removePaymentMethod,
    setDefaultPaymentMethod,
    clearErrors,
    hasPaymentMethods,
  } = usePaymentMethods(email);

  const [showAddModal, setShowAddModal] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [settingDefaultId, setSettingDefaultId] = useState<string | null>(null);

  const handleAddPaymentMethod = () => {
    setShowAddModal(true);
    clearErrors();
  };

  const handleAddSuccess = async () => {
    setShowAddModal(false);
    await refreshPaymentMethods();
  };

  const handleRemovePaymentMethod = async (id: string) => {
    setRemovingId(id);
    try {
      await removePaymentMethod(id);
    } catch (error) {
      // Error is handled by the hook
    } finally {
      setRemovingId(null);
    }
  };

  const handleSetDefaultPaymentMethod = async (id: string) => {
    setSettingDefaultId(id);
    try {
      await setDefaultPaymentMethod(id);
    } catch (error) {
      // Error is handled by the hook
    } finally {
      setSettingDefaultId(null);
    }
  };

  const canRemoveMethod = (methodId: string) => {
    const method = paymentMethods.find(m => m.id === methodId);
    // Can't remove if it's the only payment method or if it's the default and there are others
    return hasPaymentMethods && paymentMethods.length > 1 && !method?.is_default;
  };

  if (loading && !hasPaymentMethods) {
    return (
      <Card className="p-6">
        <VStack space="lg">
          <HStack className="items-center">
            <Icon as={CreditCard} size="sm" className="text-typography-600 mr-2" />
            <Heading size="md" className="text-typography-900">
              Payment Methods
            </Heading>
          </HStack>

          <VStack space="md" className="items-center py-8">
            <Spinner size="large" />
            <Text className="text-typography-600">Loading payment methods...</Text>
          </VStack>
        </VStack>
      </Card>
    );
  }

  if (error && !hasPaymentMethods) {
    return (
      <Card className="p-6">
        <VStack space="lg">
          <HStack className="items-center">
            <Icon as={CreditCard} size="sm" className="text-typography-600 mr-2" />
            <Heading size="md" className="text-typography-900">
              Payment Methods
            </Heading>
          </HStack>

          <VStack space="md" className="items-center py-8">
            <Icon as={AlertTriangle} size="xl" className="text-error-500" />
            <VStack space="sm" className="items-center">
              <Heading size="sm" className="text-error-900">
                Unable to Load Payment Methods
              </Heading>
              <Text className="text-error-700 text-sm text-center">{error}</Text>
            </VStack>
            <Button action="secondary" variant="outline" size="sm" onPress={refreshPaymentMethods}>
              <ButtonIcon as={RefreshCw} />
              <ButtonText>Try Again</ButtonText>
            </Button>
          </VStack>
        </VStack>
      </Card>
    );
  }

  return (
    <>
      <Card className="p-6">
        <VStack space="lg">
          {/* Header */}
          <HStack className="items-center justify-between">
            <VStack space="xs">
              <HStack className="items-center">
                <Icon as={CreditCard} size="sm" className="text-typography-600 mr-2" />
                <Heading size="md" className="text-typography-900">
                  Payment Methods
                </Heading>
              </HStack>
              <Text className="text-sm text-typography-600">
                Manage your saved payment methods for tutoring hour purchases
              </Text>
            </VStack>

            <Button action="primary" variant="solid" size="sm" onPress={handleAddPaymentMethod}>
              <ButtonIcon as={Plus} />
              <ButtonText>Add Payment Method</ButtonText>
            </Button>
          </HStack>

          {/* Operation error display */}
          {operationError && (
            <Card className="p-4 border-error-200 bg-error-50">
              <HStack space="sm" className="items-center">
                <Icon as={AlertTriangle} size="sm" className="text-error-500" />
                <VStack space="xs" className="flex-1">
                  <Text className="text-sm font-medium text-error-800">Operation Failed</Text>
                  <Text className="text-sm text-error-700">{operationError}</Text>
                </VStack>
                <Button action="secondary" variant="outline" size="xs" onPress={clearErrors}>
                  <ButtonText>Dismiss</ButtonText>
                </Button>
              </HStack>
            </Card>
          )}

          {/* Payment Methods List */}
          {hasPaymentMethods ? (
            <VStack space="md">
              {paymentMethods.map(method => (
                <PaymentMethodCard
                  key={method.id}
                  paymentMethod={method}
                  onSetDefault={handleSetDefaultPaymentMethod}
                  onRemove={handleRemovePaymentMethod}
                  isSettingDefault={settingDefaultId === method.id}
                  isRemoving={removingId === method.id}
                  canRemove={canRemoveMethod(method.id)}
                />
              ))}

              {/* Refresh button */}
              <HStack className="justify-center pt-4">
                <Button
                  action="secondary"
                  variant="outline"
                  size="sm"
                  onPress={refreshPaymentMethods}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <Spinner size="sm" />
                      <ButtonText className="ml-2">Refreshing...</ButtonText>
                    </>
                  ) : (
                    <>
                      <ButtonIcon as={RefreshCw} />
                      <ButtonText>Refresh</ButtonText>
                    </>
                  )}
                </Button>
              </HStack>
            </VStack>
          ) : (
            /* Empty State */
            <VStack space="md" className="items-center py-8">
              <Icon as={CreditCard} size="xl" className="text-typography-300" />
              <VStack space="xs" className="items-center">
                <Text className="font-medium text-typography-600">No Payment Methods</Text>
                <Text className="text-sm text-typography-500 text-center max-w-sm">
                  Add a payment method to make purchasing tutoring hours more convenient. Your
                  payment information is stored securely.
                </Text>
              </VStack>
              <Button action="primary" variant="solid" size="md" onPress={handleAddPaymentMethod}>
                <ButtonIcon as={Plus} />
                <ButtonText>Add Your First Payment Method</ButtonText>
              </Button>
            </VStack>
          )}

          {/* Security Notice */}
          <Card className="p-4 bg-success-50 border-success-200">
            <VStack space="sm">
              <Text className="text-sm font-medium text-success-800">
                Secure Payment Processing
              </Text>
              <Text className="text-sm text-success-700">
                All payment methods are processed and stored securely by Stripe. We never store your
                complete card information on our servers.
              </Text>
            </VStack>
          </Card>
        </VStack>
      </Card>

      {/* Add Payment Method Modal */}
      <AddPaymentMethodModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={handleAddSuccess}
      />
    </>
  );
}
