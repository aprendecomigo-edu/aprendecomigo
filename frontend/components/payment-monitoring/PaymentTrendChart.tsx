/**
 * Payment Trend Chart Component - GitHub Issue #117
 *
 * Displays payment trends using victory-native for cross-platform charts.
 * Shows transaction volume, revenue, and success rate trends over time.
 */

import { TrendingUp, BarChart3, DollarSign, Percent } from 'lucide-react-native';
import React, { useMemo } from 'react';
import { Dimensions } from 'react-native';

import { Box } from '@/components/ui/box';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Skeleton } from '@/components/ui/skeleton';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Victory Native imports - Placeholder for now
// TODO: Install victory-native package for production charts
// import {
//   VictoryChart,
//   VictoryLine,
//   VictoryArea,
//   VictoryAxis,
//   VictoryTheme,
//   VictoryTooltip,
//   VictoryLabel,
//   VictoryContainer,
// } from 'victory-native';

import type { PaymentTrendData, PaymentMonitoringState } from '@/types/paymentMonitoring';

interface PaymentTrendChartProps {
  data: PaymentTrendData;
  metric: 'transactions' | 'revenue' | 'success_rate';
  timeRange: PaymentMonitoringState['timeRange'];
  height?: number;
}

interface ChartMetric {
  key: keyof PaymentTrendData;
  label: string;
  icon: React.ComponentType<any>;
  color: string;
  unit: string;
  format: (value: number) => string;
}

