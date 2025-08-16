/**
 * Payment Metrics Grid Component - GitHub Issue #117
 *
 * Displays key payment metrics in a responsive grid layout with
 * real-time updates and trend indicators.
 */

import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  CreditCard,
  AlertTriangle,
  CheckCircle,
  Clock,
  Shield,
} from 'lucide-react-native';
import React from 'react';

import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Card } from '@/components/ui/card';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Skeleton } from '@/components/ui/skeleton';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import type { PaymentMetrics, PaymentMonitoringState } from '@/types/paymentMonitoring';

interface PaymentMetricsGridProps {
  metrics: PaymentMetrics;
  timeRange: PaymentMonitoringState['timeRange'];
  loading?: boolean;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'stable';
    timeframe: string;
  };
  icon: React.ComponentType<any>;
  iconColor: string;
  badge?: {
    text: string;
    variant: 'success' | 'warning' | 'error' | 'info';
  };
  loading?: boolean;
}

function MetricCard({
  title,
  value,
  subtitle,
  trend,
  icon: IconComponent,
  iconColor,
  badge,
  loading,
}: MetricCardProps) {
  if (loading) {
    return (
      <Card className="p-6">
        <VStack space="md">
          <HStack className="justify-between items-start">
            <VStack space="xs" flex={1}>
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-8 w-16" />
            </VStack>
            <Skeleton className="h-10 w-10 rounded-full" />
          </HStack>
          <Skeleton className="h-4 w-32" />
        </VStack>
      </Card>
    );
  }

  const formatValue = (val: string | number) => {
    if (typeof val === 'number') {
      return val.toLocaleString();
    }
    // Handle currency values
    if (val.includes('.')) {
      const num = parseFloat(val);
      return `€${num.toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`;
    }
    return val;
  };

  const getTrendIcon = () => {
    if (!trend) return null;

    switch (trend.direction) {
      case 'up':
        return <Icon as={TrendingUp} size="xs" className="text-success-600" />;
      case 'down':
        return <Icon as={TrendingDown} size="xs" className="text-error-600" />;
      default:
        return null;
    }
  };

  const getTrendColor = () => {
    if (!trend) return 'text-typography-500';

    switch (trend.direction) {
      case 'up':
        return 'text-success-600';
      case 'down':
        return 'text-error-600';
      default:
        return 'text-typography-500';
    }
  };

  return (
    <Card className="p-6 hover:shadow-md transition-shadow">
      <VStack space="md">
        {/* Header with title and icon */}
        <HStack className="justify-between items-start">
          <VStack space="xs" flex={1}>
            <Text size="sm" className="text-typography-600 font-medium">
              {title}
            </Text>
            <Text size="2xl" className="text-typography-900 font-bold">
              {formatValue(value)}
            </Text>
            {subtitle && (
              <Text size="xs" className="text-typography-500">
                {subtitle}
              </Text>
            )}
          </VStack>

          <Box className={`p-2 rounded-full ${iconColor}`}>
            <Icon as={IconComponent} size="sm" className="text-white" />
          </Box>
        </HStack>

        {/* Footer with trend and badge */}
        <HStack className="justify-between items-center">
          {trend ? (
            <HStack space="xs" className="items-center">
              {getTrendIcon()}
              <Text size="xs" className={getTrendColor()}>
                {trend.direction === 'up' ? '+' : trend.direction === 'down' ? '-' : ''}
                {Math.abs(trend.value)}% {trend.timeframe}
              </Text>
            </HStack>
          ) : (
            <Box />
          )}

          {badge && (
            <Badge variant={badge.variant} size="sm">
              <Text size="xs">{badge.text}</Text>
            </Badge>
          )}
        </HStack>
      </VStack>
    </Card>
  );
}

