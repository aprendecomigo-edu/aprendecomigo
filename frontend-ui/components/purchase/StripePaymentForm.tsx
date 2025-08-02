/**
 * Stripe Payment Form Component
 *
 * Integrates with Stripe Elements for secure payment processing.
 * Handles payment form display, validation, and submission with comprehensive error handling.
 */

import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import { CreditCard, Lock, AlertCircle, CheckCircle } from 'lucide-react-native';
import React, { useEffect, useState } from 'react';
import { Platform } from 'react-native';

import { Alert } from '@/components/ui/alert';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { View } from '@/components/ui/view';
import { VStack } from '@/components/ui/vstack';
import type { PricingPlan, StripeConfig } from '@/types/purchase';

// Web-only Stripe integration
const isWeb = Platform.OS === 'web';

interface StripePaymentFormProps {
  stripeConfig: StripeConfig;
  clientSecret: string;
  selectedPlan: PricingPlan;
  onPaymentSuccess: () => void;
  onPaymentError: (error: string) => void;
  disabled?: boolean;
  className?: string;
}

/**
 * Main Stripe payment form wrapper component.
 */
export function StripePaymentForm({
  stripeConfig,
  clientSecret,
  selectedPlan,
  onPaymentSuccess,
  onPaymentError,
  disabled = false,
  className = '',
}: StripePaymentFormProps) {
  const [stripePromise, setStripePromise] = useState<any>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    if (!isWeb) {
      setLoadError('Payment processing is only available on web platform');
      return;
    }

    if (!stripeConfig.public_key) {
      setLoadError('Payment configuration not available');
      return;
    }

    // Load Stripe
    const loadStripeInstance = async () => {
      try {
        const stripe = await loadStripe(stripeConfig.public_key);
        if (!stripe) {
          throw new Error('Failed to load Stripe');
        }
        setStripePromise(stripe);
      } catch (error: any) {
        console.error('Error loading Stripe:', error);
        setLoadError('Failed to load payment processor');
      }
    };

    loadStripeInstance();
  }, [stripeConfig.public_key]);

  // Show platform not supported message for mobile
  if (!isWeb) {
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

  // Show loading state
  if (!stripePromise && !loadError) {
    return (
      <Card className={`p-6 ${className}`}>
        <VStack space="md" className="items-center">
          <Spinner size="large" />
          <Text className="text-typography-600">Loading payment form...</Text>
        </VStack>
      </Card>
    );
  }

  // Show load error
  if (loadError) {
    return (
      <Card className={`p-6 ${className}`}>
        <Alert action="error" variant="solid">
          <Icon as={AlertCircle} className="text-error-600" />
          <VStack space="sm" className="flex-1">
            <Heading size="sm" className="text-error-900">
              Payment Setup Error
            </Heading>
            <Text className="text-error-800 text-sm">{loadError}</Text>
          </VStack>
        </Alert>
      </Card>
    );
  }

  const elementsOptions = {
    clientSecret,
    appearance: {
      theme: 'stripe' as const,
      variables: {
        colorPrimary: '#6366f1',
        colorBackground: '#ffffff',
        colorText: '#1f2937',
        colorDanger: '#ef4444',
        fontFamily: 'system-ui, sans-serif',
        spacingUnit: '4px',
        borderRadius: '8px',
      },
    },
  };

  return (
    <Elements stripe={stripePromise} options={elementsOptions}>
      <PaymentFormContent
        selectedPlan={selectedPlan}
        onPaymentSuccess={onPaymentSuccess}
        onPaymentError={onPaymentError}
        disabled={disabled}
        className={className}
      />
    </Elements>
  );
}

/**
 * Internal payment form content component that uses Stripe hooks.
 */
function PaymentFormContent({
  selectedPlan,
  onPaymentSuccess,
  onPaymentError,
  disabled,
  className,
}: {
  selectedPlan: PricingPlan;
  onPaymentSuccess: () => void;
  onPaymentError: (error: string) => void;
  disabled?: boolean;
  className?: string;
}) {
  const stripe = useStripe();
  const elements = useElements();
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentError, setPaymentError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!stripe || !elements || isProcessing || disabled) {
      return;
    }

    setIsProcessing(true);
    setPaymentError(null);

    try {
      const { error, paymentIntent } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/purchase/success`,
        },
        redirect: 'if_required',
      });

      if (error) {
        console.error('Payment confirmation failed:', error);
        const errorMessage = error.message || 'Payment failed';
        setPaymentError(errorMessage);
        onPaymentError(errorMessage);
      } else if (paymentIntent?.status === 'succeeded') {
        onPaymentSuccess();
      } else {
        const errorMessage = 'Payment processing incomplete';
        setPaymentError(errorMessage);
        onPaymentError(errorMessage);
      }
    } catch (error: any) {
      console.error('Payment processing error:', error);
      const errorMessage = error.message || 'Payment processing failed';
      setPaymentError(errorMessage);
      onPaymentError(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  // Format price for display
  const formatPrice = (price: string) => {
    const numPrice = parseFloat(price);
    return numPrice % 1 === 0 ? numPrice.toString() : numPrice.toFixed(2);
  };

  return (
    <Card className={`p-6 ${className}`}>
      <form onSubmit={handleSubmit}>
        <VStack space="lg">
          {/* Payment form header */}
          <VStack space="sm">
            <HStack space="sm" className="items-center">
              <Icon as={CreditCard} size="lg" className="text-primary-600" />
              <Heading size="lg" className="text-typography-900">
                Payment Details
              </Heading>
            </HStack>

            {/* Order summary */}
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
          </VStack>

          {/* Stripe Payment Element */}
          <VStack space="sm">
            <Text className="font-medium text-typography-800">Card Information</Text>
            <View className="p-3 border border-outline-200 rounded-lg bg-white">
              <PaymentElement />
            </View>
          </VStack>

          {/* Payment error display */}
          {paymentError && (
            <Alert action="error" variant="solid">
              <Icon as={AlertCircle} className="text-error-600" />
              <VStack space="sm" className="flex-1">
                <Heading size="sm" className="text-error-900">
                  Payment Error
                </Heading>
                <Text className="text-error-800 text-sm">{paymentError}</Text>
              </VStack>
            </Alert>
          )}

          {/* Security notice */}
          <HStack space="xs" className="items-center justify-center p-3 bg-success-50 rounded-lg">
            <Icon as={Lock} size="sm" className="text-success-600" />
            <Text className="text-sm text-success-800">
              Your payment information is secure and encrypted
            </Text>
          </HStack>

          {/* Submit button */}
          <Button
            type="submit"
            action="primary"
            variant="solid"
            size="lg"
            className="w-full"
            disabled={!stripe || !elements || isProcessing || disabled}
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

          {/* Terms notice */}
          <Text className="text-xs text-typography-500 text-center">
            By completing this purchase, you agree to our Terms of Service and acknowledge our
            Privacy Policy. Your payment will be processed securely by Stripe.
          </Text>
        </VStack>
      </form>
    </Card>
  );
}
