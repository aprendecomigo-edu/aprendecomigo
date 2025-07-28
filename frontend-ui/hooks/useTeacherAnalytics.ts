import { useState, useEffect, useCallback, useMemo } from 'react';
import { TeacherAnalytics, getTeacherAnalytics } from '@/api/userApi';
import { useAuth } from '@/api/authContext';

interface UseTeacherAnalyticsOptions {
  schoolId?: number;
  autoFetch?: boolean;
  refreshInterval?: number; // in milliseconds
}

interface UseTeacherAnalyticsReturn {
  analytics: TeacherAnalytics | null;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  
  // Actions
  fetchAnalytics: (schoolId?: number) => Promise<void>;
  refresh: () => Promise<void>;
  
  // Computed analytics
  getCompletionTrend: () => 'improving' | 'declining' | 'stable';
  getHighPriorityIssues: () => string[];
  getTopMissingFields: (limit?: number) => Array<{ field: string; count: number; percentage: number }>;
  getCompletionDistributionPercentages: () => Record<string, number>;
  
  // Status helpers
  isHealthy: () => boolean;
  needsAttention: () => boolean;
  getCriticalTeachersCount: () => number;
  getAverageCompletionGrade: () => 'A' | 'B' | 'C' | 'D' | 'F';
}

export const useTeacherAnalytics = (options: UseTeacherAnalyticsOptions = {}): UseTeacherAnalyticsReturn => {
  const { schoolId: initialSchoolId, autoFetch = true, refreshInterval } = options;
  const { userProfile } = useAuth();
  
  const [analytics, setAnalytics] = useState<TeacherAnalytics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Determine school ID from options or user profile
  const schoolId = useMemo(() => {
    if (initialSchoolId) return initialSchoolId;
    
    // Try to get school ID from user profile admin schools
    // This would need to be implemented based on your auth context structure
    return userProfile?.school_id || null;
  }, [initialSchoolId, userProfile]);

  const fetchAnalytics = useCallback(async (targetSchoolId?: number) => {
    const schoolIdToUse = targetSchoolId || schoolId;
    
    if (!schoolIdToUse) {
      setError('No school ID available');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const analyticsData = await getTeacherAnalytics(schoolIdToUse);
      setAnalytics(analyticsData);
      setLastUpdated(new Date());
    } catch (err: any) {
      console.error('Error fetching teacher analytics:', err);
      setError(err.message || 'Failed to load teacher analytics');
    } finally {
      setLoading(false);
    }
  }, [schoolId]);

  const refresh = useCallback(async () => {
    await fetchAnalytics();
  }, [fetchAnalytics]);

  // Auto-fetch on mount and when schoolId changes
  useEffect(() => {
    if (autoFetch && schoolId) {
      fetchAnalytics();
    }
  }, [autoFetch, schoolId, fetchAnalytics]);

  // Set up refresh interval if specified
  useEffect(() => {
    if (refreshInterval && refreshInterval > 0) {
      const interval = setInterval(() => {
        if (schoolId) {
          fetchAnalytics();
        }
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [refreshInterval, schoolId, fetchAnalytics]);

  // Computed analytics
  const getCompletionTrend = useCallback((): 'improving' | 'declining' | 'stable' => {
    if (!analytics) return 'stable';
    
    // This would need historical data to determine trend
    // For now, we'll use completion distribution as a proxy
    const { completion_distribution } = analytics;
    const highCompletion = completion_distribution['76-100%'] || 0;
    const lowCompletion = completion_distribution['0-25%'] || 0;
    
    if (highCompletion > lowCompletion * 2) return 'improving';
    if (lowCompletion > highCompletion * 2) return 'declining';
    return 'stable';
  }, [analytics]);

  const getHighPriorityIssues = useCallback((): string[] => {
    if (!analytics) return [];
    
    const issues: string[] = [];
    
    // Check for low completion rate
    if (analytics.average_completion < 50) {
      issues.push('Low average profile completion rate');
    }
    
    // Check for high number of incomplete profiles
    const incompletePercentage = (analytics.incomplete_profiles / analytics.total_teachers) * 100;
    if (incompletePercentage > 60) {
      issues.push('High number of incomplete teacher profiles');
    }
    
    // Check for common missing critical fields
    const criticalFields = analytics.common_missing_fields.filter(field => 
      ['bio', 'hourly_rate', 'teaching_subjects'].includes(field.field) && field.percentage > 30
    );
    
    if (criticalFields.length > 0) {
      issues.push(`Critical fields missing in many profiles: ${criticalFields.map(f => f.field).join(', ')}`);
    }
    
    // Check for teachers needing attention
    if (analytics.profile_completion_stats?.needs_attention?.length > 0) {
      issues.push(`${analytics.profile_completion_stats.needs_attention.length} teachers need immediate attention`);
    }
    
    return issues;
  }, [analytics]);

  const getTopMissingFields = useCallback((limit: number = 5) => {
    if (!analytics) return [];
    
    return analytics.common_missing_fields
      .slice(0, limit)
      .sort((a, b) => b.percentage - a.percentage);
  }, [analytics]);

  const getCompletionDistributionPercentages = useCallback((): Record<string, number> => {
    if (!analytics || analytics.total_teachers === 0) {
      return { '0-25%': 0, '26-50%': 0, '51-75%': 0, '76-100%': 0 };
    }
    
    const { completion_distribution, total_teachers } = analytics;
    
    return Object.entries(completion_distribution).reduce((acc, [range, count]) => {
      acc[range] = (count / total_teachers) * 100;
      return acc;
    }, {} as Record<string, number>);
  }, [analytics]);

  // Status helpers
  const isHealthy = useCallback((): boolean => {
    if (!analytics) return false;
    
    return (
      analytics.average_completion >= 70 &&
      analytics.complete_profiles / analytics.total_teachers >= 0.6 &&
      getHighPriorityIssues().length === 0
    );
  }, [analytics, getHighPriorityIssues]);

  const needsAttention = useCallback((): boolean => {
    if (!analytics) return false;
    
    return (
      analytics.average_completion < 50 ||
      analytics.incomplete_profiles / analytics.total_teachers > 0.7 ||
      getHighPriorityIssues().length > 2
    );
  }, [analytics, getHighPriorityIssues]);

  const getCriticalTeachersCount = useCallback((): number => {
    if (!analytics) return 0;
    
    return analytics.profile_completion_stats?.needs_attention?.length || 0;
  }, [analytics]);

  const getAverageCompletionGrade = useCallback((): 'A' | 'B' | 'C' | 'D' | 'F' => {
    if (!analytics) return 'F';
    
    const avg = analytics.average_completion;
    if (avg >= 90) return 'A';
    if (avg >= 80) return 'B';
    if (avg >= 70) return 'C';
    if (avg >= 60) return 'D';
    return 'F';
  }, [analytics]);

  return {
    analytics,
    loading,
    error,
    lastUpdated,
    
    // Actions
    fetchAnalytics,
    refresh,
    
    // Computed analytics
    getCompletionTrend,
    getHighPriorityIssues,
    getTopMissingFields,
    getCompletionDistributionPercentages,
    
    // Status helpers
    isHealthy,
    needsAttention,
    getCriticalTeachersCount,
    getAverageCompletionGrade
  };
};

export default useTeacherAnalytics;