export default function PaymentMetricsGrid({
  metrics,
  timeRange,
  loading,
}: PaymentMetricsGridProps) {
  const getTimeframeSuffix = () => {
    switch (timeRange) {
      case 'last_24h':
        return '24h';
      case 'last_7d':
        return '7d';
      case 'last_30d':
        return '30d';
      default:
        return '';
    }
  };

  const calculateSuccessRateTrend = () => {
    // Calculate trend based on current vs previous period
    const current = metrics.success_rate_24h;
    const previous =
      timeRange === 'last_24h'
        ? metrics.success_rate_7d / 7
        : timeRange === 'last_7d'
          ? metrics.success_rate_30d / 4
          : 95; // Fallback average

    const change = ((current - previous) / previous) * 100;
    return {
      value: Math.abs(change),
      direction:
        change > 0 ? ('up' as const) : change < 0 ? ('down' as const) : ('stable' as const),
      timeframe: 'vs prev period',
    };
  };

  const getSuccessRateValue = () => {
    switch (timeRange) {
      case 'last_24h':
        return `${metrics.success_rate_24h.toFixed(1)}%`;
      case 'last_7d':
        return `${metrics.success_rate_7d.toFixed(1)}%`;
      case 'last_30d':
        return `${metrics.success_rate_30d.toFixed(1)}%`;
      default:
        return `${metrics.success_rate_24h.toFixed(1)}%`;
    }
  };

  const getTransactionCount = () => {
    switch (timeRange) {
      case 'last_24h':
        return metrics.total_transactions_24h;
      case 'last_7d':
        return metrics.total_transactions_7d;
      case 'last_30d':
        return metrics.total_transactions_30d;
      default:
        return metrics.total_transactions_24h;
    }
  };

  const getRevenue = () => {
    switch (timeRange) {
      case 'last_24h':
        return metrics.total_revenue_24h;
      case 'last_7d':
        return metrics.total_revenue_7d;
      case 'last_30d':
        return metrics.total_revenue_30d;
      default:
        return metrics.total_revenue_24h;
    }
  };

  const metricsData = [
    {
      title: 'Success Rate',
      value: getSuccessRateValue(),
      subtitle: `${getTimeframeSuffix()} success rate`,
      trend: calculateSuccessRateTrend(),
      icon: CheckCircle,
      iconColor: 'bg-success-500',
      badge:
        metrics.success_rate_24h >= 95
          ? { text: 'Excellent', variant: 'success' as const }
          : metrics.success_rate_24h >= 90
            ? { text: 'Good', variant: 'info' as const }
            : { text: 'Needs Attention', variant: 'warning' as const },
    },
    {
      title: 'Transaction Volume',
      value: getTransactionCount(),
      subtitle: `Total transactions (${getTimeframeSuffix()})`,
      icon: CreditCard,
      iconColor: 'bg-primary-500',
    },
    {
      title: 'Revenue',
      value: getRevenue(),
      subtitle: `Total revenue (${getTimeframeSuffix()})`,
      icon: DollarSign,
      iconColor: 'bg-success-600',
    },
    {
      title: 'Average Transaction',
      value: metrics.average_transaction_value,
      subtitle: 'Mean transaction value',
      icon: TrendingUp,
      iconColor: 'bg-info-500',
    },
    {
      title: 'Failed Transactions',
      value: metrics.failed_transactions_24h,
      subtitle: 'Failed in last 24h',
      icon: AlertTriangle,
      iconColor: 'bg-error-500',
      badge:
        metrics.failed_transactions_24h > 0
          ? { text: 'Attention Required', variant: 'error' as const }
          : { text: 'All Good', variant: 'success' as const },
    },
    {
      title: 'Pending Transactions',
      value: metrics.pending_transactions,
      subtitle: 'Currently pending',
      icon: Clock,
      iconColor: 'bg-warning-500',
      badge:
        metrics.pending_transactions > 10
          ? { text: 'High Volume', variant: 'warning' as const }
          : { text: 'Normal', variant: 'info' as const },
    },
    {
      title: 'Active Disputes',
      value: metrics.active_disputes,
      subtitle: 'Requiring attention',
      icon: Shield,
      iconColor: 'bg-warning-600',
      badge:
        metrics.active_disputes > 0
          ? { text: 'Action Needed', variant: 'warning' as const }
          : { text: 'None', variant: 'success' as const },
    },
    {
      title: 'Fraud Alerts',
      value: metrics.fraud_alerts,
      subtitle: 'Active alerts',
      icon: AlertTriangle,
      iconColor: 'bg-error-600',
      badge:
        metrics.fraud_alerts > 0
          ? { text: 'Investigate', variant: 'error' as const }
          : { text: 'Clean', variant: 'success' as const },
    },
  ];

  return (
    <VStack space="md">
      {/* Grid Container - Responsive layout */}
      <Box className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metricsData.map((metric, index) => (
          <MetricCard
            key={index}
            title={metric.title}
            value={metric.value}
            subtitle={metric.subtitle}
            trend={metric.trend}
            icon={metric.icon}
            iconColor={metric.iconColor}
            badge={metric.badge}
            loading={loading}
          />
        ))}
      </Box>
    </VStack>
  );
}
