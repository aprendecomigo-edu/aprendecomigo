/**
 * Stripe Payment Form - Common Logic and Types
 *
 * Shared business logic, types, and utilities for Stripe payment processing
 * across web and native platforms.
 */

import { CreditCard, Lock, AlertCircle, CheckCircle } from 'lucide-react-native';
import React from 'react';

import { Alert } from '@/components/ui/alert';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import type { PricingPlan, StripeConfig } from '@/types/purchase';

// Shared types and interfaces
export interface StripePaymentFormProps {
  stripeConfig: StripeConfig;
  clientSecret: string;
  selectedPlan: PricingPlan;
  onPaymentSuccess: () => void;
  onPaymentError: (error: string) => void;
  disabled?: boolean;
  className?: string;
}

// Format price for display
export const formatPrice = (price: string): string => {
  const numPrice = parseFloat(price);
  return numPrice % 1 === 0 ? numPrice.toString() : numPrice.toFixed(2);
};

// Shared loading state component
export function LoadingState({ className }: { className?: string }) {
  return (
    <Card className={`p-6 ${className}`}>
      <VStack space="md" className="items-center">
        <Spinner size="large" />
        <Text className="text-typography-600">Loading payment form...</Text>
      </VStack>
    </Card>
  );
}

// Shared error state component
export function ErrorState({ error, className }: { error: string; className?: string }) {
  return (
    <Card className={`p-6 ${className}`}>
      <Alert action="error" variant="solid">
        <Icon as={AlertCircle} className="text-error-600" />
        <VStack space="sm" className="flex-1">
          <Heading size="sm" className="text-error-900">
            Payment Setup Error
          </Heading>
          <Text className="text-error-800 text-sm">{error}</Text>
        </VStack>
      </Alert>
    </Card>
  );
}

// Shared platform not supported component
export function PlatformNotSupportedState({ className }: { className?: string }) {
  return (
    <Card className={`p-6 ${className}`}>
      <VStack space="md" className="items-center">
        <Icon as={AlertCircle} size="xl" className="text-warning-500" />
        <VStack space="sm" className="items-center">
          <Heading size="md" className="text-typography-900">
            Payment Processing
          </Heading>
          <Text className="text-typography-600 text-center">
            Payment processing is currently available on the web version. Please visit our website
            to complete your purchase.
          </Text>
        </VStack>
      </VStack>
    </Card>
  );
}

// Shared order summary component
export function OrderSummary({ selectedPlan }: { selectedPlan: PricingPlan }) {
  return (
    <Card className="p-4 bg-background-50">
      <VStack space="sm">
        <HStack className="items-center justify-between">
          <Text className="font-medium text-typography-800">{selectedPlan.name}</Text>
          <Text className="font-bold text-typography-900">
            €{formatPrice(selectedPlan.price_eur)}
          </Text>
        </HStack>
        <Text className="text-sm text-typography-600">{selectedPlan.description}</Text>
        <HStack className="items-center justify-between">
          <Text className="text-sm text-typography-600">Hours included:</Text>
          <Text className="text-sm font-medium text-typography-800">
            {selectedPlan.hours_included}
          </Text>
        </HStack>
      </VStack>
    </Card>
  );
}

// Shared security notice component
export function SecurityNotice() {
  return (
    <HStack space="xs" className="items-center justify-center p-3 bg-success-50 rounded-lg">
      <Icon as={Lock} size="sm" className="text-success-600" />
      <Text className="text-sm text-success-800">
        Secure Payment - Your payment information is secure and encrypted
      </Text>
    </HStack>
  );
}

// Shared payment form header
export function PaymentFormHeader({ selectedPlan }: { selectedPlan: PricingPlan }) {
  return (
    <VStack space="sm">
      <HStack space="sm" className="items-center">
        <Icon as={CreditCard} size="lg" className="text-primary-600" />
        <Heading size="lg" className="text-typography-900">
          Complete Payment
        </Heading>
      </HStack>
      <OrderSummary selectedPlan={selectedPlan} />
    </VStack>
  );
}

// Shared payment error display
export function PaymentErrorDisplay({ error }: { error: string }) {
  return (
    <Alert action="error" variant="solid">
      <Icon as={AlertCircle} className="text-error-600" />
      <VStack space="sm" className="flex-1">
        <Heading size="sm" className="text-error-900">
          Payment Error
        </Heading>
        <Text className="text-error-800 text-sm">{error}</Text>
      </VStack>
    </Alert>
  );
}

// Shared submit button component
export function SubmitButton({
  isProcessing,
  disabled,
  selectedPlan,
  onSubmit,
}: {
  isProcessing: boolean;
  disabled: boolean;
  selectedPlan: PricingPlan;
  onSubmit: () => void;
}) {
  return (
    <Button
      action="primary"
      variant="solid"
      size="lg"
      className="w-full"
      disabled={disabled || isProcessing}
      onPress={onSubmit}
    >
      {isProcessing ? (
        <>
          <Spinner size="sm" />
          <ButtonText className="ml-2">Processing...</ButtonText>
        </>
      ) : (
        <>
          <ButtonIcon as={CheckCircle} />
          <ButtonText>Complete Purchase - €{formatPrice(selectedPlan.price_eur)}</ButtonText>
        </>
      )}
    </Button>
  );
}

// Shared terms notice
export function TermsNotice() {
  return (
    <Text className="text-xs text-typography-500 text-center">
      By clicking "Pay", you agree to our Terms of Service and acknowledge our Privacy Policy. Your
      payment will be processed securely by Stripe.
    </Text>
  );
}
