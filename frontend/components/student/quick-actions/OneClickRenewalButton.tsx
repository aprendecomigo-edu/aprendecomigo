/**
 * One-Click Renewal Button Component
 *
 * Smart renewal button that detects expired subscriptions and provides
 * one-click renewal functionality using saved payment methods.
 */

import { RotateCcw, CreditCard, AlertCircle, CheckCircle } from 'lucide-react-native';
import React, { useState, useEffect } from 'react';

import { PurchaseApiClient } from '@/api/purchaseApi';
import { Alert, AlertIcon, AlertText } from '@/components/ui/alert';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { useToast } from '@/components/ui/toast';
import { VStack } from '@/components/ui/vstack';
import { usePaymentMethods } from '@/hooks/usePaymentMethods';
import { useStudentBalance } from '@/hooks/useStudentBalance';
import type { PackageInfo, PaymentMethod, RenewalRequest, RenewalResponse } from '@/types/purchase';

interface OneClickRenewalButtonProps {
  /** Optional email for admin access */
  email?: string;
  /** Callback fired when renewal is successful */
  onRenewalSuccess?: (response: RenewalResponse) => void;
  /** Callback fired when renewal fails */
  onRenewalError?: (error: string) => void;
  /** Size of the button */
  size?: 'xs' | 'sm' | 'md' | 'lg';
  /** Variant of the button */
  variant?: 'solid' | 'outline' | 'link';
  /** Show detailed plan information */
  showPlanDetails?: boolean;
}

/**
 * One-Click Renewal Button Component
 *
 * Automatically detects expired subscriptions and provides quick renewal
 * functionality using the default payment method.
 */
export function OneClickRenewalButton({
  email,
  onRenewalSuccess,
  onRenewalError,
  size = 'md',
  variant = 'solid',
  showPlanDetails = false,
}: OneClickRenewalButtonProps) {
  const toast = useToast();
  const { balance, loading: balanceLoading, refetch: refetchBalance } = useStudentBalance(email);
  const { paymentMethods, loading: paymentMethodsLoading } = usePaymentMethods(email);

  const [isRenewing, setIsRenewing] = useState(false);
  const [renewalError, setRenewalError] = useState<string | null>(null);
  const [expiredPackage, setExpiredPackage] = useState<PackageInfo | null>(null);
  const [defaultPaymentMethod, setDefaultPaymentMethod] = useState<PaymentMethod | null>(null);

  // Detect expired packages and default payment method
  useEffect(() => {
    if (!balance || !paymentMethods.length) return;

    // Find the most recently expired package
    const mostRecentExpired = balance.package_status.expired_packages.sort(
      (a, b) => new Date(b.expires_at || '').getTime() - new Date(a.expires_at || '').getTime(),
    )[0];

    setExpiredPackage(mostRecentExpired || null);

    // Find default payment method
    const defaultMethod = paymentMethods.find(method => method.is_default);
    setDefaultPaymentMethod(defaultMethod || null);
  }, [balance, paymentMethods]);

  // Check if renewal is possible
  const canRenew = !!(
    expiredPackage &&
    defaultPaymentMethod &&
    !balanceLoading &&
    !paymentMethodsLoading &&
    !isRenewing
  );

  // Handle one-click renewal
  const handleRenewal = async () => {
    if (!expiredPackage || !defaultPaymentMethod) {
      const error = 'Unable to process renewal: missing payment method or expired package';
      setRenewalError(error);
      onRenewalError?.(error);
      return;
    }

    setIsRenewing(true);
    setRenewalError(null);

    try {
      const renewalRequest: RenewalRequest = {
        use_default_payment_method: true,
        confirm_immediately: true,
      };

      const response = await PurchaseApiClient.renewSubscription(renewalRequest, email);

      if (response.success) {
        // Show success toast
        toast.show({
          placement: 'top',
          render: ({ id }) => (
            <Alert mx="$3" action="success" variant="solid">
              <AlertIcon as={CheckCircle} />
              <AlertText>
                Subscription renewed successfully! Your new balance is now available.
              </AlertText>
            </Alert>
          ),
        });

        // Refresh balance data
        await refetchBalance();

        // Clear expired package state
        setExpiredPackage(null);

        // Call success callback
        onRenewalSuccess?.(response);
      } else {
        throw new Error(response.message || 'Renewal failed');
      }
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to renew subscription';
      setRenewalError(errorMessage);

      toast.show({
        placement: 'top',
        render: ({ id }) => (
          <Alert mx="$3" action="error" variant="solid">
            <AlertIcon as={AlertCircle} />
            <AlertText>Renewal failed: {errorMessage}</AlertText>
          </Alert>
        ),
      });

      onRenewalError?.(errorMessage);
    } finally {
      setIsRenewing(false);
    }
  };

  // Don't render if no expired packages or loading
  if (balanceLoading || paymentMethodsLoading) {
    return (
      <Button action="secondary" variant="outline" size={size} disabled={true}>
        <Spinner size="sm" />
        <ButtonText className="ml-2">Loading...</ButtonText>
      </Button>
    );
  }

  // Don't render if no expired packages
  if (!expiredPackage) {
    return null;
  }

  // Show warning if no default payment method
  if (!defaultPaymentMethod) {
    return (
      <VStack space="sm">
        <Alert action="warning" variant="outline">
          <AlertIcon as={AlertCircle} />
          <VStack space="xs" className="flex-1">
            <AlertText className="font-medium">Subscription Expired</AlertText>
            <AlertText className="text-sm">
              Add a payment method to enable one-click renewal
            </AlertText>
          </VStack>
        </Alert>
      </VStack>
    );
  }

  return (
    <VStack space="sm">
      {/* Renewal Error Display */}
      {renewalError && (
        <Alert action="error" variant="outline">
          <AlertIcon as={AlertCircle} />
          <VStack space="xs" className="flex-1">
            <AlertText className="font-medium">Renewal Failed</AlertText>
            <AlertText className="text-sm">{renewalError}</AlertText>
          </VStack>
        </Alert>
      )}

      {/* Plan Details (if enabled) */}
      {showPlanDetails && (
        <VStack space="xs" className="p-3 bg-warning-50 border border-warning-200 rounded-lg">
          <Text className="text-sm font-medium text-warning-800">
            Expired: {expiredPackage.plan_name}
          </Text>
          <Text className="text-xs text-warning-700">
            {expiredPackage.hours_included} hours • Expired{' '}
            {expiredPackage.expires_at
              ? new Date(expiredPackage.expires_at).toLocaleDateString()
              : 'recently'}
          </Text>
        </VStack>
      )}

      {/* One-Click Renewal Button */}
      <Button
        action="primary"
        variant={variant}
        size={size}
        onPress={handleRenewal}
        disabled={!canRenew || isRenewing}
      >
        {isRenewing ? (
          <>
            <Spinner size="sm" />
            <ButtonText className="ml-2">Renewing...</ButtonText>
          </>
        ) : (
          <>
            <ButtonIcon as={RotateCcw} />
            <ButtonText>Renew Subscription</ButtonText>
          </>
        )}
      </Button>

      {/* Payment Method Info */}
      {defaultPaymentMethod && (
        <HStack space="xs" className="items-center justify-center">
          <Icon as={CreditCard} size="xs" className="text-typography-500" />
          <Text className="text-xs text-typography-600">
            {defaultPaymentMethod.card.brand.toUpperCase()} ••••{defaultPaymentMethod.card.last4}
          </Text>
        </HStack>
      )}
    </VStack>
  );
}
