/**
 * Notification API Client
 *
 * Handles communication with the backend notification system for balance alerts
 * and other student notifications.
 */

import apiClient from '@/api/apiClient';
import type {
  NotificationResponse,
  NotificationListResponse,
  NotificationUnreadCountResponse,
  NotificationMarkReadResponse,
  NotificationFilters,
} from '@/types/notification';

export class NotificationApiClient {
  private static baseUrl = '/api/notifications';

  /**
   * Get paginated list of notifications for the current user
   */
  static async getNotifications(
    filters?: NotificationFilters,
    page: number = 1,
    pageSize: number = 20,
  ): Promise<NotificationListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });

    if (filters?.notification_type) {
      params.append('notification_type', filters.notification_type);
    }

    if (filters?.is_read !== undefined) {
      params.append('is_read', filters.is_read.toString());
    }

    const response = await apiClient.get(`${this.baseUrl}/?${params.toString()}`);
    return response.data;
  }

  /**
   * Get detailed information about a specific notification
   */
  static async getNotification(notificationId: number): Promise<NotificationResponse> {
    const response = await apiClient.get(`${this.baseUrl}/${notificationId}/`);
    return response.data;
  }

  /**
   * Mark a notification as read
   */
  static async markNotificationAsRead(
    notificationId: number,
  ): Promise<NotificationMarkReadResponse> {
    const response = await apiClient.post(`${this.baseUrl}/${notificationId}/read/`);
    return response.data;
  }

  /**
   * Get the count of unread notifications
   */
  static async getUnreadCount(): Promise<NotificationUnreadCountResponse> {
    const response = await apiClient.get(`${this.baseUrl}/unread-count/`);
    return response.data;
  }

  /**
   * Mark all notifications as read (batch operation)
   */
  static async markAllAsRead(): Promise<void> {
    // Get all unread notifications and mark them as read
    const notifications = await this.getNotifications({ is_read: false }, 1, 100);

    // Mark each notification as read with graceful degradation
    const promises = notifications.results.map(notification =>
      this.markNotificationAsRead(notification.id),
    );

    const results = await Promise.allSettled(promises);

    // Count successful and failed operations
    const successful = results.filter(result => result.status === 'fulfilled').length;
    const failed = results.filter(result => result.status === 'rejected').length;

    // Log failed operations for monitoring
    results.forEach((result, index) => {
      if (result.status === 'rejected') {
        console.error(
          `Failed to mark notification ${notifications.results[index].id} as read:`,
          result.reason,
        );
      }
    });

    // Partial success is acceptable for this operation
    if (failed > 0) {
      console.warn(
        `Mark all as read completed with ${successful} successful and ${failed} failed operations.`,
      );
    }
  }

  /**
   * Get notifications with real-time polling support
   */
  static async pollNotifications(
    lastCheckTimestamp?: string,
    filters?: NotificationFilters,
  ): Promise<NotificationListResponse> {
    const params = new URLSearchParams();

    if (lastCheckTimestamp) {
      params.append('since', lastCheckTimestamp);
    }

    if (filters?.notification_type) {
      params.append('notification_type', filters.notification_type);
    }

    if (filters?.is_read !== undefined) {
      params.append('is_read', filters.is_read.toString());
    }

    const response = await apiClient.get(`${this.baseUrl}/?${params.toString()}`);
    return response.data;
  }
}
