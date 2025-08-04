/**
 * Dashboard Overview Component
 *
 * Displays comprehensive account overview including balance summary,
 * active packages, expiration warnings, and quick action buttons.
 */

import useRouter from '@unitools/router';
import {
  Calendar,
  Clock,
  CreditCard,
  Package,
  Plus,
  RefreshCw,
  TrendingUp,
  AlertTriangle,
  ShoppingCart,
  BookOpen,
} from 'lucide-react-native';
import React from 'react';

import { StudentBalanceCard } from '@/components/purchase';
import { UsageAnalyticsSection } from '@/components/student/analytics/UsageAnalyticsSection';
import { NotificationSystem } from '@/components/student/notifications/NotificationSystem';
import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import type { StudentBalanceResponse } from '@/types/purchase';

interface DashboardOverviewProps {
  balance: StudentBalanceResponse | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => Promise<void>;
  onPurchase: () => void;
  onTabChange?: (tab: string) => void;
}

/**
 * Quick action button configuration
 */
const QUICK_ACTIONS = [
  {
    id: 'schedule',
    label: 'Schedule Session',
    description: 'Book a tutoring session',
    icon: Calendar,
    route: '/calendar',
    color: 'primary',
  },
  {
    id: 'purchase',
    label: 'Purchase Hours',
    description: 'Buy more tutoring hours',
    icon: ShoppingCart,
    route: '/purchase',
    color: 'secondary',
  },
  {
    id: 'history',
    label: 'View History',
    description: 'See transaction history',
    icon: Clock,
    action: 'transactions',
    color: 'tertiary',
  },
  {
    id: 'materials',
    label: 'Study Materials',
    description: 'Access learning resources',
    icon: BookOpen,
    route: '/materials',
    color: 'success',
  },
];

/**
 * Dashboard Overview Component
 */
