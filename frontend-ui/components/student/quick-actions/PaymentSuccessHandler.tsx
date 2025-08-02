/**
 * Payment Success Handler Component
 * 
 * Handles successful payment states, balance refresh, and success feedback
 * for renewal and quick top-up transactions.
 */

import React, { useEffect, useState } from 'react';
import { CheckCircle, RotateCcw, Zap, Clock, Euro, Calendar, ArrowRight } from 'lucide-react-native';

import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { Divider } from '@/components/ui/divider';
import { Badge, BadgeText } from '@/components/ui/badge';
import { useToast } from '@/components/ui/toast';

import { useStudentBalance } from '@/hooks/useStudentBalance';
import type { 
  RenewalResponse, 
  QuickTopUpResponse, 
  StudentBalanceResponse 
} from '@/types/purchase';

interface PaymentSuccessHandlerProps {
  /** Type of successful transaction */
  transactionType: 'renewal' | 'topup';
  /** Renewal response data */
  renewalResponse?: RenewalResponse;
  /** Top-up response data */
  topUpResponse?: QuickTopUpResponse;
  /** Email for admin access */
  email?: string;
  /** Callback when balance is refreshed */
  onBalanceRefreshed?: (balance: StudentBalanceResponse) => void;
  /** Callback when done viewing success */
  onDone?: () => void;
  /** Show detailed transaction information */
  showDetails?: boolean;
  /** Auto-refresh balance on mount */
  autoRefreshBalance?: boolean;
}

/**
 * Payment Success Handler Component
 * 
 * Displays success state and handles post-payment operations.
 */
