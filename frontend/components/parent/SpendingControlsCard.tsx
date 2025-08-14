/**
 * SpendingControlsCard Component
 *
 * Compact budget management card for dashboard view displaying:
 * - Current budget status and limits
 * - Spending overview with visual indicators
 * - Quick access to detailed settings
 * - Alerts for budget concerns
 */

import {
  Shield,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Settings,
  Euro,
  Calendar,
  Clock,
  Target,
  BarChart3,
} from 'lucide-react-native';
import React, { useMemo } from 'react';

import { FamilyBudgetControl, FamilyMetrics } from '@/api/parentApi';
import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Progress } from '@/components/ui/progress';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface SpendingControlsCardProps {
  budgetControls: FamilyBudgetControl[];
  familyMetrics: FamilyMetrics;
  onOpenSettings: () => void;
  onViewAnalytics: () => void;
  compact?: boolean;
}

interface BudgetStatus {
  type: 'monthly' | 'weekly' | 'daily';
  limit: number;
  spent: number;
  percentage: number;
  status: 'safe' | 'warning' | 'danger' | 'exceeded';
  daysRemaining?: number;
}

export const SpendingControlsCard: React.FC<SpendingControlsCardProps> = ({
  budgetControls,
  familyMetrics,
  onOpenSettings,
  onViewAnalytics,
  compact = false,
}) => {
  // Calculate budget statuses
  const budgetStatuses = useMemo((): BudgetStatus[] => {
    const statuses: BudgetStatus[] = [];
    const currentSpent = parseFloat(familyMetrics.total_spent_this_month);

    // Get the most restrictive budget control (for simplicity, use the first active one)
    const activeBudgetControl = budgetControls.find(bc => bc.is_active);

    if (!activeBudgetControl) return statuses;

    // Monthly budget status
    if (activeBudgetControl.monthly_limit) {
      const monthlyLimit = parseFloat(activeBudgetControl.monthly_limit);
      const percentage = (currentSpent / monthlyLimit) * 100;

      statuses.push({
        type: 'monthly',
        limit: monthlyLimit,
        spent: currentSpent,
        percentage,
        status:
          percentage >= 100
            ? 'exceeded'
            : percentage >= 90
            ? 'danger'
            : percentage >= 75
            ? 'warning'
            : 'safe',
        daysRemaining:
          new Date().getDate() <= 15
            ? new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate() -
              new Date().getDate()
            : new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate() -
              new Date().getDate(),
      });
    }

    // Weekly budget status (simplified calculation)
    if (activeBudgetControl.weekly_limit) {
      const weeklyLimit = parseFloat(activeBudgetControl.weekly_limit);
      // Simplified: assume 25% of monthly spending is this week
      const weeklySpent = currentSpent * 0.25;
      const percentage = (weeklySpent / weeklyLimit) * 100;

      statuses.push({
        type: 'weekly',
        limit: weeklyLimit,
        spent: weeklySpent,
        percentage,
        status:
          percentage >= 100
            ? 'exceeded'
            : percentage >= 90
            ? 'danger'
            : percentage >= 75
            ? 'warning'
            : 'safe',
        daysRemaining: 7 - new Date().getDay(),
      });
    }

    // Daily budget status (simplified calculation)
    if (activeBudgetControl.daily_limit) {
      const dailyLimit = parseFloat(activeBudgetControl.daily_limit);
      // Simplified: assume even distribution
      const daysInMonth = new Date(
        new Date().getFullYear(),
        new Date().getMonth() + 1,
        0
      ).getDate();
      const dailySpent = currentSpent / new Date().getDate();
      const percentage = (dailySpent / dailyLimit) * 100;

      statuses.push({
        type: 'daily',
        limit: dailyLimit,
        spent: dailySpent,
        percentage,
        status:
          percentage >= 100
            ? 'exceeded'
            : percentage >= 90
            ? 'danger'
            : percentage >= 75
            ? 'warning'
            : 'safe',
      });
    }

    return statuses;
  }, [budgetControls, familyMetrics]);

  // Get overall status
  const overallStatus = useMemo(() => {
    if (budgetStatuses.length === 0) return 'no-limits';

    const hasExceeded = budgetStatuses.some(status => status.status === 'exceeded');
    const hasDanger = budgetStatuses.some(status => status.status === 'danger');
    const hasWarning = budgetStatuses.some(status => status.status === 'warning');

    if (hasExceeded) return 'exceeded';
    if (hasDanger) return 'danger';
    if (hasWarning) return 'warning';
    return 'safe';
  }, [budgetStatuses]);

  // Get status color and icon
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'exceeded':
        return 'text-red-600';
      case 'danger':
        return 'text-red-500';
      case 'warning':
        return 'text-orange-500';
      case 'safe':
        return 'text-green-600';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'exceeded':
      case 'danger':
        return AlertTriangle;
      case 'warning':
        return Clock;
      case 'safe':
        return CheckCircle;
      default:
        return Shield;
    }
  };

  const getProgressColor = (status: string) => {
    switch (status) {
      case 'exceeded':
        return 'bg-red-500';
      case 'danger':
        return 'bg-red-400';
      case 'warning':
        return 'bg-orange-400';
      case 'safe':
        return 'bg-green-500';
      default:
        return 'bg-gray-400';
    }
  };

  // Format currency
  const formatCurrency = (amount: number) => {
    return `€${amount.toFixed(2)}`;
  };

  // No budget controls set up
  if (budgetControls.length === 0 || !budgetControls.some(bc => bc.is_active)) {
    return (
      <Card className="bg-white border border-gray-200">
        <CardContent className="p-4">
          <VStack className="items-center space-y-3">
            <Icon as={Shield} size={32} className="text-gray-400" />
            <VStack className="items-center space-y-1">
              <Heading size="sm" className="text-gray-900">
                No Budget Limits Set
              </Heading>
              <Text className="text-sm text-gray-600 text-center">
                Set spending limits to control purchases
              </Text>
            </VStack>
            <Button action="primary" size="sm" onPress={onOpenSettings}>
              <ButtonIcon as={Settings} size={16} />
              <ButtonText className="ml-1">Set Up Controls</ButtonText>
            </Button>
          </VStack>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-white border border-gray-200">
      <CardHeader className="pb-3">
        <HStack className="justify-between items-center">
          <HStack className="space-x-2">
            <Icon
              as={getStatusIcon(overallStatus)}
              size={20}
              className={getStatusColor(overallStatus)}
            />
            <Heading size="md" className="text-gray-900">
              Spending Controls
            </Heading>
          </HStack>

          <HStack className="space-x-2">
            <Badge
              variant="solid"
              action={
                overallStatus === 'exceeded' || overallStatus === 'danger'
                  ? 'error'
                  : overallStatus === 'warning'
                  ? 'warning'
                  : overallStatus === 'safe'
                  ? 'success'
                  : 'secondary'
              }
              size="sm"
            >
              <Text className="text-xs font-medium">
                {overallStatus === 'exceeded'
                  ? 'Over Budget'
                  : overallStatus === 'danger'
                  ? 'High Usage'
                  : overallStatus === 'warning'
                  ? 'Watch Usage'
                  : overallStatus === 'safe'
                  ? 'On Track'
                  : 'No Limits'}
              </Text>
            </Badge>

            <Button variant="ghost" size="sm" onPress={onOpenSettings}>
              <ButtonIcon as={Settings} size={14} />
            </Button>
          </HStack>
        </HStack>
      </CardHeader>

      <CardContent>
        <VStack className="space-y-4">
          {/* Monthly Overview */}
          <VStack className="space-y-3">
            <HStack className="justify-between items-center">
              <Text className="text-sm font-medium text-gray-700">This Month</Text>
              <Text className="text-sm text-gray-900">
                {formatCurrency(parseFloat(familyMetrics.total_spent_this_month))} spent
              </Text>
            </HStack>

            {/* Budget Progress Bars */}
            {budgetStatuses.map(budget => (
              <VStack key={budget.type} className="space-y-2">
                <HStack className="justify-between items-center">
                  <HStack className="items-center space-x-2">
                    <Icon
                      as={
                        budget.type === 'monthly'
                          ? Calendar
                          : budget.type === 'weekly'
                          ? Calendar
                          : Clock
                      }
                      size={14}
                      className="text-gray-500"
                    />
                    <Text className="text-xs text-gray-600 capitalize">{budget.type} Limit</Text>
                  </HStack>

                  <HStack className="items-center space-x-2">
                    <Text className="text-xs text-gray-900">
                      {formatCurrency(budget.spent)} / {formatCurrency(budget.limit)}
                    </Text>
                    <Badge
                      variant="outline"
                      action={
                        budget.status === 'exceeded' || budget.status === 'danger'
                          ? 'error'
                          : budget.status === 'warning'
                          ? 'warning'
                          : 'success'
                      }
                      size="sm"
                    >
                      <Text className="text-xs">{Math.round(budget.percentage)}%</Text>
                    </Badge>
                  </HStack>
                </HStack>

                <Progress value={Math.min(budget.percentage, 100)} className="h-2" />

                {budget.daysRemaining && !compact && (
                  <Text className="text-xs text-gray-500">
                    {budget.daysRemaining} days remaining in{' '}
                    {budget.type === 'monthly' ? 'month' : 'week'}
                  </Text>
                )}
              </VStack>
            ))}
          </VStack>

          {!compact && (
            <>
              <Divider />

              {/* Quick Stats */}
              <HStack className="justify-between">
                <VStack className="items-center space-y-1">
                  <Text className="text-xs text-gray-600">Active Children</Text>
                  <Text className="text-sm font-semibold text-gray-900">
                    {familyMetrics.active_children}
                  </Text>
                </VStack>

                <VStack className="items-center space-y-1">
                  <Text className="text-xs text-gray-600">Hours Used</Text>
                  <Text className="text-sm font-semibold text-gray-900">
                    {familyMetrics.total_hours_consumed_this_month}
                  </Text>
                </VStack>

                <VStack className="items-center space-y-1">
                  <Text className="text-xs text-gray-600">Pending</Text>
                  <Text className="text-sm font-semibold text-gray-900">
                    {familyMetrics.pending_approvals}
                  </Text>
                </VStack>
              </HStack>

              <Divider />

              {/* Action Buttons */}
              <HStack className="space-x-2">
                <Button variant="outline" size="sm" className="flex-1" onPress={onViewAnalytics}>
                  <ButtonIcon as={BarChart3} size={16} />
                  <ButtonText className="ml-1">Analytics</ButtonText>
                </Button>

                <Button action="primary" size="sm" className="flex-1" onPress={onOpenSettings}>
                  <ButtonIcon as={Settings} size={16} />
                  <ButtonText className="ml-1">Settings</ButtonText>
                </Button>
              </HStack>
            </>
          )}

          {/* Alerts */}
          {overallStatus === 'exceeded' && (
            <VStack className="p-3 bg-red-50 rounded-lg border border-red-200 space-y-1">
              <HStack className="items-center space-x-2">
                <Icon as={AlertTriangle} size={16} className="text-red-600" />
                <Text className="text-sm font-medium text-red-800">Budget Exceeded</Text>
              </HStack>
              <Text className="text-xs text-red-700">
                Some spending limits have been exceeded. Review your budget settings.
              </Text>
            </VStack>
          )}

          {overallStatus === 'danger' && (
            <VStack className="p-3 bg-orange-50 rounded-lg border border-orange-200 space-y-1">
              <HStack className="items-center space-x-2">
                <Icon as={AlertTriangle} size={16} className="text-orange-600" />
                <Text className="text-sm font-medium text-orange-800">High Usage Alert</Text>
              </HStack>
              <Text className="text-xs text-orange-700">
                Approaching budget limits. Monitor spending closely.
              </Text>
            </VStack>
          )}
        </VStack>
      </CardContent>
    </Card>
  );
};
