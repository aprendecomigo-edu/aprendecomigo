/**
 * Saved Payment Selector Component
 *
 * Payment method selection component with default method highlighting
 * and support for biometric authentication confirmation.
 */

import { CreditCard, Check, Plus, Shield, Fingerprint } from 'lucide-react-native';
import React, { useState, useEffect } from 'react';

import { Alert, AlertIcon, AlertText } from '@/components/ui/alert';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { usePaymentMethods } from '@/hooks/usePaymentMethods';
import type { PaymentMethod, BiometricAuthState } from '@/types/purchase';

interface SavedPaymentSelectorProps {
  /** Optional email for admin access */
  email?: string;
  /** Currently selected payment method ID */
  selectedPaymentMethodId?: string;
  /** Callback when payment method is selected */
  onPaymentMethodSelect: (paymentMethod: PaymentMethod) => void;
  /** Callback when add new payment method is requested */
  onAddPaymentMethod?: () => void;
  /** Show biometric authentication option */
  enableBiometricAuth?: boolean;
  /** Callback when biometric auth is requested */
  onBiometricAuth?: (paymentMethod: PaymentMethod) => Promise<boolean>;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Show detailed card information */
  showCardDetails?: boolean;
}

/**
 * Saved Payment Selector Component
 *
 * Displays saved payment methods with selection functionality and biometric auth support.
 */
