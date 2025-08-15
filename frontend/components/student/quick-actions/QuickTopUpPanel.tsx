/**
 * Quick Top-Up Panel Component
 *
 * Provides quick hour purchase interface with preset packages (5, 10, 20 hours)
 * and one-click purchasing using saved payment methods.
 */

import { Clock, Zap, Star, CreditCard, AlertCircle, CheckCircle } from 'lucide-react-native';
import React, { useState, useEffect } from 'react';

import { PurchaseApiClient } from '@/api/purchaseApi';
import { Alert, AlertIcon, AlertText } from '@/components/ui/alert';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { useToast } from '@/components/ui/toast';
import { VStack } from '@/components/ui/vstack';
import { usePaymentMethods } from '@/hooks/usePaymentMethods';
import { useStudentBalance } from '@/hooks/useStudentBalance';
import { useDependencies } from '@/services/di/context';
import type { TopUpPackage, PaymentMethod, QuickTopUpResponse } from '@/types/purchase';

interface QuickTopUpPanelProps {
  /** Optional email for admin access */
  email?: string;
  /** Callback fired when top-up is successful */
  onTopUpSuccess?: (response: QuickTopUpResponse) => void;
  /** Callback fired when top-up fails */
  onTopUpError?: (error: string) => void;
  /** Show the panel in modal format */
  isModal?: boolean;
  /** Callback to close modal */
  onClose?: () => void;
}

/**
 * Quick Top-Up Panel Component
 *
 * Shows preset hour packages and allows quick purchase with saved payment methods.
 */
