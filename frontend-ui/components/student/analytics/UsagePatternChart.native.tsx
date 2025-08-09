/**
 * Usage Pattern Chart - Native Implementation
 *
 * Native-specific implementation using simple visual bars for usage pattern display.
 * Optimized for mobile devices with text-based representations and horizontal bars.
 */

import React from 'react';

import {
  UsagePatternChartProps,
  ChartData,
  useProcessedChartData,
  usePatternInsights,
  LoadingState,
  EmptyState,
  ChartHeader,
  InsightsSummary,
  PatternInsightsCard,
} from './usage-pattern-common';

import { Card } from '@/components/ui/card';
import { HStack } from '@/components/ui/hstack';
import { Text } from '@/components/ui/text';
import { View } from '@/components/ui/view';
import { VStack } from '@/components/ui/vstack';

/**
 * Simple horizontal bar chart component for native
 */
function SimpleBarChart({
  data,
  title,
}: {
  data: { label: string; value: number; color?: string }[];
  title: string;
}) {
  const maxValue = Math.max(...data.map(d => d.value));

  if (data.length === 0) {
    return (
      <VStack space="sm">
        <Text className="text-sm font-medium text-typography-800">{title}</Text>
        <Text className="text-sm text-typography-500">No data available</Text>
      </VStack>
    );
  }

  return (
    <VStack space="sm">
      <Text className="text-sm font-medium text-typography-800">{title}</Text>
      <VStack space="xs">
        {data.slice(0, 5).map((item, index) => (
          <HStack key={index} className="items-center justify-between">
            <Text className="text-sm text-typography-700 flex-shrink-0 min-w-16">{item.label}</Text>
            <HStack space="xs" className="items-center flex-1">
              <View
                className={`h-3 rounded-full min-w-1`}
                style={{
                  width: `${Math.max((item.value / maxValue) * 100, 8)}%`,
                  backgroundColor: item.color || '#6366f1',
                }}
              />
              <Text className="text-sm font-medium text-typography-900 min-w-8 flex-shrink-0">
                {item.value}
              </Text>
            </HStack>
          </HStack>
        ))}
      </VStack>
    </VStack>
  );
}

/**
 * Usage Pattern Chart Component - Native Implementation
 */
export function UsagePatternChart({ patterns, loading, timeRange }: UsagePatternChartProps) {
  const chartData = useProcessedChartData(patterns);
  const insights = usePatternInsights(patterns);

  if (loading) {
    return <LoadingState />;
  }

  if (!chartData || patterns.length === 0) {
    return <EmptyState />;
  }

  return (
    <Card className="p-6">
      <VStack space="lg">
        {/* Header */}
        <ChartHeader />

        {/* Insights Summary */}
        {insights && <InsightsSummary insights={insights} />}

        {/* Charts - Stacked vertically on mobile */}
        <VStack space="md">
          {/* Hourly Activity Chart */}
          {chartData.hourly.length > 0 && (
            <Card className="p-4">
              <SimpleBarChart data={chartData.hourly} title="Activity by Hour" />
            </Card>
          )}

          {/* Weekly Activity Chart */}
          <Card className="p-4">
            <SimpleBarChart data={chartData.weekly} title="Activity by Day" />
          </Card>

          {/* Subject Distribution */}
          {chartData.subjects.length > 0 && (
            <Card className="p-4">
              <SimpleBarChart data={chartData.subjects} title="Most Active Subjects" />
            </Card>
          )}
        </VStack>

        {/* Pattern Insights */}
        {insights && <PatternInsightsCard insights={insights} chartData={chartData} />}
      </VStack>
    </Card>
  );
}
