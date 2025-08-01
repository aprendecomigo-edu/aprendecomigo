/**
 * Notification System Component
 * 
 * Handles real-time notifications for low balance alerts, renewal prompts,
 * and other important student account notifications.
 */

import React, { useState, useEffect } from 'react';
import { 
  Bell, 
  AlertTriangle, 
  CreditCard, 
  TrendingDown, 
  X, 
  Settings,
  Clock,
  Package,
  CheckCircle
} from 'lucide-react-native';

import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { 
  Modal, 
  ModalBackdrop, 
  ModalBody, 
  ModalCloseButton, 
  ModalContent, 
  ModalFooter, 
  ModalHeader 
} from '@/components/ui/modal';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useAnalytics } from '@/hooks/useAnalytics';
import useRouter from '@unitools/router';

interface Notification {
  id: string;
  type: 'low_balance' | 'renewal_prompt' | 'package_expiry' | 'session_reminder' | 'insight';
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  timestamp: Date;
  isRead: boolean;
  actionLabel?: string;
  actionUrl?: string;
}

interface NotificationSystemProps {
  email?: string;
  className?: string;
}

/**
 * Get notification styling based on type and priority
 */
function getNotificationStyle(type: Notification['type'], priority: Notification['priority']) {
  const baseClasses = "border-l-4";
  
  switch (priority) {
    case 'urgent':
      return {
        containerClass: `${baseClasses} border-l-error-500 bg-error-50`,
        iconColor: 'text-error-600',
        titleColor: 'text-error-900',
        icon: AlertTriangle,
      };
    case 'high':
      return {
        containerClass: `${baseClasses} border-l-warning-500 bg-warning-50`,
        iconColor: 'text-warning-600',
        titleColor: 'text-warning-900',
        icon: type === 'low_balance' ? TrendingDown : AlertTriangle,
      };
    case 'medium':
      return {
        containerClass: `${baseClasses} border-l-primary-500 bg-primary-50`,
        iconColor: 'text-primary-600',
        titleColor: 'text-primary-900',
        icon: type === 'renewal_prompt' ? CreditCard : type === 'package_expiry' ? Package : Bell,
      };
    default:
      return {
        containerClass: `${baseClasses} border-l-typography-300 bg-background-50`,
        iconColor: 'text-typography-600',
        titleColor: 'text-typography-900',
        icon: Bell,
      };
  }
}

/**
 * Individual notification item component
 */
