/**
 * Webhook Status Indicator Component - GitHub Issue #117
 *
 * Displays real-time webhook health monitoring with status indicators,
 * response times, and failure alerts.
 */

import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  Zap,
  Activity,
  ExternalLink,
  RefreshCw,
} from 'lucide-react-native';
import React from 'react';

import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import type { WebhookStatus } from '@/types/paymentMonitoring';

interface WebhookStatusIndicatorProps {
  status: WebhookStatus[];
  compact?: boolean;
  onRefresh?: () => void;
  loading?: boolean;
}

interface WebhookStatusCardProps {
  webhook: WebhookStatus;
  compact?: boolean;
}

function WebhookStatusCard({ webhook, compact }: WebhookStatusCardProps) {
  const getStatusInfo = () => {
    if (webhook.is_healthy) {
      return {
        icon: CheckCircle,
        color: 'text-success-600',
        bgColor: 'bg-success-50',
        borderColor: 'border-success-200',
        status: 'Healthy',
        variant: 'success' as const,
      };
    } else if (webhook.failure_count_24h > 10) {
      return {
        icon: XCircle,
        color: 'text-error-600',
        bgColor: 'bg-error-50',
        borderColor: 'border-error-200',
        status: 'Critical',
        variant: 'error' as const,
      };
    } else {
      return {
        icon: AlertTriangle,
        color: 'text-warning-600',
        bgColor: 'bg-warning-50',
        borderColor: 'border-warning-200',
        status: 'Warning',
        variant: 'warning' as const,
      };
    }
  };

  const statusInfo = getStatusInfo();
  const IconComponent = statusInfo.icon;

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getEndpointName = (url: string) => {
    try {
      const urlObj = new URL(url);
      return urlObj.pathname.split('/').pop() || 'webhook';
    } catch {
      return 'webhook';
    }
  };

  if (compact) {
    return (
      <HStack
        space="sm"
        className={`p-3 rounded-lg border ${statusInfo.borderColor} ${statusInfo.bgColor}`}
      >
        <Icon as={IconComponent} size="sm" className={statusInfo.color} />
        <VStack space="xs" flex={1}>
          <Text size="sm" className="font-medium text-typography-900">
            {getEndpointName(webhook.endpoint_url)}
          </Text>
          <HStack space="sm" className="items-center">
            <Badge variant={statusInfo.variant} size="sm">
              <Text size="xs">{statusInfo.status}</Text>
            </Badge>
            <Text size="xs" className="text-typography-500">
              {webhook.response_time_avg}ms avg
            </Text>
          </HStack>
        </VStack>
      </HStack>
    );
  }

  return (
    <Card className={`p-4 border ${statusInfo.borderColor}`}>
      <VStack space="md">
        {/* Header */}
        <HStack className="justify-between items-start">
          <VStack space="xs" flex={1}>
            <HStack space="sm" className="items-center">
              <Icon as={IconComponent} size="sm" className={statusInfo.color} />
              <Text size="md" className="font-semibold text-typography-900">
                {getEndpointName(webhook.endpoint_url)}
              </Text>
            </HStack>
            <Text size="xs" className="text-typography-500 break-all">
              {webhook.endpoint_url}
            </Text>
          </VStack>

          <Badge variant={statusInfo.variant} size="sm">
            <Text size="xs">{statusInfo.status}</Text>
          </Badge>
        </HStack>

        {/* Metrics */}
        <VStack space="sm">
          {/* Response Time */}
          <HStack className="justify-between items-center">
            <HStack space="xs" className="items-center">
              <Icon as={Clock} size="xs" className="text-typography-500" />
              <Text size="sm" className="text-typography-600">
                Response Time
              </Text>
            </HStack>
            <Text size="sm" className="font-medium text-typography-900">
              {webhook.response_time_avg}ms
            </Text>
          </HStack>

          {/* Response Time Progress Bar */}
          <Progress
            value={Math.min((webhook.response_time_avg / 1000) * 100, 100)}
            className="h-2"
            // Color based on response time: green < 200ms, yellow < 500ms, red >= 500ms
            style={{
              backgroundColor:
                webhook.response_time_avg < 200
                  ? '#10B981'
                  : webhook.response_time_avg < 500
                    ? '#F59E0B'
                    : '#EF4444',
            }}
          />

          {/* Failure Count */}
          <HStack className="justify-between items-center">
            <HStack space="xs" className="items-center">
              <Icon as={AlertTriangle} size="xs" className="text-typography-500" />
              <Text size="sm" className="text-typography-600">
                Failures (24h)
              </Text>
            </HStack>
            <Text
              size="sm"
              className={`font-medium ${
                webhook.failure_count_24h === 0
                  ? 'text-success-600'
                  : webhook.failure_count_24h < 5
                    ? 'text-warning-600'
                    : 'text-error-600'
              }`}
            >
              {webhook.failure_count_24h}
            </Text>
          </HStack>

          {/* Last Status */}
          {webhook.status_code_last && (
            <HStack className="justify-between items-center">
              <HStack space="xs" className="items-center">
                <Icon as={Activity} size="xs" className="text-typography-500" />
                <Text size="sm" className="text-typography-600">
                  Last Status
                </Text>
              </HStack>
              <Badge
                variant={
                  webhook.status_code_last >= 200 && webhook.status_code_last < 300
                    ? 'success'
                    : 'error'
                }
                size="sm"
              >
                <Text size="xs">{webhook.status_code_last}</Text>
              </Badge>
            </HStack>
          )}
        </VStack>

        {/* Timestamps */}
        <VStack space="xs" className="pt-2 border-t border-border-100">
          <HStack className="justify-between">
            <Text size="xs" className="text-typography-500">
              Last Success:
            </Text>
            <Text size="xs" className="text-success-600 font-medium">
              {formatDate(webhook.last_success)}
            </Text>
          </HStack>

          {webhook.last_failure && (
            <HStack className="justify-between">
              <Text size="xs" className="text-typography-500">
                Last Failure:
              </Text>
              <Text size="xs" className="text-error-600 font-medium">
                {formatDate(webhook.last_failure)}
              </Text>
            </HStack>
          )}
        </VStack>

        {/* Error Message */}
        {webhook.error_message_last && (
          <Box className="p-2 bg-error-50 rounded border border-error-200">
            <Text size="xs" className="text-error-700 font-mono">
              {webhook.error_message_last}
            </Text>
          </Box>
        )}
      </VStack>
    </Card>
  );
}

