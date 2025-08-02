/**
 * Balance Alert Provider
 * 
 * React Context provider for app-wide balance monitoring and notification management.
 * Handles real-time balance updates, notification state, and alert preferences.
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { NotificationApiClient } from '@/api/notificationApi';
import { useStudentBalance } from '@/hooks/useStudentBalance';
import { useAuth } from '@/api/authContext';
import { useToast } from '@/components/ui/toast';
import { useBalanceUpdates } from '@/hooks/useBalanceWebSocket';
import { getBalanceStatus } from './BalanceStatusBar';
import type { 
  BalanceAlertContextType, 
  BalanceAlertState, 
  BalanceAlertActions,
  NotificationResponse,
  NotificationSettings,
  ToastNotificationData
} from '@/types/notification';

const BalanceAlertContext = createContext<BalanceAlertContextType | undefined>(undefined);

interface BalanceAlertProviderProps {
  children: React.ReactNode;
  /** Polling interval in milliseconds (default: 30 seconds) */
  pollingInterval?: number;
  /** Enable automatic balance monitoring */
  enableMonitoring?: boolean;
}

const DEFAULT_SETTINGS: NotificationSettings = {
  low_balance_alerts: true,
  package_expiration: true,
  renewal_prompts: true,
  session_reminders: true,
  learning_insights: false,
  weekly_reports: false,
  in_app_notifications: true,
  email_notifications: true,
};

/**
 * BalanceAlertProvider Component
 */
