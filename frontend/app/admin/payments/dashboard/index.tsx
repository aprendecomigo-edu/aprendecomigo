/**
 * Payment Monitoring Dashboard Screen - GitHub Issue #117
 *
 * Main payment monitoring dashboard that provides administrators with
 * real-time visibility into payment system health, metrics, and monitoring.
 */

import {
  RefreshCw,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  DollarSign,
  Activity,
} from 'lucide-react-native';
import React, { useEffect, useState } from 'react';
import { ScrollView } from 'react-native';

import { PaymentMonitoringApiClient } from '@/api/paymentMonitoringApi';
import FraudAlertsSummary from '@/components/payment-monitoring/FraudAlertsSummary';
import PaymentMetricsGrid from '@/components/payment-monitoring/PaymentMetricsGrid';
import PaymentTrendChart from '@/components/payment-monitoring/PaymentTrendChart';
import RecentTransactionsTable from '@/components/payment-monitoring/RecentTransactionsTable';
import WebhookStatusIndicator from '@/components/payment-monitoring/WebhookStatusIndicator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Import custom components (to be created)

// Import API and hooks
import { usePaymentMonitoringWebSocket } from '@/hooks/usePaymentMonitoringWebSocket';
import type { PaymentMetrics, PaymentTrendData } from '@/types/paymentMonitoring';

interface DashboardState {
  timeRange: 'last_24h' | 'last_7d' | 'last_30d';
  autoRefresh: boolean;
  refreshInterval: number; // seconds
}