export default function WebhookStatusIndicator({
  status,
  compact = false,
  onRefresh,
  loading,
}: WebhookStatusIndicatorProps) {
  if (loading) {
    return (
      <Card className="p-6">
        <VStack space="md">
          <HStack className="justify-between items-center">
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-8 w-20" />
          </HStack>
          <VStack space="sm">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </VStack>
        </VStack>
      </Card>
    );
  }

  const getOverallStatus = () => {
    if (status.length === 0) return { status: 'Unknown', color: 'text-typography-500', count: 0 };

    const healthy = status.filter(w => w.is_healthy).length;
    const total = status.length;

    if (healthy === total) {
      return { status: 'All Healthy', color: 'text-success-600', count: healthy };
    } else if (healthy > total / 2) {
      return { status: 'Mostly Healthy', color: 'text-warning-600', count: healthy };
    } else {
      return { status: 'Issues Detected', color: 'text-error-600', count: healthy };
    }
  };

  const overallStatus = getOverallStatus();

  return (
    <Card className="p-6">
      <VStack space="lg">
        {/* Header */}
        <HStack className="justify-between items-center">
          <VStack space="xs">
            <HStack space="sm" className="items-center">
              <Icon as={Zap} size="sm" className="text-primary-600" />
              <Text size="lg" className="font-semibold text-typography-900">
                Webhook Status
              </Text>
            </HStack>
            <HStack space="sm" className="items-center">
              <Text size="sm" className={overallStatus.color}>
                {overallStatus.status}
              </Text>
              <Text size="sm" className="text-typography-500">
                ({overallStatus.count}/{status.length} healthy)
              </Text>
            </HStack>
          </VStack>

          {onRefresh && (
            <Button variant="outline" size="sm" onPress={onRefresh}>
              <Icon as={RefreshCw} size="xs" />
            </Button>
          )}
        </HStack>

        {/* Webhooks List */}
        {status.length === 0 ? (
          <Box className="py-8 text-center">
            <Icon as={Zap} size="lg" className="text-typography-400 mx-auto mb-3" />
            <Text className="text-typography-500">No webhooks configured</Text>
          </Box>
        ) : (
          <VStack space={compact ? 'xs' : 'sm'}>
            {status.map((webhook, index) => (
              <WebhookStatusCard
                key={webhook.endpoint_url || index}
                webhook={webhook}
                compact={compact}
              />
            ))}
          </VStack>
        )}

        {/* Quick Actions */}
        {!compact && status.length > 0 && (
          <HStack space="sm" className="pt-4 border-t border-border-100">
            <Button variant="outline" size="sm" className="flex-1">
              <Icon as={ExternalLink} size="xs" />
              <Text size="sm" className="ml-1">
                View Logs
              </Text>
            </Button>
            <Button variant="outline" size="sm" className="flex-1">
              <Icon as={Activity} size="xs" />
              <Text size="sm" className="ml-1">
                Test Webhooks
              </Text>
            </Button>
          </HStack>
        )}
      </VStack>
    </Card>
  );
}
