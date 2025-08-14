import { useState, useEffect, useCallback } from 'react';

import CommunicationApi, {
  EmailAnalytics,
  EmailCommunication,
  AnalyticsFilters,
  EmailTemplateType,
} from '@/api/communicationApi';

export const useEmailAnalytics = (autoFetch = true) => {
  const [analytics, setAnalytics] = useState<EmailAnalytics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<AnalyticsFilters>({});

  const fetchAnalytics = useCallback(
    async (newFilters?: AnalyticsFilters) => {
      try {
        setLoading(true);
        setError(null);

        const activeFilters = newFilters || filters;
        const analyticsData = await CommunicationApi.getEmailAnalytics(activeFilters);
        setAnalytics(analyticsData);

        if (newFilters) {
          setFilters(newFilters);
        }
      } catch (err: any) {
        const errorMessage =
          err.response?.data?.detail || err.message || 'Failed to fetch email analytics';
        setError(errorMessage);
        console.error('Error fetching email analytics:', err);
      } finally {
        setLoading(false);
      }
    },
    [filters]
  );

  const updateFilters = useCallback(
    (newFilters: AnalyticsFilters) => {
      setFilters(newFilters);
      fetchAnalytics(newFilters);
    },
    [fetchAnalytics]
  );

  const refreshAnalytics = useCallback(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  useEffect(() => {
    if (autoFetch) {
      fetchAnalytics();
    }
  }, [autoFetch, fetchAnalytics]);

  return {
    analytics,
    loading,
    error,
    filters,
    fetchAnalytics,
    updateFilters,
    refreshAnalytics,
    clearError: () => setError(null),
  };
};

export const useEmailCommunications = (autoFetch = true) => {
  const [communications, setCommunications] = useState<EmailCommunication[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null as string | null,
    previous: null as string | null,
    currentPage: 1,
  });

  const fetchCommunications = useCallback(
    async (params?: {
      template_type?: keyof EmailTemplateType;
      status?: EmailCommunication['status'];
      start_date?: string;
      end_date?: string;
      page?: number;
    }) => {
      try {
        setLoading(true);
        setError(null);

        const response = await CommunicationApi.getEmailCommunications(params);

        setCommunications(response.results);
        setPagination({
          count: response.count,
          next: response.next || null,
          previous: response.previous || null,
          currentPage: params?.page || 1,
        });
      } catch (err: any) {
        const errorMessage =
          err.response?.data?.detail || err.message || 'Failed to fetch email communications';
        setError(errorMessage);
        console.error('Error fetching email communications:', err);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const refreshCommunications = useCallback(() => {
    fetchCommunications({ page: pagination.currentPage });
  }, [fetchCommunications, pagination.currentPage]);

  useEffect(() => {
    if (autoFetch) {
      fetchCommunications();
    }
  }, [autoFetch, fetchCommunications]);

  return {
    communications,
    loading,
    error,
    pagination,
    fetchCommunications,
    refreshCommunications,
    clearError: () => setError(null),
  };
};

export const useAnalyticsDateRange = () => {
  const [dateRange, setDateRange] = useState<{
    start_date: string;
    end_date: string;
    preset?: string;
  }>({
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 days ago
    end_date: new Date().toISOString().split('T')[0], // Today
    preset: '30d',
  });

  const presetRanges = [
    {
      label: 'Last 7 days',
      value: '7d',
      start_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end_date: new Date().toISOString().split('T')[0],
    },
    {
      label: 'Last 30 days',
      value: '30d',
      start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end_date: new Date().toISOString().split('T')[0],
    },
    {
      label: 'Last 90 days',
      value: '90d',
      start_date: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end_date: new Date().toISOString().split('T')[0],
    },
    {
      label: 'This month',
      value: 'month',
      start_date: new Date(new Date().getFullYear(), new Date().getMonth(), 1)
        .toISOString()
        .split('T')[0],
      end_date: new Date().toISOString().split('T')[0],
    },
    {
      label: 'Last month',
      value: 'last_month',
      start_date: new Date(new Date().getFullYear(), new Date().getMonth() - 1, 1)
        .toISOString()
        .split('T')[0],
      end_date: new Date(new Date().getFullYear(), new Date().getMonth(), 0)
        .toISOString()
        .split('T')[0],
    },
  ];

  const setPresetRange = useCallback(
    (preset: string) => {
      const range = presetRanges.find(r => r.value === preset);
      if (range) {
        setDateRange({
          start_date: range.start_date,
          end_date: range.end_date,
          preset: preset,
        });
      }
    },
    [presetRanges]
  );

  const setCustomRange = useCallback((start_date: string, end_date: string) => {
    setDateRange({
      start_date,
      end_date,
      preset: undefined,
    });
  }, []);

  return {
    dateRange,
    presetRanges,
    setPresetRange,
    setCustomRange,
    setDateRange,
  };
};

export const useAnalyticsChartData = (analytics: EmailAnalytics | null) => {
  const [chartData, setChartData] = useState<{
    deliveryChart: any[];
    engagementChart: any[];
    templatePerformanceChart: any[];
    timelineChart: any[];
  }>({
    deliveryChart: [],
    engagementChart: [],
    templatePerformanceChart: [],
    timelineChart: [],
  });

  useEffect(() => {
    if (!analytics) {
      setChartData({
        deliveryChart: [],
        engagementChart: [],
        templatePerformanceChart: [],
        timelineChart: [],
      });
      return;
    }

    // Prepare delivery rate chart data
    const deliveryChart = [
      { name: 'Delivered', value: analytics.delivered_count, color: '#10B981' },
      { name: 'Failed', value: analytics.failed_count, color: '#EF4444' },
      {
        name: 'Pending',
        value: analytics.total_sent - analytics.delivered_count - analytics.failed_count,
        color: '#F59E0B',
      },
    ].filter(item => item.value > 0);

    // Prepare engagement chart data
    const engagementChart = [
      { name: 'Opened', value: analytics.opened_count, color: '#3B82F6' },
      { name: 'Clicked', value: analytics.clicked_count, color: '#8B5CF6' },
      {
        name: 'Not Opened',
        value: analytics.delivered_count - analytics.opened_count,
        color: '#6B7280',
      },
    ].filter(item => item.value > 0);

    // Prepare template performance chart data
    const templatePerformanceChart = analytics.template_performance.map(template => ({
      name: template.template_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
      sent: template.sent_count,
      open_rate: Math.round(template.open_rate * 100),
      click_rate: Math.round(template.click_rate * 100),
    }));

    // Prepare timeline chart data (from recent activity)
    const timelineChart = analytics.recent_activity
      .filter(activity => activity.sent_at)
      .reduce((acc, activity) => {
        const date = new Date(activity.sent_at!).toISOString().split('T')[0];
        const existing = acc.find(item => item.date === date);

        if (existing) {
          existing.count += 1;
          if (activity.status === 'delivered') existing.delivered += 1;
          if (activity.status === 'opened') existing.opened += 1;
          if (activity.status === 'clicked') existing.clicked += 1;
        } else {
          acc.push({
            date,
            count: 1,
            delivered: activity.status === 'delivered' ? 1 : 0,
            opened: activity.status === 'opened' ? 1 : 0,
            clicked: activity.status === 'clicked' ? 1 : 0,
          });
        }

        return acc;
      }, [] as any[])
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    setChartData({
      deliveryChart,
      engagementChart,
      templatePerformanceChart,
      timelineChart,
    });
  }, [analytics]);

  return chartData;
};

export const useAnalyticsMetrics = (analytics: EmailAnalytics | null) => {
  const [metrics, setMetrics] = useState<{
    kpis: {
      label: string;
      value: string;
      change?: string;
      trend?: 'up' | 'down' | 'neutral';
      color: string;
    }[];
    insights: string[];
  }>({
    kpis: [],
    insights: [],
  });

  useEffect(() => {
    if (!analytics) {
      setMetrics({ kpis: [], insights: [] });
      return;
    }

    // Calculate KPIs
    const kpis = [
      {
        label: 'Total Sent',
        value: analytics.total_sent.toLocaleString(),
        color: '#3B82F6',
      },
      {
        label: 'Delivery Rate',
        value: `${Math.round(analytics.delivery_rate * 100)}%`,
        color:
          analytics.delivery_rate >= 0.95
            ? '#10B981'
            : analytics.delivery_rate >= 0.85
            ? '#F59E0B'
            : '#EF4444',
      },
      {
        label: 'Open Rate',
        value: `${Math.round(analytics.open_rate * 100)}%`,
        color:
          analytics.open_rate >= 0.25
            ? '#10B981'
            : analytics.open_rate >= 0.15
            ? '#F59E0B'
            : '#EF4444',
      },
      {
        label: 'Click Rate',
        value: `${Math.round(analytics.click_rate * 100)}%`,
        color:
          analytics.click_rate >= 0.05
            ? '#10B981'
            : analytics.click_rate >= 0.02
            ? '#F59E0B'
            : '#EF4444',
      },
    ];

    // Generate insights
    const insights = [];

    if (analytics.delivery_rate < 0.9) {
      insights.push('Delivery rate is below 90%. Consider reviewing your email list quality.');
    }

    if (analytics.open_rate > 0.3) {
      insights.push('Excellent open rate! Your subject lines are engaging.');
    } else if (analytics.open_rate < 0.15) {
      insights.push('Consider A/B testing different subject lines to improve open rates.');
    }

    if (analytics.click_rate > 0.05) {
      insights.push('Great click-through rate! Your content is compelling.');
    } else if (analytics.click_rate < 0.02) {
      insights.push('Consider adding clearer call-to-action buttons to improve engagement.');
    }

    // Find best performing template
    const bestTemplate = analytics.template_performance.reduce((best, current) =>
      current.open_rate > best.open_rate ? current : best
    );
    if (bestTemplate) {
      insights.push(
        `Your "${bestTemplate.template_type}" template has the highest open rate at ${Math.round(
          bestTemplate.open_rate * 100
        )}%.`
      );
    }

    setMetrics({ kpis, insights });
  }, [analytics]);

  return metrics;
};
