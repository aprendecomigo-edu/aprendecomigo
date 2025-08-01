/**
 * Add Payment Method Modal Component
 * 
 * Allows users to securely add new payment methods using Stripe Elements
 * with proper validation and error handling.
 */

import React, { useState, useEffect } from 'react';
import { Platform } from 'react-native';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { CreditCard, Plus, Lock, AlertCircle, X } from 'lucide-react-native';

import { Alert } from '@/components/ui/alert';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Modal, 
  ModalBackdrop, 
  ModalBody, 
  ModalCloseButton, 
  ModalContent, 
  ModalFooter, 
  ModalHeader 
} from '@/components/ui/modal';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { View } from '@/components/ui/view';
import { PurchaseApiClient } from '@/api/purchaseApi';
import { usePaymentMethods } from '@/hooks/usePaymentMethods';
import type { StripeConfig } from '@/types/purchase';

// Web-only Stripe integration
const isWeb = Platform.OS === 'web';

interface AddPaymentMethodModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

/**
 * Stripe setup intent creation for payment method addition
 */
async function createSetupIntent(): Promise<{ client_secret: string; setup_intent_id: string }> {
  try {
    // Note: This endpoint needs to be created in the backend
    const response = await PurchaseApiClient.getStripeConfig();
    
    // For now, we'll simulate this - in reality, you'd need a setup intent endpoint
    // POST /api/student-balance/payment-methods/setup-intent/
    throw new Error('Setup intent creation not yet implemented in backend');
  } catch (error: any) {
    console.error('Error creating setup intent:', error);
    throw new Error('Failed to initialize payment method setup');
  }
}

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
          <Text className="font-medium text-typography-800">
            Card Information
          </Text>
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
            onChange={(checked) => setSetAsDefault(checked)}
            aria-label="Set as default payment method"
          />
          <VStack space="0" className="flex-1">
            <Text className="text-sm font-medium text-typography-800">
              Set as default payment method
            </Text>
            <Text className="text-xs text-typography-600">
              {hasPaymentMethods 
                ? 'Use this card for future purchases by default'
                : 'This will be your default payment method'
              }
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
              <Text className="text-error-800 text-sm">
                {formError}
              </Text>
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
        <Text className="text-xs text-typography-500 text-center">
          By adding a payment method, you agree to our Terms of Service. 
          Your payment information is processed securely by Stripe.
        </Text>
      </VStack>
    </form>
  );
}

/**
 * Add Payment Method Modal Component
 */
export function AddPaymentMethodModal({
  isOpen,
  onClose,
  onSuccess,
}: AddPaymentMethodModalProps) {
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
    if (!isWeb) {
      setError('Payment method management is only available on web platform');
      return;
    }

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

  const elementsOptions = stripePromise ? {
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
  } : undefined;

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="lg">
      <ModalBackdrop />
      <ModalContent className="max-w-lg mx-auto">
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

        <ModalBody>
          {/* Platform not supported */}
          {!isWeb && (
            <VStack space="md" className="items-center py-8">
              <Icon as={AlertCircle} size="xl" className="text-warning-500" />
              <VStack space="sm" className="items-center">
                <Heading size="md" className="text-typography-900">
                  Web Only Feature
                </Heading>
                <Text className="text-typography-600 text-center">
                  Payment method management is currently available on the web version only. 
                  Please visit our website to manage your payment methods.
                </Text>
              </VStack>
            </VStack>
          )}

          {/* Loading state */}
          {isWeb && loading && (
            <VStack space="md" className="items-center py-8">
              <Spinner size="large" />
              <Text className="text-typography-600">Loading payment form...</Text>
            </VStack>
          )}

          {/* Error state */}
          {isWeb && error && !loading && (
            <VStack space="md" className="py-4">
              <Alert action="error" variant="solid">
                <Icon as={AlertCircle} className="text-error-600" />
                <VStack space="sm" className="flex-1">
                  <Heading size="sm" className="text-error-900">
                    Setup Error
                  </Heading>
                  <Text className="text-error-800 text-sm">
                    {error}
                  </Text>
                </VStack>
              </Alert>
              <Button
                action="secondary"
                variant="outline"
                size="sm"
                onPress={loadStripeConfiguration}
              >
                <ButtonText>Try Again</ButtonText>
              </Button>
            </VStack>
          )}

          {/* Stripe form */}
          {isWeb && stripePromise && stripeConfig && !loading && !error && (
            <Elements stripe={stripePromise} options={elementsOptions}>
              <PaymentMethodFormContent
                onSuccess={handleSuccess}
                onError={handleError}
                hasPaymentMethods={hasPaymentMethods}
              />
            </Elements>
          )}
        </ModalBody>

        {/* Footer only for non-web or error states */}
        {(!isWeb || error) && (
          <ModalFooter className="pt-4">
            <Button
              action="secondary"
              variant="outline"
              size="md"
              onPress={handleClose}
              className="w-full"
            >
              <ButtonText>Close</ButtonText>
            </Button>
          </ModalFooter>
        )}
      </ModalContent>
    </Modal>
  );
}