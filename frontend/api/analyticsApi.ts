/**
 * API client functions for analytics and usage tracking operations.
 *
 * Handles communication with the backend analytics APIs including
 * usage statistics, learning insights, and usage pattern analysis.
 */

import apiClient from './apiClient';

export interface UsageStatistics {
  total_sessions: number;
  total_hours_consumed: number;
  average_session_duration: number;
  sessions_this_month: number;
  hours_this_month: number;
  most_active_subject?: string;
  preferred_time_slot?: string;
  streak_days: number;
}

export interface LearningInsight {
  id: string;
  type: 'achievement' | 'suggestion' | 'milestone' | 'warning';
  title: string;
  description: string;
  icon: string;
  created_at: string;
  is_read: boolean;
}

export interface UsagePattern {
  hour: number;
  day_of_week: number;
  session_count: number;
  average_duration: number;
  subjects: {
    [subject: string]: {
      session_count: number;
      total_hours: number;
    };
  };
}

export interface AnalyticsTimeRange {
  start_date: string;
  end_date: string;
}

export interface NotificationPreferences {
  low_balance_alerts: boolean;
  session_reminders: boolean;
  package_expiration: boolean;
  weekly_reports: boolean;
  learning_insights: boolean;
  renewal_prompts: boolean;
  email_notifications: boolean;
  in_app_notifications: boolean;
}

/**
 * Analytics API client with comprehensive error handling and type safety.
 */
