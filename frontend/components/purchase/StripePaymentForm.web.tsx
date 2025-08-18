/**
 * Stripe Payment Form - Web Implementation
 *
 * Web-specific implementation using Stripe Elements for secure payment processing.
 * Handles payment form display, validation, and submission with comprehensive error handling.
 */

import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import React, { useEffect, useState } from 'react';

import {
  StripePaymentFormProps,
  LoadingState,
  ErrorState,
  PaymentFormHeader,
  PaymentErrorDisplay,
  SecurityNotice,
  TermsNotice,
  formatPrice,
} from './stripe-payment-common';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { View } from '@/components/ui/view';
import { VStack } from '@/components/ui/vstack';

/**
 * Main Stripe payment form wrapper component for web.
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
        if (__DEV__) {
          console.error('Error loading Stripe:', error);
        }
        setLoadError('Failed to load payment processor');
      }
    };

    loadStripeInstance();
  }, [stripeConfig.public_key]);

  // Show loading state
  if (!stripePromise && !loadError) {
    return <LoadingState className={className} />;
  }

  // Show load error
  if (loadError) {
    return <ErrorState error={loadError} className={className} />;
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
  selectedPlan: any;
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
        if (__DEV__) {
          console.error('Payment confirmation failed:', error);
        }
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
      if (__DEV__) {
        console.error('Payment processing error:', error);
      }
      const errorMessage = error.message || 'Payment processing failed';
      setPaymentError(errorMessage);
      onPaymentError(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Card className={`p-6 ${className}`}>
      <form onSubmit={handleSubmit} role="form">
        <VStack space="lg">
          {/* Payment form header */}
          <PaymentFormHeader selectedPlan={selectedPlan} />

          {/* Stripe Payment Element */}
          <VStack space="sm">
            <Text className="font-medium text-typography-800">Card Information</Text>
            <View className="p-3 border border-outline-200 rounded-lg bg-white">
              <PaymentElement />
            </View>
          </VStack>

          {/* Payment error display */}
          {paymentError && <PaymentErrorDisplay error={paymentError} />}

          {/* Security notice */}
          <SecurityNotice />

          {/* Submit button */}
          <Button
            action="primary"
            variant="solid"
            size="lg"
            className="w-full"
            disabled={!stripe || !elements || disabled || isProcessing}
            type="submit"
            role="button"
          >
            {isProcessing ? (
              <>
                <Spinner size="sm" />
                <Text className="ml-2">Processing...</Text>
              </>
            ) : (
              <Text>Pay €{formatPrice(selectedPlan.price_eur)}</Text>
            )}
          </Button>

          {/* Terms notice */}
          <TermsNotice />
        </VStack>
      </form>
    </Card>
  );
}
