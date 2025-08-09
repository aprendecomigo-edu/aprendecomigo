import { useState, useEffect, useCallback } from 'react';

import { schedulerApi, ClassSchedule } from '@/api/schedulerApi';

export interface UseSchedulesResult {
  schedules: ClassSchedule[];
  loading: boolean;
  error: string | null;
  refreshSchedules: () => Promise<void>;
  getMyClasses: () => Promise<void>;
}

export const useSchedules = (autoFetch: boolean = true): UseSchedulesResult => {
  const [schedules, setSchedules] = useState<ClassSchedule[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSchedules = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch user's classes (upcoming classes)
      const schedulesData = await schedulerApi.getMyClasses();
      setSchedules(schedulesData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch schedules';
      setError(errorMessage);
      console.error('Error fetching schedules:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshSchedules = useCallback(async () => {
    await fetchSchedules();
  }, [fetchSchedules]);

  const getMyClasses = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const classesData = await schedulerApi.getMyClasses();
      setSchedules(classesData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch user classes';
      setError(errorMessage);
      console.error('Error fetching user classes:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (autoFetch) {
      fetchSchedules();
    }
  }, [autoFetch, fetchSchedules]);

  return {
    schedules,
    loading,
    error,
    refreshSchedules,
    getMyClasses,
  };
};

export default useSchedules;