export default function PaymentMonitoringDashboard() {
  // State management
  const [state, setState] = useState<DashboardState>({
    timeRange: 'last_24h',
    autoRefresh: true,
    refreshInterval: 30,
  });

  const [metrics, setMetrics] = useState<PaymentMetrics | null>(null);
  const [trendData, setTrendData] = useState<PaymentTrendData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // WebSocket connection for real-time updates
  const {
    isConnected: wsConnected,
    error: wsError,
    metrics: wsMetrics,
    trendData: wsTrendData,
    webhookStatus,
    recentTransactions,
    activeFraudAlerts,
    activeDisputes,
    setMetrics: setWsMetrics,
    setTrendData: setWsTrendData,
  } = usePaymentMonitoringWebSocket(state.autoRefresh);

  // Load initial data
  const loadDashboardData = async () => {
    try {
      setError(null);
      setLoading(true);

      // Load metrics and trend data in parallel with graceful degradation
      const results = await Promise.allSettled([
        PaymentMonitoringApiClient.getDashboardMetrics(state.timeRange),
        PaymentMonitoringApiClient.getPaymentTrends(state.timeRange),
      ]);

      const [metricsResult, trendsResult] = results;

      // Handle metrics result
      if (metricsResult.status === 'fulfilled') {
        setMetrics(metricsResult.value);
        setWsMetrics(metricsResult.value);
      } else {
        console.error('Failed to load payment metrics:', metricsResult.reason);
        setMetrics(null);
      }

      // Handle trends result
      if (trendsResult.status === 'fulfilled') {
        setTrendData(trendsResult.value);
        setWsTrendData(trendsResult.value);
      } else {
        console.error('Failed to load payment trends:', trendsResult.reason);
        setTrendData(null);
      }

      setLastUpdated(new Date());

      // Set error if both operations failed
      const failedCount = results.filter(result => result.status === 'rejected').length;
      if (failedCount === results.length) {
        setError('Failed to load dashboard data. Please try again.');
      } else if (failedCount > 0) {
        setError(
          `Some dashboard data could not be loaded. ${failedCount} of ${results.length} operations failed.`,
        );
      }
    } catch (err: any) {
      if (__DEV__) {
        console.error('Error loading dashboard data:', err); // TODO: Review for sensitive data
      }
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  // Update from WebSocket data
  useEffect(() => {
    if (wsMetrics) {
      setMetrics(wsMetrics);
      setLastUpdated(new Date());
    }
  }, [wsMetrics]);

  useEffect(() => {
    if (wsTrendData) {
      setTrendData(wsTrendData);
    }
  }, [wsTrendData]);

  // Auto-refresh setup
  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;

    if (state.autoRefresh && state.refreshInterval > 0) {
      intervalId = setInterval(() => {
        if (!wsConnected) {
          // Only refresh via API if WebSocket is not connected
          loadDashboardData();
        }
      }, state.refreshInterval * 1000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [state.autoRefresh, state.refreshInterval, wsConnected]);

  // Initial data load
  useEffect(() => {
    loadDashboardData();
  }, [state.timeRange]);

  // Handle time range change
  const handleTimeRangeChange = (newTimeRange: DashboardState['timeRange']) => {
    setState(prev => ({ ...prev, timeRange: newTimeRange }));
  };

  // Handle refresh
  const handleRefresh = () => {
    loadDashboardData();
  };

  // Toggle auto-refresh
  const toggleAutoRefresh = () => {
    setState(prev => ({ ...prev, autoRefresh: !prev.autoRefresh }));
  };

  // Connection status indicator
  const getConnectionStatus = () => {
    if (wsConnected) {
      return { status: 'connected', color: 'success', text: 'Live updates active' };
    } else if (wsError) {
      return { status: 'error', color: 'error', text: 'Connection error' };
    } else {
      return { status: 'disconnected', color: 'warning', text: 'Connecting...' };
    }
  };

  const connectionStatus = getConnectionStatus();

  if (loading && !metrics) {
    return (
      <VStack flex={1} className="justify-center items-center p-6">
        <Spinner size="large" />
        <Text className="mt-4 text-typography-600">Loading payment monitoring dashboard...</Text>
      </VStack>
    );
  }

  return (
    <VStack flex={1} className="bg-background-0">
      {/* Header */}
      <VStack space="md" className="p-6 border-b border-border-200 bg-background-50">
        <HStack className="justify-between items-center">
          <VStack space="xs">
            <Heading size="xl" className="text-typography-900">
              Payment Monitoring Dashboard
            </Heading>
            <HStack space="md" className="items-center">
              <Badge variant={connectionStatus.color as any} className="flex-row items-center">
                <Icon
                  as={
                    connectionStatus.status === 'connected'
                      ? CheckCircle
                      : connectionStatus.status === 'error'
                        ? AlertCircle
                        : Activity
                  }
                  size="xs"
                  className="mr-1"
                />
                <Text size="xs">{connectionStatus.text}</Text>
              </Badge>

              {lastUpdated && (
                <Text size="sm" className="text-typography-500">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </Text>
              )}
            </HStack>
          </VStack>

          <HStack space="sm" className="items-center">
            {/* Time Range Selector */}
            <HStack space="xs">
              {(['last_24h', 'last_7d', 'last_30d'] as const).map(range => (
                <Button
                  key={range}
                  variant={state.timeRange === range ? 'solid' : 'outline'}
                  size="sm"
                  onPress={() => handleTimeRangeChange(range)}
                >
                  <Text size="sm">
                    {range === 'last_24h' ? '24h' : range === 'last_7d' ? '7d' : '30d'}
                  </Text>
                </Button>
              ))}
            </HStack>

            {/* Auto-refresh toggle */}
            <Button
              variant={state.autoRefresh ? 'solid' : 'outline'}
              size="sm"
              onPress={toggleAutoRefresh}
            >
              <Icon as={Activity} size="xs" />
              <Text size="sm" className="ml-1">
                {state.autoRefresh ? 'Live' : 'Manual'}
              </Text>
            </Button>

            {/* Manual refresh */}
            <Button variant="outline" size="sm" onPress={handleRefresh} disabled={loading}>
              <Icon as={RefreshCw} size="xs" className={loading ? 'animate-spin' : ''} />
            </Button>
          </HStack>
        </HStack>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive">
            <Icon as={AlertCircle} size="sm" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </VStack>

      {/* Dashboard Content */}
      <ScrollView
        className="flex-1"
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ padding: 24 }}
      >
        <VStack space="lg">
          {/* Metrics Grid */}
          {metrics && (
            <PaymentMetricsGrid metrics={metrics} timeRange={state.timeRange} loading={loading} />
          )}

          {/* Charts and Status Row */}
          <HStack space="lg" className="items-start">
            {/* Payment Trends Chart */}
            <Box flex={2}>
              {trendData && (
                <PaymentTrendChart
                  data={trendData}
                  metric="transactions"
                  timeRange={state.timeRange}
                  height={300}
                />
              )}
            </Box>

            {/* Webhook Status */}
            <Box flex={1}>
              <WebhookStatusIndicator status={webhookStatus} compact={false} />
            </Box>
          </HStack>

          {/* Recent Activity Row */}
          <HStack space="lg" className="items-start">
            {/* Recent Transactions */}
            <Box flex={2}>
              <RecentTransactionsTable transactions={recentTransactions} loading={loading} />
            </Box>

            {/* Fraud Alerts Summary */}
            <Box flex={1}>
              <FraudAlertsSummary alerts={activeFraudAlerts} disputes={activeDisputes} />
            </Box>
          </HStack>
        </VStack>
      </ScrollView>
    </VStack>
  );
}