const chartMetrics: Record<string, ChartMetric> = {
  transactions: {
    key: 'transactions',
    label: 'Transaction Volume',
    icon: BarChart3,
    color: '#3B82F6', // blue-500
    unit: 'transactions',
    format: value => value.toLocaleString(),
  },
  revenue: {
    key: 'revenue',
    label: 'Revenue',
    icon: DollarSign,
    color: '#10B981', // emerald-500
    unit: 'EUR',
    format: value =>
      `€${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
  },
  success_rate: {
    key: 'success_rate',
    label: 'Success Rate',
    icon: Percent,
    color: '#8B5CF6', // violet-500
    unit: '%',
    format: value => `${value.toFixed(1)}%`,
  },
};

export default function PaymentTrendChart({
  data,
  metric,
  timeRange,
  height = 300,
}: PaymentTrendChartProps) {
  const screenWidth = Dimensions.get('window').width;
  const chartWidth = Math.min(screenWidth - 48, 600); // Max width with padding

  const currentMetric = chartMetrics[metric];
  const chartData = data[currentMetric.key];

  // Transform data for Victory charts
  const transformedData = useMemo(() => {
    if (!chartData || chartData.length === 0) return [];

    return chartData.map((point, index) => ({
      x: new Date(point.timestamp),
      y: point.value,
      index,
      timestamp: point.timestamp,
      formattedValue: currentMetric.format(point.value),
    }));
  }, [chartData, currentMetric]);

  // Calculate statistics
  const stats = useMemo(() => {
    if (!transformedData || transformedData.length === 0) {
      return { min: 0, max: 0, average: 0, trend: 0 };
    }

    const values = transformedData.map(d => d.y);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const average = values.reduce((sum, val) => sum + val, 0) / values.length;

    // Calculate trend (simple linear regression slope)
    const n = values.length;
    const sumX = values.reduce((sum, _, i) => sum + i, 0);
    const sumY = values.reduce((sum, val) => sum + val, 0);
    const sumXY = values.reduce((sum, val, i) => sum + i * val, 0);
    const sumXX = values.reduce((sum, _, i) => sum + i * i, 0);

    const trend = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);

    return { min, max, average, trend };
  }, [transformedData]);

  // Format tick values based on metric type
  const formatTick = (value: any, isAxis: 'x' | 'y') => {
    if (isAxis === 'x') {
      const date = new Date(value);
      if (timeRange === 'last_24h') {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      } else {
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
      }
    } else {
      return currentMetric.format(value);
    }
  };

  // Custom tooltip component
  const CustomTooltip = ({ datum }: any) => {
    if (!datum) return null;

    return (
      <VStack
        space="xs"
        className="bg-background-0 p-3 rounded-lg border border-border-200 shadow-lg"
      >
        <Text size="xs" className="text-typography-500">
          {new Date(datum.timestamp).toLocaleString()}
        </Text>
        <Text size="sm" className="font-medium text-typography-900">
          {datum.formattedValue}
        </Text>
      </VStack>
    );
  };

  if (!chartData || chartData.length === 0) {
    return (
      <Card className="p-6">
        <VStack space="md" className="items-center justify-center" style={{ height }}>
          <Icon as={currentMetric.icon} size="lg" className="text-typography-400" />
          <Text className="text-typography-500 text-center">
            No trend data available for {currentMetric.label.toLowerCase()}
          </Text>
        </VStack>
      </Card>
    );
  }

  const IconComponent = currentMetric.icon;

  return (
    <Card className="p-6">
      <VStack space="lg">
        {/* Header */}
        <HStack className="justify-between items-start">
          <VStack space="xs">
            <HStack space="sm" className="items-center">
              <Icon as={IconComponent} size="sm" style={{ color: currentMetric.color }} />
              <Text size="lg" className="font-semibold text-typography-900">
                {currentMetric.label}
              </Text>
            </HStack>
            <Text size="sm" className="text-typography-500">
              Trend over {timeRange.replace('_', ' ')}
            </Text>
          </VStack>

          {/* Quick Stats */}
          <VStack space="xs" className="items-end">
            <HStack space="lg">
              <VStack space="xs" className="items-center">
                <Text size="xs" className="text-typography-500">
                  Average
                </Text>
                <Text size="sm" className="font-medium text-typography-700">
                  {currentMetric.format(stats.average)}
                </Text>
              </VStack>
              <VStack space="xs" className="items-center">
                <Text size="xs" className="text-typography-500">
                  Trend
                </Text>
                <HStack space="xs" className="items-center">
                  <Icon
                    as={TrendingUp}
                    size="xs"
                    className={stats.trend >= 0 ? 'text-success-600' : 'text-error-600'}
                    style={{
                      transform: [{ rotate: stats.trend >= 0 ? '0deg' : '180deg' }],
                    }}
                  />
                  <Text
                    size="sm"
                    className={`font-medium ${
                      stats.trend >= 0 ? 'text-success-600' : 'text-error-600'
                    }`}
                  >
                    {stats.trend >= 0 ? '+' : ''}
                    {stats.trend.toFixed(2)}
                  </Text>
                </HStack>
              </VStack>
            </HStack>
          </VStack>
        </HStack>

        {/* Chart Container - Placeholder */}
        <Box className="items-center justify-center bg-gray-100 rounded-lg" style={{ height }}>
          <VStack space="md" className="items-center">
            <Icon as={currentMetric.icon} size="xl" className="text-gray-400" />
            <Text className="text-gray-600 font-medium">Chart Placeholder</Text>
            <Text className="text-gray-500 text-sm text-center">
              Victory Native charts will be rendered here
            </Text>
            <VStack space="xs" className="mt-4">
              <Text className="text-xs text-gray-600">Current Data:</Text>
              <Text className="text-sm font-medium">{transformedData.length} data points</Text>
              <Text className="text-sm">
                Latest: {transformedData[transformedData.length - 1]?.formattedValue || 'N/A'}
              </Text>
            </VStack>
          </VStack>
        </Box>

        {/* Footer with additional info */}
        <HStack className="justify-between items-center pt-4 border-t border-border-100">
          <Text size="xs" className="text-typography-500">
            {transformedData.length} data points
          </Text>
          <HStack space="md">
            <HStack space="xs" className="items-center">
              <Text size="xs" className="text-typography-500">
                Min:
              </Text>
              <Text size="xs" className="font-medium text-typography-700">
                {currentMetric.format(stats.min)}
              </Text>
            </HStack>
            <HStack space="xs" className="items-center">
              <Text size="xs" className="text-typography-500">
                Max:
              </Text>
              <Text size="xs" className="font-medium text-typography-700">
                {currentMetric.format(stats.max)}
              </Text>
            </HStack>
          </HStack>
        </HStack>
      </VStack>
    </Card>
  );
}
