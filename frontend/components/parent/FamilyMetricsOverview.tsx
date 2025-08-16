/**
 * FamilyMetricsOverview Component
 *
 * Aggregate family usage and spending metrics display
 * with timeframe selection and trend visualization.
 */

import {
  Users,
  CreditCard,
  Clock,
  TrendingUp,
  TrendingDown,
  Activity,
  AlertCircle,
  CheckCircle,
  Calendar,
} from 'lucide-react-native';
import React from 'react';

import { FamilyMetrics } from '@/api/parentApi';
import { Badge } from '@/components/ui/badge';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface FamilyMetricsOverviewProps {
  metrics: FamilyMetrics;
  timeframe: 'week' | 'month' | 'quarter';
  onTimeframeChange: (timeframe: 'week' | 'month' | 'quarter') => void;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<any>;
  iconColor: string;
  iconBgColor: string;
  trend?: {
    direction: 'up' | 'down' | 'neutral';
    percentage: number;
    label: string;
  };
  badge?: {
    text: string;
    variant: 'success' | 'warning' | 'error' | 'info';
  };
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  iconColor,
  iconBgColor,
  trend,
  badge,
}) => {
  return (
    <VStack className="bg-white rounded-lg p-4 border border-gray-200 space-y-3">
      {/* Header */}
      <HStack className="justify-between items-start">
        <VStack
          className={`
            items-center justify-center w-10 h-10 rounded-full
            ${iconBgColor}
          `}
        >
          <Icon as={icon} size={20} className={iconColor} />
        </VStack>

        {badge && (
          <Badge variant="solid" action={badge.variant} size="sm">
            <Text className="text-xs font-medium">{badge.text}</Text>
          </Badge>
        )}
      </HStack>

      {/* Value */}
      <VStack className="space-y-1">
        <Text className="text-2xl font-bold text-gray-900">{value}</Text>
        <Text className="text-sm text-gray-600">{title}</Text>
        {subtitle && <Text className="text-xs text-gray-500">{subtitle}</Text>}
      </VStack>

      {/* Trend */}
      {trend && (
        <HStack className="items-center space-x-1">
          <Icon
            as={trend.direction === 'up' ? TrendingUp : TrendingDown}
            size={14}
            className={
              trend.direction === 'up'
                ? 'text-green-600'
                : trend.direction === 'down'
                  ? 'text-red-600'
                  : 'text-gray-600'
            }
          />
          <Text
            className={`
              text-xs font-medium
              ${
                trend.direction === 'up'
                  ? 'text-green-600'
                  : trend.direction === 'down'
                    ? 'text-red-600'
                    : 'text-gray-600'
              }
            `}
          >
            {trend.percentage}% {trend.label}
          </Text>
        </HStack>
      )}
    </VStack>
  );
};