export function SavedPaymentSelector({
  email,
  selectedPaymentMethodId,
  onPaymentMethodSelect,
  onAddPaymentMethod,
  enableBiometricAuth = false,
  onBiometricAuth,
  size = 'md',
  showCardDetails = true,
}: SavedPaymentSelectorProps) {
  const { paymentMethods, loading, error } = usePaymentMethods(email);
  const [biometricState, setBiometricState] = useState<BiometricAuthState>({
    isSupported: false,
    isEnabled: enableBiometricAuth,
    isAuthenticating: false,
    error: null,
  });

  // Check biometric support on mount
  useEffect(() => {
    const checkBiometricSupport = async () => {
      // In a real implementation, you would check for biometric availability
      // This is a placeholder for the actual biometric API check
      const isSupported =
        enableBiometricAuth &&
        // Check for TouchID/FaceID on iOS or fingerprint on Android
        typeof window !== 'undefined' &&
        ('TouchID' in window || 'FaceID' in window || 'AndroidFingerprint' in window);

      setBiometricState(prev => ({
        ...prev,
        isSupported,
      }));
    };

    if (enableBiometricAuth) {
      checkBiometricSupport();
    }
  }, [enableBiometricAuth]);

  // Handle payment method selection with optional biometric auth
  const handlePaymentMethodSelect = async (paymentMethod: PaymentMethod) => {
    if (biometricState.isSupported && onBiometricAuth) {
      setBiometricState(prev => ({ ...prev, isAuthenticating: true, error: null }));

      try {
        const authenticated = await onBiometricAuth(paymentMethod);
        if (authenticated) {
          onPaymentMethodSelect(paymentMethod);
        }
      } catch (error: any) {
        setBiometricState(prev => ({
          ...prev,
          error: error.message || 'Biometric authentication failed',
        }));
      } finally {
        setBiometricState(prev => ({ ...prev, isAuthenticating: false }));
      }
    } else {
      onPaymentMethodSelect(paymentMethod);
    }
  };

  // Get card brand icon color
  const getCardBrandColor = (brand: string) => {
    switch (brand.toLowerCase()) {
      case 'visa':
        return 'text-blue-600';
      case 'mastercard':
        return 'text-red-600';
      case 'amex':
        return 'text-green-600';
      default:
        return 'text-typography-600';
    }
  };

  // Get size classes
  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return { card: 'p-3', text: 'text-sm', icon: 'sm' as const };
      case 'lg':
        return { card: 'p-5', text: 'text-base', icon: 'lg' as const };
      default:
        return { card: 'p-4', text: 'text-sm', icon: 'md' as const };
    }
  };

  const sizeClasses = getSizeClasses();

  if (loading) {
    return (
      <VStack space="sm">
        <Text className="font-medium text-typography-700">Payment Method</Text>
        <Card className={sizeClasses.card}>
          <Text className={`${sizeClasses.text} text-typography-600`}>
            Loading payment methods...
          </Text>
        </Card>
      </VStack>
    );
  }

  if (error) {
    return (
      <VStack space="sm">
        <Text className="font-medium text-typography-700">Payment Method</Text>
        <Alert action="error" variant="outline">
          <AlertIcon as={CreditCard} />
          <AlertText>Unable to load payment methods: {error}</AlertText>
        </Alert>
      </VStack>
    );
  }

  if (!paymentMethods.length) {
    return (
      <VStack space="sm">
        <Text className="font-medium text-typography-700">Payment Method</Text>
        <Card className={sizeClasses.card}>
          <VStack space="sm" className="items-center">
            <Icon as={CreditCard} size={sizeClasses.icon} className="text-typography-400" />
            <Text className={`${sizeClasses.text} text-typography-600 text-center`}>
              No saved payment methods
            </Text>
            {onAddPaymentMethod && (
              <Button action="primary" variant="outline" size="sm" onPress={onAddPaymentMethod}>
                <ButtonIcon as={Plus} />
                <ButtonText>Add Payment Method</ButtonText>
              </Button>
            )}
          </VStack>
        </Card>
      </VStack>
    );
  }

  return (
    <VStack space="sm">
      <HStack className="items-center justify-between">
        <Text className="font-medium text-typography-700">Payment Method</Text>
        {biometricState.isSupported && (
          <HStack space="xs" className="items-center">
            <Icon as={Fingerprint} size="xs" className="text-success-600" />
            <Text className="text-xs text-success-600">Biometric Auth</Text>
          </HStack>
        )}
      </HStack>

      {/* Biometric Error */}
      {biometricState.error && (
        <Alert action="error" variant="outline">
          <AlertIcon as={Shield} />
          <AlertText>{biometricState.error}</AlertText>
        </Alert>
      )}

      <VStack space="sm">
        {paymentMethods.map(method => {
          const isSelected = selectedPaymentMethodId === method.id;
          const isDefault = method.is_default;

          return (
            <Pressable
              key={method.id}
              onPress={() => handlePaymentMethodSelect(method)}
              disabled={biometricState.isAuthenticating}
            >
              <Card
                className={`${sizeClasses.card} border-2 ${
                  isSelected
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-outline-200 bg-background-0'
                } ${biometricState.isAuthenticating ? 'opacity-50' : ''}`}
              >
                <HStack className="items-center justify-between">
                  <HStack space="md" className="items-center flex-1">
                    {/* Card Icon */}
                    <Icon
                      as={CreditCard}
                      size={sizeClasses.icon}
                      className={getCardBrandColor(method.card.brand)}
                    />

                    {/* Card Details */}
                    <VStack space="xs" className="flex-1">
                      <HStack space="sm" className="items-center">
                        <Text className={`${sizeClasses.text} font-semibold text-typography-900`}>
                          {method.card.brand.toUpperCase()} ••••{method.card.last4}
                        </Text>
                        {isDefault && (
                          <Badge action="success" variant="solid" size="sm">
                            <BadgeText>Default</BadgeText>
                          </Badge>
                        )}
                      </HStack>

                      {showCardDetails && (
                        <VStack space="xs">
                          <Text className="text-xs text-typography-600">
                            Expires {method.card.exp_month.toString().padStart(2, '0')}/
                            {method.card.exp_year}
                          </Text>
                          {method.billing_details?.name && (
                            <Text className="text-xs text-typography-600">
                              {method.billing_details.name}
                            </Text>
                          )}
                        </VStack>
                      )}
                    </VStack>

                    {/* Selection Indicator */}
                    {isSelected && <Icon as={Check} size="sm" className="text-primary-600" />}
                  </HStack>
                </HStack>
              </Card>
            </Pressable>
          );
        })}

        {/* Add New Payment Method */}
        {onAddPaymentMethod && (
          <Pressable onPress={onAddPaymentMethod}>
            <Card
              className={`${sizeClasses.card} border-2 border-dashed border-outline-300 bg-background-0`}
            >
              <HStack space="md" className="items-center justify-center">
                <Icon as={Plus} size={sizeClasses.icon} className="text-typography-500" />
                <Text className={`${sizeClasses.text} text-typography-600`}>
                  Add New Payment Method
                </Text>
              </HStack>
            </Card>
          </Pressable>
        )}
      </VStack>

      {/* Security Notice */}
      <Card className="p-3 bg-success-50 border-success-200">
        <HStack space="sm" className="items-center">
          <Icon as={Shield} size="sm" className="text-success-600" />
          <VStack space="xs" className="flex-1">
            <Text className="text-xs font-medium text-success-800">Secure Payment Processing</Text>
            <Text className="text-xs text-success-700">
              Your payment methods are stored securely by Stripe and protected with
              industry-standard encryption.
            </Text>
          </VStack>
        </HStack>
      </Card>
    </VStack>
  );
}
