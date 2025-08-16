/**
 * Usage Analytics Section Component
 *
 * Displays comprehensive usage analytics including statistics,
 * trends, and visualizations for student learning patterns.
 */

import {
  TrendingUp,
  Clock,
  BookOpen,
  Target,
  Calendar,
  BarChart3,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react-native';
import React, { useState } from 'react';

import { LearningInsightsCard } from './LearningInsightsCard';
import { UsagePatternChart } from './UsagePatternChart';

import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useAnalytics } from '@/hooks/useAnalytics';

interface UsageAnalyticsSectionProps {
  email?: string;
}

/**
 * Statistics card component
 */
function StatCard({
  icon: IconComponent,
  title,
  value,
  subtitle,
  trend,
  trendColor = 'text-typography-600',
  bgColor = 'bg-background-50',
}: {
  icon: any;
  title: string;
  value: string | number;
  subtitle: string;
  trend?: string;
  trendColor?: string;
  bgColor?: string;
}) {
  return (
    <Card className={`p-4 ${bgColor}`}>
      <VStack space="sm">
        <HStack className="items-center justify-between">
          <Icon as={IconComponent} size="sm" className="text-primary-600" />
          {trend && <Text className={`text-xs ${trendColor}`}>{trend}</Text>}
        </HStack>

        <VStack space="xs">
          <Text className="text-2xl font-bold text-typography-900">{value}</Text>
          <Text className="text-sm font-medium text-typography-700">{title}</Text>
          <Text className="text-xs text-typography-600">{subtitle}</Text>
        </VStack>
      </VStack>
    </Card>
  );
}

/**
 * Time range selector component
 */
function TimeRangeSelector({
  selectedRange,
  onRangeChange,
}: {
  selectedRange: string;
  onRangeChange: (range: string) => void;
}) {
  const ranges = [
    { id: 'week', label: 'This Week' },
    { id: 'month', label: 'This Month' },
    { id: 'quarter', label: 'Last 3 Months' },
    { id: 'year', label: 'This Year' },
  ];

  return (
    <HStack space="xs" className="flex-wrap">
      {ranges.map(range => (
        <Button
          key={range.id}
          action={selectedRange === range.id ? 'primary' : 'secondary'}
          variant={selectedRange === range.id ? 'solid' : 'outline'}
          size="sm"
          onPress={() => onRangeChange(range.id)}
        >
          <ButtonText>{range.label}</ButtonText>
        </Button>
      ))}
    </HStack>
  );
}

/**
 * Usage Analytics Section Component
 */