export function QuickTopUpPanel({
  email,
  onTopUpSuccess,
  onTopUpError,
  isModal = false,
  onClose,
}: QuickTopUpPanelProps) {
  const toast = useToast();
  const { paymentService } = useDependencies();
  const { paymentMethods, loading: paymentMethodsLoading } = usePaymentMethods(email);
  const { refetch: refetchBalance } = useStudentBalance(email);

  const [packages, setPackages] = useState<TopUpPackage[]>([]);
  const [selectedPackage, setSelectedPackage] = useState<TopUpPackage | null>(null);
  const [defaultPaymentMethod, setDefaultPaymentMethod] = useState<PaymentMethod | null>(null);
  const [loading, setLoading] = useState(true);
  const [isPurchasing, setIsPurchasing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load top-up packages and payment methods
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        // For this component, we only have one API call, but we'll prepare for future additions
        const results = await Promise.allSettled([PurchaseApiClient.getTopUpPackages(email)]);
        
        const packagesData = results[0].status === 'fulfilled' 
          ? results[0].value 
          : [];

        if (results[0].status === 'rejected') {
          console.error('Failed to load top-up packages:', results[0].reason);
          throw results[0].reason;
        }

        setPackages(packagesData.sort((a, b) => a.display_order - b.display_order));
      } catch (err: any) {
        setError(err.message || 'Failed to load top-up packages');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [email]);

  // Set default payment method
  useEffect(() => {
    const defaultMethod = paymentMethods.find(method => method.is_default);
    setDefaultPaymentMethod(defaultMethod || null);
  }, [paymentMethods]);

  // Handle package selection
  const handlePackageSelect = (pkg: TopUpPackage) => {
    setSelectedPackage(pkg);
    setError(null);
  };

  // Handle quick purchase
  const handleQuickPurchase = async () => {
    if (!selectedPackage || !defaultPaymentMethod) {
      const errorMsg = 'Please select a package and ensure you have a default payment method';
      setError(errorMsg);
      onTopUpError?.(errorMsg);
      return;
    }

    setIsPurchasing(true);
    setError(null);

    try {
      // Use PaymentService to create the request
      const request = await paymentService.processQuickTopUp(
        selectedPackage.id,
        null, // Use default payment method
        email
      );

      const response = await PurchaseApiClient.quickTopUp(request, email);

      if (response.success) {
        toast.show({
          placement: 'top',
          render: () => (
            <Alert mx="$3" action="success" variant="solid">
              <AlertIcon as={CheckCircle} />
              <AlertText>
                Successfully purchased {selectedPackage.hours} hours! Your balance has been updated.
              </AlertText>
            </Alert>
          ),
        });

        // Refresh balance data
        await refetchBalance();

        // Clear selection
        setSelectedPackage(null);

        // Call success callback
        onTopUpSuccess?.(response);

        // Close modal if needed
        if (isModal && onClose) {
          onClose();
        }
      } else {
        throw new Error(response.message || 'Purchase failed');
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to purchase hours';
      setError(errorMessage);

      toast.show({
        placement: 'top',
        render: () => (
          <Alert mx="$3" action="error" variant="solid">
            <AlertIcon as={AlertCircle} />
            <AlertText>Purchase failed: {errorMessage}</AlertText>
          </Alert>
        ),
      });

      onTopUpError?.(errorMessage);
    } finally {
      setIsPurchasing(false);
    }
  };

  // Loading state
  if (loading || paymentMethodsLoading) {
    return (
      <Card className="p-6">
        <VStack space="lg" className="items-center">
          <Spinner size="large" />
          <Text className="text-typography-600">Loading packages...</Text>
        </VStack>
      </Card>
    );
  }

  // Error state
  if (error && !packages.length) {
    return (
      <Card className="p-6">
        <VStack space="lg">
          <Alert action="error" variant="outline">
            <AlertIcon as={AlertCircle} />
            <VStack space="xs" className="flex-1">
              <AlertText className="font-medium">Unable to Load Packages</AlertText>
              <AlertText className="text-sm">{error}</AlertText>
            </VStack>
          </Alert>
          <Button
            action="primary"
            variant="outline"
            size="sm"
            onPress={() => window.location.reload()}
          >
            <ButtonText>Try Again</ButtonText>
          </Button>
        </VStack>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <VStack space="lg">
        {/* Header */}
        <VStack space="xs">
          <HStack className="items-center">
            <Icon as={Zap} size="sm" className="text-primary-600 mr-2" />
            <Heading size="lg" className="text-typography-900">
              Quick Top-Up
            </Heading>
          </HStack>
          <Text className="text-sm text-typography-600">
            Purchase additional hours instantly with your saved payment method
          </Text>
        </VStack>

        {/* Error Display */}
        {error && (
          <Alert action="error" variant="outline">
            <AlertIcon as={AlertCircle} />
            <AlertText>{error}</AlertText>
          </Alert>
        )}

        {/* No Payment Method Warning */}
        {!defaultPaymentMethod && (
          <Alert action="warning" variant="outline">
            <AlertIcon as={AlertCircle} />
            <VStack space="xs" className="flex-1">
              <AlertText className="font-medium">No Default Payment Method</AlertText>
              <AlertText className="text-sm">
                Add a payment method to enable quick purchases
              </AlertText>
            </VStack>
          </Alert>
        )}

        {/* Package Selection */}
        <VStack space="md">
          <Text className="font-medium text-typography-800">Choose Package</Text>

          <VStack space="sm">
            {packages.map(pkg => (
              <Pressable
                key={pkg.id}
                onPress={() => handlePackageSelect(pkg)}
                disabled={!defaultPaymentMethod}
              >
                <Card
                  className={`p-4 border-2 ${
                    selectedPackage?.id === pkg.id
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-outline-200 bg-background-0'
                  } ${!defaultPaymentMethod ? 'opacity-50' : ''}`}
                >
                  <HStack className="items-center justify-between">
                    <HStack space="md" className="items-center">
                      {/* Package Icon */}
                      <VStack className="items-center">
                        <Icon
                          as={Clock}
                          size="lg"
                          className={
                            selectedPackage?.id === pkg.id
                              ? 'text-primary-600'
                              : 'text-typography-500'
                          }
                        />
                        {pkg.is_popular && (
                          <HStack space="xs" className="items-center mt-1">
                            <Icon as={Star} size="xs" className="text-warning-500" />
                            <Text className="text-xs text-warning-600 font-medium">POPULAR</Text>
                          </HStack>
                        )}
                      </VStack>

                      {/* Package Details */}
                      <VStack space="xs">
                        <Text className="font-semibold text-typography-900">{pkg.name}</Text>
                        <Text className="text-sm text-typography-600">
                          {pkg.hours} hours • €{pkg.price_per_hour}/hour
                        </Text>
                        {pkg.discount_percentage && (
                          <Text className="text-xs text-success-600 font-medium">
                            {pkg.discount_percentage}% discount
                          </Text>
                        )}
                      </VStack>
                    </HStack>

                    {/* Price */}
                    <VStack className="items-end">
                      <Text className="text-lg font-bold text-typography-900">
                        €{pkg.price_eur}
                      </Text>
                      <Text className="text-xs text-typography-500">Total</Text>
                    </VStack>
                  </HStack>
                </Card>
              </Pressable>
            ))}
          </VStack>
        </VStack>

        {/* Payment Method Display */}
        {defaultPaymentMethod && (
          <VStack space="xs">
            <Text className="text-sm font-medium text-typography-700">Payment Method</Text>
            <HStack
              space="sm"
              className="items-center p-3 bg-background-50 rounded-lg border border-outline-200"
            >
              <Icon as={CreditCard} size="sm" className="text-typography-600" />
              <VStack space="xs">
                <Text className="text-sm font-medium text-typography-800">
                  {defaultPaymentMethod.card.brand.toUpperCase()} ••••
                  {defaultPaymentMethod.card.last4}
                </Text>
                <Text className="text-xs text-typography-600">
                  Expires {defaultPaymentMethod.card.exp_month}/{defaultPaymentMethod.card.exp_year}
                </Text>
              </VStack>
            </HStack>
          </VStack>
        )}

        {/* Purchase Button */}
        <Button
          action="primary"
          variant="solid"
          size="lg"
          onPress={handleQuickPurchase}
          disabled={!selectedPackage || !defaultPaymentMethod || isPurchasing}
        >
          {isPurchasing ? (
            <>
              <Spinner size="sm" />
              <ButtonText className="ml-2">Processing...</ButtonText>
            </>
          ) : selectedPackage ? (
            <>
              <ButtonIcon as={Zap} />
              <ButtonText>
                Purchase {selectedPackage.hours} Hours for €{selectedPackage.price_eur}
              </ButtonText>
            </>
          ) : (
            <ButtonText>Select a Package</ButtonText>
          )}
        </Button>

        {/* Security Notice */}
        <Card className="p-3 bg-success-50 border-success-200">
          <VStack space="xs">
            <Text className="text-xs font-medium text-success-800">Secure & Instant</Text>
            <Text className="text-xs text-success-700">
              Your payment is processed securely by Stripe. Hours are added to your account
              immediately after successful payment.
            </Text>
          </VStack>
        </Card>
      </VStack>
    </Card>
  );
}