export function DashboardOverview({
  balance,
  loading,
  error,
  onRefresh,
  onPurchase,
  onTabChange,
}: DashboardOverviewProps) {
  const router = useRouter();

  const handleQuickAction = (action: (typeof QUICK_ACTIONS)[0]) => {
    if (action.route) {
      router.push(action.route);
    } else if (action.action === 'transactions' && onTabChange) {
      // Switch to transactions tab within dashboard
      onTabChange('transactions');
    } else if (action.action === 'transactions') {
      // Fallback to balance page if no tab change handler
      router.push('/(student)/balance');
    } else if (action.id === 'purchase') {
      onPurchase();
    }
  };

  if (loading) {
    return (
      <VStack space="lg" className="items-center py-12">
        <Spinner size="large" />
        <Text className="text-typography-600">Loading account overview...</Text>
      </VStack>
    );
  }

  if (error) {
    return (
      <Card className="p-6 border-error-200">
        <VStack space="md" className="items-center">
          <Icon as={AlertTriangle} size="xl" className="text-error-500" />
          <VStack space="sm" className="items-center">
            <Heading size="sm" className="text-error-900">
              Unable to Load Overview
            </Heading>
            <Text className="text-error-700 text-sm text-center">{error}</Text>
          </VStack>
          <Button action="secondary" variant="outline" size="sm" onPress={onRefresh}>
            <ButtonIcon as={RefreshCw} />
            <ButtonText>Try Again</ButtonText>
          </Button>
        </VStack>
      </Card>
    );
  }

  return (
    <VStack space="lg">
      {/* Balance Overview Card */}
      <StudentBalanceCard email={undefined} onRefresh={onRefresh} showStudentInfo={true} />

      {/* Quick Actions */}
      <VStack space="md">
        <Heading size="lg" className="text-typography-900">
          Quick Actions
        </Heading>

        <HStack space="md" className="flex-wrap">
          {QUICK_ACTIONS.map(action => (
            <Pressable
              key={action.id}
              className="flex-1 min-w-40"
              onPress={() => handleQuickAction(action)}
            >
              <Card className="p-4 hover:shadow-md transition-shadow">
                <VStack space="sm" className="items-center">
                  <Icon as={action.icon} size="lg" className={`text-${action.color}-600`} />
                  <VStack space="xs" className="items-center">
                    <Text className="font-semibold text-center text-typography-900">
                      {action.label}
                    </Text>
                    <Text className="text-xs text-center text-typography-600">
                      {action.description}
                    </Text>
                  </VStack>
                </VStack>
              </Card>
            </Pressable>
          ))}
        </HStack>
      </VStack>

      {/* Recent Activity Summary */}
      {balance && (
        <VStack space="md">
          <Heading size="lg" className="text-typography-900">
            Account Summary
          </Heading>

          <Card className="p-6">
            <VStack space="lg">
              {/* Usage Statistics */}
              <VStack space="md">
                <HStack className="items-center justify-between">
                  <Text className="font-semibold text-typography-800">Usage Statistics</Text>
                  <Icon as={TrendingUp} size="sm" className="text-success-600" />
                </HStack>

                <HStack className="justify-between">
                  <VStack space="xs" className="items-center flex-1">
                    <Text className="text-lg font-semibold text-typography-700">
                      {parseFloat(balance.balance_summary.hours_purchased).toFixed(1)}
                    </Text>
                    <Text className="text-xs text-typography-500 text-center">Total Purchased</Text>
                  </VStack>

                  <VStack space="xs" className="items-center flex-1">
                    <Text className="text-lg font-semibold text-typography-700">
                      {parseFloat(balance.balance_summary.hours_consumed).toFixed(1)}
                    </Text>
                    <Text className="text-xs text-typography-500 text-center">Hours Used</Text>
                  </VStack>

                  <VStack space="xs" className="items-center flex-1">
                    <Text className="text-lg font-semibold text-primary-600">
                      {(
                        (parseFloat(balance.balance_summary.hours_consumed) /
                          parseFloat(balance.balance_summary.hours_purchased)) *
                        100
                      ).toFixed(0)}
                      %
                    </Text>
                    <Text className="text-xs text-typography-500 text-center">Utilization</Text>
                  </VStack>
                </HStack>
              </VStack>

              {/* Package Status */}
              {balance.package_status.active_packages.length > 0 && (
                <>
                  <Divider />
                  <VStack space="sm">
                    <HStack className="items-center justify-between">
                      <Text className="font-semibold text-typography-800">Active Packages</Text>
                      <Badge variant="solid" action="success" size="sm">
                        <Text className="text-xs">
                          {balance.package_status.active_packages.length} Active
                        </Text>
                      </Badge>
                    </HStack>

                    <VStack space="xs">
                      {balance.package_status.active_packages.slice(0, 3).map((pkg, index) => (
                        <HStack
                          key={pkg.transaction_id}
                          className="items-center justify-between p-2 bg-background-50 rounded-md"
                        >
                          <HStack space="sm" className="items-center flex-1">
                            <Icon as={Package} size="sm" className="text-success-600" />
                            <VStack space="0" className="flex-1">
                              <Text className="text-sm font-medium text-typography-800">
                                {pkg.plan_name}
                              </Text>
                              <Text className="text-xs text-typography-600">
                                {parseFloat(pkg.hours_remaining).toFixed(1)} hours remaining
                              </Text>
                            </VStack>
                          </HStack>

                          {pkg.days_until_expiry && pkg.days_until_expiry <= 7 && (
                            <Badge
                              variant="solid"
                              action={pkg.days_until_expiry <= 3 ? 'error' : 'warning'}
                              size="sm"
                            >
                              <Text className="text-xs">{pkg.days_until_expiry}d left</Text>
                            </Badge>
                          )}
                        </HStack>
                      ))}

                      {balance.package_status.active_packages.length > 3 && (
                        <Text className="text-xs text-typography-500 text-center mt-2">
                          And {balance.package_status.active_packages.length - 3} more packages...
                        </Text>
                      )}
                    </VStack>
                  </VStack>
                </>
              )}

              {/* Expiration Warnings */}
              {balance.upcoming_expirations.length > 0 && (
                <>
                  <Divider />
                  <VStack space="sm">
                    <HStack className="items-center">
                      <Icon as={AlertTriangle} size="sm" className="text-warning-600" />
                      <Text className="font-semibold text-typography-800 ml-2">Expiring Soon</Text>
                    </HStack>

                    <VStack space="xs">
                      {balance.upcoming_expirations.slice(0, 2).map((expiration, index) => (
                        <HStack
                          key={expiration.transaction_id}
                          className="items-center justify-between p-2 bg-warning-50 rounded-md"
                        >
                          <VStack space="0" className="flex-1">
                            <Text className="text-sm font-medium text-typography-800">
                              {expiration.plan_name}
                            </Text>
                            <Text className="text-xs text-typography-600">
                              {parseFloat(expiration.hours_remaining).toFixed(1)} hours remaining
                            </Text>
                          </VStack>

                          <Badge
                            variant="solid"
                            action={
                              expiration.days_until_expiry && expiration.days_until_expiry <= 3
                                ? 'error'
                                : 'warning'
                            }
                            size="sm"
                          >
                            <Text className="text-xs">
                              {expiration.days_until_expiry} days left
                            </Text>
                          </Badge>
                        </HStack>
                      ))}
                    </VStack>

                    <Button
                      action="primary"
                      variant="solid"
                      size="sm"
                      onPress={onPurchase}
                      className="mt-2"
                    >
                      <ButtonIcon as={Plus} />
                      <ButtonText>Purchase More Hours</ButtonText>
                    </Button>
                  </VStack>
                </>
              )}

              {/* Empty State */}
              {balance.package_status.active_packages.length === 0 &&
                balance.upcoming_expirations.length === 0 &&
                parseFloat(balance.balance_summary.remaining_hours) === 0 && (
                  <>
                    <Divider />
                    <VStack space="sm" className="items-center py-6">
                      <Icon as={Package} size="xl" className="text-typography-300" />
                      <VStack space="xs" className="items-center">
                        <Text className="text-typography-600 font-medium">No Active Packages</Text>
                        <Text className="text-sm text-typography-500 text-center">
                          Purchase a tutoring package to get started with your learning journey.
                        </Text>
                      </VStack>
                      <Button
                        action="primary"
                        variant="solid"
                        size="md"
                        onPress={onPurchase}
                        className="mt-4"
                      >
                        <ButtonIcon as={ShoppingCart} />
                        <ButtonText>Browse Packages</ButtonText>
                      </Button>
                    </VStack>
                  </>
                )}
            </VStack>
          </Card>
        </VStack>
      )}

      {/* Analytics Section */}
      <UsageAnalyticsSection />

      {/* Notification System */}
      <NotificationSystem />
    </VStack>
  );
}
