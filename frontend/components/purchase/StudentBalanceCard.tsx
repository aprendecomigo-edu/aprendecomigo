/**
 * Student Balance Card Component
 *
 * Displays comprehensive student balance information including hours,
 * active packages, and upcoming expirations in a clean card format.
 */

import useRouter from '@unitools/router';
import { Clock, Package, AlertTriangle, RefreshCw, User, ShoppingCart } from 'lucide-react-native';
import React, { useMemo, useCallback } from 'react';

import {
  BalanceStatusBar,
  CompactBalanceStatusBar,
} from '@/components/student/balance/BalanceStatusBar';
import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useStudentBalance } from '@/hooks/useStudentBalance';
import type { StudentBalanceResponse, PackageInfo } from '@/types/purchase';

interface StudentBalanceCardProps {
  email?: string;
  onRefresh?: () => void;
  className?: string;
  showStudentInfo?: boolean;
  /** Show visual balance status bar */
  showStatusBar?: boolean;
  /** Use compact layout */
  compact?: boolean;
}

/**
 * Component for displaying student balance information with real-time updates.
 */
export const StudentBalanceCard = React.memo<StudentBalanceCardProps>(function StudentBalanceCard({
  email,
  onRefresh,
  className = '',
  showStudentInfo = true,
  showStatusBar = true,
  compact = false,
}: StudentBalanceCardProps) {
  const router = useRouter();
  const { balance, loading, error, refetch } = useStudentBalance(email);

  const handleRefresh = useCallback(() => {
    refetch();
    onRefresh?.();
  }, [refetch, onRefresh]);

  const handlePurchaseHours = useCallback(() => {
    router.push('/purchase');
  }, [router]);

  if (loading) {
    return (
      <Card className={`p-6 ${className}`}>
        <VStack space="md" className="items-center">
          <Spinner size="large" />
          <Text className="text-typography-600">Loading balance information...</Text>
        </VStack>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`p-6 border-error-200 ${className}`}>
        <VStack space="md" className="items-center">
          <Icon as={AlertTriangle} size="xl" className="text-error-500" />
          <VStack space="sm" className="items-center">
            <Heading size="sm" className="text-error-900">
              Unable to Load Balance
            </Heading>
            <Text className="text-error-700 text-sm text-center">{error}</Text>
          </VStack>
          <Button action="secondary" variant="outline" size="sm" onPress={handleRefresh}>
            <ButtonIcon as={RefreshCw} />
            <ButtonText>Try Again</ButtonText>
          </Button>
        </VStack>
      </Card>
    );
  }

  if (!balance) {
    return (
      <Card className={`p-6 ${className}`}>
        <VStack space="md" className="items-center">
          <Text className="text-typography-600">No balance information available</Text>
          <Button action="secondary" variant="outline" size="sm" onPress={handleRefresh}>
            <ButtonIcon as={RefreshCw} />
            <ButtonText>Refresh</ButtonText>
          </Button>
        </VStack>
      </Card>
    );
  }

  // Memoize expensive calculations
  const remainingHours = useMemo(() => 
    parseFloat(balance.balance_summary.remaining_hours), 
    [balance.balance_summary.remaining_hours]
  );
  
  const totalHours = useMemo(() => 
    parseFloat(balance.balance_summary.hours_purchased), 
    [balance.balance_summary.hours_purchased]
  );
  
  const daysUntilExpiry = useMemo(() => 
    balance.upcoming_expirations[0]?.days_until_expiry || null, 
    [balance.upcoming_expirations]
  );

  return (
    <Card className={`p-6 ${className}`}>
      <VStack space="lg">
        {/* Header with student info and refresh button */}
        <HStack className="items-center justify-between">
          <VStack space="xs" className="flex-1">
            <Heading size="lg" className="text-typography-900">
              Account Balance
            </Heading>
            {showStudentInfo && (
              <HStack space="xs" className="items-center">
                <Icon as={User} size="sm" className="text-typography-500" />
                <Text className="text-sm text-typography-600">
                  {balance.student_info.name} ({balance.student_info.email})
                </Text>
              </HStack>
            )}
          </VStack>
          <Button action="secondary" variant="outline" size="sm" onPress={handleRefresh}>
            <ButtonIcon as={RefreshCw} />
          </Button>
        </HStack>

        {/* Balance Status Bar */}
        {showStatusBar && (
          <BalanceStatusBar
            remainingHours={remainingHours}
            totalHours={totalHours}
            daysUntilExpiry={daysUntilExpiry}
            showDetails={!compact}
            className="mb-2"
          />
        )}

        {/* Balance summary */}
        <VStack space="md">
          <HStack className="items-center justify-between">
            <Heading size="md" className="text-typography-800">
              Hours Summary
            </Heading>
            {parseFloat(balance.balance_summary.remaining_hours) <= 2 && (
              <Button action="primary" variant="solid" size="sm" onPress={handlePurchaseHours}>
                <ButtonIcon as={ShoppingCart} />
                <ButtonText>Buy Hours</ButtonText>
              </Button>
            )}
          </HStack>

          <HStack className="justify-between">
            <VStack space="xs" className="items-center flex-1">
              <Text
                className={`text-2xl font-bold ${
                  parseFloat(balance.balance_summary.remaining_hours) <= 2
                    ? 'text-error-600'
                    : parseFloat(balance.balance_summary.remaining_hours) <= 5
                    ? 'text-warning-600'
                    : 'text-primary-600'
                }`}
              >
                {parseFloat(balance.balance_summary.remaining_hours).toFixed(1)}
              </Text>
              <Text className="text-xs text-typography-500 text-center">Hours Remaining</Text>
            </VStack>

            <VStack space="xs" className="items-center flex-1">
              <Text className="text-lg font-semibold text-typography-700">
                {parseFloat(balance.balance_summary.hours_purchased).toFixed(1)}
              </Text>
              <Text className="text-xs text-typography-500 text-center">Hours Purchased</Text>
            </VStack>

            <VStack space="xs" className="items-center flex-1">
              <Text className="text-lg font-semibold text-typography-700">
                {parseFloat(balance.balance_summary.hours_consumed).toFixed(1)}
              </Text>
              <Text className="text-xs text-typography-500 text-center">Hours Used</Text>
            </VStack>
          </HStack>
        </VStack>

        {/* Active packages */}
        {balance.package_status.active_packages.length > 0 && (
          <>
            <Divider />
            <VStack space="sm">
              <HStack space="xs" className="items-center">
                <Icon as={Package} size="sm" className="text-success-600" />
                <Heading size="sm" className="text-typography-800">
                  Active Packages
                </Heading>
              </HStack>

              <VStack space="xs">
                {balance.package_status.active_packages.map((pkg, index) => (
                  <PackageItem key={pkg.transaction_id} package={pkg} />
                ))}
              </VStack>
            </VStack>
          </>
        )}

        {/* Upcoming expirations */}
        {balance.upcoming_expirations.length > 0 && (
          <>
            <Divider />
            <VStack space="sm">
              <HStack space="xs" className="items-center">
                <Icon as={Clock} size="sm" className="text-warning-600" />
                <Heading size="sm" className="text-typography-800">
                  Expiring Soon
                </Heading>
              </HStack>

              <VStack space="xs">
                {balance.upcoming_expirations.map((expiration, index) => (
                  <ExpirationItem key={expiration.transaction_id} expiration={expiration} />
                ))}
              </VStack>
            </VStack>
          </>
        )}

        {/* Empty state for no active packages */}
        {balance.package_status.active_packages.length === 0 &&
          balance.upcoming_expirations.length === 0 &&
          parseFloat(balance.balance_summary.remaining_hours) === 0 && (
            <>
              <Divider />
              <VStack space="sm" className="items-center py-4">
                <Icon as={Package} size="xl" className="text-typography-300" />
                <VStack space="xs" className="items-center">
                  <Text className="text-typography-600 font-medium">No Active Packages</Text>
                  <Text className="text-sm text-typography-500 text-center">
                    Purchase a tutoring package to get started with your learning journey.
                  </Text>
                </VStack>
              </VStack>
            </>
          )}
      </VStack>
    </Card>
  );
}, (prevProps, nextProps) => {
  // Custom comparison function for StudentBalanceCard
  return (
    prevProps.email === nextProps.email &&
    prevProps.className === nextProps.className &&
    prevProps.showStudentInfo === nextProps.showStudentInfo &&
    prevProps.showStatusBar === nextProps.showStatusBar &&
    prevProps.compact === nextProps.compact
  );
});

