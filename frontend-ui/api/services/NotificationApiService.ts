/**
 * Notification API Service
 * Handles all notification-related API operations using dependency injection
 */

import { ApiClient } from '../client/ApiClient';

export interface Notification {
  id: number;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'error' | 'success';
  is_read: boolean;
  created_at: string;
  read_at?: string;
  action_url?: string;
}

export interface NotificationFilters {
  is_read?: boolean;
  type?: 'info' | 'warning' | 'error' | 'success';
  limit?: number;
  offset?: number;
}

export class NotificationApiService {
  constructor(private readonly apiClient: ApiClient) {}

  /**
   * Get all notifications for the current user
   */
  async getNotifications(filters?: NotificationFilters): Promise<Notification[]> {
    const params = new URLSearchParams();

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }

    const url = `/notifications/${params.toString() ? `?${params}` : ''}`;
    const response = await this.apiClient.get<Notification[]>(url);
    return response.data;
  }

  /**
   * Get a specific notification
   */
  async getNotification(notificationId: number): Promise<Notification> {
    const response = await this.apiClient.get<Notification>(`/notifications/${notificationId}/`);
    return response.data;
  }

  /**
   * Mark a notification as read
   */
  async markAsRead(notificationId: number): Promise<Notification> {
    const response = await this.apiClient.patch<Notification>(`/notifications/${notificationId}/`, {
      is_read: true,
    });
    return response.data;
  }

  /**
   * Mark all notifications as read
   */
  async markAllAsRead(): Promise<void> {
    await this.apiClient.post('/notifications/mark-all-read/');
  }

  /**
   * Delete a notification
   */
  async deleteNotification(notificationId: number): Promise<void> {
    await this.apiClient.delete(`/notifications/${notificationId}/`);
  }

  /**
   * Get unread notification count
   */
  async getUnreadCount(): Promise<{ count: number }> {
    const response = await this.apiClient.get<{ count: number }>('/notifications/unread-count/');
    return response.data;
  }
}