export function BalanceAlertProvider({
  children,
  pollingInterval = 30000, // 30 seconds
  enableMonitoring = true,
}: BalanceAlertProviderProps) {
  const { userProfile } = useAuth();
  const { balance, loading: balanceLoading, error: balanceError, refetch: refetchBalance } = useStudentBalance();
  const { showToast } = useToast();
  
  // State management (moved before hooks that depend on it)
  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastBalanceCheck, setLastBalanceCheck] = useState<Date | null>(null);
  
  // Refs for polling and toast management
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastNotificationCheckRef = useRef<string | null>(null);
  const activeToastsRef = useRef<Set<string>>(new Set());
  
  /**
   * Show a balance-related toast notification
   */
  const showBalanceToast = useCallback((data: ToastNotificationData) => {
    if (!settings?.in_app_notifications) return;

    const toastType = data.type === 'low_balance' || data.type === 'balance_depleted' 
      ? 'error' 
      : data.type === 'package_expiring' 
      ? 'error' 
      : 'success';

    showToast(toastType, `${data.title}: ${data.message}`, data.duration);
    
    // Remove from active toasts after duration
    setTimeout(() => {
      activeToastsRef.current.delete(data.id);
    }, data.duration || 5000);
  }, [settings, showToast]);
  
  // WebSocket integration for real-time updates
  const { connected: wsConnected, latestBalance: wsBalance, latestNotification: wsNotification } = useBalanceUpdates(
    // Handle balance updates from WebSocket
    useCallback((newBalance) => {
      console.log('Received real-time balance update:', newBalance);
      // The useStudentBalance hook will be updated automatically through WebSocket
    }, []),
    
    // Handle notifications from WebSocket
    useCallback((notification) => {
      console.log('Received real-time notification:', notification);
      setNotifications(prev => [notification, ...prev]);
      setUnreadCount(prev => prev + 1);
      
      // Show toast for high-priority notifications
      if (
        settings?.in_app_notifications &&
        (notification.priority === 'high' || notification.priority === 'urgent')
      ) {
        const toastId = `ws-notification-${notification.id}`;
        
        if (!activeToastsRef.current.has(toastId)) {
          activeToastsRef.current.add(toastId);
          
          const toastData: ToastNotificationData = {
            id: toastId,
            type: notification.notification_type as any,
            title: notification.title,
            message: notification.message,
            priority: notification.priority,
            duration: notification.priority === 'urgent' ? 8000 : 5000,
            actionLabel: getActionLabel(notification.notification_type),
            actionUrl: getActionUrl(notification.notification_type),
          };

          showBalanceToast(toastData);
        }
      }
    }, [settings, showBalanceToast])
  );

  // Calculate balance status
  const balanceStatus = balance ? getBalanceStatus(
    parseFloat(balance.balance_summary.remaining_hours),
    parseFloat(balance.balance_summary.hours_purchased)
  ) : null;

  const state: BalanceAlertState = {
    currentBalance: balance ? parseFloat(balance.balance_summary.remaining_hours) : 0,
    totalHours: balance ? parseFloat(balance.balance_summary.hours_purchased) : 0,
    isLowBalance: balanceStatus ? ['low', 'critical'].includes(balanceStatus.level) : false,
    isCriticalBalance: balanceStatus ? balanceStatus.level === 'critical' : false,
    daysUntilExpiry: balance?.upcoming_expirations[0]?.days_until_expiry || null,
    lastBalanceCheck,
    notifications,
    unreadCount,
    wsConnected, // Add WebSocket connection status
  };

  /**
   * Fetch notifications from the API
   */
  const fetchNotifications = useCallback(async () => {
    if (!userProfile) return;

    try {
      setLoading(true);
      setError(null);

      const [notificationsResponse, unreadResponse] = await Promise.all([
        NotificationApiClient.getNotifications({ is_read: false }, 1, 50),
        NotificationApiClient.getUnreadCount(),
      ]);

      setNotifications(notificationsResponse.results);
      setUnreadCount(unreadResponse.unread_count);
      lastNotificationCheckRef.current = new Date().toISOString();
    } catch (err: any) {
      console.error('Failed to fetch notifications:', err);
      setError(err.message || 'Failed to load notifications');
    } finally {
      setLoading(false);
    }
  }, [userProfile]);

  /**
   * Check for new notifications and show toasts if needed
   */
  const checkForNewNotifications = useCallback(async () => {
    if (!userProfile || !settings?.in_app_notifications) return;

    try {
      const response = await NotificationApiClient.pollNotifications(
        lastNotificationCheckRef.current || undefined,
        { is_read: false }
      );

      // Show toasts for new high-priority notifications
      response.results.forEach((notification) => {
        if (
          notification.priority === 'high' || 
          notification.priority === 'urgent'
        ) {
          const toastId = `notification-${notification.id}`;
          
          // Avoid showing duplicate toasts
          if (!activeToastsRef.current.has(toastId)) {
            activeToastsRef.current.add(toastId);
            
            const toastData: ToastNotificationData = {
              id: toastId,
              type: notification.notification_type as any,
              title: notification.title,
              message: notification.message,
              priority: notification.priority,
              duration: notification.priority === 'urgent' ? 8000 : 5000,
              actionLabel: getActionLabel(notification.notification_type),
              actionUrl: getActionUrl(notification.notification_type),
            };

            showBalanceToast(toastData);
          }
        }
      });

      // Update notifications list
      if (response.results.length > 0) {
        setNotifications(prev => [...response.results, ...prev]);
        setUnreadCount(prev => prev + response.results.length);
      }

      lastNotificationCheckRef.current = new Date().toISOString();
    } catch (err) {
      console.error('Failed to check for new notifications:', err);
    }
  }, [userProfile, settings, showToast]);

  /**
   * Check balance and trigger notifications if needed
   */
  const checkBalance = useCallback(async () => {
    await refetchBalance();
    await fetchNotifications();
    setLastBalanceCheck(new Date());
  }, [refetchBalance, fetchNotifications]);

  /**
   * Mark a notification as read
   */
  const markNotificationAsRead = useCallback(async (id: number) => {
    try {
      await NotificationApiClient.markNotificationAsRead(id);
      
      setNotifications(prev => 
        prev.map(n => n.id === id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err: any) {
      console.error('Failed to mark notification as read:', err);
      setError(err.message || 'Failed to update notification');
    }
  }, []);

  /**
   * Mark all notifications as read
   */
  const markAllAsRead = useCallback(async () => {
    try {
      await NotificationApiClient.markAllAsRead();
      
      setNotifications(prev => 
        prev.map(n => ({ ...n, is_read: true, read_at: new Date().toISOString() }))
      );
      setUnreadCount(0);
    } catch (err: any) {
      console.error('Failed to mark all notifications as read:', err);
      setError(err.message || 'Failed to update notifications');
    }
  }, []);

  /**
   * Dismiss a toast notification
   */
  const dismissToast = useCallback((id: string) => {
    activeToastsRef.current.delete(id);
  }, []);

  /**
   * Update notification settings
   */
  const updateSettings = useCallback(async (newSettings: Partial<NotificationSettings>) => {
    setSettings(prev => ({ ...DEFAULT_SETTINGS, ...prev, ...newSettings }));
    // In a real implementation, you would persist these to the backend
  }, []);

  const actions: BalanceAlertActions = {
    checkBalance,
    markNotificationAsRead,
    markAllAsRead,
    dismissToast,
    showToast: showBalanceToast,
    updateSettings,
  };

  // Initialize settings on mount
  useEffect(() => {
    setSettings(DEFAULT_SETTINGS);
  }, []);

  // Initial data fetch
  useEffect(() => {
    if (userProfile && settings) {
      fetchNotifications();
    }
  }, [userProfile, settings, fetchNotifications]);

  // Set up polling for new notifications
  useEffect(() => {
    if (!enableMonitoring || !userProfile || !settings?.in_app_notifications) {
      return;
    }

    pollingIntervalRef.current = setInterval(() => {
      checkForNewNotifications();
    }, pollingInterval);

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [enableMonitoring, userProfile, settings, pollingInterval, checkForNewNotifications]);

  // Monitor balance changes and trigger alerts
  useEffect(() => {
    if (!balance || !settings) return;

    const remainingHours = parseFloat(balance.balance_summary.remaining_hours);
    const status = getBalanceStatus(remainingHours, parseFloat(balance.balance_summary.hours_purchased));

    // Show toast for critical balance
    if (
      status.level === 'critical' && 
      settings.low_balance_alerts && 
      !activeToastsRef.current.has('critical-balance-alert')
    ) {
      const toastData: ToastNotificationData = {
        id: 'critical-balance-alert',
        type: 'low_balance',
        title: 'Critical Balance Alert',
        message: `Only ${remainingHours.toFixed(1)} hours remaining`,
        priority: 'urgent',
        duration: 8000,
        actionLabel: 'Purchase Hours',
        actionUrl: '/purchase',
      };

      showBalanceToast(toastData);
    }
  }, [balance, settings, showBalanceToast]);

  const contextValue: BalanceAlertContextType = {
    state,
    actions,
    settings,
    loading: loading || balanceLoading,
    error: error || balanceError,
  };

  return (
    <BalanceAlertContext.Provider value={contextValue}>
      {children}
    </BalanceAlertContext.Provider>
  );
}

/**
 * Hook to use the BalanceAlert context
 */
export function useBalanceAlert(): BalanceAlertContextType {
  const context = useContext(BalanceAlertContext);
  if (context === undefined) {
    throw new Error('useBalanceAlert must be used within a BalanceAlertProvider');
  }
  return context;
}

/**
 * Helper functions
 */
function getActionLabel(notificationType: string): string {
  switch (notificationType) {
    case 'low_balance':
    case 'balance_depleted':
      return 'Purchase Hours';
    case 'package_expiring':
      return 'Renew Package';
    case 'renewal_prompt':
      return 'View Plans';
    default:
      return 'View Details';
  }
}

function getActionUrl(notificationType: string): string {
  switch (notificationType) {
    case 'low_balance':
    case 'balance_depleted':
    case 'package_expiring':
    case 'renewal_prompt':
      return '/purchase';
    default:
      return '/student/dashboard';
  }
}