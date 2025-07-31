import { useCallback, useEffect, useState } from 'react';

import { getTutorAnalytics, TutorAnalytics } from '@/api/tutorApi';
import { useAuth } from '@/api/authContext';

interface UseTutorAnalyticsResult {
  analytics: TutorAnalytics | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

const useTutorAnalytics = (schoolId?: number): UseTutorAnalyticsResult => {
  const { userProfile } = useAuth();
  const [analytics, setAnalytics] = useState<TutorAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const data = await getTutorAnalytics(schoolId);
      setAnalytics(data);
    } catch (err) {
      console.error('Error fetching tutor analytics:', err);
      setError('Falha ao carregar métricas de negócio');
    } finally {
      setIsLoading(false);
    }
  }, [schoolId]);

  const refresh = useCallback(async () => {
    await fetchAnalytics();
  }, [fetchAnalytics]);

  useEffect(() => {
    if (userProfile) {
      fetchAnalytics();
    }
  }, [userProfile, fetchAnalytics]);

  return {
    analytics,
    isLoading,
    error,
    refresh,
  };
};

// Export both named and default exports for compatibility
export { useTutorAnalytics };
export default useTutorAnalytics;