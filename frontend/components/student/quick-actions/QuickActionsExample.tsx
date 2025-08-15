/**
 * Quick Actions Example Integration
 *
 * Example showing how to integrate the one-click renewal and quick top-up
 * components into a student balance dashboard or notification system.
 *
 * This demonstrates the complete UX flow as specified in Issue #110.
 */

import { AlertTriangle, Zap, RotateCcw } from 'lucide-react-native';
import React, { useState } from 'react';

import { OneClickRenewalButton, QuickTopUpPanel, QuickActionsModal } from './index';

import { Alert, AlertIcon, AlertText } from '@/components/ui/alert';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { usePaymentMethods } from '@/hooks/usePaymentMethods';
import { useStudentBalance } from '@/hooks/useStudentBalance';

interface QuickActionsExampleProps {
  email?: string;
}

/**
 * Example integration of quick actions in a student dashboard
 *
 * This shows how the components work together to provide the complete
 * one-click renewal and quick top-up experience.
 */
export function QuickActionsExample({ email }: QuickActionsExampleProps) {
  const { balance, loading, refetch } = useStudentBalance(email);
  const { paymentMethods, defaultPaymentMethod } = usePaymentMethods(email);

  const [showQuickActionsModal, setShowQuickActionsModal] = useState(false);
  const [modalInitialAction, setModalInitialAction] = useState<'renewal' | 'topup' | undefined>();

  // Check for low balance (less than 2 hours)
  const isLowBalance = balance && parseFloat(balance.balance_summary.remaining_hours) < 2;

  // Check for expired packages
  const hasExpiredPackages = balance && balance.package_status.expired_packages.length > 0;

  // Get the next expiring package
  const nextExpiringPackage = balance?.upcoming_expirations?.[0];
  const isNearExpiry = nextExpiringPackage && (nextExpiringPackage.days_until_expiry || 0) <= 7;

  if (loading) {
    return (
      <Card className="p-6">
        <Text>Loading balance information...</Text>
      </Card>
    );
  }

  if (!balance) {
    return (
      <Card className="p-6">
        <Text>Unable to load balance information</Text>
      </Card>
    );
  }

  return (
    <VStack space="lg">
      {/* Balance Overview */}
      <Card className="p-6">
        <VStack space="md">
          <Heading size="lg">Your Balance</Heading>

          <HStack className="items-center justify-between">
            <VStack space="xs">
              <Text className="text-2xl font-bold text-primary-600">
                {balance.balance_summary.remaining_hours}
              </Text>
              <Text className="text-sm text-typography-600">Hours Remaining</Text>
            </VStack>

            <VStack space="xs" className="items-end">
              <Text className="text-lg font-semibold text-typography-900">
                €{balance.balance_summary.balance_amount}
              </Text>
              <Text className="text-sm text-typography-600">Balance Value</Text>
            </VStack>
          </HStack>
        </VStack>
      </Card>

      {/* Quick Actions Section */}
      <VStack space="md">
        <Heading size="md">Quick Actions</Heading>

        {/* Low Balance Alert with Quick Top-Up */}
        {isLowBalance && (
          <Alert action="warning" variant="outline">
            <AlertIcon as={AlertTriangle} />
            <VStack space="sm" className="flex-1">
              <AlertText className="font-medium">Low Balance Alert</AlertText>
              <AlertText className="text-sm">
                You have less than 2 hours remaining. Consider purchasing more hours to continue
                your tutoring sessions.
              </AlertText>

              <HStack space="sm" className="mt-2">
                <Button
                  action="primary"
                  variant="solid"
                  size="sm"
                  onPress={() => {
                    setModalInitialAction('topup');
                    setShowQuickActionsModal(true);
                  }}
                >
                  <ButtonIcon as={Zap} />
                  <ButtonText>Quick Top-Up</ButtonText>
                </Button>

                <Button
                  action="secondary"
                  variant="outline"
                  size="sm"
                  onPress={() => setShowQuickActionsModal(true)}
                >
                  <ButtonText>View Options</ButtonText>
                </Button>
              </HStack>
            </VStack>
          </Alert>
        )}

        {/* Expired Package Renewal */}
        {hasExpiredPackages && (
          <Card className="p-4 bg-error-50 border-error-200">
            <VStack space="sm">
              <HStack className="items-center">
                <Icon as={AlertTriangle} size="sm" className="text-error-600" />
                <Text className="font-medium text-error-800">Subscription Expired</Text>
              </HStack>

              <Text className="text-sm text-error-700">
                You have expired packages that can be renewed with one click.
              </Text>

              <OneClickRenewalButton
                email={email}
                size="md"
                showPlanDetails={true}
                onRenewalSuccess={() => {
                  refetch(); // Refresh balance after successful renewal
                }}
              />
            </VStack>
          </Card>
        )}

        {/* Near Expiry Warning */}
        {isNearExpiry && nextExpiringPackage && (
          <Alert action="info" variant="outline">
            <AlertIcon as={RotateCcw} />
            <VStack space="sm" className="flex-1">
              <AlertText className="font-medium">Package Expiring Soon</AlertText>
              <AlertText className="text-sm">
                Your {nextExpiringPackage.plan_name} package expires in{' '}
                {nextExpiringPackage.days_until_expiry} days.
              </AlertText>

              <Button
                action="primary"
                variant="outline"
                size="sm"
                onPress={() => {
                  setModalInitialAction('renewal');
                  setShowQuickActionsModal(true);
                }}
              >
                <ButtonIcon as={RotateCcw} />
                <ButtonText>Renew Now</ButtonText>
              </Button>
            </VStack>
          </Alert>
        )}

        {/* General Quick Actions */}
        {!isLowBalance && !hasExpiredPackages && (
          <Card className="p-4 border border-outline-200">
            <VStack space="md">
              <Text className="font-medium text-typography-800">Need more hours?</Text>

              <HStack space="sm">
                <Button
                  action="primary"
                  variant="solid"
                  size="md"
                  onPress={() => {
                    setModalInitialAction('topup');
                    setShowQuickActionsModal(true);
                  }}
                  className="flex-1"
                >
                  <ButtonIcon as={Zap} />
                  <ButtonText>Quick Top-Up</ButtonText>
                </Button>

                <Button
                  action="secondary"
                  variant="outline"
                  size="md"
                  onPress={() => setShowQuickActionsModal(true)}
                  className="flex-1"
                >
                  <ButtonText>All Options</ButtonText>
                </Button>
              </HStack>

              {defaultPaymentMethod && (
                <HStack space="xs" className="items-center justify-center">
                  <Text className="text-xs text-typography-600">
                    Using {defaultPaymentMethod.card.brand.toUpperCase()} ••••
                    {defaultPaymentMethod.card.last4}
                  </Text>
                </HStack>
              )}
            </VStack>
          </Card>
        )}

        {/* No Payment Method Warning */}
        {!defaultPaymentMethod && paymentMethods.length === 0 && (
          <Alert action="warning" variant="outline">
            <AlertIcon as={AlertTriangle} />
            <VStack space="sm" className="flex-1">
              <AlertText className="font-medium">Add Payment Method</AlertText>
              <AlertText className="text-sm">
                Add a payment method to enable quick purchases and one-click renewals.
              </AlertText>

              <Button
                action="primary"
                variant="outline"
                size="sm"
                onPress={() => {
                  // Navigate to payment methods management
                  // This would typically use navigation
                  if (__DEV__) {
                    console.log('Navigate to payment methods');
                  }
                }}
              >
                <ButtonText>Add Payment Method</ButtonText>
              </Button>
            </VStack>
          </Alert>
        )}
      </VStack>

      {/* Standalone Quick Top-Up Panel Example */}
      <VStack space="md">
        <Heading size="md">Quick Top-Up Panel (Standalone)</Heading>
        <QuickTopUpPanel
          email={email}
          onTopUpSuccess={response => {
            if (__DEV__) {
              console.log('Top-up successful:', response);
            }
            refetch(); // Refresh balance
          }}
          onTopUpError={error => {
            console.error('Top-up failed:', error);
          }}
        />
      </VStack>

      {/* Quick Actions Modal */}
      <QuickActionsModal
        isOpen={showQuickActionsModal}
        onClose={() => {
          setShowQuickActionsModal(false);
          setModalInitialAction(undefined);
        }}
        initialAction={modalInitialAction}
        email={email}
        onTransactionSuccess={(type, response) => {
          if (__DEV__) {
            console.log(`${type} successful:`, response);
          }
          refetch(); // Refresh balance after successful transaction
        }}
      />
    </VStack>
  );
}

