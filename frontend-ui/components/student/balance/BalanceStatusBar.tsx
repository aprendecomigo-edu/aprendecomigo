/**
 * Balance Status Bar Component
 *
 * Visual balance indicator with color-coded status (green/yellow/red)
 * and progress bar representation of remaining hours.
 */

import { AlertTriangle, Clock, TrendingUp, CheckCircle } from 'lucide-react-native';
import React from 'react';

import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Progress } from '@/components/ui/progress';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useDependencies } from '@/services/di/context';

interface BalanceStatusBarProps {
  /** Remaining hours */
  remainingHours: number;
  /** Total purchased hours */
  totalHours: number;
  /** Number of days until next expiration */
  daysUntilExpiry?: number | null;
  /** Show detailed breakdown */
  showDetails?: boolean;
  /** Custom className */
  className?: string;
}

export interface BalanceStatus {
  level: 'critical' | 'low' | 'medium' | 'healthy';
  color: string;
  bgColor: string;
  progressColor: string;
  icon: any;
  message: string;
  urgency: 'urgent' | 'warning' | 'info' | 'success';
}

/**
 * Map BalanceStatusLevel to icon components
 */
const getIconComponent = (iconName: string) => {
  switch (iconName) {
    case 'AlertTriangle':
      return AlertTriangle;
    case 'Clock':
      return Clock;
    case 'TrendingUp':
      return TrendingUp;
    case 'CheckCircle':
      return CheckCircle;
    default:
      return AlertTriangle;
  }
};

/**
 * Determine balance status based on remaining hours and percentage
 * @deprecated Use BalanceService.getBalanceStatus instead. This function is kept for backward compatibility.
 */
export function getBalanceStatus(remainingHours: number, totalHours: number): BalanceStatus {
  const percentage = totalHours > 0 ? (remainingHours / totalHours) * 100 : 0;

  if (remainingHours <= 0) {
    return {
      level: 'critical',
      color: 'text-error-700',
      bgColor: 'bg-error-50',
      progressColor: 'text-error-500',
      icon: AlertTriangle,
      message: 'Balance depleted',
      urgency: 'urgent',
    };
  }

  if (remainingHours <= 2 || percentage <= 10) {
    return {
      level: 'critical',
      color: 'text-error-700',
      bgColor: 'bg-error-50',
      progressColor: 'text-error-500',
      icon: AlertTriangle,
      message: 'Critical balance',
      urgency: 'urgent',
    };
  }

  if (remainingHours <= 5 || percentage <= 25) {
    return {
      level: 'low',
      color: 'text-warning-700',
      bgColor: 'bg-warning-50',
      progressColor: 'text-warning-500',
      icon: Clock,
      message: 'Low balance',
      urgency: 'warning',
    };
  }

  if (percentage <= 50) {
    return {
      level: 'medium',
      color: 'text-primary-700',
      bgColor: 'bg-primary-50',
      progressColor: 'text-primary-500',
      icon: TrendingUp,
      message: 'Moderate balance',
      urgency: 'info',
    };
  }

  return {
    level: 'healthy',
    color: 'text-success-700',
    bgColor: 'bg-success-50',
    progressColor: 'text-success-500',
    icon: CheckCircle,
    message: 'Healthy balance',
    urgency: 'success',
  };
}

/**
 * BalanceStatusBar Component
 */
export function BalanceStatusBar({
  remainingHours,
  totalHours,
  daysUntilExpiry,
  showDetails = true,
  className = '',
}: BalanceStatusBarProps) {
  const { balanceService } = useDependencies();

  const balanceStatus = balanceService.getBalanceStatus(remainingHours, totalHours);
  const status = {
    ...balanceStatus,
    icon: getIconComponent(balanceStatus.icon),
  };

  const percentage = totalHours > 0 ? Math.min((remainingHours / totalHours) * 100, 100) : 0;

  // Convert to progress value (0-100)
  const progressValue = Math.max(0, percentage);

  return (
    <Card
      className={`p-4 border-l-4 border-l-${
        status.level === 'critical'
          ? 'error'
          : status.level === 'low'
          ? 'warning'
          : status.level === 'medium'
          ? 'primary'
          : 'success'
      }-500 ${status.bgColor} ${className}`}
    >
      <VStack space="sm">
        {/* Header with status icon and message */}
        <HStack className="items-center justify-between">
          <HStack space="sm" className="items-center flex-1">
            <Icon as={status.icon} size="sm" className={status.color} />
            <VStack space="xs" className="flex-1">
              <HStack className="items-center justify-between">
                <Text className={`font-semibold ${status.color}`}>{status.message}</Text>
                <Badge variant="solid" action={status.urgency} size="sm">
                  <Text className="text-xs">{remainingHours.toFixed(1)}h</Text>
                </Badge>
              </HStack>

              {showDetails && (
                <Text className="text-xs text-typography-600">
                  {percentage.toFixed(0)}% of {totalHours.toFixed(1)} hours remaining
                </Text>
              )}
            </VStack>
          </HStack>
        </HStack>

        {/* Progress Bar */}
        <VStack space="xs">
          <Progress value={progressValue} className="h-2 w-full" size="sm" />

          {showDetails && (
            <HStack className="items-center justify-between">
              <Text className="text-xs text-typography-500">0h</Text>
              <Text className="text-xs text-typography-500">{totalHours.toFixed(1)}h</Text>
            </HStack>
          )}
        </VStack>

        {/* Expiry warning if applicable */}
        {daysUntilExpiry !== null && daysUntilExpiry !== undefined && daysUntilExpiry <= 7 && (
          <HStack space="xs" className="items-center">
            <Icon as={Clock} size="xs" className="text-warning-600" />
            <Text className="text-xs text-warning-700">
              {daysUntilExpiry <= 0
                ? 'Hours expire today'
                : `${daysUntilExpiry} day${daysUntilExpiry === 1 ? '' : 's'} until expiry`}
            </Text>
          </HStack>
        )}
      </VStack>
    </Card>
  );
}

/**
 * Compact version for use in smaller spaces
 */
export function CompactBalanceStatusBar({
  remainingHours,
  totalHours,
  className = '',
}: Pick<BalanceStatusBarProps, 'remainingHours' | 'totalHours' | 'className'>) {
  const { balanceService } = useDependencies();

  const balanceStatus = balanceService.getBalanceStatus(remainingHours, totalHours);
  const status = {
    ...balanceStatus,
    icon: getIconComponent(balanceStatus.icon),
  };

  const percentage = totalHours > 0 ? (remainingHours / totalHours) * 100 : 0;

  return (
    <HStack space="sm" className={`items-center ${className}`}>
      <Icon as={status.icon} size="sm" className={status.color} />
      <VStack space="xs" className="flex-1">
        <HStack className="items-center justify-between">
          <Text className={`text-sm font-medium ${status.color}`}>
            {remainingHours.toFixed(1)}h
          </Text>
          <Text className="text-xs text-typography-500">{percentage.toFixed(0)}%</Text>
        </HStack>
        <Progress value={Math.max(0, percentage)} className="h-1 w-full" size="xs" />
      </VStack>
    </HStack>
  );
}
