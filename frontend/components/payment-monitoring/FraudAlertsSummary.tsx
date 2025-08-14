/**
 * Fraud Alerts Summary Component - GitHub Issue #117
 *
 * Displays a summary of active fraud alerts and disputes
 * with priority indicators and quick action buttons.
 */

import {
  Shield,
  AlertTriangle,
  Eye,
  FileText,
  Clock,
  TrendingUp,
  ExternalLink,
  ChevronRight,
} from 'lucide-react-native';
import React from 'react';

import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Skeleton } from '@/components/ui/skeleton';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import type { FraudAlert, DisputeRecord } from '@/types/paymentMonitoring';

interface FraudAlertsSummaryProps {
  alerts: FraudAlert[];
  disputes: DisputeRecord[];
  loading?: boolean;
  onViewAlert?: (alert: FraudAlert) => void;
  onViewDispute?: (dispute: DisputeRecord) => void;
  onViewAllAlerts?: () => void;
  onViewAllDisputes?: () => void;
}

interface AlertItemProps {
  alert: FraudAlert;
  onView?: (alert: FraudAlert) => void;
}

interface DisputeItemProps {
  dispute: DisputeRecord;
  onView?: (dispute: DisputeRecord) => void;
}

function AlertItem({ alert, onView }: AlertItemProps) {
  const getRiskColor = (score: number) => {
    if (score >= 80) return 'text-error-600';
    if (score >= 50) return 'text-warning-600';
    return 'text-info-600';
  };

  const getRiskBadge = (score: number) => {
    if (score >= 80) return { variant: 'error' as const, label: 'High Risk' };
    if (score >= 50) return { variant: 'warning' as const, label: 'Medium Risk' };
    return { variant: 'info' as const, label: 'Low Risk' };
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-error-600';
      case 'investigating':
        return 'text-warning-600';
      case 'resolved':
        return 'text-success-600';
      case 'false_positive':
        return 'text-typography-500';
      default:
        return 'text-typography-600';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  const riskBadge = getRiskBadge(alert.risk_score);

  return (
    <Pressable
      onPress={() => onView?.(alert)}
      className="p-3 rounded-lg border border-border-200 hover:bg-background-50 active:bg-background-100"
    >
      <VStack space="sm">
        {/* Header */}
        <HStack className="justify-between items-start">
          <VStack space="xs" flex={1}>
            <Text size="sm" className="font-medium text-typography-900">
              {alert.alert_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </Text>
            <Text size="xs" className="text-typography-500">
              {alert.customer_email}
            </Text>
          </VStack>

          <Badge variant={riskBadge.variant} size="sm">
            <Text size="xs">{riskBadge.label}</Text>
          </Badge>
        </HStack>

        {/* Details */}
        <VStack space="xs">
          <HStack className="justify-between items-center">
            <Text size="xs" className="text-typography-500">
              Risk Score:
            </Text>
            <Text size="xs" className={`font-medium ${getRiskColor(alert.risk_score)}`}>
              {alert.risk_score}/100
            </Text>
          </HStack>

          <HStack className="justify-between items-center">
            <Text size="xs" className="text-typography-500">
              Amount:
            </Text>
            <Text size="xs" className="font-medium text-typography-700">
              €{parseFloat(alert.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </Text>
          </HStack>

          <HStack className="justify-between items-center">
            <Text size="xs" className="text-typography-500">
              Status:
            </Text>
            <Text size="xs" className={`font-medium ${getStatusColor(alert.status)}`}>
              {alert.status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </Text>
          </HStack>
        </VStack>

        {/* Footer */}
        <HStack className="justify-between items-center pt-2 border-t border-border-100">
          <Text size="xs" className="text-typography-500">
            {formatDate(alert.created_at)}
          </Text>
          <Icon as={ChevronRight} size="xs" className="text-typography-400" />
        </HStack>
      </VStack>
    </Pressable>
  );
}

function DisputeItem({ dispute, onView }: DisputeItemProps) {
  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'warning_needs_response':
      case 'needs_response':
        return { variant: 'error' as const, label: 'Response Needed', urgent: true };
      case 'warning_under_review':
      case 'under_review':
        return { variant: 'warning' as const, label: 'Under Review', urgent: false };
      case 'won':
        return { variant: 'success' as const, label: 'Won', urgent: false };
      case 'lost':
      case 'charge_refunded':
        return { variant: 'error' as const, label: 'Lost', urgent: false };
      case 'warning_closed':
        return { variant: 'info' as const, label: 'Closed', urgent: false };
      default:
        return { variant: 'info' as const, label: status.replace(/_/g, ' '), urgent: false };
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'No deadline';

    const date = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (diffInDays < 0) return 'Overdue';
    if (diffInDays === 0) return 'Due today';
    if (diffInDays === 1) return 'Due tomorrow';
    return `${diffInDays} days left`;
  };

  const statusInfo = getStatusInfo(dispute.status);

  return (
    <Pressable
      onPress={() => onView?.(dispute)}
      className="p-3 rounded-lg border border-border-200 hover:bg-background-50 active:bg-background-100"
    >
      <VStack space="sm">
        {/* Header */}
        <HStack className="justify-between items-start">
          <VStack space="xs" flex={1}>
            <Text size="sm" className="font-medium text-typography-900">
              {dispute.reason.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </Text>
            <Text size="xs" className="text-typography-500">
              {dispute.customer_email}
            </Text>
          </VStack>

          <Badge variant={statusInfo.variant} size="sm">
            <Text size="xs">{statusInfo.label}</Text>
          </Badge>
        </HStack>

        {/* Details */}
        <VStack space="xs">
          <HStack className="justify-between items-center">
            <Text size="xs" className="text-typography-500">
              Amount:
            </Text>
            <Text size="xs" className="font-medium text-typography-700">
              €{parseFloat(dispute.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </Text>
          </HStack>

          {dispute.evidence_due_by && (
            <HStack className="justify-between items-center">
              <Text size="xs" className="text-typography-500">
                Evidence Due:
              </Text>
              <Text
                size="xs"
                className={`font-medium ${
                  formatDate(dispute.evidence_due_by).includes('Overdue') ||
                  formatDate(dispute.evidence_due_by).includes('today')
                    ? 'text-error-600'
                    : 'text-warning-600'
                }`}
              >
                {formatDate(dispute.evidence_due_by)}
              </Text>
            </HStack>
          )}

          <HStack className="justify-between items-center">
            <Text size="xs" className="text-typography-500">
              Evidence:
            </Text>
            <Text
              size="xs"
              className={`font-medium ${
                dispute.evidence_submitted ? 'text-success-600' : 'text-error-600'
              }`}
            >
              {dispute.evidence_submitted ? 'Submitted' : 'Not Submitted'}
            </Text>
          </HStack>
        </VStack>

        {/* Footer */}
        <HStack className="justify-between items-center pt-2 border-t border-border-100">
          <Text size="xs" className="text-typography-500">
            {new Date(dispute.created_at).toLocaleDateString([], {
              month: 'short',
              day: 'numeric',
            })}
          </Text>
          <Icon as={ChevronRight} size="xs" className="text-typography-400" />
        </HStack>
      </VStack>
    </Pressable>
  );
}

function LoadingCard() {
  return (
    <Box className="p-3 rounded-lg border border-border-200">
      <VStack space="sm">
        <HStack className="justify-between">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-5 w-16" />
        </HStack>
        <Skeleton className="h-3 w-32" />
        <VStack space="xs">
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-full" />
        </VStack>
      </VStack>
    </Box>
  );
}

export default function FraudAlertsSummary({
  alerts,
  disputes,
  loading,
  onViewAlert,
  onViewDispute,
  onViewAllAlerts,
  onViewAllDisputes,
}: FraudAlertsSummaryProps) {
  const activeAlerts = alerts.filter(
    alert => alert.status === 'active' || alert.status === 'investigating'
  );
  const urgentDisputes = disputes.filter(
    dispute =>
      dispute.status.includes('needs_response') ||
      (dispute.evidence_due_by &&
        new Date(dispute.evidence_due_by) <= new Date(Date.now() + 24 * 60 * 60 * 1000))
  );

  if (loading) {
    return (
      <Card className="p-6">
        <VStack space="lg">
          <Skeleton className="h-6 w-32" />
          <VStack space="sm">
            {[...Array(3)].map((_, i) => (
              <LoadingCard key={i} />
            ))}
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
          <HStack space="sm" className="items-center">
            <Icon as={Shield} size="sm" className="text-primary-600" />
            <Text size="lg" className="font-semibold text-typography-900">
              Security Alerts
            </Text>
          </HStack>
          <Text size="sm" className="text-typography-500">
            Fraud detection and disputes
          </Text>
        </VStack>

        {/* Summary Stats */}
        <HStack space="md" className="justify-between">
          <VStack space="xs" className="items-center flex-1">
            <Text
              size="xl"
              className={`font-bold ${
                activeAlerts.length > 0 ? 'text-error-600' : 'text-success-600'
              }`}
            >
              {activeAlerts.length}
            </Text>
            <Text size="xs" className="text-typography-500 text-center">
              Active Fraud{'\n'}Alerts
            </Text>
          </VStack>

          <VStack space="xs" className="items-center flex-1">
            <Text
              size="xl"
              className={`font-bold ${
                urgentDisputes.length > 0 ? 'text-warning-600' : 'text-success-600'
              }`}
            >
              {urgentDisputes.length}
            </Text>
            <Text size="xs" className="text-typography-500 text-center">
              Urgent{'\n'}Disputes
            </Text>
          </VStack>

          <VStack space="xs" className="items-center flex-1">
            <Text
              size="xl"
              className={`font-bold ${disputes.length > 0 ? 'text-info-600' : 'text-success-600'}`}
            >
              {disputes.length}
            </Text>
            <Text size="xs" className="text-typography-500 text-center">
              Total{'\n'}Disputes
            </Text>
          </VStack>
        </HStack>

        {/* Active Fraud Alerts */}
        {activeAlerts.length > 0 && (
          <VStack space="sm">
            <HStack className="justify-between items-center">
              <Text size="md" className="font-medium text-typography-900">
                Fraud Alerts
              </Text>
              {onViewAllAlerts && (
                <Button variant="ghost" size="sm" onPress={onViewAllAlerts}>
                  <Text size="sm">View All</Text>
                  <Icon as={ExternalLink} size="xs" className="ml-1" />
                </Button>
              )}
            </HStack>

            <VStack space="xs">
              {activeAlerts.slice(0, 3).map(alert => (
                <AlertItem key={alert.id} alert={alert} onView={onViewAlert} />
              ))}
              {activeAlerts.length > 3 && (
                <Button variant="ghost" size="sm" onPress={onViewAllAlerts}>
                  <Text size="sm">+ {activeAlerts.length - 3} more alerts</Text>
                </Button>
              )}
            </VStack>
          </VStack>
        )}

        {/* Urgent Disputes */}
        {urgentDisputes.length > 0 && (
          <VStack space="sm">
            <HStack className="justify-between items-center">
              <Text size="md" className="font-medium text-typography-900">
                Urgent Disputes
              </Text>
              {onViewAllDisputes && (
                <Button variant="ghost" size="sm" onPress={onViewAllDisputes}>
                  <Text size="sm">View All</Text>
                  <Icon as={ExternalLink} size="xs" className="ml-1" />
                </Button>
              )}
            </HStack>

            <VStack space="xs">
              {urgentDisputes.slice(0, 2).map(dispute => (
                <DisputeItem key={dispute.id} dispute={dispute} onView={onViewDispute} />
              ))}
              {urgentDisputes.length > 2 && (
                <Button variant="ghost" size="sm" onPress={onViewAllDisputes}>
                  <Text size="sm">+ {urgentDisputes.length - 2} more disputes</Text>
                </Button>
              )}
            </VStack>
          </VStack>
        )}

        {/* Empty State */}
        {activeAlerts.length === 0 && urgentDisputes.length === 0 && (
          <VStack space="md" className="items-center py-8">
            <Icon as={Shield} size="lg" className="text-success-500" />
            <VStack space="xs" className="items-center">
              <Text size="md" className="font-medium text-success-600">
                All Clear
              </Text>
              <Text size="sm" className="text-typography-500 text-center">
                No active fraud alerts or urgent disputes
              </Text>
            </VStack>
          </VStack>
        )}

        {/* Quick Actions */}
        <HStack space="sm" className="pt-4 border-t border-border-100">
          <Button variant="outline" size="sm" className="flex-1" onPress={onViewAllAlerts}>
            <Icon as={AlertTriangle} size="xs" />
            <Text size="sm" className="ml-1">
              All Alerts
            </Text>
          </Button>
          <Button variant="outline" size="sm" className="flex-1" onPress={onViewAllDisputes}>
            <Icon as={FileText} size="xs" />
            <Text size="sm" className="ml-1">
              All Disputes
            </Text>
          </Button>
        </HStack>
      </VStack>
    </Card>
  );
}