/**
 * Usage Examples:
 *
 * 1. In Student Balance Dashboard:
 * ```tsx
 * import { QuickActionsExample } from '@/components/student/quick-actions/QuickActionsExample';
 *
 * function StudentDashboard() {
 *   return (
 *     <VStack space="lg">
 *       <QuickActionsExample />
 *       // ... other dashboard components
 *     </VStack>
 *   );
 * }
 * ```
 *
 * 2. In Low Balance Notification:
 * ```tsx
 * import { OneClickRenewalButton, QuickTopUpPanel } from '@/components/student/quick-actions';
 *
 * function LowBalanceNotification({ onDismiss }) {
 *   return (
 *     <Alert action="warning">
 *       <AlertText>Your balance is low!</AlertText>
 *       <QuickTopUpPanel
 *         isModal={true}
 *         onTopUpSuccess={onDismiss}
 *       />
 *     </Alert>
 *   );
 * }
 * ```
 *
 * 3. In Expired Package Flow:
 * ```tsx
 * import { OneClickRenewalButton } from '@/components/student/quick-actions';
 *
 * function ExpiredPackageAlert() {
 *   return (
 *     <Alert action="error">
 *       <AlertText>Your subscription has expired</AlertText>
 *       <OneClickRenewalButton
 *         showPlanDetails={true}
 if (__DEV__) {
   *         onRenewalSuccess={() => console.log('Renewed!')}
 }
 *       />
 *     </Alert>
 *   );
 * }
 * ```
 */
