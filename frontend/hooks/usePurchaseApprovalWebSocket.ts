/**
 * Purchase Approval WebSocket Hook
 *
 * Real-time WebSocket integration for purchase approval notifications:
 * - New approval requests from children
 * - Request status changes (approved/rejected)
 * - Budget threshold alerts
 * - Auto-approval notifications
 */

import { useEffect, useState, useCallback } from 'react';

import { useWebSocket } from './useWebSocket';

import { PurchaseApprovalRequest } from '@/api/parentApi';

export interface PurchaseApprovalNotification {
  id: string;
  type:
    | 'new_request'
    | 'request_approved'
    | 'request_rejected'
    | 'request_expired'
    | 'budget_alert'
    | 'auto_approved';
  timestamp: string;
  title: string;
  message: string;
  data: {
    request_id?: number;
    child_name?: string;
    amount?: string;
    plan_name?: string;
    budget_type?: 'monthly' | 'weekly' | 'daily';
    budget_percentage?: number;
    approval_request?: PurchaseApprovalRequest;
  };
  priority: 'low' | 'medium' | 'high' | 'urgent';
  read: boolean;
  actionable: boolean;
}

interface UsePurchaseApprovalWebSocketProps {
  parentId?: string;
  onNewRequest?: (notification: PurchaseApprovalNotification) => void;
  onRequestStatusChange?: (notification: PurchaseApprovalNotification) => void;
  onBudgetAlert?: (notification: PurchaseApprovalNotification) => void;
  onAutoApproval?: (notification: PurchaseApprovalNotification) => void;
  enablePushNotifications?: boolean;
}

interface UsePurchaseApprovalWebSocketResult {
  isConnected: boolean;
  notifications: PurchaseApprovalNotification[];
  unreadCount: number;
  markAsRead: (notificationId: string) => void;
  markAllAsRead: () => void;
  clearNotification: (notificationId: string) => void;
  clearAllNotifications: () => void;
  sendAcknowledgment: (requestId: string, action: 'received' | 'viewed') => void;
}

export const usePurchaseApprovalWebSocket = ({
  parentId,
  onNewRequest,
  onRequestStatusChange,
  onBudgetAlert,
  onAutoApproval,
  enablePushNotifications = true,
}: UsePurchaseApprovalWebSocketProps): UsePurchaseApprovalWebSocketResult => {
  const [notifications, setNotifications] = useState<PurchaseApprovalNotification[]>([]);

  // Build WebSocket URL for purchase approvals
  const wsUrl = parentId
    ? `${process.env.EXPO_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/parent/${parentId}/approvals/`
    : null;

  // Handle WebSocket messages
  const handleMessage = useCallback(
    (message: any) => {
      try {
        const data = typeof message === 'string' ? JSON.parse(message) : message;

        if (data.type === 'purchase_approval_notification') {
          const notification: PurchaseApprovalNotification = {
            id: data.notification_id || `notif_${Date.now()}`,
            type: data.notification_type,
            timestamp: data.timestamp || new Date().toISOString(),
            title: data.title,
            message: data.message,
            data: data.data || {},
            priority: data.priority || 'medium',
            read: false,
            actionable: data.actionable || false,
          };

          // Add notification to state
          setNotifications(prev => [notification, ...prev.slice(0, 49)]); // Keep max 50 notifications

          // Trigger appropriate callback
          switch (notification.type) {
            case 'new_request':
              onNewRequest?.(notification);
              break;
            case 'request_approved':
            case 'request_rejected':
            case 'request_expired':
              onRequestStatusChange?.(notification);
              break;
            case 'budget_alert':
              onBudgetAlert?.(notification);
              break;
            case 'auto_approved':
              onAutoApproval?.(notification);
              break;
          }

          // Show push notification if enabled
          if (
            enablePushNotifications &&
            'Notification' in window &&
            Notification.permission === 'granted'
          ) {
            const pushNotification = new Notification(notification.title, {
              body: notification.message,
              icon: '/icon.png',
              badge: '/badge.png',
              tag: `approval_${notification.id}`,
              requireInteraction: notification.priority === 'urgent',
              data: {
                notificationId: notification.id,
                requestId: notification.data.request_id,
              },
            });

            pushNotification.onclick = () => {
              // Focus window and mark as read
              window.focus();
              markAsRead(notification.id);
              pushNotification.close();
            };

            // Auto-close non-urgent notifications
            if (notification.priority !== 'urgent') {
              setTimeout(() => pushNotification.close(), 5000);
            }
          }
        }
      } catch (error) {
        console.error('Error processing purchase approval notification:', error);
      }
    },
    [onNewRequest, onRequestStatusChange, onBudgetAlert, onAutoApproval, enablePushNotifications],
  );

  // Initialize WebSocket connection
  const { isConnected, sendMessage } = useWebSocket({
    url: wsUrl || '',
    channelName: 'purchase_approvals',
    onMessage: handleMessage,
    shouldConnect: !!parentId && !!wsUrl,
  });

  // Request push notification permission on mount
  useEffect(() => {
    if (
      enablePushNotifications &&
      'Notification' in window &&
      Notification.permission === 'default'
    ) {
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          if (__DEV__) {
            console.log('Push notifications enabled for purchase approvals');
          }
        }
      });
    }
  }, [enablePushNotifications]);

  // Mark notification as read
  const markAsRead = useCallback((notificationId: string) => {
    setNotifications(prev =>
      prev.map(notification =>
        notification.id === notificationId ? { ...notification, read: true } : notification,
      ),
    );
  }, []);

  // Mark all notifications as read
  const markAllAsRead = useCallback(() => {
    setNotifications(prev => prev.map(notification => ({ ...notification, read: true })));
  }, []);

  // Clear specific notification
  const clearNotification = useCallback((notificationId: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== notificationId));
  }, []);

  // Clear all notifications
  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // Send acknowledgment to server
  const sendAcknowledgment = useCallback(
    (requestId: string, action: 'received' | 'viewed') => {
      if (isConnected) {
        sendMessage({
          type: 'purchase_approval_ack',
          request_id: requestId,
          action,
          timestamp: new Date().toISOString(),
        });
      }
    },
    [isConnected, sendMessage],
  );

  // Calculate unread count
  const unreadCount = notifications.filter(n => !n.read).length;

  return {
    isConnected,
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    clearNotification,
    clearAllNotifications,
    sendAcknowledgment,
  };
};

/**
 * Hook for managing purchase approval notification preferences
 */
export const usePurchaseApprovalPreferences = () => {
  const [preferences, setPreferences] = useState({
    enablePushNotifications: true,
    enableEmailNotifications: true,
    enableSMSNotifications: false,
    notificationTypes: {
      new_request: true,
      budget_alerts: true,
      auto_approvals: true,
      status_changes: false,
    },
    quietHours: {
      enabled: false,
      start: '22:00',
      end: '08:00',
    },
    priorityFiltering: {
      showLowPriority: true,
      showMediumPriority: true,
      showHighPriority: true,
      showUrgentPriority: true,
    },
  });

  const updatePreferences = useCallback((updates: Partial<typeof preferences>) => {
    setPreferences(prev => ({ ...prev, ...updates }));
  }, []);

  return {
    preferences,
    updatePreferences,
  };
};

export default usePurchaseApprovalWebSocket;
