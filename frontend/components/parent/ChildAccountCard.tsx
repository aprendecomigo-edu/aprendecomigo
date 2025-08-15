/**
 * ChildAccountCard Component
 *
 * Individual child account summary card showing balance,
 * activity status, and quick access to child management features.
 */

import useRouter from '@unitools/router';
import {
  User,
  Clock,
  CreditCard,
  Activity,
  AlertTriangle,
  CheckCircle,
  ChevronRight,
  Settings,
  Eye,
} from 'lucide-react-native';
import React, { useCallback } from 'react';

import { ChildProfile } from '@/api/parentApi';
import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface ChildAccountCardProps {
  child: ChildProfile;
  metrics?: {
    child_id: number;
    child_name: string;
    current_balance: string;
    hours_consumed_this_month: number;
    last_activity: string | null;
    status: 'active' | 'inactive' | 'suspended';
  };
  isSelected?: boolean;
  onSelect?: () => void;
  showActions?: boolean;
}

export const ChildAccountCard = React.memo<ChildAccountCardProps>(({
  child,
  metrics,
  isSelected = false,
  onSelect,
  showActions = true,
}) => {
  const router = useRouter();

  // Get status color and icon
  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'active':
        return {
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          icon: CheckCircle,
          label: 'Active',
          badgeAction: 'success' as const,
        };
      case 'suspended':
        return {
          color: 'text-red-600',
          bgColor: 'bg-red-100',
          icon: AlertTriangle,
          label: 'Suspended',
          badgeAction: 'error' as const,
        };
      default:
        return {
          color: 'text-gray-600',
          bgColor: 'bg-gray-100',
          icon: Clock,
          label: 'Inactive',
          badgeAction: 'secondary' as const,
        };
    }
  };

  const statusInfo = getStatusInfo(metrics?.status || 'inactive');

  // Format balance
  const formatBalance = (balance: string | number) => {
    const numBalance = typeof balance === 'string' ? parseFloat(balance) : balance;
    return isNaN(numBalance) ? '0' : numBalance.toFixed(0);
  };

  // Format last activity
  const formatLastActivity = (lastActivity: string | null) => {
    if (!lastActivity) return 'No recent activity';

    const date = new Date(lastActivity);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

    if (diffInHours < 1) return 'Active now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`;
    return date.toLocaleDateString();
  };

  // Navigate to child detail view
  const handleViewDetails = useCallback(() => {
    router.push(`/(parent)/child/${child.id}`);
  }, [router, child.id]);

  return (
    <Card
      className={`
        bg-white border
        ${isSelected ? 'border-blue-300 shadow-lg' : 'border-gray-200'}
      `}
    >
      <CardContent className="p-4">
        <Pressable onPress={onSelect} className="active:opacity-70">
          {/* Header */}
          <HStack className="justify-between items-start mb-4">
            <HStack className="flex-1 space-x-3">
              <VStack
                className={`
                  items-center justify-center w-12 h-12 rounded-full
                  ${statusInfo.bgColor}
                `}
              >
                <Icon as={statusInfo.icon} size={20} className={statusInfo.color} />
              </VStack>

              <VStack className="flex-1">
                <HStack className="items-center space-x-2">
                  <Text className="text-gray-900 font-semibold text-base">
                    {child.child_user.name ||
                      `${child.child_user.first_name} ${child.child_user.last_name}`.trim()}
                  </Text>
                  {child.is_primary_contact && (
                    <Badge variant="solid" action="info" size="sm">
                      <Text className="text-xs font-medium">Primary</Text>
                    </Badge>
                  )}
                </HStack>

                <Text className="text-sm text-gray-600">{child.child_user.email}</Text>

                <HStack className="items-center space-x-2 mt-1">
                  <Badge variant="outline" action={statusInfo.badgeAction} size="sm">
                    <Text className="text-xs font-medium">{statusInfo.label}</Text>
                  </Badge>

                  <Text className="text-xs text-gray-500">
                    {formatLastActivity(metrics?.last_activity || null)}
                  </Text>
                </HStack>
              </VStack>
            </HStack>

            {showActions && (
              <Button variant="ghost" size="sm" onPress={handleViewDetails}>
                <ButtonIcon as={ChevronRight} size={16} />
              </Button>
            )}
          </HStack>

          {/* Metrics */}
          {metrics && (
            <>
              <Divider className="my-3" />

              <HStack className="justify-between items-center">
                {/* Balance */}
                <VStack className="items-center flex-1">
                  <HStack className="items-center space-x-1 mb-1">
                    <Icon as={CreditCard} size={14} className="text-gray-500" />
                    <Text className="text-xs text-gray-600 font-medium">Balance</Text>
                  </HStack>
                  <Text className="text-lg font-bold text-gray-900">
                    {formatBalance(metrics.current_balance)}h
                  </Text>
                </VStack>

                <Divider orientation="vertical" className="h-8 mx-4" />

                {/* Hours This Month */}
                <VStack className="items-center flex-1">
                  <HStack className="items-center space-x-1 mb-1">
                    <Icon as={Activity} size={14} className="text-gray-500" />
                    <Text className="text-xs text-gray-600 font-medium">This Month</Text>
                  </HStack>
                  <Text className="text-lg font-bold text-gray-900">
                    {metrics.hours_consumed_this_month}h
                  </Text>
                </VStack>

                <Divider orientation="vertical" className="h-8 mx-4" />

                {/* Status */}
                <VStack className="items-center flex-1">
                  <HStack className="items-center space-x-1 mb-1">
                    <Icon as={statusInfo.icon} size={14} className="text-gray-500" />
                    <Text className="text-xs text-gray-600 font-medium">Status</Text>
                  </HStack>
                  <Text className={`text-sm font-semibold ${statusInfo.color}`}>
                    {statusInfo.label}
                  </Text>
                </VStack>
              </HStack>
            </>
          )}

          {/* Action Buttons */}
          {showActions && (
            <>
              <Divider className="my-4" />

              <HStack className="space-x-2">
                <Button variant="outline" size="sm" className="flex-1" onPress={handleViewDetails}>
                  <ButtonIcon as={Eye} size={14} />
                  <ButtonText className="ml-1">View Details</ButtonText>
                </Button>

                <Button variant="outline" size="sm" className="flex-1">
                  <ButtonIcon as={Settings} size={14} />
                  <ButtonText className="ml-1">Settings</ButtonText>
                </Button>
              </HStack>
            </>
          )}
        </Pressable>
      </CardContent>
    </Card>
  );
}, (prevProps, nextProps) => {
  // Custom comparison function to prevent unnecessary re-renders
  return (
    prevProps.child.id === nextProps.child.id &&
    prevProps.isSelected === nextProps.isSelected &&
    prevProps.showActions === nextProps.showActions &&
    JSON.stringify(prevProps.metrics) === JSON.stringify(nextProps.metrics)
  );
});
