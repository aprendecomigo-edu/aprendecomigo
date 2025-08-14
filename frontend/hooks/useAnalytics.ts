/**
 * Custom hook for managing analytics data and operations.
 *
 * Provides state management for usage statistics, learning insights,
 * usage patterns, and notification preferences.
 */

import { useState, useCallback, useEffect } from 'react';

import {
  AnalyticsApiClient,
  type UsageStatistics,
  type LearningInsight,
  type UsagePattern,
  type NotificationPreferences,
  type AnalyticsTimeRange,
} from '@/api/analyticsApi';

interface UseAnalyticsResult {
  // Usage statistics
  usageStats: UsageStatistics | null;
  usageStatsLoading: boolean;
  usageStatsError: string | null;

  // Learning insights
  insights: LearningInsight[];
  insightsLoading: boolean;
  insightsError: string | null;

  // Usage patterns
  patterns: UsagePattern[];
  patternsLoading: boolean;
  patternsError: string | null;

  // Notification preferences
  preferences: NotificationPreferences | null;
  preferencesLoading: boolean;
  preferencesError: string | null;
  preferencesUpdating: boolean;

  // Actions
  refreshUsageStats: (timeRange?: AnalyticsTimeRange) => Promise<void>;
  refreshInsights: (limit?: number) => Promise<void>;
  refreshPatterns: (timeRange?: AnalyticsTimeRange) => Promise<void>;
  refreshPreferences: () => Promise<void>;
  updatePreferences: (preferences: Partial<NotificationPreferences>) => Promise<void>;
  markInsightAsRead: (insightId: string) => Promise<void>;
  refreshAll: () => Promise<void>;
  clearErrors: () => void;

  // Computed values
  unreadInsights: LearningInsight[];
  hasLowBalance: boolean;
  shouldShowRenewalPrompt: boolean;
}

/**
 * Hook for managing analytics data and operations.
 */
