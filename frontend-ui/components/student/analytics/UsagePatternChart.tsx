/**
 * Usage Pattern Chart Component
 * 
 * Visualizes student usage patterns including peak hours,
 * days of week activity, and subject distribution using charts.
 */

import React, { useMemo } from 'react';
import { Platform } from 'react-native';
import { BarChart3, Clock, Calendar, AlertTriangle } from 'lucide-react-native';

import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { Badge } from '@/components/ui/badge';
import type { UsagePattern } from '@/api/analyticsApi';

interface UsagePatternChartProps {
  patterns: UsagePattern[];
  loading: boolean;
  timeRange: string;
}

/**
 * Simple bar chart component for web
 */
function SimpleBarChart({ 
  data, 
  title, 
  xAxisLabel, 
  yAxisLabel 
}: {
  data: { label: string; value: number; color?: string }[];
  title: string;
  xAxisLabel: string;
  yAxisLabel: string;
}) {
  const maxValue = Math.max(...data.map(d => d.value));
  
  if (Platform.OS !== 'web') {
    // Simple text representation for mobile
    return (
      <VStack space="sm">
        <Text className="text-sm font-medium text-typography-800">
          {title}
        </Text>
        <VStack space="xs">
          {data.slice(0, 5).map((item, index) => (
            <HStack key={index} className="items-center justify-between">
              <Text className="text-sm text-typography-700">
                {item.label}
              </Text>
              <HStack space="xs" className="items-center">
                <div 
                  className={`h-2 rounded-full ${item.color || 'bg-primary-500'}`}
                  style={{ width: `${(item.value / maxValue) * 60}px` }}
                />
                <Text className="text-sm font-medium text-typography-900 min-w-8">
                  {item.value}
                </Text>
              </HStack>
            </HStack>
          ))}
        </VStack>
      </VStack>
    );
  }

  // Web-based SVG chart
  const chartWidth = 300;
  const chartHeight = 200;
  const margin = { top: 20, right: 20, bottom: 40, left: 40 };
  const innerWidth = chartWidth - margin.left - margin.right;
  const innerHeight = chartHeight - margin.top - margin.bottom;
  
  const barWidth = innerWidth / data.length * 0.8;
  const barSpacing = innerWidth / data.length * 0.2;

  return (
    <VStack space="sm">
      <Text className="text-sm font-medium text-typography-800">
        {title}
      </Text>
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
              <line
                x1={margin.left - 5}
                y1={y}
                x2={margin.left}
                y2={y}
                stroke="#9ca3af"
              />
              <text
                x={margin.left - 10}
                y={y + 3}
                textAnchor="end"
                fontSize="10"
                fill="#6b7280"
              >
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
 * Usage Pattern Chart Component
 */
export function UsagePatternChart({ 
  patterns, 
  loading, 
  timeRange 
}: UsagePatternChartProps) {
  // Process patterns data for visualization
  const chartData = useMemo(() => {
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

  // Calculate peak usage insights
  const insights = useMemo(() => {
    if (!patterns || patterns.length === 0) return null;

    const totalSessions = patterns.reduce((sum, p) => sum + p.session_count, 0);
    const avgDuration = patterns.reduce((sum, p) => sum + p.average_duration, 0) / patterns.length;
    
    // Find peak hour
    const hourCounts = new Map<number, number>();
    patterns.forEach(p => {
      const current = hourCounts.get(p.hour) || 0;
      hourCounts.set(p.hour, current + p.session_count);
    });
    
    const peakHour = Array.from(hourCounts.entries())
      .sort((a, b) => b[1] - a[1])[0]?.[0];

    // Find peak day
    const dayCounts = new Map<number, number>();
    patterns.forEach(p => {
      const current = dayCounts.get(p.day_of_week) || 0;
      dayCounts.set(p.day_of_week, current + p.session_count);
    });
    
    const dayLabels = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const peakDay = Array.from(dayCounts.entries())
      .sort((a, b) => b[1] - a[1])[0]?.[0];

    return {
      totalSessions,
      avgDuration: avgDuration.toFixed(1),
      peakHour: peakHour !== undefined ? `${peakHour}:00` : null,
      peakDay: peakDay !== undefined ? dayLabels[peakDay] : null,
    };
  }, [patterns]);

  if (loading) {
    return (
      <Card className="p-6">
        <VStack space="md" className="items-center py-8">
          <Spinner size="large" />
          <Text className="text-typography-600">Loading usage patterns...</Text>
        </VStack>
      </Card>
    );
  }

  if (!chartData || patterns.length === 0) {
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
              <Text className="font-medium text-typography-600">
                No Pattern Data
              </Text>
              <Text className="text-sm text-typography-500 text-center">
                Complete more sessions to see your learning patterns and peak usage times
              </Text>
            </VStack>
          </VStack>
        </VStack>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <VStack space="lg">
        {/* Header */}
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

        {/* Insights Summary */}
        {insights && (
          <HStack space="md" className="flex-wrap">
            <HStack space="xs" className="items-center">
              <Icon as={Clock} size="sm" className="text-primary-600" />
              <VStack space="0">
                <Text className="text-sm font-medium text-typography-900">
                  Peak Time: {insights.peakHour || 'N/A'}
                </Text>
                <Text className="text-xs text-typography-600">
                  Most active hour
                </Text>
              </VStack>
            </HStack>

            <HStack space="xs" className="items-center">
              <Icon as={Calendar} size="sm" className="text-success-600" />
              <VStack space="0">
                <Text className="text-sm font-medium text-typography-900">
                  Peak Day: {insights.peakDay || 'N/A'}
                </Text>
                <Text className="text-xs text-typography-600">
                  Most active day
                </Text>
              </VStack>
            </HStack>

            <Badge variant="solid" action="secondary" size="sm">
              <Text className="text-xs">
                {insights.totalSessions} sessions • {insights.avgDuration}h avg
              </Text>
            </Badge>
          </HStack>
        )}

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Hourly Activity Chart */}
          {chartData.hourly.length > 0 && (
            <Card className="p-4">
              <SimpleBarChart
                data={chartData.hourly}
                title="Activity by Hour"
                xAxisLabel="Hour of Day"
                yAxisLabel="Sessions"
              />
            </Card>
          )}

          {/* Weekly Activity Chart */}
          <Card className="p-4">
            <SimpleBarChart
              data={chartData.weekly}
              title="Activity by Day"
              xAxisLabel="Day of Week"
              yAxisLabel="Sessions"
            />
          </Card>

          {/* Subject Distribution */}
          {chartData.subjects.length > 0 && (
            <Card className="p-4 lg:col-span-2">
              <SimpleBarChart
                data={chartData.subjects}
                title="Most Active Subjects"
                xAxisLabel="Subject"
                yAxisLabel="Sessions"
              />
            </Card>
          )}
        </div>

        {/* Pattern Insights */}
        <Card className="p-4 bg-primary-50 border-primary-200">
          <VStack space="sm">
            <Text className="text-sm font-medium text-primary-900">
              Pattern Insights
            </Text>
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
                  • Your top subject is {chartData.subjects[0].label} with {chartData.subjects[0].value} sessions
                </Text>
              )}
            </VStack>
          </VStack>
        </Card>
      </VStack>
    </Card>
  );
}