function NotificationItem({ 
  notification, 
  onDismiss, 
  onAction 
}: { 
  notification: Notification;
  onDismiss: (id: string) => void;
  onAction: (notification: Notification) => void;
}) {
  const style = getNotificationStyle(notification.type, notification.priority);

  return (
    <Card className={`p-4 ${style.containerClass}`}>
      <VStack space="sm">
        <HStack className="items-start justify-between">
          <HStack space="sm" className="items-start flex-1">
            <Icon as={style.icon} size="sm" className={style.iconColor} />
            <VStack space="xs" className="flex-1">
              <HStack space="xs" className="items-center flex-wrap">
                <Text className={`font-medium ${style.titleColor}`}>
                  {notification.title}
                </Text>
                {!notification.isRead && (
                  <Badge variant="solid" action="primary" size="xs">
                    <Text className="text-xs">New</Text>
                  </Badge>
                )}
              </HStack>
              <Text className="text-sm text-typography-700">
                {notification.message}
              </Text>
              {notification.actionLabel && (
                <Button
                  action={notification.priority === 'urgent' ? 'negative' : 'primary'}
                  variant="solid"
                  size="sm"
                  onPress={() => onAction(notification)}
                  className="self-start mt-2"
                >
                  <ButtonText>{notification.actionLabel}</ButtonText>
                </Button>
              )}
            </VStack>
          </HStack>

          <Pressable
            onPress={() => onDismiss(notification.id)}
            className="p-1 rounded-full hover:bg-white/50 active:bg-white/75"
          >
            <Icon as={X} size="xs" className="text-typography-400" />
          </Pressable>
        </HStack>

        <HStack className="items-center justify-between">
          <Text className="text-xs text-typography-500">
            {notification.timestamp.toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </Text>

          <Badge 
            variant="outline" 
            action={notification.priority === 'urgent' ? 'error' : 
                   notification.priority === 'high' ? 'warning' :
                   notification.priority === 'medium' ? 'primary' : 'secondary'} 
            size="xs"
          >
            <Text className="text-xs capitalize">
              {notification.priority}
            </Text>
          </Badge>
        </HStack>
      </VStack>
    </Card>
  );
}

/**
 * Notification preferences modal
 */
function NotificationPreferencesModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const { preferences, updatePreferences, preferencesUpdating } = useAnalytics();

  const handlePreferenceChange = async (key: string, value: boolean) => {
    if (!preferences) return;
    
    try {
      await updatePreferences({ [key]: value });
    } catch (error) {
      console.error('Failed to update preferences:', error);
    }
  };

  if (!preferences) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md">
      <ModalBackdrop />
      <ModalContent className="max-w-md mx-auto">
        <ModalHeader>
          <VStack space="xs">
            <HStack space="sm" className="items-center">
              <Icon as={Settings} size="sm" className="text-typography-600" />
              <Heading size="md">Notification Preferences</Heading>
            </HStack>
            <Text className="text-sm text-typography-600">
              Choose which notifications you'd like to receive
            </Text>
          </VStack>
          <ModalCloseButton />
        </ModalHeader>

        <ModalBody>
          <VStack space="md">
            <VStack space="sm">
              <Text className="text-sm font-medium text-typography-800">
                Balance & Payment Alerts
              </Text>
              
              <HStack className="items-center justify-between">
                <VStack space="xs" className="flex-1">
                  <Text className="text-sm text-typography-700">
                    Low Balance Alerts
                  </Text>
                  <Text className="text-xs text-typography-600">
                    Get notified when your tutoring hours are running low
                  </Text>
                </VStack>
                <Switch
                  size="sm"
                  isChecked={preferences.low_balance_alerts}
                  onToggle={(checked) => handlePreferenceChange('low_balance_alerts', checked)}
                  disabled={preferencesUpdating}
                />
              </HStack>

              <HStack className="items-center justify-between">
                <VStack space="xs" className="flex-1">
                  <Text className="text-sm text-typography-700">
                    Package Expiration
                  </Text>
                  <Text className="text-xs text-typography-600">
                    Get alerted before your hour packages expire
                  </Text>
                </VStack>
                <Switch
                  size="sm"
                  isChecked={preferences.package_expiration}
                  onToggle={(checked) => handlePreferenceChange('package_expiration', checked)}
                  disabled={preferencesUpdating}
                />
              </HStack>

              <HStack className="items-center justify-between">
                <VStack space="xs" className="flex-1">
                  <Text className="text-sm text-typography-700">
                    Renewal Prompts
                  </Text>
                  <Text className="text-xs text-typography-600">
                    Smart reminders to purchase more hours
                  </Text>
                </VStack>
                <Switch
                  size="sm"
                  isChecked={preferences.renewal_prompts}
                  onToggle={(checked) => handlePreferenceChange('renewal_prompts', checked)}
                  disabled={preferencesUpdating}
                />
              </HStack>
            </VStack>

            <VStack space="sm">
              <Text className="text-sm font-medium text-typography-800">
                Learning & Sessions
              </Text>

              <HStack className="items-center justify-between">
                <VStack space="xs" className="flex-1">
                  <Text className="text-sm text-typography-700">
                    Session Reminders
                  </Text>
                  <Text className="text-xs text-typography-600">
                    Reminders about upcoming tutoring sessions
                  </Text>
                </VStack>
                <Switch
                  size="sm"
                  isChecked={preferences.session_reminders}
                  onToggle={(checked) => handlePreferenceChange('session_reminders', checked)}
                  disabled={preferencesUpdating}
                />
              </HStack>

              <HStack className="items-center justify-between">
                <VStack space="xs" className="flex-1">
                  <Text className="text-sm text-typography-700">
                    Learning Insights
                  </Text>
                  <Text className="text-xs text-typography-600">
                    Personalized insights about your learning progress
                  </Text>
                </VStack>
                <Switch
                  size="sm"
                  isChecked={preferences.learning_insights}
                  onToggle={(checked) => handlePreferenceChange('learning_insights', checked)}
                  disabled={preferencesUpdating}
                />
              </HStack>

              <HStack className="items-center justify-between">
                <VStack space="xs" className="flex-1">
                  <Text className="text-sm text-typography-700">
                    Weekly Reports
                  </Text>
                  <Text className="text-xs text-typography-600">
                    Weekly summaries of your learning activity
                  </Text>
                </VStack>
                <Switch
                  size="sm"
                  isChecked={preferences.weekly_reports}
                  onToggle={(checked) => handlePreferenceChange('weekly_reports', checked)}
                  disabled={preferencesUpdating}
                />
              </HStack>
            </VStack>

            <VStack space="sm">
              <Text className="text-sm font-medium text-typography-800">
                Delivery Methods
              </Text>

              <HStack className="items-center justify-between">
                <VStack space="xs" className="flex-1">
                  <Text className="text-sm text-typography-700">
                    In-App Notifications
                  </Text>
                  <Text className="text-xs text-typography-600">
                    Show notifications within the app
                  </Text>
                </VStack>
                <Switch
                  size="sm"
                  isChecked={preferences.in_app_notifications}
                  onToggle={(checked) => handlePreferenceChange('in_app_notifications', checked)}
                  disabled={preferencesUpdating}
                />
              </HStack>

              <HStack className="items-center justify-between">
                <VStack space="xs" className="flex-1">
                  <Text className="text-sm text-typography-700">
                    Email Notifications
                  </Text>
                  <Text className="text-xs text-typography-600">
                    Send notifications to your email address
                  </Text>
                </VStack>
                <Switch
                  size="sm"
                  isChecked={preferences.email_notifications}
                  onToggle={(checked) => handlePreferenceChange('email_notifications', checked)}
                  disabled={preferencesUpdating}
                />
              </HStack>
            </VStack>
          </VStack>
        </ModalBody>

        <ModalFooter>
          <Button
            action="primary"
            variant="solid"
            size="md"
            onPress={onClose}
            className="w-full"
          >
            <ButtonIcon as={CheckCircle} />
            <ButtonText>Save Preferences</ButtonText>
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}