export const FamilyMetricsOverview: React.FC<FamilyMetricsOverviewProps> = ({
  metrics,
  timeframe,
  onTimeframeChange,
}) => {
  // Format currency
  const formatCurrency = (amount: string | number) => {
    const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
    return isNaN(numAmount) ? '€0' : `€${numAmount.toFixed(0)}`;
  };

  // Get timeframe label
  const getTimeframeLabel = (tf: string) => {
    switch (tf) {
      case 'week':
        return 'This Week';
      case 'month':
        return 'This Month';
      case 'quarter':
        return 'This Quarter';
      default:
        return 'This Month';
    }
  };

  // Calculate engagement rate (placeholder calculation)
  const calculateEngagementRate = () => {
    if (metrics.total_children === 0) return 0;
    return Math.round((metrics.active_children / metrics.total_children) * 100);
  };

  // Metric cards data
  const metricCards: MetricCardProps[] = [
    {
      title: 'Total Children',
      value: metrics.total_children,
      subtitle: `${metrics.active_children} active`,
      icon: Users,
      iconColor: 'text-blue-600',
      iconBgColor: 'bg-blue-100',
      badge:
        metrics.active_children > 0
          ? {
              text: `${calculateEngagementRate()}% active`,
              variant: calculateEngagementRate() > 70 ? 'success' : 'warning',
            }
          : undefined,
    },
    {
      title: `Spent ${getTimeframeLabel(timeframe)}`,
      value: formatCurrency(metrics.total_spent_this_month),
      subtitle: 'Family total',
      icon: CreditCard,
      iconColor: 'text-green-600',
      iconBgColor: 'bg-green-100',
      // TODO: Add trend calculation when we have historical data
    },
    {
      title: `Hours Used ${getTimeframeLabel(timeframe)}`,
      value: `${metrics.total_hours_consumed_this_month}h`,
      subtitle: 'Across all children',
      icon: Clock,
      iconColor: 'text-purple-600',
      iconBgColor: 'bg-purple-100',
      // TODO: Add trend calculation when we have historical data
    },
    {
      title: 'Pending Approvals',
      value: metrics.pending_approvals,
      subtitle: 'Require attention',
      icon: AlertCircle,
      iconColor: metrics.pending_approvals > 0 ? 'text-orange-600' : 'text-gray-600',
      iconBgColor: metrics.pending_approvals > 0 ? 'bg-orange-100' : 'bg-gray-100',
      badge:
        metrics.pending_approvals > 0
          ? {
              text: 'Action needed',
              variant: 'warning',
            }
          : {
              text: 'All clear',
              variant: 'success',
            },
    },
  ];

  return (
    <Card className="bg-white">
      <CardHeader className="pb-3">
        <HStack className="justify-between items-center">
          <Heading size="md" className="text-gray-900">
            Family Overview
          </Heading>

          {/* Timeframe Selector */}
          <HStack className="space-x-1">
            {(['week', 'month', 'quarter'] as const).map(tf => (
              <Button
                key={tf}
                variant={timeframe === tf ? 'solid' : 'outline'}
                action={timeframe === tf ? 'primary' : 'secondary'}
                size="sm"
                onPress={() => onTimeframeChange(tf)}
              >
                <ButtonText className="capitalize text-xs">{tf}</ButtonText>
              </Button>
            ))}
          </HStack>
        </HStack>
      </CardHeader>

      <CardContent>
        {/* Metrics Grid */}
        <VStack className="space-y-4 mb-6">
          {/* Top row - 2 cards */}
          <HStack className="space-x-4">
            <VStack className="flex-1">
              <MetricCard {...metricCards[0]} />
            </VStack>
            <VStack className="flex-1">
              <MetricCard {...metricCards[1]} />
            </VStack>
          </HStack>

          {/* Bottom row - 2 cards */}
          <HStack className="space-x-4">
            <VStack className="flex-1">
              <MetricCard {...metricCards[2]} />
            </VStack>
            <VStack className="flex-1">
              <MetricCard {...metricCards[3]} />
            </VStack>
          </HStack>
        </VStack>

        {/* Children Summary */}
        {metrics.children_summary.length > 0 && (
          <>
            <Divider className="mb-4" />

            <VStack className="space-y-3">
              <Heading size="sm" className="text-gray-900">
                Children Activity Summary
              </Heading>

              <VStack className="space-y-2">
                {metrics.children_summary.slice(0, 3).map(child => (
                  <HStack key={child.child_id} className="justify-between items-center py-2">
                    <HStack className="flex-1 space-x-3">
                      <VStack
                        className={`
                          w-8 h-8 rounded-full items-center justify-center
                          ${child.status === 'active' ? 'bg-green-100' : 'bg-gray-100'}
                        `}
                      >
                        <Icon
                          as={child.status === 'active' ? CheckCircle : AlertCircle}
                          size={14}
                          className={child.status === 'active' ? 'text-green-600' : 'text-gray-600'}
                        />
                      </VStack>

                      <VStack className="flex-1">
                        <Text className="text-gray-900 font-medium">{child.child_name}</Text>
                        <Text className="text-xs text-gray-600">
                          {child.hours_consumed_this_month}h used • {child.current_balance}h
                          remaining
                        </Text>
                      </VStack>
                    </HStack>

                    <Badge
                      variant="outline"
                      action={child.status === 'active' ? 'success' : 'secondary'}
                      size="sm"
                    >
                      <Text className="text-xs font-medium capitalize">{child.status}</Text>
                    </Badge>
                  </HStack>
                ))}

                {metrics.children_summary.length > 3 && (
                  <Pressable className="py-2">
                    <Text className="text-sm text-blue-600 font-medium text-center">
                      View all {metrics.children_summary.length} children
                    </Text>
                  </Pressable>
                )}
              </VStack>
            </VStack>
          </>
        )}
      </CardContent>
    </Card>
  );
};
