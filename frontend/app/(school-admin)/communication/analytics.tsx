import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import { router } from 'expo-router';
import {
  BarChart3Icon,
  TrendingUpIcon,
  TrendingDownIcon,
  MailIcon,
  SendIcon,
  EyeIcon,
  MousePointerClickIcon,
  XCircleIcon,
  RefreshCwIcon,
  DownloadIcon,
  FilterIcon,
  CalendarIcon,
} from 'lucide-react-native';
import React, { useState, useCallback, useMemo, useEffect } from 'react';

import { EmailTemplateType, AnalyticsFilters } from '@/api/communicationApi';
import MainLayout from '@/components/layouts/MainLayout';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Select, SelectContent, SelectItem, SelectTrigger } from '@/components/ui/select';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useEmailAnalytics } from '@/hooks/useEmailAnalytics';

const CommunicationAnalyticsPage = () => {
  // Filters state
  const [filters, setFilters] = useState<AnalyticsFilters>({
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 days ago
    end_date: new Date().toISOString().split('T')[0], // Today
  });

  const [showFilters, setShowFilters] = useState(false);

  // Analytics hook
  const { analytics, loading, error, refreshAnalytics } = useEmailAnalytics(filters);

  // Template type options
  const templateTypeOptions = [
    { value: 'all', label: 'All Types' },
    { value: 'invitation', label: 'Invitations' },
    { value: 'reminder', label: 'Reminders' },
    { value: 'welcome', label: 'Welcome' },
    { value: 'profile_reminder', label: 'Profile Reminders' },
    { value: 'completion_celebration', label: 'Completions' },
    { value: 'ongoing_support', label: 'Support' },
  ];

  const statusOptions = [
    { value: 'all', label: 'All Status' },
    { value: 'sent', label: 'Sent' },
    { value: 'delivered', label: 'Delivered' },
    { value: 'opened', label: 'Opened' },
    { value: 'clicked', label: 'Clicked' },
    { value: 'failed', label: 'Failed' },
  ];

  // Update filters
  const updateFilter = useCallback((key: keyof AnalyticsFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value === 'all' ? undefined : value,
    }));
  }, []);

  // Apply filters
  const applyFilters = useCallback(() => {
    refreshAnalytics();
    setShowFilters(false);
  }, [refreshAnalytics]);

  // Clear filters
  const clearFilters = useCallback(() => {
    setFilters({
      start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end_date: new Date().toISOString().split('T')[0],
    });
  }, []);

  // Export data (placeholder)
  const exportData = useCallback(() => {
    if (!analytics) return;

    // In a real implementation, this would generate and download a CSV/Excel file
    const data = {
      summary: {
        total_sent: analytics.total_sent,
        delivered_count: analytics.delivered_count,
        opened_count: analytics.opened_count,
        clicked_count: analytics.clicked_count,
        failed_count: analytics.failed_count,
        delivery_rate: analytics.delivery_rate,
        open_rate: analytics.open_rate,
        click_rate: analytics.click_rate,
        bounce_rate: analytics.bounce_rate,
      },
      template_performance: analytics.template_performance,
      recent_activity: analytics.recent_activity,
    };

    if (__DEV__) {

      if (__DEV__) {
        console.log('Export data:', data);
      }

    }
    // TODO: Implement actual file download
  }, [analytics]);

  // Calculate trend indicators
  const getTrendIcon = useCallback((value: number, threshold: number = 0) => {
    if (value > threshold) return TrendingUpIcon;
    if (value < threshold) return TrendingDownIcon;
    return BarChart3Icon;
  }, []);

  const getTrendColor = useCallback((value: number, threshold: number = 0) => {
    if (value > threshold) return 'text-green-600';
    if (value < threshold) return 'text-red-600';
    return 'text-gray-600';
  }, []);

  // Performance metrics with colors
  const getPerformanceColor = useCallback((rate: number, type: 'delivery' | 'open' | 'click') => {
    switch (type) {
      case 'delivery':
        return rate >= 0.95 ? 'text-green-600' : rate >= 0.85 ? 'text-yellow-600' : 'text-red-600';
      case 'open':
        return rate >= 0.25 ? 'text-green-600' : rate >= 0.15 ? 'text-yellow-600' : 'text-red-600';
      case 'click':
        return rate >= 0.05 ? 'text-green-600' : rate >= 0.02 ? 'text-yellow-600' : 'text-red-600';
      default:
        return 'text-gray-600';
    }
  }, []);

  // Quick preset filters
  const presetFilters = [
    {
      label: 'Last 7 days',
      start_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end_date: new Date().toISOString().split('T')[0],
    },
    {
      label: 'Last 30 days',
      start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end_date: new Date().toISOString().split('T')[0],
    },
    {
      label: 'Last 90 days',
      start_date: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end_date: new Date().toISOString().split('T')[0],
    },
  ];

  const applyPresetFilter = useCallback((preset: (typeof presetFilters)[0]) => {
    setFilters(prev => ({
      ...prev,
      start_date: preset.start_date,
      end_date: preset.end_date,
    }));
  }, []);

  // Loading state
  if (loading && !analytics) {
    return (
      <MainLayout _title="Email Analytics">
        <Center className="flex-1">
          <VStack space="md" className="items-center">
            <Spinner size="large" />
            <Text className="text-gray-600">Loading analytics...</Text>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  return (
    <ScrollView
      showsVerticalScrollIndicator={false}
      contentContainerStyle={{
        paddingBottom: isWeb ? 0 : 100,
        flexGrow: 1,
      }}
      className="flex-1 bg-gray-50"
    >
      <VStack className="p-6" space="lg">
        {/* Header */}
        <HStack className="justify-between items-center">
          <VStack space="xs">
            <Heading size="xl" className="text-gray-900">
              Email Analytics
            </Heading>
            <Text className="text-gray-600">
              Track the performance of your teacher communication emails
            </Text>
          </VStack>

          <HStack space="sm">
            <Button onPress={() => setShowFilters(!showFilters)} variant="outline">
              <HStack space="xs" className="items-center">
                <Icon as={FilterIcon} size="sm" className="text-gray-600" />
                <ButtonText>Filters</ButtonText>
              </HStack>
            </Button>

            <Button onPress={refreshAnalytics} variant="outline" disabled={loading}>
              <HStack space="xs" className="items-center">
                <Icon
                  as={RefreshCwIcon}
                  size="sm"
                  className={`text-gray-600 ${loading ? 'animate-spin' : ''}`}
                />
                <ButtonText>Refresh</ButtonText>
              </HStack>
            </Button>

            <Button onPress={exportData} variant="outline" disabled={!analytics}>
              <HStack space="xs" className="items-center">
                <Icon as={DownloadIcon} size="sm" className="text-gray-600" />
                <ButtonText>Export</ButtonText>
              </HStack>
            </Button>
          </HStack>
        </HStack>

        {/* Error Display */}
        {error && (
          <Card className="p-4 bg-red-50 border-red-200">
            <HStack space="sm" className="items-start">
              <Icon as={XCircleIcon} size="sm" className="text-red-600 mt-0.5" />
              <VStack space="xs" className="flex-1">
                <Text className="font-medium text-red-800">Error Loading Analytics</Text>
                <Text className="text-sm text-red-600">{error}</Text>
                <Button
                  onPress={refreshAnalytics}
                  size="sm"
                  variant="outline"
                  className="border-red-300 self-start"
                >
                  <ButtonText>Try Again</ButtonText>
                </Button>
              </VStack>
            </HStack>
          </Card>
        )}

        {/* Filters Panel */}
        {showFilters && (
          <Card className="p-6">
            <VStack space="lg">
              <HStack className="justify-between items-center">
                <Heading size="md" className="text-gray-900">
                  Filters
                </Heading>
                <Button onPress={() => setShowFilters(false)} size="sm" variant="outline">
                  <ButtonText>Close</ButtonText>
                </Button>
              </HStack>

              {/* Quick Presets */}
              <VStack space="sm">
                <Text className="font-medium text-gray-900">Quick Filters</Text>
                <HStack space="sm" className="flex-wrap">
                  {presetFilters.map(preset => (
                    <Button
                      key={preset.label}
                      onPress={() => applyPresetFilter(preset)}
                      size="sm"
                      variant="outline"
                    >
                      <ButtonText>{preset.label}</ButtonText>
                    </Button>
                  ))}
                </HStack>
              </VStack>

              {/* Date Range */}
              <VStack space="md">
                <Text className="font-medium text-gray-900">Date Range</Text>
                <HStack space="md" className="items-center">
                  <VStack space="xs" className="flex-1">
                    <Text className="text-sm text-gray-600">Start Date</Text>
                    <Input>
                      <InputField
                        type="date"
                        value={filters.start_date || ''}
                        onChangeText={value => updateFilter('start_date', value)}
                      />
                    </Input>
                  </VStack>
                  <VStack space="xs" className="flex-1">
                    <Text className="text-sm text-gray-600">End Date</Text>
                    <Input>
                      <InputField
                        type="date"
                        value={filters.end_date || ''}
                        onChangeText={value => updateFilter('end_date', value)}
                      />
                    </Input>
                  </VStack>
                </HStack>
              </VStack>

              {/* Template Type Filter */}
              <VStack space="sm">
                <Text className="font-medium text-gray-900">Template Type</Text>
                <Select
                  value={filters.template_type || 'all'}
                  onValueChange={value => updateFilter('template_type', value)}
                >
                  <SelectTrigger>
                    <Text>
                      {
                        templateTypeOptions.find(
                          opt => opt.value === (filters.template_type || 'all')
                        )?.label
                      }
                    </Text>
                  </SelectTrigger>
                  <SelectContent>
                    {templateTypeOptions.map(option => (
                      <SelectItem key={option.value} value={option.value} label={option.label} />
                    ))}
                  </SelectContent>
                </Select>
              </VStack>

              {/* Status Filter */}
              <VStack space="sm">
                <Text className="font-medium text-gray-900">Email Status</Text>
                <Select
                  value={filters.status || 'all'}
                  onValueChange={value => updateFilter('status', value)}
                >
                  <SelectTrigger>
                    <Text>
                      {statusOptions.find(opt => opt.value === (filters.status || 'all'))?.label}
                    </Text>
                  </SelectTrigger>
                  <SelectContent>
                    {statusOptions.map(option => (
                      <SelectItem key={option.value} value={option.value} label={option.label} />
                    ))}
                  </SelectContent>
                </Select>
              </VStack>

              {/* Actions */}
              <HStack space="sm">
                <Button onPress={applyFilters} className="bg-blue-600 flex-1">
                  <ButtonText className="text-white">Apply Filters</ButtonText>
                </Button>
                <Button onPress={clearFilters} variant="outline" className="flex-1">
                  <ButtonText>Clear All</ButtonText>
                </Button>
              </HStack>
            </VStack>
          </Card>
        )}

        {analytics ? (
          <>
            {/* Overview Cards */}
            <VStack space="md" className={isWeb ? 'lg:grid lg:grid-cols-4 lg:gap-4' : ''}>
              {/* Total Sent */}
              <Card className="p-6">
                <VStack space="md">
                  <HStack className="justify-between items-start">
                    <Icon as={SendIcon} size="lg" className="text-blue-600" />
                    <Icon
                      as={getTrendIcon(analytics.total_sent)}
                      size="sm"
                      className={getTrendColor(analytics.total_sent)}
                    />
                  </HStack>
                  <VStack space="xs">
                    <Text className="text-3xl font-bold text-gray-900">
                      {analytics.total_sent.toLocaleString()}
                    </Text>
                    <Text className="text-sm text-gray-600">Total Emails Sent</Text>
                  </VStack>
                </VStack>
              </Card>

              {/* Delivery Rate */}
              <Card className="p-6">
                <VStack space="md">
                  <HStack className="justify-between items-start">
                    <Icon as={MailIcon} size="lg" className="text-green-600" />
                    <Icon
                      as={getTrendIcon(analytics.delivery_rate, 0.9)}
                      size="sm"
                      className={getTrendColor(analytics.delivery_rate, 0.9)}
                    />
                  </HStack>
                  <VStack space="xs">
                    <Text
                      className={`text-3xl font-bold ${getPerformanceColor(
                        analytics.delivery_rate,
                        'delivery'
                      )}`}
                    >
                      {Math.round(analytics.delivery_rate * 100)}%
                    </Text>
                    <Text className="text-sm text-gray-600">Delivery Rate</Text>
                    <Text className="text-xs text-gray-500">
                      {analytics.delivered_count.toLocaleString()} delivered
                    </Text>
                  </VStack>
                </VStack>
              </Card>

              {/* Open Rate */}
              <Card className="p-6">
                <VStack space="md">
                  <HStack className="justify-between items-start">
                    <Icon as={EyeIcon} size="lg" className="text-purple-600" />
                    <Icon
                      as={getTrendIcon(analytics.open_rate, 0.2)}
                      size="sm"
                      className={getTrendColor(analytics.open_rate, 0.2)}
                    />
                  </HStack>
                  <VStack space="xs">
                    <Text
                      className={`text-3xl font-bold ${getPerformanceColor(
                        analytics.open_rate,
                        'open'
                      )}`}
                    >
                      {Math.round(analytics.open_rate * 100)}%
                    </Text>
                    <Text className="text-sm text-gray-600">Open Rate</Text>
                    <Text className="text-xs text-gray-500">
                      {analytics.opened_count.toLocaleString()} opened
                    </Text>
                  </VStack>
                </VStack>
              </Card>

              {/* Click Rate */}
              <Card className="p-6">
                <VStack space="md">
                  <HStack className="justify-between items-start">
                    <Icon as={MousePointerClickIcon} size="lg" className="text-orange-600" />
                    <Icon
                      as={getTrendIcon(analytics.click_rate, 0.03)}
                      size="sm"
                      className={getTrendColor(analytics.click_rate, 0.03)}
                    />
                  </HStack>
                  <VStack space="xs">
                    <Text
                      className={`text-3xl font-bold ${getPerformanceColor(
                        analytics.click_rate,
                        'click'
                      )}`}
                    >
                      {Math.round(analytics.click_rate * 100)}%
                    </Text>
                    <Text className="text-sm text-gray-600">Click Rate</Text>
                    <Text className="text-xs text-gray-500">
                      {analytics.clicked_count.toLocaleString()} clicked
                    </Text>
                  </VStack>
                </VStack>
              </Card>
            </VStack>

            {/* Template Performance */}
            <Card className="p-6">
              <VStack space="lg">
                <HStack className="justify-between items-center">
                  <Heading size="md" className="text-gray-900">
                    Template Performance
                  </Heading>
                  <Button
                    onPress={() => router.push('/(school-admin)/communication/templates')}
                    variant="link"
                    size="sm"
                  >
                    <ButtonText>Manage Templates</ButtonText>
                  </Button>
                </HStack>

                {analytics.template_performance.length > 0 ? (
                  <VStack space="md">
                    {analytics.template_performance.map((template, index) => (
                      <Card key={index} className="p-4 bg-gray-50">
                        <HStack className="justify-between items-center">
                          <VStack space="xs" className="flex-1">
                            <Text className="font-medium text-gray-900">
                              {template.template_type
                                .replace('_', ' ')
                                .replace(/\b\w/g, l => l.toUpperCase())}
                            </Text>
                            <Text className="text-sm text-gray-600">
                              {template.sent_count.toLocaleString()} emails sent
                            </Text>
                          </VStack>

                          <HStack space="lg">
                            <VStack space="xs" className="items-center">
                              <Text
                                className={`font-bold ${getPerformanceColor(
                                  template.open_rate,
                                  'open'
                                )}`}
                              >
                                {Math.round(template.open_rate * 100)}%
                              </Text>
                              <Text className="text-xs text-gray-500">Open Rate</Text>
                            </VStack>

                            <VStack space="xs" className="items-center">
                              <Text
                                className={`font-bold ${getPerformanceColor(
                                  template.click_rate,
                                  'click'
                                )}`}
                              >
                                {Math.round(template.click_rate * 100)}%
                              </Text>
                              <Text className="text-xs text-gray-500">Click Rate</Text>
                            </VStack>
                          </HStack>
                        </HStack>
                      </Card>
                    ))}
                  </VStack>
                ) : (
                  <Center className="py-8">
                    <VStack space="sm" className="items-center">
                      <Icon as={BarChart3Icon} size="xl" className="text-gray-400" />
                      <Text className="text-gray-500">No template performance data available</Text>
                      <Text className="text-xs text-gray-400 text-center">
                        Send emails using templates to see performance metrics
                      </Text>
                    </VStack>
                  </Center>
                )}
              </VStack>
            </Card>

            {/* Recent Activity */}
            <Card className="p-6">
              <VStack space="lg">
                <HStack className="justify-between items-center">
                  <Heading size="md" className="text-gray-900">
                    Recent Email Activity
                  </Heading>
                  <Text className="text-sm text-gray-500">
                    Last {analytics.recent_activity.length} emails
                  </Text>
                </HStack>

                {analytics.recent_activity.length > 0 ? (
                  <VStack space="md">
                    {analytics.recent_activity.map(email => (
                      <Card key={email.id} className="p-4 bg-gray-50">
                        <HStack className="justify-between items-start">
                          <VStack space="xs" className="flex-1">
                            <HStack space="sm" className="items-center">
                              <Text className="font-medium text-gray-900">{email.subject}</Text>
                              <Badge
                                className={
                                  email.status === 'delivered'
                                    ? 'bg-green-100 text-green-800'
                                    : email.status === 'opened'
                                    ? 'bg-blue-100 text-blue-800'
                                    : email.status === 'clicked'
                                    ? 'bg-purple-100 text-purple-800'
                                    : email.status === 'failed'
                                    ? 'bg-red-100 text-red-800'
                                    : 'bg-gray-100 text-gray-800'
                                }
                              >
                                <Text className="text-xs font-medium capitalize">
                                  {email.status}
                                </Text>
                              </Badge>
                            </HStack>
                            <Text className="text-sm text-gray-600">
                              To: {email.recipient_email}
                            </Text>
                            <Text className="text-xs text-gray-500">
                              {email.template_type
                                .replace('_', ' ')
                                .replace(/\b\w/g, l => l.toUpperCase())}{' '}
                              •{' '}
                              {email.sent_at
                                ? new Date(email.sent_at).toLocaleDateString()
                                : 'Not sent'}
                            </Text>
                          </VStack>
                        </HStack>
                      </Card>
                    ))}
                  </VStack>
                ) : (
                  <Center className="py-8">
                    <VStack space="sm" className="items-center">
                      <Icon as={MailIcon} size="xl" className="text-gray-400" />
                      <Text className="text-gray-500">No recent email activity</Text>
                      <Text className="text-xs text-gray-400 text-center">
                        Start sending emails to see recent activity here
                      </Text>
                    </VStack>
                  </Center>
                )}
              </VStack>
            </Card>

            {/* Performance Summary */}
            <Card className="p-6">
              <VStack space="lg">
                <Heading size="md" className="text-gray-900">
                  Performance Summary
                </Heading>

                <VStack space="md">
                  {/* Delivery Performance */}
                  <HStack className="justify-between items-center">
                    <HStack space="sm" className="items-center">
                      <Icon as={SendIcon} size="sm" className="text-gray-600" />
                      <Text className="text-gray-700">Email Delivery</Text>
                    </HStack>
                    <VStack space="xs" className="items-end">
                      <Text
                        className={`font-semibold ${getPerformanceColor(
                          analytics.delivery_rate,
                          'delivery'
                        )}`}
                      >
                        {Math.round(analytics.delivery_rate * 100)}%
                      </Text>
                      <Text className="text-xs text-gray-500">
                        {analytics.failed_count > 0 && `${analytics.failed_count} failed`}
                      </Text>
                    </VStack>
                  </HStack>

                  {/* Engagement Performance */}
                  <HStack className="justify-between items-center">
                    <HStack space="sm" className="items-center">
                      <Icon as={EyeIcon} size="sm" className="text-gray-600" />
                      <Text className="text-gray-700">Email Engagement</Text>
                    </HStack>
                    <VStack space="xs" className="items-end">
                      <Text
                        className={`font-semibold ${getPerformanceColor(
                          analytics.open_rate,
                          'open'
                        )}`}
                      >
                        {Math.round(analytics.open_rate * 100)}% open
                      </Text>
                      <Text
                        className={`text-xs ${getPerformanceColor(analytics.click_rate, 'click')}`}
                      >
                        {Math.round(analytics.click_rate * 100)}% click
                      </Text>
                    </VStack>
                  </HStack>

                  {/* Bounce Rate */}
                  <HStack className="justify-between items-center">
                    <HStack space="sm" className="items-center">
                      <Icon as={XCircleIcon} size="sm" className="text-gray-600" />
                      <Text className="text-gray-700">Bounce Rate</Text>
                    </HStack>
                    <Text
                      className={`font-semibold ${
                        analytics.bounce_rate > 0.05 ? 'text-red-600' : 'text-green-600'
                      }`}
                    >
                      {Math.round(analytics.bounce_rate * 100)}%
                    </Text>
                  </HStack>
                </VStack>
              </VStack>
            </Card>
          </>
        ) : (
          <Card className="p-12">
            <Center>
              <VStack space="md" className="items-center max-w-md">
                <Icon as={BarChart3Icon} size="xl" className="text-gray-400" />
                <Heading size="md" className="text-gray-900 text-center">
                  No Analytics Data Available
                </Heading>
                <Text className="text-gray-600 text-center">
                  Start sending emails to teachers to see analytics and performance metrics here.
                </Text>
                <Button onPress={() => router.push('/(school-admin)/communication/templates')}>
                  <ButtonText>Create Email Template</ButtonText>
                </Button>
              </VStack>
            </Center>
          </Card>
        )}
      </VStack>
    </ScrollView>
  );
};

const CommunicationAnalyticsPageWrapper = () => {
  return (
    <MainLayout _title="Email Analytics">
      <CommunicationAnalyticsPage />
    </MainLayout>
  );
};

export default CommunicationAnalyticsPageWrapper;
