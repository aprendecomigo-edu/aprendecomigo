/**
 * Add Payment Method Modal - Web Implementation
 *
 * Web-specific implementation using Stripe Elements for secure payment method addition.
 * Allows users to securely add new payment methods with proper validation and error handling.
 */

import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import { Plus, AlertCircle } from 'lucide-react-native';
import React, { useState, useEffect } from 'react';

import {
  AddPaymentMethodModalProps,
  PaymentMethodModalHeader,
  LoadingContent,
  ErrorContent,
  SecurityNotice,
  TermsNotice,
} from './add-payment-method-common';

import { PurchaseApiClient } from '@/api/purchaseApi';
import { Alert } from '@/components/ui/alert';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Modal, ModalBackdrop, ModalBody, ModalContent } from '@/components/ui/modal';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { View } from '@/components/ui/view';
import { VStack } from '@/components/ui/vstack';
import { usePaymentMethods } from '@/hooks/usePaymentMethods';
import type { StripeConfig } from '@/types/purchase';

/**
 * Payment method form content component that uses Stripe hooks
 */
function PaymentMethodFormContent({
  onSuccess,
  onError,
  hasPaymentMethods,
}: {
  onSuccess: () => void;
  onError: (error: string) => void;
  hasPaymentMethods: boolean;
}) {
  const stripe = useStripe();
  const elements = useElements();
  const { addPaymentMethod, adding } = usePaymentMethods();

  const [isProcessing, setIsProcessing] = useState(false);
  const [setAsDefault, setSetAsDefault] = useState(!hasPaymentMethods); // Auto-set as default if no existing methods
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!stripe || !elements || isProcessing) {
      return;
    }

    setIsProcessing(true);
    setFormError(null);

    try {
      // Create a payment method
      const { error, paymentMethod } = await stripe.createPaymentMethod({
        elements,
        params: {
          billing_details: {
            // These would be collected from additional form fields if needed
          },
        },
      });

      if (error) {
        console.error('Payment method creation failed:', error);
        const errorMessage = error.message || 'Failed to create payment method';
        setFormError(errorMessage);
        onError(errorMessage);
        return;
      }

      if (!paymentMethod) {
        const errorMessage = 'Payment method creation failed';
        setFormError(errorMessage);
        onError(errorMessage);
        return;
      }

      // Add the payment method via our API
      const result = await addPaymentMethod({
        payment_method_id: paymentMethod.id,
        set_as_default: setAsDefault,
      });

      if (result?.success) {
        onSuccess();
      } else {
        const errorMessage = result?.message || 'Failed to save payment method';
        setFormError(errorMessage);
        onError(errorMessage);
      }
    } catch (error: any) {
      console.error('Error adding payment method:', error);
      const errorMessage = error.message || 'Failed to add payment method';
      setFormError(errorMessage);
      onError(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <VStack space="lg">
        {/* Stripe Payment Element for card collection */}
        <VStack space="sm">
          <Text className="font-medium text-typography-800">Card Information</Text>
          <View className="p-3 border border-outline-200 rounded-lg bg-white">
            <PaymentElement
              options={{
                layout: 'tabs',
                paymentMethodOrder: ['card'],
              }}
            />
          </View>
        </VStack>

        {/* Set as default option */}
        <HStack space="sm" className="items-center">
          <Checkbox
            value="set-default"
            isChecked={setAsDefault}
            onChange={checked => setSetAsDefault(checked)}
            aria-label="Set as default payment method"
          />
          <VStack space="0" className="flex-1">
            <Text className="text-sm font-medium text-typography-800">
              Set as default payment method
            </Text>
            <Text className="text-xs text-typography-600">
              {hasPaymentMethods
                ? 'Use this card for future purchases by default'
                : 'This will be your default payment method'}
            </Text>
          </VStack>
        </HStack>

        {/* Form error display */}
        {formError && (
          <Alert action="error" variant="solid">
            <Icon as={AlertCircle} className="text-error-600" />
            <VStack space="sm" className="flex-1">
              <Heading size="sm" className="text-error-900">
                Error Adding Payment Method
              </Heading>
              <Text className="text-error-800 text-sm">{formError}</Text>
            </VStack>
          </Alert>
        )}

        {/* Security notice */}
        <SecurityNotice />

        {/* Submit button */}
        <Button
          type="submit"
          action="primary"
          variant="solid"
          size="lg"
          className="w-full"
          disabled={!stripe || !elements || isProcessing || adding}
        >
          {isProcessing || adding ? (
            <>
              <Spinner size="sm" />
              <ButtonText className="ml-2">Adding Payment Method...</ButtonText>
            </>
          ) : (
            <>
              <ButtonIcon as={Plus} />
              <ButtonText>Add Payment Method</ButtonText>
            </>
          )}
        </Button>

        {/* Terms notice */}
        <TermsNotice />
      </VStack>
    </form>
  );
}

/**
 * Add Payment Method Modal Component - Web Implementation
 */
export function AddPaymentMethodModal({ isOpen, onClose, onSuccess }: AddPaymentMethodModalProps) {
  const { hasPaymentMethods } = usePaymentMethods();
  const [stripePromise, setStripePromise] = useState<any>(null);
  const [stripeConfig, setStripeConfig] = useState<StripeConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load Stripe configuration when modal opens
  useEffect(() => {
    if (isOpen && !stripeConfig) {
      loadStripeConfiguration();
    }
  }, [isOpen]);

  const loadStripeConfiguration = async () => {
    setLoading(true);
    setError(null);

    try {
      const config = await PurchaseApiClient.getStripeConfig();
      setStripeConfig(config);

      if (config.public_key) {
        const stripe = await loadStripe(config.public_key);
        if (!stripe) {
          throw new Error('Failed to load Stripe');
        }
        setStripePromise(stripe);
      }
    } catch (error: any) {
      console.error('Error loading Stripe configuration:', error);
      setError(error.message || 'Failed to load payment processor');
    } finally {
      setLoading(false);
    }
  };

  const handleSuccess = () => {
    onSuccess();
    onClose();
  };

  const handleError = (errorMessage: string) => {
    setError(errorMessage);
  };

  const handleClose = () => {
    setError(null);
    onClose();
  };

  const elementsOptions = stripePromise
    ? {
        mode: 'setup' as const,
        currency: 'eur',
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
      }
    : undefined;

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="lg">
      <ModalBackdrop />
      <ModalContent className="max-w-lg mx-auto">
        <PaymentMethodModalHeader onClose={handleClose} />

        <ModalBody>
          {/* Loading state */}
          {loading && <LoadingContent />}

          {/* Error state */}
          {error && !loading && <ErrorContent error={error} onRetry={loadStripeConfiguration} />}

          {/* Stripe form */}
          {stripePromise && stripeConfig && !loading && !error && (
            <Elements stripe={stripePromise} options={elementsOptions}>
              <PaymentMethodFormContent
                onSuccess={handleSuccess}
                onError={handleError}
                hasPaymentMethods={hasPaymentMethods}
              />
            </Elements>
          )}
        </ModalBody>
      </ModalContent>
    </Modal>
  );
}
