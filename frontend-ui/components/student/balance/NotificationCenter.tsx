/**
 * Notification Center Component
 * 
 * Centralized view for all balance-related notifications with filtering,
 * read/unread status management, and action buttons.
 */

import React, { useState, useEffect } from 'react';
import { 
  Bell, 
  AlertTriangle, 
  Clock, 
  Package, 
  CreditCard, 
  CheckCircle, 
  X, 
  Settings,
  Filter,
  RefreshCw,
  Trash2,
  ExternalLink
} from 'lucide-react-native';
import useRouter from '@unitools/router';

import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Select, SelectTrigger, SelectInput, SelectIcon, SelectPortal, SelectBackdrop, SelectContent, SelectDragIndicatorWrapper, SelectDragIndicator, SelectItem } from '@/components/ui/select';
import { Spinner } from '@/components/ui/spinner';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { NotificationBadge, NotificationDot } from '@/components/ui/notification-badge';
import { useBalanceAlert } from './BalanceAlertProvider';
import type { NotificationResponse, NotificationType, NotificationPriority } from '@/types/notification';

interface NotificationCenterProps {
  /** Show settings panel */
  showSettings?: boolean;
  /** Show filters */
  showFilters?: boolean;
  /** Maximum number of notifications to display */
  maxNotifications?: number;
  /** Custom className */
  className?: string;
}

interface NotificationFilters {
  type: NotificationType | 'all';
  status: 'all' | 'unread' | 'read';
  priority: NotificationPriority | 'all';
}

/**
 * Get notification icon based on type
 */
function getNotificationIcon(type: NotificationType) {
  switch (type) {
    case 'low_balance':
    case 'balance_depleted':
      return AlertTriangle;
    case 'package_expiring':
      return Clock;
    case 'renewal_prompt':
      return CreditCard;
    case 'session_reminder':
      return Package;
    case 'learning_insight':
      return CheckCircle;
    default:
      return Bell;
  }
}

/**
 * Get notification styling based on priority
 */
function getNotificationStyle(priority: NotificationPriority) {
  switch (priority) {
    case 'urgent':
      return {
        containerClass: 'border-l-4 border-l-error-500 bg-error-50',
        iconColor: 'text-error-600',
        titleColor: 'text-error-900',
        badgeAction: 'error' as const,
      };
    case 'high':
      return {
        containerClass: 'border-l-4 border-l-warning-500 bg-warning-50',
        iconColor: 'text-warning-600',
        titleColor: 'text-warning-900',
        badgeAction: 'warning' as const,
      };
    case 'medium':
      return {
        containerClass: 'border-l-4 border-l-primary-500 bg-primary-50',
        iconColor: 'text-primary-600',
        titleColor: 'text-primary-900',
        badgeAction: 'primary' as const,
      };
    default:
      return {
        containerClass: 'border-l-4 border-l-typography-300 bg-background-50',
        iconColor: 'text-typography-600',
        titleColor: 'text-typography-900',
        badgeAction: 'secondary' as const,
      };
  }
}

/**
 * Individual notification item component
 */
function NotificationItem({ 
  notification, 
  onMarkAsRead, 
  onAction 
}: { 
  notification: NotificationResponse;
  onMarkAsRead: (id: number) => void;
  onAction: (notification: NotificationResponse) => void;
}) {
  const style = getNotificationStyle(notification.priority);
  const IconComponent = getNotificationIcon(notification.notification_type);
  
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Card className={`p-4 ${style.containerClass} ${notification.is_read ? 'opacity-75' : ''}`}>
      <VStack space="sm">
        <HStack className="items-start justify-between">
          <HStack space="sm" className="items-start flex-1">
            <Icon as={IconComponent} size="sm" className={style.iconColor} />
            <VStack space="xs" className="flex-1">
              <HStack space="xs" className="items-center flex-wrap">
                <Text className={`font-medium ${style.titleColor}`}>
                  {notification.title}
                </Text>
                {!notification.is_read && (
                  <NotificationDot type={style.badgeAction} size="sm" />
                )}
              </HStack>
              
              <Text className="text-sm text-typography-700">
                {notification.message}
              </Text>

              {/* Action buttons */}
              <HStack space="sm" className="mt-2">
                <Button
                  action={notification.priority === 'urgent' ? 'negative' : 'primary'}
                  variant="solid"
                  size="sm"
                  onPress={() => onAction(notification)}
                >
                  <ButtonIcon as={ExternalLink} />
                  <ButtonText>
                    {notification.notification_type === 'low_balance' || notification.notification_type === 'balance_depleted' 
                      ? 'Purchase Hours'
                      : notification.notification_type === 'package_expiring'
                      ? 'Renew Package'
                      : 'View Details'
                    }
                  </ButtonText>
                </Button>
                
                {!notification.is_read && (
                  <Button
                    action="secondary"
                    variant="outline"
                    size="sm"
                    onPress={() => onMarkAsRead(notification.id)}
                  >
                    <ButtonIcon as={CheckCircle} />
                    <ButtonText>Mark Read</ButtonText>
                  </Button>
                )}
              </HStack>
            </VStack>
          </HStack>
        </HStack>

        <HStack className="items-center justify-between">
          <Text className="text-xs text-typography-500">
            {formatDate(notification.created_at)}
          </Text>

          <HStack space="sm" className="items-center">
            <Badge 
              variant="outline" 
              action={style.badgeAction}
              size="xs"
            >
              <Text className="text-xs capitalize">
                {notification.priority}
              </Text>
            </Badge>
            
            <Badge 
              variant="outline" 
              action="secondary"
              size="xs"
            >
              <Text className="text-xs">
                {notification.notification_type.replace('_', ' ')}
              </Text>
            </Badge>
          </HStack>
        </HStack>
      </VStack>
    </Card>
  );
}