export function PaymentSuccessHandler({
  transactionType,
  renewalResponse,
  topUpResponse,
  email,
  onBalanceRefreshed,
  onDone,
  showDetails = true,
  autoRefreshBalance = true,
}: PaymentSuccessHandlerProps) {
  const toast = useToast();
  const { balance, refetch: refetchBalance } = useStudentBalance(email);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [hasRefreshedOnce, setHasRefreshedOnce] = useState(false);

  // Auto-refresh balance on mount
  useEffect(() => {
    if (autoRefreshBalance && !hasRefreshedOnce) {
      handleBalanceRefresh();
    }
  }, [autoRefreshBalance, hasRefreshedOnce]);

  // Handle balance refresh
  const handleBalanceRefresh = async () => {
    setIsRefreshing(true);
    try {
      const refreshedBalance = await refetchBalance();
      setHasRefreshedOnce(true);
      
      if (refreshedBalance && onBalanceRefreshed) {
        onBalanceRefreshed(refreshedBalance);
      }

      // Show success toast if not auto-refreshing
      if (!autoRefreshBalance) {
        toast.show({
          placement: 'top',
          render: ({ id }) => (
            <Card className="mx-3 p-4 bg-success-500">
              <HStack space="sm" className="items-center">
                <Icon as={CheckCircle} size="sm" className="text-white" />
                <Text className="text-white font-medium">
                  Balance updated successfully!
                </Text>
              </HStack>
            </Card>
          ),
        });
      }
    } catch (error) {
      console.error('Failed to refresh balance:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Get response data based on transaction type
  const getResponseData = () => {
    if (transactionType === 'renewal' && renewalResponse) {
      return {
        title: 'Subscription Renewed Successfully!',
        icon: RotateCcw,
        iconColor: 'text-success-600',
        bgColor: 'bg-success-50',
        borderColor: 'border-success-200',
        transactionId: renewalResponse.transaction_id,
        details: renewalResponse.renewal_details,
        message: renewalResponse.message,
      };
    } else if (transactionType === 'topup' && topUpResponse) {
      return {
        title: 'Hours Purchased Successfully!',
        icon: Zap,
        iconColor: 'text-warning-600',
        bgColor: 'bg-warning-50',
        borderColor: 'border-warning-200',
        transactionId: topUpResponse.transaction_id,
        details: topUpResponse.package_details,
        message: topUpResponse.message,
      };
    }
    return null;
  };

  const responseData = getResponseData();
  if (!responseData) return null;

  return (
    <VStack space="lg" className="p-6">
      {/* Success Header */}
      <VStack space="md" className="items-center">
        <Card className={`p-4 ${responseData.bgColor} border ${responseData.borderColor} items-center`}>
          <Icon as={CheckCircle} size="xl" className="text-success-600" />
        </Card>
        
        <VStack space="xs" className="items-center">
          <Heading size="xl" className="text-center text-typography-900">
            {responseData.title}
          </Heading>
          {responseData.message && (
            <Text className="text-center text-typography-600">
              {responseData.message}
            </Text>
          )}
        </VStack>
      </VStack>

      {/* Transaction Details */}
      {showDetails && responseData.details && (
        <Card className="p-4 border border-outline-200">
          <VStack space="md">
            <HStack className="items-center justify-between">
              <Text className="font-semibold text-typography-900">
                Transaction Details
              </Text>
              <Badge action="success" variant="solid" size="sm">
                <BadgeText>Completed</BadgeText>
              </Badge>
            </HStack>

            <Divider />

            <VStack space="sm">
              {/* Transaction ID */}
              {responseData.transactionId && (
                <HStack className="items-center justify-between">
                  <Text className="text-sm text-typography-700">Transaction ID</Text>
                  <Text className="text-sm font-mono text-typography-900">
                    #{responseData.transactionId}
                  </Text>
                </HStack>
              )}

              {/* Plan/Package Name */}
              {(responseData.details?.plan_name || responseData.details?.package_name) && (
                <HStack className="items-center justify-between">
                  <Text className="text-sm text-typography-700">
                    {transactionType === 'renewal' ? 'Plan' : 'Package'}
                  </Text>
                  <Text className="text-sm font-medium text-typography-900">
                    {responseData.details.plan_name || responseData.details?.package_name}
                  </Text>
                </HStack>
              )}

              {/* Hours */}
              {(responseData.details?.hours_included || responseData.details?.hours_purchased) && (
                <HStack className="items-center justify-between">
                  <HStack space="xs" className="items-center">
                    <Icon as={Clock} size="sm" className="text-typography-500" />
                    <Text className="text-sm text-typography-700">Hours Added</Text>
                  </HStack>
                  <Text className="text-sm font-medium text-typography-900">
                    {responseData.details.hours_included || responseData.details?.hours_purchased}
                  </Text>
                </HStack>
              )}

              {/* Amount */}
              {responseData.details?.amount_paid && (
                <HStack className="items-center justify-between">
                  <HStack space="xs" className="items-center">
                    <Icon as={Euro} size="sm" className="text-typography-500" />
                    <Text className="text-sm text-typography-700">Amount Paid</Text>
                  </HStack>
                  <Text className="text-sm font-bold text-typography-900">
                    €{responseData.details.amount_paid}
                  </Text>
                </HStack>
              )}

              {/* Expiry (for renewals) */}
              {responseData.details?.expires_at && (
                <HStack className="items-center justify-between">
                  <HStack space="xs" className="items-center">
                    <Icon as={Calendar} size="sm" className="text-typography-500" />
                    <Text className="text-sm text-typography-700">Expires</Text>
                  </HStack>
                  <Text className="text-sm font-medium text-typography-900">
                    {new Date(responseData.details.expires_at).toLocaleDateString()}
                  </Text>
                </HStack>
              )}
            </VStack>
          </VStack>
        </Card>
      )}

      {/* Balance Update Status */}
      <Card className={`p-4 ${hasRefreshedOnce ? 'bg-success-50 border-success-200' : 'bg-info-50 border-info-200'}`}>
        <HStack space="sm" className="items-center justify-between">
          <VStack space="xs" className="flex-1">
            <Text className={`font-medium ${hasRefreshedOnce ? 'text-success-800' : 'text-info-800'}`}>
              {hasRefreshedOnce ? 'Balance Updated' : 'Updating Balance'}
            </Text>
            <Text className={`text-sm ${hasRefreshedOnce ? 'text-success-700' : 'text-info-700'}`}>
              {hasRefreshedOnce 
                ? 'Your new balance is now available in your account'
                : 'Your account balance is being updated with the new hours'
              }
            </Text>
          </VStack>
          
          {!hasRefreshedOnce && (
            <Button
              action="secondary"
              variant="outline"
              size="sm"
              onPress={handleBalanceRefresh}
              disabled={isRefreshing}
            >
              {isRefreshing ? (
                <Text className="text-sm">Refreshing...</Text>
              ) : (
                <>
                  <ButtonIcon as={RotateCcw} />
                  <ButtonText>Refresh</ButtonText>
                </>
              )}
            </Button>
          )}
        </HStack>
      </Card>

      {/* Current Balance Display */}
      {balance && hasRefreshedOnce && (
        <Card className="p-4 bg-primary-50 border-primary-200">
          <VStack space="sm">
            <Text className="font-medium text-primary-800">
              Your Current Balance
            </Text>
            <HStack className="items-center justify-between">
              <Text className="text-primary-700">Remaining Hours</Text>
              <Text className="text-2xl font-bold text-primary-900">
                {balance.balance_summary.remaining_hours}
              </Text>
            </HStack>
            <HStack className="items-center justify-between">
              <Text className="text-primary-700">Balance Amount</Text>
              <Text className="text-lg font-semibold text-primary-900">
                €{balance.balance_summary.balance_amount}
              </Text>
            </HStack>
          </VStack>
        </Card>
      )}

      {/* Action Buttons */}
      <VStack space="sm">
        {onDone && (
          <Button
            action="primary"
            variant="solid"
            size="lg"
            onPress={onDone}
          >
            <ButtonText>Continue</ButtonText>
            <ButtonIcon as={ArrowRight} />
          </Button>
        )}

        {!hasRefreshedOnce && (
          <Button
            action="secondary"
            variant="outline"
            size="md"
            onPress={handleBalanceRefresh}
            disabled={isRefreshing}
          >
            {isRefreshing ? (
              <ButtonText>Updating Balance...</ButtonText>
            ) : (
              <>
                <ButtonIcon as={RotateCcw} />
                <ButtonText>Update Balance Now</ButtonText>
              </>
            )}
          </Button>
        )}
      </VStack>

      {/* Receipt Notice */}
      <Card className="p-3 bg-info-50 border-info-200">
        <Text className="text-xs text-center text-info-700">
          A receipt has been sent to your email address. You can also view all your transactions in the Account Settings.
        </Text>
      </Card>
    </VStack>
  );
}