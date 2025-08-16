/**
 * Notifications Hook
 *
 * Custom hook for managing student balance notifications and API integration.
 * Provides reactive access to notifications with filtering and pagination support.
 */

import { useState, useEffect, useCallback, useRef } from 'react';

import { useUserProfile } from '@/api/auth';
import { useInterval, usePolling } from './useTimer';
import { NotificationApiClient } from '@/api/notificationApi';
import type {
  NotificationResponse,
  NotificationFilters,
  NotificationListResponse,
  NotificationSettings,
} from '@/types/notification';

interface UseNotificationsOptions {
  /** Auto-refresh interval in milliseconds */
  pollingInterval?: number;
  /** Enable automatic polling */
  enablePolling?: boolean;
  /** Items per page */
  pageSize?: number;
  /** Initial filters */
  initialFilters?: NotificationFilters;
}

interface UseNotificationsResult {
  // Data
  notifications: NotificationResponse[];
  unreadCount: number;
  hasMore: boolean;
  currentPage: number;

  // State
  loading: boolean;
  error: string | null;
  refreshing: boolean;

  // Actions
  refresh: () => Promise<void>;
  loadMore: () => Promise<void>;
  markAsRead: (id: number) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  setFilters: (filters: NotificationFilters) => void;

  // Current filters
  filters: NotificationFilters;
}

/**
 * Hook for managing notifications
 */
export function useNotifications(options: UseNotificationsOptions = {}): UseNotificationsResult {
  const {
    pollingInterval = 30000, // 30 seconds
    enablePolling = false,
    pageSize = 20,
    initialFilters = {},
  } = options;

  const { userProfile } = useUserProfile();

  // State
  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [filters, setFilters] = useState<NotificationFilters>(initialFilters);

  // Refs
  const lastFetchTimestamp = useRef<string | null>(null);

  /**
   * Fetch notifications from API
   */
  const fetchNotifications = useCallback(
    async (
      page: number = 1,
      append: boolean = false,
      currentFilters: NotificationFilters = filters,
    ) => {
      if (!userProfile) return;

      try {
        if (!append) {
          setLoading(true);
        }
        setError(null);

        const response = await NotificationApiClient.getNotifications(
          currentFilters,
          page,
          pageSize,
        );

        if (append) {
          setNotifications(prev => [...prev, ...response.results]);
        } else {
          setNotifications(response.results);
        }

        setHasMore(response.next !== null);
        setCurrentPage(page);
        lastFetchTimestamp.current = new Date().toISOString();
      } catch (err: any) {
        console.error('Failed to fetch notifications:', err);
        setError(err.message || 'Failed to load notifications');
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [userProfile, filters, pageSize],
  );

  /**
   * Fetch unread count
   */
  const fetchUnreadCount = useCallback(async () => {
    if (!userProfile) return;

    try {
      const response = await NotificationApiClient.getUnreadCount();
      setUnreadCount(response.unread_count);
    } catch (err: any) {
      console.error('Failed to fetch unread count:', err);
    }
  }, [userProfile]);

  /**
   * Refresh notifications (reset to page 1) with graceful degradation
   */
  const refresh = useCallback(async () => {
    setRefreshing(true);
    setCurrentPage(1);

    // Use Promise.allSettled for graceful degradation
    const results = await Promise.allSettled([fetchNotifications(1, false), fetchUnreadCount()]);

    // Log any failures for monitoring
    results.forEach((result, index) => {
      if (result.status === 'rejected') {
        const operation = index === 0 ? 'notifications' : 'unread count';
        console.error(`Failed to refresh ${operation}:`, result.reason);
      }
    });

    // Continue with available data even if some operations failed
  }, [fetchNotifications, fetchUnreadCount]);

  /**
   * Load more notifications (pagination)
   */
  const loadMore = useCallback(async () => {
    if (!hasMore || loading) return;

    const nextPage = currentPage + 1;
    await fetchNotifications(nextPage, true);
  }, [hasMore, loading, currentPage, fetchNotifications]);

  /**
   * Mark notification as read
   */
  const markAsRead = useCallback(
    async (id: number) => {
      try {
        await NotificationApiClient.markNotificationAsRead(id);

        // Update local state
        setNotifications(prev =>
          prev.map(notification =>
            notification.id === id
              ? { ...notification, is_read: true, read_at: new Date().toISOString() }
              : notification,
          ),
        );

        // Update unread count
        const notification = notifications.find(n => n.id === id);
        if (notification && !notification.is_read) {
          setUnreadCount(prev => Math.max(0, prev - 1));
        }
      } catch (err: any) {
        console.error('Failed to mark notification as read:', err);
        setError(err.message || 'Failed to update notification');
      }
    },
    [notifications],
  );

  /**
   * Mark all notifications as read
   */
  const markAllAsRead = useCallback(async () => {
    try {
      await NotificationApiClient.markAllAsRead();

      // Update local state
      setNotifications(prev =>
        prev.map(notification => ({
          ...notification,
          is_read: true,
          read_at: notification.read_at || new Date().toISOString(),
        })),
      );

      setUnreadCount(0);
    } catch (err: any) {
      console.error('Failed to mark all notifications as read:', err);
      setError(err.message || 'Failed to update notifications');
    }
  }, []);

  /**
   * Update filters and refresh
   */
  const updateFilters = useCallback(
    (newFilters: NotificationFilters) => {
      setFilters(newFilters);
      setCurrentPage(1);
      fetchNotifications(1, false, newFilters);
    },
    [fetchNotifications],
  );

  /**
   * Poll for new notifications
   */
  const pollForUpdates = useCallback(async () => {
    if (!userProfile || !lastFetchTimestamp.current) return;

    try {
      const response = await NotificationApiClient.pollNotifications(lastFetchTimestamp.current, {
        is_read: false,
      });

      // If there are new notifications, refresh the list
      if (response.results.length > 0) {
        await refresh();
      }
    } catch (err) {
      console.error('Failed to poll for notification updates:', err);
    }
  }, [userProfile, refresh]);

  // Initial fetch
  useEffect(() => {
    if (userProfile) {
      refresh();
    }
  }, [userProfile, refresh]);

  // Setup polling with exponential backoff for better error handling
  usePolling(
    pollForUpdates,
    {
      interval: pollingInterval,
      enabled: enablePolling && userProfile,
      maxRetries: 5,
      backoffMultiplier: 2,
      maxInterval: 30000, // Max 30 seconds between retries for notifications
    }
  );

  return {
    // Data
    notifications,
    unreadCount,
    hasMore,
    currentPage,

    // State
    loading,
    error,
    refreshing,

    // Actions
    refresh,
    loadMore,
    markAsRead,
    markAllAsRead,
    setFilters: updateFilters,

    // Current filters
    filters,
  };
}

/**
 * Hook for getting unread notification count only
 * Useful for navigation badges
 */
export function useUnreadNotificationCount() {
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const { userProfile } = useUserProfile();

  const fetchUnreadCount = useCallback(async () => {
    if (!userProfile) return;

    try {
      setLoading(true);
      const response = await NotificationApiClient.getUnreadCount();
      setUnreadCount(response.unread_count);
    } catch (err) {
      console.error('Failed to fetch unread count:', err);
    } finally {
      setLoading(false);
    }
  }, [userProfile]);

  // Initial fetch
  useEffect(() => {
    fetchUnreadCount();
  }, [fetchUnreadCount]);

  // Set up polling for unread count with safe timer management
  useInterval(
    fetchUnreadCount,
    60000, // Check every minute
    [fetchUnreadCount]
  );

  return { unreadCount, loading, refresh: fetchUnreadCount };
}
