/**
 * SpendingAnalytics Component
 *
 * Visual spending tracking and analytics with:
 * - Spending trends and patterns
 * - Budget utilization charts
 * - Comparative analysis across children
 * - Time-based breakdowns
 * - Mobile-optimized chart displays
 */

import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Calendar,
  Clock,
  Euro,
  Target,
  Users,
  ChevronLeft,
  ChevronRight,
  Filter,
  Download,
  PieChart,
  Activity,
} from 'lucide-react-native';
import React, { useState, useMemo } from 'react';

import { FamilyMetrics, FamilyBudgetControl } from '@/api/parentApi';
import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Progress } from '@/components/ui/progress';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface SpendingData {
  date: string;
  amount: number;
  child_id: number;
  child_name: string;
  plan_name: string;
  hours: number;
}

interface SpendingAnalyticsProps {
  familyMetrics: FamilyMetrics;
  budgetControls: FamilyBudgetControl[];
  spendingHistory: SpendingData[];
  timeframe: 'week' | 'month' | 'quarter';
  onTimeframeChange: (timeframe: 'week' | 'month' | 'quarter') => void;
}

type ViewMode = 'overview' | 'trends' | 'comparison' | 'breakdown';

export const SpendingAnalytics: React.FC<SpendingAnalyticsProps> = ({
  familyMetrics,
  budgetControls,
  spendingHistory,
  timeframe,
  onTimeframeChange,
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>('overview');

  // Calculate spending trends
  const spendingTrends = useMemo(() => {
    const now = new Date();
    const periods = [];

    // Create time periods based on timeframe
    for (let i = 6; i >= 0; i--) {
      let periodStart, periodEnd, label;

      if (timeframe === 'week') {
        periodStart = new Date(now.getTime() - i * 7 * 24 * 60 * 60 * 1000);
        periodEnd = new Date(periodStart.getTime() + 7 * 24 * 60 * 60 * 1000);
        label = periodStart.toLocaleDateString('en-GB', { month: 'short', day: 'numeric' });
      } else if (timeframe === 'month') {
        periodStart = new Date(now.getFullYear(), now.getMonth() - i, 1);
        periodEnd = new Date(now.getFullYear(), now.getMonth() - i + 1, 0);
        label = periodStart.toLocaleDateString('en-GB', { month: 'short' });
      } else {
        periodStart = new Date(now.getFullYear(), now.getMonth() - i * 3, 1);
        periodEnd = new Date(now.getFullYear(), now.getMonth() - i * 3 + 3, 0);
        label = `Q${Math.floor(periodStart.getMonth() / 3) + 1} ${periodStart.getFullYear()}`;
      }

      const periodSpending = spendingHistory
        .filter(s => {
          const date = new Date(s.date);
          return date >= periodStart && date <= periodEnd;
        })
        .reduce((sum, s) => sum + s.amount, 0);

      periods.push({
        label,
        amount: periodSpending,
        start: periodStart,
        end: periodEnd,
      });
    }

    return periods;
  }, [spendingHistory, timeframe]);

  // Calculate child comparison data
  const childComparison = useMemo(() => {
    const childData = new Map();

    spendingHistory.forEach(spend => {
      if (!childData.has(spend.child_id)) {
        childData.set(spend.child_id, {
          id: spend.child_id,
          name: spend.child_name,
          totalSpent: 0,
          totalHours: 0,
          purchases: 0,
        });
      }

      const child = childData.get(spend.child_id);
      child.totalSpent += spend.amount;
      child.totalHours += spend.hours;
      child.purchases += 1;
    });

    return Array.from(childData.values()).sort((a, b) => b.totalSpent - a.totalSpent);
  }, [spendingHistory]);

  // Budget utilization analysis
  const budgetUtilization = useMemo(() => {
    const activeBudget = budgetControls.find(bc => bc.is_active);
    if (!activeBudget) return null;

    const currentSpent = parseFloat(familyMetrics.total_spent_this_month);
    const monthlyLimit = activeBudget.monthly_limit ? parseFloat(activeBudget.monthly_limit) : null;

    return {
      spent: currentSpent,
      monthlyLimit,
      percentage: monthlyLimit ? (currentSpent / monthlyLimit) * 100 : 0,
      remaining: monthlyLimit ? monthlyLimit - currentSpent : null,
      status: monthlyLimit
        ? currentSpent >= monthlyLimit
          ? 'exceeded'
          : currentSpent >= monthlyLimit * 0.9
          ? 'warning'
          : currentSpent >= monthlyLimit * 0.75
          ? 'caution'
          : 'safe'
        : 'no-limit',
    };
  }, [budgetControls, familyMetrics]);

  // Calculate spending velocity (rate of spending)
  const spendingVelocity = useMemo(() => {
    const last7Days = spendingHistory.filter(s => {
      const date = new Date(s.date);
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      return date >= sevenDaysAgo;
    });

    const previous7Days = spendingHistory.filter(s => {
      const date = new Date(s.date);
      const fourteenDaysAgo = new Date();
      fourteenDaysAgo.setDate(fourteenDaysAgo.getDate() - 14);
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      return date >= fourteenDaysAgo && date < sevenDaysAgo;
    });

    const currentWeekSpending = last7Days.reduce((sum, s) => sum + s.amount, 0);
    const previousWeekSpending = previous7Days.reduce((sum, s) => sum + s.amount, 0);

    const change =
      previousWeekSpending > 0
        ? ((currentWeekSpending - previousWeekSpending) / previousWeekSpending) * 100
        : 0;

    return {
      currentWeek: currentWeekSpending,
      previousWeek: previousWeekSpending,
      change,
      trend: change > 10 ? 'increasing' : change < -10 ? 'decreasing' : 'stable',
    };
  }, [spendingHistory]);

  // Format currency
  const formatCurrency = (amount: number) => `€${amount.toFixed(2)}`;

  // Get max amount for chart scaling
  const maxAmount = Math.max(...spendingTrends.map(t => t.amount), 1);

  return (
    <VStack className="space-y-6">
      {/* Header with timeframe selector */}
      <Card className="bg-white">
        <CardHeader>
          <HStack className="justify-between items-center">
            <HStack className="space-x-2">
              <Icon as={BarChart3} size={24} className="text-blue-600" />
              <Heading size="lg" className="text-gray-900">
                Spending Analytics
              </Heading>
            </HStack>

            <HStack className="space-x-1">
              {(['week', 'month', 'quarter'] as const).map(period => (
                <Button
                  key={period}
                  variant={timeframe === period ? 'solid' : 'outline'}
                  size="sm"
                  onPress={() => onTimeframeChange(period)}
                >
                  <ButtonText className="text-xs capitalize">{period}</ButtonText>
                </Button>
              ))}
            </HStack>
          </HStack>

          {/* View mode selector */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <HStack className="space-x-2 mt-3">
              {[
                { key: 'overview' as ViewMode, label: 'Overview', icon: Activity },
                { key: 'trends' as ViewMode, label: 'Trends', icon: TrendingUp },
                { key: 'comparison' as ViewMode, label: 'Children', icon: Users },
                { key: 'breakdown' as ViewMode, label: 'Breakdown', icon: PieChart },
              ].map(mode => (
                <Button
                  key={mode.key}
                  variant={viewMode === mode.key ? 'solid' : 'outline'}
                  size="sm"
                  onPress={() => setViewMode(mode.key)}
                >
                  <ButtonIcon as={mode.icon} size={14} />
                  <ButtonText className="ml-1 text-xs">{mode.label}</ButtonText>
                </Button>
              ))}
            </HStack>
          </ScrollView>
        </CardHeader>
      </Card>

      {/* Overview Mode */}
      {viewMode === 'overview' && (
        <VStack className="space-y-4">
          {/* Key Metrics Cards */}
          <HStack className="space-x-3">
            <Card className="bg-white flex-1">
              <CardContent className="p-4">
                <VStack className="space-y-2">
                  <HStack className="items-center space-x-2">
                    <Icon as={Euro} size={16} className="text-blue-600" />
                    <Text className="text-sm text-gray-600">Total Spent</Text>
                  </HStack>
                  <Text className="text-xl font-bold text-gray-900">
                    {formatCurrency(parseFloat(familyMetrics.total_spent_this_month))}
                  </Text>
                  <HStack className="items-center space-x-1">
                    <Icon
                      as={
                        spendingVelocity.trend === 'increasing'
                          ? TrendingUp
                          : spendingVelocity.trend === 'decreasing'
                          ? TrendingDown
                          : Activity
                      }
                      size={12}
                      className={
                        spendingVelocity.trend === 'increasing'
                          ? 'text-red-500'
                          : spendingVelocity.trend === 'decreasing'
                          ? 'text-green-500'
                          : 'text-gray-500'
                      }
                    />
                    <Text
                      className={`text-xs ${
                        spendingVelocity.trend === 'increasing'
                          ? 'text-red-600'
                          : spendingVelocity.trend === 'decreasing'
                          ? 'text-green-600'
                          : 'text-gray-600'
                      }`}
                    >
                      {Math.abs(spendingVelocity.change).toFixed(1)}% vs last week
                    </Text>
                  </HStack>
                </VStack>
              </CardContent>
            </Card>

            <Card className="bg-white flex-1">
              <CardContent className="p-4">
                <VStack className="space-y-2">
                  <HStack className="items-center space-x-2">
                    <Icon as={Clock} size={16} className="text-green-600" />
                    <Text className="text-sm text-gray-600">Hours Used</Text>
                  </HStack>
                  <Text className="text-xl font-bold text-gray-900">
                    {familyMetrics.total_hours_consumed_this_month}
                  </Text>
                  <Text className="text-xs text-gray-600">
                    Across {familyMetrics.active_children} children
                  </Text>
                </VStack>
              </CardContent>
            </Card>
          </HStack>

          {/* Budget Status */}
          {budgetUtilization && budgetUtilization.monthlyLimit && (
            <Card className="bg-white">
              <CardContent className="p-4">
                <VStack className="space-y-3">
                  <HStack className="justify-between items-center">
                    <HStack className="items-center space-x-2">
                      <Icon as={Target} size={20} className="text-blue-600" />
                      <Text className="text-sm font-medium text-gray-900">
                        Monthly Budget Status
                      </Text>
                    </HStack>
                    <Badge
                      variant="solid"
                      action={
                        budgetUtilization.status === 'exceeded'
                          ? 'error'
                          : budgetUtilization.status === 'warning'
                          ? 'warning'
                          : budgetUtilization.status === 'caution'
                          ? 'info'
                          : 'success'
                      }
                      size="sm"
                    >
                      <Text className="text-xs font-medium">
                        {budgetUtilization.percentage.toFixed(0)}% Used
                      </Text>
                    </Badge>
                  </HStack>

                  <Progress value={Math.min(budgetUtilization.percentage, 100)} className="h-3" />

                  <HStack className="justify-between items-center">
                    <Text className="text-sm text-gray-600">
                      {formatCurrency(budgetUtilization.spent)} /{' '}
                      {formatCurrency(budgetUtilization.monthlyLimit)}
                    </Text>
                    {budgetUtilization.remaining !== null && (
                      <Text
                        className={`text-sm font-medium ${
                          budgetUtilization.remaining < 0 ? 'text-red-600' : 'text-green-600'
                        }`}
                      >
                        {budgetUtilization.remaining < 0 ? 'Over by ' : 'Remaining: '}
                        {formatCurrency(Math.abs(budgetUtilization.remaining))}
                      </Text>
                    )}
                  </HStack>
                </VStack>
              </CardContent>
            </Card>
          )}
        </VStack>
      )}

      {/* Trends Mode */}
      {viewMode === 'trends' && (
        <Card className="bg-white">
          <CardContent className="p-4">
            <VStack className="space-y-4">
              <Text className="text-sm font-medium text-gray-900">
                Spending Trend ({timeframe})
              </Text>

              {/* Simple bar chart */}
              <VStack className="space-y-3">
                {spendingTrends.map((trend, index) => (
                  <VStack key={index} className="space-y-1">
                    <HStack className="justify-between items-center">
                      <Text className="text-xs text-gray-600">{trend.label}</Text>
                      <Text className="text-xs font-medium text-gray-900">
                        {formatCurrency(trend.amount)}
                      </Text>
                    </HStack>
                    <Progress value={(trend.amount / maxAmount) * 100} className="h-2" />
                  </VStack>
                ))}
              </VStack>

              {/* Trend summary */}
              <HStack className="justify-between items-center p-3 bg-gray-50 rounded-lg">
                <Text className="text-sm text-gray-700">Average per {timeframe}:</Text>
                <Text className="text-sm font-semibold text-gray-900">
                  {formatCurrency(
                    spendingTrends.reduce((sum, t) => sum + t.amount, 0) / spendingTrends.length
                  )}
                </Text>
              </HStack>
            </VStack>
          </CardContent>
        </Card>
      )}

      {/* Child Comparison Mode */}
      {viewMode === 'comparison' && (
        <Card className="bg-white">
          <CardContent className="p-4">
            <VStack className="space-y-4">
              <Text className="text-sm font-medium text-gray-900">Spending by Child</Text>

              {childComparison.length === 0 ? (
                <VStack className="items-center py-8 space-y-2">
                  <Icon as={Users} size={32} className="text-gray-400" />
                  <Text className="text-sm text-gray-600">No spending data available</Text>
                </VStack>
              ) : (
                <VStack className="space-y-3">
                  {childComparison.map(child => (
                    <VStack key={child.id} className="space-y-2 p-3 bg-gray-50 rounded-lg">
                      <HStack className="justify-between items-center">
                        <Text className="text-sm font-medium text-gray-900">{child.name}</Text>
                        <Text className="text-sm font-bold text-gray-900">
                          {formatCurrency(child.totalSpent)}
                        </Text>
                      </HStack>

                      <HStack className="justify-between items-center">
                        <Text className="text-xs text-gray-600">
                          {child.totalHours} hours • {child.purchases} purchases
                        </Text>
                        <Text className="text-xs text-gray-600">
                          Avg: {formatCurrency(child.totalSpent / child.purchases)}
                        </Text>
                      </HStack>

                      <Progress
                        value={
                          (child.totalSpent / Math.max(...childComparison.map(c => c.totalSpent))) *
                          100
                        }
                        className="h-2"
                      />
                    </VStack>
                  ))}
                </VStack>
              )}
            </VStack>
          </CardContent>
        </Card>
      )}

      {/* Breakdown Mode */}
      {viewMode === 'breakdown' && (
        <VStack className="space-y-4">
          {/* Purchase type breakdown */}
          <Card className="bg-white">
            <CardContent className="p-4">
              <VStack className="space-y-3">
                <Text className="text-sm font-medium text-gray-900">Recent Purchases</Text>

                {spendingHistory.slice(0, 5).map((purchase, index) => (
                  <HStack
                    key={index}
                    className="justify-between items-center p-2 bg-gray-50 rounded"
                  >
                    <VStack className="flex-1">
                      <HStack className="justify-between items-start w-full">
                        <Text className="text-sm font-medium text-gray-900">
                          {purchase.plan_name}
                        </Text>
                        <Text className="text-sm font-bold text-gray-900">
                          {formatCurrency(purchase.amount)}
                        </Text>
                      </HStack>
                      <HStack className="justify-between items-center w-full">
                        <Text className="text-xs text-gray-600">
                          {purchase.child_name} • {new Date(purchase.date).toLocaleDateString()}
                        </Text>
                        <Text className="text-xs text-gray-600">{purchase.hours} hours</Text>
                      </HStack>
                    </VStack>
                  </HStack>
                ))}
              </VStack>
            </CardContent>
          </Card>
        </VStack>
      )}
    </VStack>
  );
};
