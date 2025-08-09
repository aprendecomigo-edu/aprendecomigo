/**
 * Usage Pattern Chart - Web Implementation
 *
 * Web-specific implementation using SVG charts for better data visualization.
 * Provides interactive charts for usage patterns including peak hours,
 * days of week activity, and subject distribution.
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
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

/**
 * SVG bar chart component for web
 */
function SVGBarChart({
  data,
  title,
  xAxisLabel,
  yAxisLabel,
}: {
  data: { label: string; value: number; color?: string }[];
  title: string;
  xAxisLabel: string;
  yAxisLabel: string;
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

  // Web-based SVG chart
  const chartWidth = 300;
  const chartHeight = 200;
  const margin = { top: 20, right: 20, bottom: 40, left: 40 };
  const innerWidth = chartWidth - margin.left - margin.right;
  const innerHeight = chartHeight - margin.top - margin.bottom;

  const barWidth = (innerWidth / data.length) * 0.8;
  const barSpacing = (innerWidth / data.length) * 0.2;

  return (
    <VStack space="sm">
      <Text className="text-sm font-medium text-typography-800">{title}</Text>
      <svg width={chartWidth} height={chartHeight} className="border border-outline-200 rounded-lg">
        {/* Chart background */}
        <rect
          x={margin.left}
          y={margin.top}
          width={innerWidth}
          height={innerHeight}
          fill="transparent"
          stroke="#e5e7eb"
        />

        {/* Bars */}
        {data.map((item, index) => {
          const barHeight = (item.value / maxValue) * innerHeight;
          const x = margin.left + index * (barWidth + barSpacing) + barSpacing / 2;
          const y = margin.top + innerHeight - barHeight;

          return (
            <g key={index}>
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={barHeight}
                fill={item.color || '#6366f1'}
                rx={2}
              />
              <text
                x={x + barWidth / 2}
                y={margin.top + innerHeight + 15}
                textAnchor="middle"
                fontSize="10"
                fill="#6b7280"
              >
                {item.label}
              </text>
              <text
                x={x + barWidth / 2}
                y={y - 5}
                textAnchor="middle"
                fontSize="10"
                fill="#374151"
                fontWeight="bold"
              >
                {item.value}
              </text>
            </g>
          );
        })}

        {/* Y-axis labels */}
        {[0, Math.floor(maxValue / 2), maxValue].map((value, index) => {
          const y = margin.top + innerHeight - (value / maxValue) * innerHeight;
          return (
            <g key={index}>
              <line x1={margin.left - 5} y1={y} x2={margin.left} y2={y} stroke="#9ca3af" />
              <text x={margin.left - 10} y={y + 3} textAnchor="end" fontSize="10" fill="#6b7280">
                {value}
              </text>
            </g>
          );
        })}
      </svg>
    </VStack>
  );
}

/**
 * Usage Pattern Chart Component - Web Implementation
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

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Hourly Activity Chart */}
          {chartData.hourly.length > 0 && (
            <Card className="p-4">
              <SVGBarChart
                data={chartData.hourly}
                title="Activity by Hour"
                xAxisLabel="Hour of Day"
                yAxisLabel="Sessions"
              />
            </Card>
          )}

          {/* Weekly Activity Chart */}
          <Card className="p-4">
            <SVGBarChart
              data={chartData.weekly}
              title="Activity by Day"
              xAxisLabel="Day of Week"
              yAxisLabel="Sessions"
            />
          </Card>

          {/* Subject Distribution */}
          {chartData.subjects.length > 0 && (
            <Card className="p-4 lg:col-span-2">
              <SVGBarChart
                data={chartData.subjects}
                title="Most Active Subjects"
                xAxisLabel="Subject"
                yAxisLabel="Sessions"
              />
            </Card>
          )}
        </div>

        {/* Pattern Insights */}
        {insights && <PatternInsightsCard insights={insights} chartData={chartData} />}
      </VStack>
    </Card>
  );
}