export function useAnalytics(email?: string): UseAnalyticsResult {
  // Usage statistics state
  const [usageStats, setUsageStats] = useState<UsageStatistics | null>(null);
  const [usageStatsLoading, setUsageStatsLoading] = useState(true);
  const [usageStatsError, setUsageStatsError] = useState<string | null>(null);

  // Learning insights state
  const [insights, setInsights] = useState<LearningInsight[]>([]);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [insightsError, setInsightsError] = useState<string | null>(null);

  // Usage patterns state
  const [patterns, setPatterns] = useState<UsagePattern[]>([]);
  const [patternsLoading, setPatternsLoading] = useState(false);
  const [patternsError, setPatternsError] = useState<string | null>(null);

  // Notification preferences state
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [preferencesLoading, setPreferencesLoading] = useState(false);
  const [preferencesError, setPreferencesError] = useState<string | null>(null);
  const [preferencesUpdating, setPreferencesUpdating] = useState(false);

  // Refresh usage statistics
  const refreshUsageStats = useCallback(
    async (timeRange?: AnalyticsTimeRange) => {
      setUsageStatsLoading(true);
      setUsageStatsError(null);

      try {
        const statsData = await AnalyticsApiClient.getUsageStatistics(timeRange, email);
        setUsageStats(statsData);
      } catch (error: any) {
        console.error('Error fetching usage statistics:', error);
        setUsageStatsError(error.message || 'Failed to load usage statistics');
        setUsageStats(null);
      } finally {
        setUsageStatsLoading(false);
      }
    },
    [email]
  );

  // Refresh learning insights
  const refreshInsights = useCallback(
    async (limit?: number) => {
      setInsightsLoading(true);
      setInsightsError(null);

      try {
        const insightsData = await AnalyticsApiClient.getLearningInsights(limit, email);
        setInsights(insightsData);
      } catch (error: any) {
        console.error('Error fetching learning insights:', error);
        setInsightsError(error.message || 'Failed to load learning insights');
        setInsights([]);
      } finally {
        setInsightsLoading(false);
      }
    },
    [email]
  );

  // Refresh usage patterns
  const refreshPatterns = useCallback(
    async (timeRange?: AnalyticsTimeRange) => {
      setPatternsLoading(true);
      setPatternsError(null);

      try {
        const patternsData = await AnalyticsApiClient.getUsagePatterns(timeRange, email);
        setPatterns(patternsData);
      } catch (error: any) {
        console.error('Error fetching usage patterns:', error);
        setPatternsError(error.message || 'Failed to load usage patterns');
        setPatterns([]);
      } finally {
        setPatternsLoading(false);
      }
    },
    [email]
  );

  // Refresh notification preferences
  const refreshPreferences = useCallback(async () => {
    setPreferencesLoading(true);
    setPreferencesError(null);

    try {
      const preferencesData = await AnalyticsApiClient.getNotificationPreferences(email);
      setPreferences(preferencesData);
    } catch (error: any) {
      console.error('Error fetching notification preferences:', error);
      setPreferencesError(error.message || 'Failed to load notification preferences');
      setPreferences(null);
    } finally {
      setPreferencesLoading(false);
    }
  }, [email]);

  // Update notification preferences
  const updatePreferences = useCallback(
    async (updatedPreferences: Partial<NotificationPreferences>) => {
      setPreferencesUpdating(true);
      setPreferencesError(null);

      try {
        await AnalyticsApiClient.updateNotificationPreferences(updatedPreferences, email);

        // Update local state
        setPreferences(prev => (prev ? { ...prev, ...updatedPreferences } : null));
      } catch (error: any) {
        console.error('Error updating notification preferences:', error);
        setPreferencesError(error.message || 'Failed to update notification preferences');
        throw error; // Re-throw to allow component to handle
      } finally {
        setPreferencesUpdating(false);
      }
    },
    [email]
  );

  // Mark insight as read
  const markInsightAsRead = useCallback(
    async (insightId: string) => {
      try {
        await AnalyticsApiClient.markInsightAsRead(insightId, email);

        // Update local state
        setInsights(prev =>
          prev.map(insight => (insight.id === insightId ? { ...insight, is_read: true } : insight))
        );
      } catch (error: any) {
        console.error('Error marking insight as read:', error);
        // Don't show error for this operation as it's not critical
      }
    },
    [email]
  );

  // Refresh all data
  const refreshAll = useCallback(async () => {
    await Promise.all([
      refreshUsageStats(),
      refreshInsights(10),
      refreshPatterns(),
      refreshPreferences(),
    ]);
  }, [refreshUsageStats, refreshInsights, refreshPatterns, refreshPreferences]);

  // Clear all errors
  const clearErrors = useCallback(() => {
    setUsageStatsError(null);
    setInsightsError(null);
    setPatternsError(null);
    setPreferencesError(null);
  }, []);

  // Computed values
  const unreadInsights = insights.filter(insight => !insight.is_read);

  // Determine if balance is low (less than 2 hours remaining)
  const hasLowBalance = usageStats
    ? usageStats.total_hours_consumed > 0 &&
      (usageStats.total_sessions > 0
        ? (usageStats.total_hours_consumed / usageStats.total_sessions) * 2 > 2
        : false)
    : false;

  // Determine if should show renewal prompt (based on usage patterns and remaining balance)
  const shouldShowRenewalPrompt = usageStats
    ? hasLowBalance && usageStats.sessions_this_month > 0
    : false;

  // Initial data fetch
  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  return {
    usageStats,
    usageStatsLoading,
    usageStatsError,
    insights,
    insightsLoading,
    insightsError,
    patterns,
    patternsLoading,
    patternsError,
    preferences,
    preferencesLoading,
    preferencesError,
    preferencesUpdating,
    refreshUsageStats,
    refreshInsights,
    refreshPatterns,
    refreshPreferences,
    updatePreferences,
    markInsightAsRead,
    refreshAll,
    clearErrors,
    unreadInsights,
    hasLowBalance,
    shouldShowRenewalPrompt,
  };
}
