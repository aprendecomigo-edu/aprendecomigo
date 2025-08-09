/**
 * Usage Pattern Chart - Common Logic and Types
 *
 * Shared business logic, types, and utilities for usage pattern visualization
 * across web and native platforms.
 */

import { BarChart3, Clock, Calendar, AlertTriangle } from 'lucide-react-native';
import React, { useMemo } from 'react';

import type { UsagePattern } from '@/api/analyticsApi';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Shared types and interfaces
export interface UsagePatternChartProps {
  patterns: UsagePattern[];
  loading: boolean;
  timeRange: string;
}

export interface ChartData {
  hourly: { label: string; value: number; color?: string }[];
  weekly: { label: string; value: number; color?: string }[];
  subjects: { label: string; value: number; color?: string }[];
}

export interface PatternInsights {
  totalSessions: number;
  avgDuration: string;
  peakHour: string | null;
  peakDay: string | null;
}

// Shared data processing logic
export const useProcessedChartData = (patterns: UsagePattern[]): ChartData | null => {
  return useMemo(() => {
    if (!patterns || patterns.length === 0) return null;

    // Aggregate by hour of day
    const hourlyData = Array.from({ length: 24 }, (_, hour) => {
      const hourPatterns = patterns.filter(p => p.hour === hour);
      const totalSessions = hourPatterns.reduce((sum, p) => sum + p.session_count, 0);
      return {
        label: `${hour}:00`,
        value: totalSessions,
        color: totalSessions > 0 ? '#6366f1' : '#e5e7eb',
      };
    }).filter(d => d.value > 0); // Only show hours with activity

    // Aggregate by day of week
    const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const weeklyData = Array.from({ length: 7 }, (_, day) => {
      const dayPatterns = patterns.filter(p => p.day_of_week === day);
      const totalSessions = dayPatterns.reduce((sum, p) => sum + p.session_count, 0);
      return {
        label: dayLabels[day],
        value: totalSessions,
        color: totalSessions > 0 ? '#10b981' : '#e5e7eb',
      };
    });

    // Get top subjects
    const subjectMap = new Map<string, number>();
    patterns.forEach(pattern => {
      Object.entries(pattern.subjects).forEach(([subject, data]) => {
        const current = subjectMap.get(subject) || 0;
        subjectMap.set(subject, current + data.session_count);
      });
    });

    const subjectData = Array.from(subjectMap.entries())
      .map(([subject, count]) => ({
        label: subject,
        value: count,
        color: '#f59e0b',
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 5);

    return {
      hourly: hourlyData.slice(0, 12), // Show top 12 active hours
      weekly: weeklyData,
      subjects: subjectData,
    };
  }, [patterns]);
};

// Shared insights calculation logic
export const usePatternInsights = (patterns: UsagePattern[]): PatternInsights | null => {
  return useMemo(() => {
    if (!patterns || patterns.length === 0) return null;

    const totalSessions = patterns.reduce((sum, p) => sum + p.session_count, 0);
    const avgDuration = patterns.reduce((sum, p) => sum + p.average_duration, 0) / patterns.length;

    // Find peak hour
    const hourCounts = new Map<number, number>();
    patterns.forEach(p => {
      const current = hourCounts.get(p.hour) || 0;
      hourCounts.set(p.hour, current + p.session_count);
    });

    const peakHour = Array.from(hourCounts.entries()).sort((a, b) => b[1] - a[1])[0]?.[0];

    // Find peak day
    const dayCounts = new Map<number, number>();
    patterns.forEach(p => {
      const current = dayCounts.get(p.day_of_week) || 0;
      dayCounts.set(p.day_of_week, current + p.session_count);
    });

    const dayLabels = [
      'Sunday',
      'Monday',
      'Tuesday',
      'Wednesday',
      'Thursday',
      'Friday',
      'Saturday',
    ];
    const peakDay = Array.from(dayCounts.entries()).sort((a, b) => b[1] - a[1])[0]?.[0];

    return {
      totalSessions,
      avgDuration: avgDuration.toFixed(1),
      peakHour: peakHour !== undefined ? `${peakHour}:00` : null,
      peakDay: peakDay !== undefined ? dayLabels[peakDay] : null,
    };
  }, [patterns]);
};

// Shared loading state component
export function LoadingState() {
  return (
    <Card className="p-6">
      <VStack space="md" className="items-center py-8">
        <Spinner size="large" />
        <Text className="text-typography-600">Loading usage patterns...</Text>
      </VStack>
    </Card>
  );
}

// Shared empty state component
export function EmptyState() {
  return (
    <Card className="p-6">
      <VStack space="md">
        <HStack className="items-center">
          <Icon as={BarChart3} size="sm" className="text-typography-600 mr-2" />
          <Heading size="md" className="text-typography-900">
            Usage Patterns
          </Heading>
        </HStack>

        <VStack space="md" className="items-center py-8">
          <Icon as={AlertTriangle} size="xl" className="text-typography-300" />
          <VStack space="xs" className="items-center">
            <Text className="font-medium text-typography-600">No Pattern Data</Text>
            <Text className="text-sm text-typography-500 text-center">
              Complete more sessions to see your learning patterns and peak usage times
            </Text>
          </VStack>
        </VStack>
      </VStack>
    </Card>
  );
}

// Shared chart header component
export function ChartHeader() {
  return (
    <VStack space="xs">
      <HStack className="items-center">
        <Icon as={BarChart3} size="sm" className="text-typography-600 mr-2" />
        <Heading size="md" className="text-typography-900">
          Usage Patterns
        </Heading>
      </HStack>
      <Text className="text-sm text-typography-600">
        Your learning activity patterns for the selected time period
      </Text>
    </VStack>
  );
}

// Shared insights summary component
export function InsightsSummary({ insights }: { insights: PatternInsights }) {
  return (
    <HStack space="md" className="flex-wrap">
      <HStack space="xs" className="items-center">
        <Icon as={Clock} size="sm" className="text-primary-600" />
        <VStack space="0">
          <Text className="text-sm font-medium text-typography-900">
            Peak Time: {insights.peakHour || 'N/A'}
          </Text>
          <Text className="text-xs text-typography-600">Most active hour</Text>
        </VStack>
      </HStack>

      <HStack space="xs" className="items-center">
        <Icon as={Calendar} size="sm" className="text-success-600" />
        <VStack space="0">
          <Text className="text-sm font-medium text-typography-900">
            Peak Day: {insights.peakDay || 'N/A'}
          </Text>
          <Text className="text-xs text-typography-600">Most active day</Text>
        </VStack>
      </HStack>

      <Badge variant="solid" action="secondary" size="sm">
        <Text className="text-xs">
          {insights.totalSessions} sessions • {insights.avgDuration}h avg
        </Text>
      </Badge>
    </HStack>
  );
}

// Shared pattern insights component
export function PatternInsightsCard({
  insights,
  chartData,
}: {
  insights: PatternInsights;
  chartData: ChartData;
}) {
  return (
    <Card className="p-4 bg-primary-50 border-primary-200">
      <VStack space="sm">
        <Text className="text-sm font-medium text-primary-900">Pattern Insights</Text>
        <VStack space="xs">
          {insights?.peakHour && (
            <Text className="text-sm text-primary-800">
              • You're most active around {insights.peakHour}
            </Text>
          )}
          {insights?.peakDay && (
            <Text className="text-sm text-primary-800">
              • {insights.peakDay}s are your most productive days
            </Text>
          )}
          {chartData.subjects.length > 0 && (
            <Text className="text-sm text-primary-800">
              • Your top subject is {chartData.subjects[0].label} with {chartData.subjects[0].value}{' '}
              sessions
            </Text>
          )}
        </VStack>
      </VStack>
    </Card>
  );
}
