import { useCallback, useEffect, useState } from 'react';

import { useAuth } from '@/api/authContext';
import {
  getSchoolActivity,
  getSchoolInfo,
  getSchoolMetrics,
  SchoolActivity,
  SchoolInfo,
  SchoolMetrics,
  updateSchoolInfo,
} from '@/api/userApi';
import { API_URL } from '@/constants/api';
import useWebSocket from './useWebSocket';

interface UseSchoolDashboardProps {
  schoolId: number;
  enableRealtime?: boolean;
  refreshInterval?: number;
}

interface SchoolDashboardWebSocketMessage {
  type: 'metrics_update' | 'activity_new' | 'invitation_status_update';
  data: any;
}

export const useSchoolDashboard = ({
  schoolId,
  enableRealtime = true,
  refreshInterval = 30000, // 30 seconds
}: UseSchoolDashboardProps) => {
  const { userProfile } = useAuth();
  
  // State management
  const [metrics, setMetrics] = useState<SchoolMetrics | null>(null);
  const [schoolInfo, setSchoolInfo] = useState<SchoolInfo | null>(null);
  const [activities, setActivities] = useState<SchoolActivity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination state for activities
  const [currentPage, setCurrentPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [totalActivities, setTotalActivities] = useState(0);

  // WebSocket URL configuration
  const wsUrl = API_URL.replace('http', 'ws').replace('/api', '') + `/ws/schools/${schoolId}/dashboard/`;

  // WebSocket message handler
  const handleWebSocketMessage = useCallback((message: any) => {
    console.log('Dashboard WebSocket message:', message);
    
    switch (message.type) {
      case 'metrics_update':
        setMetrics(prev => {
          if (!prev) return prev;
          return {
            ...prev,
            student_count: {
              ...prev.student_count,
              total: message.data.student_count?.total ?? prev.student_count.total,
            },
            teacher_count: {
              ...prev.teacher_count,
              total: message.data.teacher_count?.total ?? prev.teacher_count.total,
            },
            class_metrics: {
              ...prev.class_metrics,
              active_classes: message.data.active_classes?.total ?? prev.class_metrics.active_classes,
            },
          };
        });
        break;
        
      case 'activity_new':
        setActivities(prev => [message.data, ...prev]);
        setTotalActivities(prev => prev + 1);
        break;
        
      case 'invitation_status_update':
        // Refresh metrics when invitation status changes
        fetchMetrics();
        break;
        
      default:
        console.log('Unknown WebSocket message type:', message.type);
    }
  }, []);

  // WebSocket connection
  const { isConnected, error: wsError } = useWebSocket({
    url: wsUrl,
    channelName: `school_dashboard_${schoolId}`,
    onMessage: handleWebSocketMessage,
    shouldConnect: enableRealtime && !!userProfile && !!schoolId,
  });

  // API functions
  const fetchMetrics = useCallback(async () => {
    try {
      const data = await getSchoolMetrics(schoolId);
      setMetrics(data);
    } catch (err) {
      console.error('Error fetching school metrics:', err);
      setError('Falha ao carregar métricas da escola');
    }
  }, [schoolId]);

  const fetchSchoolInfo = useCallback(async () => {
    try {
      const data = await getSchoolInfo(schoolId);
      setSchoolInfo(data);
    } catch (err) {
      console.error('Error fetching school info:', err);
      setError('Falha ao carregar informações da escola');
    }
  }, [schoolId]);

  const fetchActivities = useCallback(async (page = 1, append = false) => {
    try {
      if (!append) {
        setIsLoading(page === 1);
      } else {
        setIsLoadingMore(true);
      }

      const data = await getSchoolActivity(schoolId, {
        page,
        page_size: 20,
      });

      if (append) {
        setActivities(prev => [...prev, ...data.results]);
      } else {
        setActivities(data.results);
      }

      setHasNextPage(!!data.next);
      setTotalActivities(data.count);
      setCurrentPage(page);
    } catch (err) {
      console.error('Error fetching school activities:', err);
      setError('Falha ao carregar atividades da escola');
    } finally {
      setIsLoading(false);
      setIsLoadingMore(false);
    }
  }, [schoolId]);

  const loadMoreActivities = useCallback(() => {
    if (!isLoadingMore && hasNextPage) {
      fetchActivities(currentPage + 1, true);
    }
  }, [fetchActivities, currentPage, hasNextPage, isLoadingMore]);

  const updateSchool = useCallback(async (data: Partial<SchoolInfo>) => {
    try {
      const updatedSchool = await updateSchoolInfo(schoolId, data);
      setSchoolInfo(updatedSchool);
      return updatedSchool;
    } catch (err) {
      console.error('Error updating school info:', err);
      throw new Error('Falha ao atualizar informações da escola');
    }
  }, [schoolId]);

  const refreshAll = useCallback(async () => {
    setError(null);
    setIsLoading(true);
    
    try {
      await Promise.all([
        fetchMetrics(),
        fetchSchoolInfo(),
        fetchActivities(1, false),
      ]);
    } catch (err) {
      console.error('Error refreshing dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [fetchMetrics, fetchSchoolInfo, fetchActivities]);

  // Auto-refresh functionality
  useEffect(() => {
    if (!enableRealtime && refreshInterval > 0) {
      const interval = setInterval(() => {
        fetchMetrics();
        fetchActivities(1, false);
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [enableRealtime, refreshInterval, fetchMetrics, fetchActivities]);

  // Initial data load
  useEffect(() => {
    if (schoolId && userProfile) {
      refreshAll();
    }
  }, [schoolId, userProfile, refreshAll]);

  // Clear error on school change
  useEffect(() => {
    setError(null);
  }, [schoolId]);

  return {
    // Data
    metrics,
    schoolInfo,
    activities,
    
    // Loading states
    isLoading,
    isLoadingMore,
    
    // Pagination
    currentPage,
    hasNextPage,
    totalActivities,
    
    // Error handling
    error,
    wsError,
    
    // WebSocket connection status
    isConnected,
    
    // Actions
    refreshAll,
    loadMoreActivities,
    updateSchool,
    fetchMetrics,
    fetchActivities,
    
    // Clear error
    clearError: () => setError(null),
  };
};

export default useSchoolDashboard;