/**
 * Notification System Component
 */
export function NotificationSystem({ 
  email, 
  className = '' 
}: NotificationSystemProps) {
  const router = useRouter();
  const { hasLowBalance, shouldShowRenewalPrompt, preferences } = useAnalytics(email);
  
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showPreferences, setShowPreferences] = useState(false);

  // Generate smart notifications based on analytics data
  useEffect(() => {
    const generateNotifications = () => {
      const newNotifications: Notification[] = [];

      // Low balance notification
      if (hasLowBalance && preferences?.low_balance_alerts) {
        newNotifications.push({
          id: 'low-balance',
          type: 'low_balance',
          title: 'Low Balance Alert',
          message: 'Your tutoring hours are running low. Consider purchasing more hours to continue your learning.',
          priority: 'high',
          timestamp: new Date(),
          isRead: false,
          actionLabel: 'Purchase Hours',
          actionUrl: '/purchase',
        });
      }

      // Renewal prompt notification
      if (shouldShowRenewalPrompt && preferences?.renewal_prompts) {
        newNotifications.push({
          id: 'renewal-prompt',
          type: 'renewal_prompt',
          title: 'Time to Renew',
          message: 'Based on your usage patterns, you might want to purchase additional tutoring hours.',
          priority: 'medium',
          timestamp: new Date(),
          isRead: false,
          actionLabel: 'View Plans',
          actionUrl: '/purchase',
        });
      }

      // Only update if notifications changed
      setNotifications(prev => {
        const existingIds = prev.map(n => n.id);
        const newIds = newNotifications.map(n => n.id);
        
        if (JSON.stringify(existingIds.sort()) !== JSON.stringify(newIds.sort())) {
          return newNotifications;
        }
        return prev;
      });
    };

    if (preferences) {
      generateNotifications();
    }
  }, [hasLowBalance, shouldShowRenewalPrompt, preferences]);

  const handleDismissNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const handleNotificationAction = (notification: Notification) => {
    if (notification.actionUrl) {
      router.push(notification.actionUrl);
    }
    handleDismissNotification(notification.id);
  };

  const unreadCount = notifications.filter(n => !n.isRead).length;

  if (!preferences?.in_app_notifications || notifications.length === 0) {
    return null;
  }

  return (
    <>
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
                {unreadCount > 0 && (
                  <Badge variant="solid" action="error" size="sm">
                    <Text className="text-xs">{unreadCount}</Text>
                  </Badge>
                )}
              </HStack>
              <Text className="text-sm text-typography-600">
                Important updates about your account and learning
              </Text>
            </VStack>

            <Button
              action="secondary"
              variant="outline"
              size="sm"
              onPress={() => setShowPreferences(true)}
            >
              <ButtonIcon as={Settings} />
              <ButtonText>Settings</ButtonText>
            </Button>
          </HStack>

          {/* Notifications List */}
          <VStack space="md">
            {notifications.map((notification) => (
              <NotificationItem
                key={notification.id}
                notification={notification}
                onDismiss={handleDismissNotification}
                onAction={handleNotificationAction}
              />
            ))}
          </VStack>
        </VStack>
      </Card>

      {/* Preferences Modal */}
      <NotificationPreferencesModal
        isOpen={showPreferences}
        onClose={() => setShowPreferences(false)}
      />
    </>
  );
}