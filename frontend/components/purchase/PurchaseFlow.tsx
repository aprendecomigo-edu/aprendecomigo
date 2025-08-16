/**
 * Purchase Flow Orchestrator Component
 *
 * Manages the complete purchase process from plan selection to payment completion.
 * Handles state transitions, error handling, and provides a seamless user experience.
 */

import { CheckCircle, XCircle, ArrowLeft, ShoppingCart } from 'lucide-react-native';
import React, { useEffect, useCallback, useMemo } from 'react';

import { PricingPlanSelector } from './PricingPlanSelector';
import { StripePaymentForm } from './StripePaymentForm';
import { StudentInfoForm } from './StudentInfoForm';

import { Alert } from '@/components/ui/alert';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Progress } from '@/components/ui/progress';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { usePurchaseFlow } from '@/hooks/usePurchaseFlow';

interface PurchaseFlowProps {
  onPurchaseComplete?: (transactionId: number) => void;
  onCancel?: () => void;
  className?: string;
}

/**
 * Main purchase flow component that orchestrates the entire purchase process.
 */
export function PurchaseFlow({ onPurchaseComplete, onCancel, className = '' }: PurchaseFlowProps) {
  const { state, actions, isLoading, canProceed } = usePurchaseFlow();

  // Handle successful purchase completion
  useEffect(() => {
    if (state.step === 'success' && state.transactionId) {
      onPurchaseComplete?.(state.transactionId);
    }
  }, [state.step, state.transactionId, onPurchaseComplete]);

  // Calculate progress percentage
  const progressPercentage = useMemo(() => {
    switch (state.step) {
      case 'plan-selection':
        return 25;
      case 'user-info':
        return 50;
      case 'payment':
        return 75;
      case 'success':
        return 100;
      default:
        return 0;
    }
  }, [state.step]);

  // Get step title
  const stepTitle = useMemo(() => {
    switch (state.step) {
      case 'plan-selection':
        return 'Select Plan';
      case 'user-info':
        return 'Student Information';
      case 'payment':
        return 'Payment';
      case 'success':
        return 'Purchase Complete';
      case 'error':
        return 'Error';
      default:
        return 'Purchase';
    }
  }, [state.step]);

  const handleBackToPlans = useCallback(() => {
    actions.selectPlan(state.formData.selectedPlan);
  }, [actions, state.formData.selectedPlan]);

  const handlePaymentSuccess = useCallback(() => {
    // Payment success is handled by the usePurchaseFlow hook
    // The state will automatically transition to 'success'
  }, []);

  const handlePaymentError = useCallback(
    (error: string) => {
      actions.setError(error);
    },
    [actions],
  );

  return (
    <SafeAreaView className={`flex-1 bg-background-50 ${className}`}>
      <ScrollView className="flex-1">
        <VStack className="flex-1 px-4 py-6 max-w-4xl mx-auto w-full" space="lg">
          {/* Header with progress */}
          <VStack space="md">
            <HStack className="items-center justify-between">
              <VStack space="xs" className="flex-1">
                <Heading size="2xl" className="text-typography-900">
                  {stepTitle}
                </Heading>
                <Text className="text-typography-600">
                  Step {Math.ceil(progressPercentage / 25)} of 4
                </Text>
              </VStack>

              {onCancel && state.step !== 'success' && (
                <Button action="secondary" variant="outline" size="sm" onPress={onCancel}>
                  <ButtonIcon as={XCircle} />
                  <ButtonText>Cancel</ButtonText>
                </Button>
              )}
            </HStack>

            {/* Progress bar */}
            <Progress value={progressPercentage} className="w-full" size="sm" />
          </VStack>

          {/* Main content based on current step */}
          {state.step === 'plan-selection' && (
            <PricingPlanSelector
              selectedPlan={state.formData.selectedPlan}
              onPlanSelect={actions.selectPlan}
              disabled={isLoading}
            />
          )}

          {state.step === 'user-info' && state.formData.selectedPlan && (
            <StudentInfoForm
              selectedPlan={state.formData.selectedPlan}
              studentName={state.formData.studentName}
              studentEmail={state.formData.studentEmail}
              errors={state.formData.errors}
              onInfoChange={actions.updateStudentInfo}
              onSubmit={actions.initiatePurchase}
              onBack={handleBackToPlans}
              disabled={isLoading}
            />
          )}

          {state.step === 'payment' &&
            state.stripeConfig &&
            state.paymentIntentSecret &&
            state.formData.selectedPlan && (
              <StripePaymentForm
                stripeConfig={state.stripeConfig}
                clientSecret={state.paymentIntentSecret}
                selectedPlan={state.formData.selectedPlan}
                onPaymentSuccess={handlePaymentSuccess}
                onPaymentError={handlePaymentError}
                disabled={isLoading}
              />
            )}

          {state.step === 'success' && (
            <PurchaseSuccessCard
              selectedPlan={state.formData.selectedPlan}
              transactionId={state.transactionId}
              onReset={actions.resetFlow}
            />
          )}

          {state.step === 'error' && (
            <PurchaseErrorCard
              errorMessage={state.errorMessage}
              onRetry={actions.resetFlow}
              onBack={() => {
                if (state.formData.selectedPlan) {
                  actions.selectPlan(state.formData.selectedPlan);
                } else {
                  actions.resetFlow();
                }
              }}
            />
          )}

          {/* Global error display */}
          {state.errorMessage && state.step !== 'error' && (
            <Alert action="error" variant="solid">
              <Icon as={XCircle} className="text-error-600" />
              <VStack space="sm" className="flex-1">
                <Heading size="sm" className="text-error-900">
                  Error
                </Heading>
                <Text className="text-error-800 text-sm">{state.errorMessage}</Text>
              </VStack>
            </Alert>
          )}
        </VStack>
      </ScrollView>
    </SafeAreaView>
  );
}

