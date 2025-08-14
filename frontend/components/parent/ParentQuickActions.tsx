/**
 * ParentQuickActions Component
 *
 * Quick action buttons for common parent tasks including
 * purchase approvals, child management, and settings access.
 */

import useRouter from '@unitools/router';
import {
  Bell,
  Plus,
  CreditCard,
  Settings,
  Users,
  RefreshCw,
  BarChart3,
  Shield,
  MessageCircle,
  Calendar,
} from 'lucide-react-native';
import React from 'react';

import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface ParentQuickActionsProps {
  pendingApprovalsCount: number;
  childrenCount: number;
  onRefresh: () => void;
  disabled?: boolean;
}

interface QuickAction {
  id: string;
  title: string;
  subtitle: string;
  icon: React.ComponentType<any>;
  iconColor: string;
  iconBgColor: string;
  badge?: {
    count: number;
    variant: 'error' | 'warning' | 'info' | 'success';
  };
  onPress: () => void;
  disabled?: boolean;
}

export const ParentQuickActions: React.FC<ParentQuickActionsProps> = ({
  pendingApprovalsCount,
  childrenCount,
  onRefresh,
  disabled = false,
}) => {
  const router = useRouter();

  // Quick action handlers
  const handleApprovals = () => {
    // Navigate to approvals view or open modal
    router.push('/(parent)/dashboard?tab=approvals');
  };

  const handleAddChild = () => {
    // Open add child modal or navigate to add child flow
    router.push('/(parent)/settings?action=add-child');
  };

  const handleBudgetSettings = () => {
    // Navigate to budget controls
    router.push('/(parent)/settings?tab=budget');
  };

  const handleFamilyReports = () => {
    // Navigate to family reports
    router.push('/(parent)/overview?tab=reports');
  };

  const handleNotifications = () => {
    // Navigate to notification settings
    router.push('/(parent)/settings?tab=notifications');
  };

  const handleScheduling = () => {
    // Navigate to family scheduling
    router.push('/calendar');
  };

  // Define quick actions
  const quickActions: QuickAction[] = [
    {
      id: 'approvals',
      title: 'Purchase Approvals',
      subtitle: 'Review pending requests',
      icon: Bell,
      iconColor: 'text-orange-600',
      iconBgColor: 'bg-orange-100',
      badge:
        pendingApprovalsCount > 0
          ? {
              count: pendingApprovalsCount,
              variant: 'warning',
            }
          : undefined,
      onPress: handleApprovals,
      disabled: disabled,
    },
    {
      id: 'add-child',
      title: 'Add Child',
      subtitle: 'Connect new account',
      icon: Plus,
      iconColor: 'text-blue-600',
      iconBgColor: 'bg-blue-100',
      onPress: handleAddChild,
      disabled: disabled,
    },
    {
      id: 'budget',
      title: 'Budget Controls',
      subtitle: 'Manage spending limits',
      icon: Shield,
      iconColor: 'text-green-600',
      iconBgColor: 'bg-green-100',
      onPress: handleBudgetSettings,
      disabled: disabled,
    },
    {
      id: 'reports',
      title: 'Family Reports',
      subtitle: 'View usage analytics',
      icon: BarChart3,
      iconColor: 'text-purple-600',
      iconBgColor: 'bg-purple-100',
      onPress: handleFamilyReports,
      disabled: disabled,
    },
  ];

  // Secondary actions (less prominent)
  const secondaryActions = [
    {
      id: 'refresh',
      title: 'Refresh',
      icon: RefreshCw,
      onPress: onRefresh,
    },
    {
      id: 'notifications',
      title: 'Notifications',
      icon: MessageCircle,
      onPress: handleNotifications,
    },
    {
      id: 'schedule',
      title: 'Schedule',
      icon: Calendar,
      onPress: handleScheduling,
    },
    {
      id: 'settings',
      title: 'Settings',
      icon: Settings,
      onPress: () => router.push('/(parent)/settings'),
    },
  ];

  return (
    <Card className="bg-white">
      <CardHeader className="pb-3">
        <Heading size="md" className="text-gray-900">
          Quick Actions
        </Heading>
      </CardHeader>

      <CardContent>
        {/* Primary Actions Grid */}
        <VStack className="space-y-4 mb-6">
          {/* Top row */}
          <HStack className="space-x-3">
            {quickActions.slice(0, 2).map(action => (
              <VStack key={action.id} className="flex-1">
                <Pressable
                  className={`
                    bg-gray-50 rounded-lg p-4 border border-gray-200 w-full
                    ${action.disabled ? 'opacity-50' : 'active:bg-gray-100'}
                  `}
                  onPress={action.onPress}
                  disabled={action.disabled}
                >
                  <VStack className="items-center space-y-3">
                    <VStack className="relative">
                      <VStack
                        className={`
                          items-center justify-center w-12 h-12 rounded-full
                          ${action.iconBgColor}
                        `}
                      >
                        <Icon as={action.icon} size={24} className={action.iconColor} />
                      </VStack>

                      {action.badge && (
                        <Badge
                          size="sm"
                          variant="solid"
                          action={action.badge.variant}
                          className="absolute -top-1 -right-1 min-w-5 h-5"
                        >
                          <Text className="text-xs text-white font-medium">
                            {action.badge.count}
                          </Text>
                        </Badge>
                      )}
                    </VStack>

                    <VStack className="items-center space-y-1">
                      <Text className="text-sm font-medium text-gray-900 text-center">
                        {action.title}
                      </Text>
                      <Text className="text-xs text-gray-600 text-center">{action.subtitle}</Text>
                    </VStack>
                  </VStack>
                </Pressable>
              </VStack>
            ))}
          </HStack>

          {/* Bottom row */}
          <HStack className="space-x-3">
            {quickActions.slice(2, 4).map(action => (
              <VStack key={action.id} className="flex-1">
                <Pressable
                  className={`
                    bg-gray-50 rounded-lg p-4 border border-gray-200 w-full
                    ${action.disabled ? 'opacity-50' : 'active:bg-gray-100'}
                  `}
                  onPress={action.onPress}
                  disabled={action.disabled}
                >
                  <VStack className="items-center space-y-3">
                    <VStack
                      className={`
                        items-center justify-center w-12 h-12 rounded-full
                        ${action.iconBgColor}
                      `}
                    >
                      <Icon as={action.icon} size={24} className={action.iconColor} />
                    </VStack>

                    <VStack className="items-center space-y-1">
                      <Text className="text-sm font-medium text-gray-900 text-center">
                        {action.title}
                      </Text>
                      <Text className="text-xs text-gray-600 text-center">{action.subtitle}</Text>
                    </VStack>
                  </VStack>
                </Pressable>
              </VStack>
            ))}
          </HStack>
        </VStack>

        {/* Secondary Actions */}
        <HStack className="justify-between items-center pt-4 border-t border-gray-100">
          {secondaryActions.map(action => (
            <Button
              key={action.id}
              variant="ghost"
              size="sm"
              onPress={action.onPress}
              className="flex-1 mx-1"
            >
              <ButtonIcon as={action.icon} size={16} />
              <ButtonText className="ml-1 text-xs">{action.title}</ButtonText>
            </Button>
          ))}
        </HStack>

        {/* Summary Info */}
        <VStack className="mt-4 pt-4 border-t border-gray-100">
          <HStack className="justify-between items-center">
            <Text className="text-sm text-gray-600">Family Status</Text>
            <HStack className="items-center space-x-4">
              <HStack className="items-center space-x-1">
                <Icon as={Users} size={14} className="text-gray-500" />
                <Text className="text-sm text-gray-700">{childrenCount} children</Text>
              </HStack>

              {pendingApprovalsCount > 0 && (
                <HStack className="items-center space-x-1">
                  <Icon as={Bell} size={14} className="text-orange-500" />
                  <Text className="text-sm text-orange-700">{pendingApprovalsCount} pending</Text>
                </HStack>
              )}
            </HStack>
          </HStack>
        </VStack>
      </CardContent>
    </Card>
  );
};