/**
 * Individual package item component.
 */
function PackageItem({ package: pkg }: { package: PackageInfo }) {
  const remainingPercent = (parseFloat(pkg.hours_remaining) / parseFloat(pkg.hours_included)) * 100;

  return (
    <HStack className="items-center justify-between p-3 bg-background-50 rounded-lg">
      <VStack space="xs" className="flex-1">
        <Text className="text-sm font-medium text-typography-800">{pkg.plan_name}</Text>
        <Text className="text-xs text-typography-600">
          {parseFloat(pkg.hours_remaining).toFixed(1)} of{' '}
          {parseFloat(pkg.hours_included).toFixed(1)} hours remaining
        </Text>
      </VStack>

      <VStack space="xs" className="items-end">
        {pkg.expires_at && (
          <Badge
            variant="outline"
            action={pkg.days_until_expiry && pkg.days_until_expiry <= 7 ? 'warning' : 'secondary'}
            size="sm"
          >
            <Text className="text-xs">
              {pkg.days_until_expiry !== null ? `${pkg.days_until_expiry} days left` : 'No expiry'}
            </Text>
          </Badge>
        )}
      </VStack>
    </HStack>
  );
}

/**
 * Individual expiration item component.
 */
function ExpirationItem({ expiration }: { expiration: any }) {
  const urgencyColor = expiration.days_until_expiry <= 3 ? 'error' : 'warning';

  return (
    <HStack className="items-center justify-between p-3 bg-warning-50 rounded-lg">
      <VStack space="xs" className="flex-1">
        <Text className="text-sm font-medium text-typography-800">{expiration.plan_name}</Text>
        <Text className="text-xs text-typography-600">
          {parseFloat(expiration.hours_remaining).toFixed(1)} hours remaining
        </Text>
      </VStack>

      <Badge variant="solid" action={urgencyColor} size="sm">
        <Icon as={AlertTriangle} size="xs" />
        <Text className="text-xs ml-1">{expiration.days_until_expiry} days left</Text>
      </Badge>
    </HStack>
  );
}