export class AnalyticsApiClient {
  /**
   * Get usage statistics for the authenticated student.
   *
   * @param timeRange Optional time range for statistics
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to usage statistics
   * @throws Error with descriptive message if request fails
   */
  static async getUsageStatistics(
    timeRange?: AnalyticsTimeRange,
    email?: string,
  ): Promise<UsageStatistics> {
    try {
      const params: any = {};
      if (email) params.email = email;
      if (timeRange) {
        params.start_date = timeRange.start_date;
        params.end_date = timeRange.end_date;
      }

      const response = await apiClient.get('/api/student-balance/analytics/usage/', { params });

      return {
        total_sessions: response.data.total_sessions,
        total_hours_consumed: response.data.total_hours_consumed,
        average_session_duration: response.data.average_session_duration,
        sessions_this_month: response.data.sessions_this_month,
        hours_this_month: response.data.hours_this_month,
        most_active_subject: response.data.most_active_subject,
        preferred_time_slot: response.data.preferred_time_slot,
        streak_days: response.data.streak_days,
      };
    } catch (error: any) {
      console.error('Error fetching usage statistics:', error);

      if (error.response?.status === 404) {
        throw new Error('Student not found');
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Unable to retrieve usage statistics.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading usage statistics');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load usage statistics. Please try again.');
      }
    }
  }

  /**
   * Get learning insights for the authenticated student.
   *
   * @param limit Optional limit for number of insights
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to array of learning insights
   * @throws Error with descriptive message if request fails
   */
  static async getLearningInsights(limit?: number, email?: string): Promise<LearningInsight[]> {
    try {
      const params: any = {};
      if (email) params.email = email;
      if (limit) params.limit = limit.toString();

      const response = await apiClient.get('/api/student-balance/analytics/insights/', { params });

      if (!Array.isArray(response.data)) {
        throw new Error('Invalid response format: expected array of insights');
      }

      return response.data.map((insight: any) => ({
        id: insight.id,
        type: insight.type,
        title: insight.title,
        description: insight.description,
        icon: insight.icon,
        created_at: insight.created_at,
        is_read: insight.is_read,
      }));
    } catch (error: any) {
      console.error('Error fetching learning insights:', error);

      if (error.response?.status === 404) {
        throw new Error('Student not found');
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Unable to retrieve learning insights.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading learning insights');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load learning insights. Please try again.');
      }
    }
  }

  /**
   * Get usage patterns for the authenticated student.
   *
   * @param timeRange Optional time range for patterns
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to array of usage patterns
   * @throws Error with descriptive message if request fails
   */
  static async getUsagePatterns(
    timeRange?: AnalyticsTimeRange,
    email?: string,
  ): Promise<UsagePattern[]> {
    try {
      const params: any = {};
      if (email) params.email = email;
      if (timeRange) {
        params.start_date = timeRange.start_date;
        params.end_date = timeRange.end_date;
      }

      const response = await apiClient.get('/api/student-balance/analytics/patterns/', { params });

      if (!Array.isArray(response.data)) {
        throw new Error('Invalid response format: expected array of usage patterns');
      }

      return response.data.map((pattern: any) => ({
        hour: pattern.hour,
        day_of_week: pattern.day_of_week,
        session_count: pattern.session_count,
        average_duration: pattern.average_duration,
        subjects: pattern.subjects,
      }));
    } catch (error: any) {
      console.error('Error fetching usage patterns:', error);

      if (error.response?.status === 404) {
        throw new Error('Student not found');
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Unable to retrieve usage patterns.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading usage patterns');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load usage patterns. Please try again.');
      }
    }
  }

  /**
   * Get notification preferences for the authenticated student.
   *
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to notification preferences
   * @throws Error with descriptive message if request fails
   */
  static async getNotificationPreferences(email?: string): Promise<NotificationPreferences> {
    try {
      const params = email ? { email } : {};
      const response = await apiClient.get('/api/student-balance/notifications/preferences/', {
        params,
      });

      return {
        low_balance_alerts: response.data.low_balance_alerts,
        session_reminders: response.data.session_reminders,
        package_expiration: response.data.package_expiration,
        weekly_reports: response.data.weekly_reports,
        learning_insights: response.data.learning_insights,
        renewal_prompts: response.data.renewal_prompts,
        email_notifications: response.data.email_notifications,
        in_app_notifications: response.data.in_app_notifications,
      };
    } catch (error: any) {
      console.error('Error fetching notification preferences:', error);

      if (error.response?.status === 404) {
        throw new Error('Student not found');
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Unable to retrieve notification preferences.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading notification preferences');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load notification preferences. Please try again.');
      }
    }
  }

  /**
   * Update notification preferences for the authenticated student.
   *
   * @param preferences Updated notification preferences
   * @param email Optional email parameter for admin access
   * @returns Promise that resolves when preferences are updated
   * @throws Error with descriptive message if request fails
   */
  static async updateNotificationPreferences(
    preferences: Partial<NotificationPreferences>,
    email?: string,
  ): Promise<void> {
    try {
      const data = email ? { ...preferences, email } : preferences;
      await apiClient.patch('/api/student-balance/notifications/preferences/', data);
    } catch (error: any) {
      console.error('Error updating notification preferences:', error);

      if (error.response?.status === 400) {
        throw new Error(error.response.data?.message || 'Invalid notification preferences');
      } else if (error.response?.status === 404) {
        throw new Error('Student not found');
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Unable to update notification preferences.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while updating notification preferences');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to update notification preferences. Please try again.');
      }
    }
  }

  /**
   * Mark a learning insight as read.
   *
   * @param insightId The insight ID to mark as read
   * @param email Optional email parameter for admin access
   * @returns Promise that resolves when insight is marked as read
   * @throws Error with descriptive message if request fails
   */
  static async markInsightAsRead(insightId: string, email?: string): Promise<void> {
    try {
      const data = email ? { email } : {};
      await apiClient.post(`/api/student-balance/analytics/insights/${insightId}/read/`, data);
    } catch (error: any) {
      console.error('Error marking insight as read:', error);

      if (error.response?.status === 404) {
        throw new Error('Insight not found');
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Unable to mark insight as read.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while marking insight as read');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to mark insight as read. Please try again.');
      }
    }
  }
}

// Convenience exports for direct function access
export const {
  getUsageStatistics,
  getLearningInsights,
  getUsagePatterns,
  getNotificationPreferences,
  updateNotificationPreferences,
  markInsightAsRead,
} = AnalyticsApiClient;