/**
 * Success card component displayed after successful purchase.
 */
function PurchaseSuccessCard({
  selectedPlan,
  transactionId,
  onReset,
}: {
  selectedPlan: any;
  transactionId: number | null;
  onReset: () => void;
}) {
  return (
    <Card className="p-8 border-success-200 bg-success-50">
      <VStack space="lg" className="items-center text-center">
        <Icon as={CheckCircle} size="3xl" className="text-success-600" />

        <VStack space="sm" className="items-center">
          <Heading size="2xl" className="text-success-900">
            Purchase Successful!
          </Heading>
          <Text className="text-success-800 text-lg">
            Thank you for your purchase. Your tutoring hours are now available.
          </Text>
        </VStack>

        {selectedPlan && (
          <Card className="p-4 bg-white border border-success-200 w-full max-w-md">
            <VStack space="sm">
              <Heading size="md" className="text-typography-900">
                Purchase Summary
              </Heading>
              <HStack className="items-center justify-between">
                <Text className="text-typography-700">Plan:</Text>
                <Text className="font-semibold text-typography-900">{selectedPlan.name}</Text>
              </HStack>
              <HStack className="items-center justify-between">
                <Text className="text-typography-700">Hours:</Text>
                <Text className="font-semibold text-typography-900">
                  {selectedPlan.hours_included}
                </Text>
              </HStack>
              {transactionId && (
                <HStack className="items-center justify-between">
                  <Text className="text-typography-700">Transaction ID:</Text>
                  <Text className="font-mono text-sm text-typography-900">#{transactionId}</Text>
                </HStack>
              )}
            </VStack>
          </Card>
        )}

        <VStack space="sm" className="w-full max-w-md">
          <Text className="text-sm text-success-700 text-center">
            A confirmation email has been sent with your purchase details and instructions on how to
            schedule your first tutoring session.
          </Text>

          <Button
            action="primary"
            variant="solid"
            size="lg"
            className="w-full mt-4"
            onPress={onReset}
          >
            <ButtonIcon as={ShoppingCart} />
            <ButtonText>Make Another Purchase</ButtonText>
          </Button>
        </VStack>
      </VStack>
    </Card>
  );
}

/**
 * Error card component displayed when purchase fails.
 */
function PurchaseErrorCard({
  errorMessage,
  onRetry,
  onBack,
}: {
  errorMessage: string | null;
  onRetry: () => void;
  onBack: () => void;
}) {
  return (
    <Card className="p-8 border-error-200 bg-error-50">
      <VStack space="lg" className="items-center text-center">
        <Icon as={XCircle} size="3xl" className="text-error-600" />

        <VStack space="sm" className="items-center">
          <Heading size="2xl" className="text-error-900">
            Purchase Failed
          </Heading>
          <Text className="text-error-800 text-lg">
            We encountered an issue processing your purchase.
          </Text>
        </VStack>

        {errorMessage && (
          <Card className="p-4 bg-white border border-error-200 w-full max-w-md">
            <VStack space="sm">
              <Heading size="sm" className="text-error-900">
                Error Details
              </Heading>
              <Text className="text-sm text-error-700">{errorMessage}</Text>
            </VStack>
          </Card>
        )}

        <VStack space="sm" className="w-full max-w-md">
          <Button action="primary" variant="solid" size="lg" className="w-full" onPress={onRetry}>
            <ButtonText>Try Again</ButtonText>
          </Button>

          <Button
            action="secondary"
            variant="outline"
            size="md"
            className="w-full"
            onPress={onBack}
          >
            <ButtonIcon as={ArrowLeft} />
            <ButtonText>Go Back</ButtonText>
          </Button>
        </VStack>

        <Text className="text-xs text-error-600 text-center">
          If the problem persists, please contact our support team for assistance.
        </Text>
      </VStack>
    </Card>
  );
}