export function UsageAnalyticsSection({ email }: UsageAnalyticsSectionProps) {
  const {
    usageStats,
    usageStatsLoading,
    usageStatsError,
    insights,
    patterns,
    refreshUsageStats,
    refreshInsights,
    refreshPatterns,
    refreshAll,
  } = useAnalytics(email);

  const [selectedTimeRange, setSelectedTimeRange] = useState('month');

  const handleTimeRangeChange = async (range: string) => {
    setSelectedTimeRange(range);

    // Calculate date range based on selection
    const now = new Date();
    let startDate: Date;

    switch (range) {
      case 'week':
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case 'quarter':
        startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
        break;
      case 'year':
        startDate = new Date(now.getFullYear(), 0, 1);
        break;
      case 'month':
      default:
        startDate = new Date(now.getFullYear(), now.getMonth(), 1);
        break;
    }

    const timeRange = {
      start_date: startDate.toISOString().split('T')[0],
      end_date: now.toISOString().split('T')[0],
    };

    // Refresh data with graceful degradation
    const results = await Promise.allSettled([
      refreshUsageStats(timeRange),
      refreshPatterns(timeRange),
    ]);

    // Log any failures for monitoring
    results.forEach((result, index) => {
      if (result.status === 'rejected') {
        const operation = index === 0 ? 'usage statistics' : 'usage patterns';
        console.error(`Failed to refresh ${operation} for time range ${range}:`, result.reason);
      }
    });
  };

  if (usageStatsLoading && !usageStats) {
    return (
      <Card className="p-6">
        <VStack space="lg">
          <HStack className="items-center">
            <Icon as={BarChart3} size="sm" className="text-typography-600 mr-2" />
            <Heading size="md" className="text-typography-900">
              Usage Analytics
            </Heading>
          </HStack>

          <VStack space="md" className="items-center py-8">
            <Spinner size="large" />
            <Text className="text-typography-600">Loading analytics...</Text>
          </VStack>
        </VStack>
      </Card>
    );
  }

  if (usageStatsError && !usageStats) {
    return (
      <Card className="p-6">
        <VStack space="lg">
          <HStack className="items-center">
            <Icon as={BarChart3} size="sm" className="text-typography-600 mr-2" />
            <Heading size="md" className="text-typography-900">
              Usage Analytics
            </Heading>
          </HStack>

          <VStack space="md" className="items-center py-8">
            <Icon as={AlertTriangle} size="xl" className="text-error-500" />
            <VStack space="sm" className="items-center">
              <Heading size="sm" className="text-error-900">
                Unable to Load Analytics
              </Heading>
              <Text className="text-error-700 text-sm text-center">{usageStatsError}</Text>
            </VStack>
            <Button action="secondary" variant="outline" size="sm" onPress={refreshAll}>
              <ButtonIcon as={RefreshCw} />
              <ButtonText>Try Again</ButtonText>
            </Button>
          </VStack>
        </VStack>
      </Card>
    );
  }

  if (!usageStats) {
    return (
      <Card className="p-6">
        <VStack space="lg">
          <HStack className="items-center">
            <Icon as={BarChart3} size="sm" className="text-typography-600 mr-2" />
            <Heading size="md" className="text-typography-900">
              Usage Analytics
            </Heading>
          </HStack>

          <VStack space="md" className="items-center py-8">
            <Icon as={BarChart3} size="xl" className="text-typography-300" />
            <VStack space="xs" className="items-center">
              <Text className="font-medium text-typography-600">No Analytics Data</Text>
              <Text className="text-sm text-typography-500 text-center">
                Start attending tutoring sessions to see your learning analytics here
              </Text>
            </VStack>
          </VStack>
        </VStack>
      </Card>
    );
  }

  return (
    <VStack space="lg">
      {/* Header with time range selector */}
      <Card className="p-6">
        <VStack space="lg">
          <HStack className="items-center justify-between">
            <VStack space="xs">
              <HStack className="items-center">
                <Icon as={BarChart3} size="sm" className="text-typography-600 mr-2" />
                <Heading size="md" className="text-typography-900">
                  Usage Analytics
                </Heading>
              </HStack>
              <Text className="text-sm text-typography-600">
                Track your learning progress and session patterns
              </Text>
            </VStack>

            <Button
              action="secondary"
              variant="outline"
              size="sm"
              onPress={refreshAll}
              disabled={usageStatsLoading}
            >
              {usageStatsLoading ? (
                <>
                  <Spinner size="sm" />
                  <ButtonText className="ml-2">Refreshing...</ButtonText>
                </>
              ) : (
                <>
                  <ButtonIcon as={RefreshCw} />
                  <ButtonText>Refresh</ButtonText>
                </>
              )}
            </Button>
          </HStack>

          {/* Time Range Selector */}
          <VStack space="sm">
            <Text className="text-sm font-medium text-typography-800">Time Period</Text>
            <TimeRangeSelector
              selectedRange={selectedTimeRange}
              onRangeChange={handleTimeRangeChange}
            />
          </VStack>
        </VStack>
      </Card>

      {/* Statistics Overview */}
      <VStack space="md">
        <Heading size="sm" className="text-typography-900 px-1">
          Overview Statistics
        </Heading>

        <VStack space="md" className="w-full">
          <HStack space="md" className="flex-wrap">
            <StatCard
              icon={BookOpen}
              title="Total Sessions"
              value={usageStats.total_sessions}
              subtitle="Sessions completed"
              trend={
                selectedTimeRange === 'month'
                  ? `${usageStats.sessions_this_month} this month`
                  : undefined
              }
              trendColor="text-primary-600"
            />

            <StatCard
              icon={Clock}
              title="Hours Consumed"
              value={`${usageStats.total_hours_consumed.toFixed(1)}h`}
              subtitle="Total learning time"
              trend={
                selectedTimeRange === 'month'
                  ? `${usageStats.hours_this_month.toFixed(1)}h this month`
                  : undefined
              }
              trendColor="text-success-600"
            />
          </HStack>

          <HStack space="md" className="flex-wrap">
            <StatCard
              icon={TrendingUp}
              title="Average Session"
              value={`${usageStats.average_session_duration.toFixed(1)}h`}
              subtitle="Session duration"
              bgColor="bg-primary-50"
            />

            <StatCard
              icon={Target}
              title="Learning Streak"
              value={`${usageStats.streak_days} days`}
              subtitle="Current streak"
              trend={
                usageStats.streak_days > 7
                  ? 'Great momentum!'
                  : usageStats.streak_days > 0
                    ? 'Keep it up!'
                    : 'Start a streak'
              }
              trendColor={
                usageStats.streak_days > 7
                  ? 'text-success-600'
                  : usageStats.streak_days > 0
                    ? 'text-warning-600'
                    : 'text-typography-600'
              }
              bgColor={
                usageStats.streak_days > 7
                  ? 'bg-success-50'
                  : usageStats.streak_days > 0
                    ? 'bg-warning-50'
                    : 'bg-background-50'
              }
            />
          </HStack>
        </VStack>
      </VStack>

      {/* Learning Preferences */}
      {(usageStats.most_active_subject || usageStats.preferred_time_slot) && (
        <Card className="p-6">
          <VStack space="md">
            <Heading size="sm" className="text-typography-900">
              Learning Preferences
            </Heading>

            <HStack space="lg" className="flex-wrap">
              {usageStats.most_active_subject && (
                <HStack space="xs" className="items-center">
                  <Text className="text-sm text-typography-600">Most Active Subject:</Text>
                  <Badge variant="solid" action="primary" size="sm">
                    <Text className="text-xs">{usageStats.most_active_subject}</Text>
                  </Badge>
                </HStack>
              )}

              {usageStats.preferred_time_slot && (
                <HStack space="xs" className="items-center">
                  <Text className="text-sm text-typography-600">Preferred Time:</Text>
                  <Badge variant="solid" action="secondary" size="sm">
                    <Icon as={Calendar} size="xs" />
                    <Text className="text-xs ml-1">{usageStats.preferred_time_slot}</Text>
                  </Badge>
                </HStack>
              )}
            </HStack>
          </VStack>
        </Card>
      )}

      {/* Usage Pattern Chart */}
      <UsagePatternChart
        patterns={patterns}
        loading={usageStatsLoading}
        timeRange={selectedTimeRange}
      />

      {/* Learning Insights */}
      <LearningInsightsCard insights={insights} onRefresh={refreshInsights} />
    </VStack>
  );
}