/**
 * NotificationCenter Component
 */
export function NotificationCenter({
  showSettings = true,
  showFilters = true,
  maxNotifications = 50,
  className = ''
}: NotificationCenterProps) {
  const router = useRouter();
  const { state, actions, settings, loading, error } = useBalanceAlert();
  
  const [filters, setFilters] = useState<NotificationFilters>({
    type: 'all',
    status: 'all',
    priority: 'all',
  });
  const [showSettingsPanel, setShowSettingsPanel] = useState(false);

  // Filter notifications based on current filters
  const filteredNotifications = state.notifications.filter(notification => {
    if (filters.type !== 'all' && notification.notification_type !== filters.type) {
      return false;
    }
    
    if (filters.status === 'unread' && notification.is_read) {
      return false;
    }
    
    if (filters.status === 'read' && !notification.is_read) {
      return false;
    }
    
    if (filters.priority !== 'all' && notification.priority !== filters.priority) {
      return false;
    }
    
    return true;
  }).slice(0, maxNotifications);

  const handleNotificationAction = (notification: NotificationResponse) => {
    // Navigate based on notification type
    switch (notification.notification_type) {
      case 'low_balance':
      case 'balance_depleted':
      case 'package_expiring':
      case 'renewal_prompt':
        router.push('/purchase');
        break;
      default:
        router.push('/student/dashboard');
    }
    
    // Mark as read if not already
    if (!notification.is_read) {
      actions.markNotificationAsRead(notification.id);
    }
  };

  const handleRefresh = async () => {
    await actions.checkBalance();
  };

  if (loading && state.notifications.length === 0) {
    return (
      <Card className={`p-6 ${className}`}>
        <VStack space="md" className="items-center">
          <Spinner size="large" />
          <Text className="text-typography-600">Loading notifications...</Text>
        </VStack>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`p-6 border-error-200 ${className}`}>
        <VStack space="md" className="items-center">
          <Icon as={AlertTriangle} size="xl" className="text-error-500" />
          <VStack space="sm" className="items-center">
            <Heading size="sm" className="text-error-900">
              Unable to Load Notifications
            </Heading>
            <Text className="text-error-700 text-sm text-center">
              {error}
            </Text>
          </VStack>
          <Button
            action="secondary"
            variant="outline"
            size="sm"
            onPress={handleRefresh}
          >
            <ButtonIcon as={RefreshCw} />
            <ButtonText>Try Again</ButtonText>
          </Button>
        </VStack>
      </Card>
    );
  }

  return (
    <Card className={`p-4 ${className}`}>
      <VStack space="lg">
        {/* Header */}
        <HStack className="items-center justify-between">
          <VStack space="xs">
            <HStack className="items-center">
              <Icon as={Bell} size="sm" className="text-typography-600 mr-2" />
              <Heading size="md" className="text-typography-900">
                Notifications
              </Heading>
              {state.unreadCount > 0 && (
                <NotificationBadge 
                  count={state.unreadCount} 
                  type="error" 
                  size="sm" 
                />
              )}
            </HStack>
            <Text className="text-sm text-typography-600">
              Balance alerts and important updates
            </Text>
          </VStack>

          <HStack space="sm">
            <Button
              action="secondary"
              variant="outline"
              size="sm"
              onPress={handleRefresh}
              disabled={loading}
            >
              <ButtonIcon as={RefreshCw} />
            </Button>
            
            {showSettings && (
              <Button
                action="secondary"
                variant="outline"
                size="sm"
                onPress={() => setShowSettingsPanel(!showSettingsPanel)}
              >
                <ButtonIcon as={Settings} />
              </Button>
            )}
          </HStack>
        </HStack>

        {/* Filters */}
        {showFilters && (
          <HStack space="sm" className="flex-wrap">
            <Select
              selectedValue={filters.type}
              onValueChange={(value) => setFilters(prev => ({ ...prev, type: value as NotificationType | 'all' }))}
            >
              <SelectTrigger variant="outline" size="sm" className="min-w-32">
                <SelectInput placeholder="Type" />
                <SelectIcon as={Filter} />
              </SelectTrigger>
              <SelectPortal>
                <SelectBackdrop />
                <SelectContent>
                  <SelectDragIndicatorWrapper>
                    <SelectDragIndicator />
                  </SelectDragIndicatorWrapper>
                  <SelectItem label="All Types" value="all" />
                  <SelectItem label="Low Balance" value="low_balance" />
                  <SelectItem label="Package Expiring" value="package_expiring" />
                  <SelectItem label="Balance Depleted" value="balance_depleted" />
                  <SelectItem label="Renewal Prompt" value="renewal_prompt" />
                </SelectContent>
              </SelectPortal>
            </Select>

            <Select
              selectedValue={filters.status}
              onValueChange={(value) => setFilters(prev => ({ ...prev, status: value as 'all' | 'unread' | 'read' }))}
            >
              <SelectTrigger variant="outline" size="sm" className="min-w-24">
                <SelectInput placeholder="Status" />
                <SelectIcon as={Filter} />
              </SelectTrigger>
              <SelectPortal>
                <SelectBackdrop />
                <SelectContent>
                  <SelectDragIndicatorWrapper>
                    <SelectDragIndicator />
                  </SelectDragIndicatorWrapper>
                  <SelectItem label="All" value="all" />
                  <SelectItem label="Unread" value="unread" />
                  <SelectItem label="Read" value="read" />
                </SelectContent>
              </SelectPortal>
            </Select>

            {state.unreadCount > 0 && (
              <Button
                action="primary"
                variant="outline"
                size="sm"
                onPress={actions.markAllAsRead}
              >
                <ButtonIcon as={CheckCircle} />
                <ButtonText>Mark All Read</ButtonText>
              </Button>
            )}
          </HStack>
        )}

        {/* Settings Panel */}
        {showSettingsPanel && settings && (
          <>
            <Divider />
            <VStack space="sm">
              <Heading size="sm" className="text-typography-800">
                Notification Settings
              </Heading>
              
              <VStack space="sm">
                <HStack className="items-center justify-between">
                  <Text className="text-sm text-typography-700">
                    Low Balance Alerts
                  </Text>
                  <Switch
                    size="sm"
                    isChecked={settings.low_balance_alerts}
                    onToggle={(checked) => actions.updateSettings({ low_balance_alerts: checked })}
                  />
                </HStack>
                
                <HStack className="items-center justify-between">
                  <Text className="text-sm text-typography-700">
                    Package Expiration
                  </Text>
                  <Switch
                    size="sm"
                    isChecked={settings.package_expiration}
                    onToggle={(checked) => actions.updateSettings({ package_expiration: checked })}
                  />
                </HStack>
                
                <HStack className="items-center justify-between">
                  <Text className="text-sm text-typography-700">
                    In-App Notifications
                  </Text>
                  <Switch
                    size="sm"
                    isChecked={settings.in_app_notifications}
                    onToggle={(checked) => actions.updateSettings({ in_app_notifications: checked })}
                  />
                </HStack>
              </VStack>
            </VStack>
          </>
        )}

        {/* Notifications List */}
        <VStack space="md">
          {filteredNotifications.length === 0 ? (
            <VStack space="sm" className="items-center py-8">
              <Icon as={CheckCircle} size="xl" className="text-success-500" />
              <VStack space="xs" className="items-center">
                <Text className="text-typography-600 font-medium">
                  No notifications
                </Text>
                <Text className="text-sm text-typography-500 text-center">
                  {filters.status === 'unread' 
                    ? "You're all caught up! No unread notifications."
                    : "No notifications match your current filters."
                  }
                </Text>
              </VStack>
            </VStack>
          ) : (
            filteredNotifications.map((notification) => (
              <NotificationItem
                key={notification.id}
                notification={notification}
                onMarkAsRead={actions.markNotificationAsRead}
                onAction={handleNotificationAction}
              />
            ))
          )}
        </VStack>
      </VStack>
    </Card>
  );
}