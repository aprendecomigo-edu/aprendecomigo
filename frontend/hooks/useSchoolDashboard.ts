import { useCallback, useEffect, useState } from 'react';

import { useUserProfile } from '@/api/auth';
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

// Error types for better error handling
export interface DashboardError {
  type: 'network' | 'permission' | 'validation' | 'server' | 'unknown';
  message: string;
  details?: string;
  canRetry: boolean;
}

// Helper function to categorize and format errors
const createDashboardError = (error: any, context: string): DashboardError => {
  console.error(`Dashboard error in ${context}:`, error);

  // Network errors
  if (!error.response || error.code === 'ERR_NETWORK' || error.code === 'ERR_CONNECTION_REFUSED') {
    return {
      type: 'network',
      message: 'Não foi possível conectar ao servidor. Verifique sua conexão com a internet.',
      details:
        'Tente novamente em alguns momentos ou entre em contato com o suporte se o problema persistir.',
      canRetry: true,
    };
  }

  // Permission errors
  if (error.response?.status === 403) {
    return {
      type: 'permission',
      message: 'Você não tem permissão para acessar estes dados.',
      details: 'Entre em contato com o administrador da escola para verificar suas permissões.',
      canRetry: false,
    };
  }

  // Not found errors
  if (error.response?.status === 404) {
    return {
      type: 'validation',
      message: 'Escola não encontrada.',
      details: 'A escola pode ter sido removida ou você pode não ter acesso a ela.',
      canRetry: false,
    };
  }

  // Authentication errors
  if (error.response?.status === 401) {
    return {
      type: 'permission',
      message: 'Sessão expirada. Por favor, faça login novamente.',
      details: 'Sua sessão de autenticação expirou por motivos de segurança.',
      canRetry: false,
    };
  }

  // Server errors
  if (error.response?.status >= 500) {
    return {
      type: 'server',
      message: 'Erro interno do servidor. Tente novamente em alguns momentos.',
      details: 'Nossos servidores estão passando por dificuldades temporárias.',
      canRetry: true,
    };
  }

  // Validation errors
  if (error.response?.status >= 400 && error.response?.status < 500) {
    const errorMessage =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      'Dados inválidos fornecidos.';
    return {
      type: 'validation',
      message: errorMessage,
      details: 'Verifique os dados fornecidos e tente novamente.',
      canRetry: true,
    };
  }

  // Unknown errors
  return {
    type: 'unknown',
    message: 'Ocorreu um erro inesperado.',
    details: error.message || 'Tente atualizar a página ou entre em contato com o suporte.',
    canRetry: true,
  };
};

interface UseSchoolDashboardProps {
  schoolId: number;
  refreshInterval?: number;
}

export const useSchoolDashboard = ({
  schoolId,
  refreshInterval = 30000, // 30 seconds
}: UseSchoolDashboardProps) => {
  const { userProfile } = useUserProfile();

  // State management
  const [metrics, setMetrics] = useState<SchoolMetrics | null>(null);
  const [schoolInfo, setSchoolInfo] = useState<SchoolInfo | null>(null);
  const [activities, setActivities] = useState<SchoolActivity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<DashboardError | null>(null);

  // Pagination state for activities
  const [currentPage, setCurrentPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [totalActivities, setTotalActivities] = useState(0);

  // API functions
  const fetchMetrics = useCallback(async () => {
    try {
      const data = await getSchoolMetrics(schoolId);
      setMetrics(data);
      // Clear error on success
      if (error?.type !== 'network') {
        setError(null);
      }
    } catch (err) {
      const dashboardError = createDashboardError(err, 'fetchMetrics');
      setError(dashboardError);
    }
  }, [schoolId, error?.type]);

  const fetchSchoolInfo = useCallback(async () => {
    try {
      const data = await getSchoolInfo(schoolId);
      setSchoolInfo(data);
      // Clear error on success
      if (error?.type !== 'network') {
        setError(null);
      }
    } catch (err) {
      const dashboardError = createDashboardError(err, 'fetchSchoolInfo');
      setError(dashboardError);
    }
  }, [schoolId, error?.type]);

  const fetchActivities = useCallback(
    async (page = 1, append = false) => {
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

        // Clear error on success
        if (error?.type !== 'network') {
          setError(null);
        }
      } catch (err) {
        const dashboardError = createDashboardError(err, 'fetchActivities');
        setError(dashboardError);
      } finally {
        setIsLoading(false);
        setIsLoadingMore(false);
      }
    },
    [schoolId, error?.type],
  );

  const loadMoreActivities = useCallback(() => {
    if (!isLoadingMore && hasNextPage) {
      fetchActivities(currentPage + 1, true);
    }
  }, [fetchActivities, currentPage, hasNextPage, isLoadingMore]);

  const updateSchool = useCallback(
    async (data: Partial<SchoolInfo>) => {
      try {
        const updatedSchool = await updateSchoolInfo(schoolId, data);
        setSchoolInfo(updatedSchool);
        return updatedSchool;
      } catch (err) {
        const dashboardError = createDashboardError(err, 'updateSchool');
        // For update operations, we throw the formatted error so the UI can handle it
        throw new Error(dashboardError.message);
      }
    },
    [schoolId],
  );

  const refreshAll = useCallback(async () => {
    setError(null);
    setIsLoading(true);

    try {
      // Use Promise.allSettled for graceful degradation
      const results = await Promise.allSettled([
        fetchMetrics(),
        fetchSchoolInfo(),
        fetchActivities(1, false),
      ]);

      // Log any failures for monitoring
      const operations = ['metrics', 'school info', 'activities'];
      results.forEach((result, index) => {
        if (result.status === 'rejected') {
          console.error(`Failed to refresh ${operations[index]}:`, result.reason);
        }
      });

      // Individual error states are handled by the respective functions
    } catch (err) {
      // This catch is for any unexpected errors during parallel execution
      console.error('Error refreshing dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [fetchMetrics, fetchSchoolInfo, fetchActivities]);

  // Auto-refresh functionality
  useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(() => {
        fetchMetrics();
        fetchActivities(1, false);
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [refreshInterval, fetchMetrics, fetchActivities]);

  // Initial data load and school change handling
  useEffect(() => {
    if (schoolId && schoolId > 0 && userProfile) {
      // Clear previous data when school changes
      setMetrics(null);
      setSchoolInfo(null);
      setActivities([]);
      setCurrentPage(1);
      setHasNextPage(false);
      setTotalActivities(0);
      setError(null);

      refreshAll();
    }
  }, [schoolId, userProfile, refreshAll]);

  // Retry mechanism for failed requests
  const retryOperation = useCallback(async (operation: () => Promise<void>, maxRetries = 3) => {
    let lastError: any;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        await operation();
        return; // Success
      } catch (error) {
        lastError = error;

        // Don't retry for permission or validation errors
        if (
          (error as any).response?.status === 401 ||
          (error as any).response?.status === 403 ||
          (error as any).response?.status === 404
        ) {
          throw error;
        }

        // Wait before retrying (exponential backoff)
        if (attempt < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
        }
      }
    }

    throw lastError;
  }, []);

  // Enhanced refresh with retry logic
  const refreshAllWithRetry = useCallback(async () => {
    if (!schoolId || schoolId <= 0) return;

    setError(null);
    setIsLoading(true);

    try {
      await retryOperation(async () => {
        // Use Promise.allSettled for graceful degradation even within retry
        const results = await Promise.allSettled([
          fetchMetrics(),
          fetchSchoolInfo(),
          fetchActivities(1, false),
        ]);

        // Log any failures for monitoring
        const operations = ['metrics', 'school info', 'activities'];
        results.forEach((result, index) => {
          if (result.status === 'rejected') {
            console.error(`Failed to refresh ${operations[index]} during retry:`, result.reason);
          }
        });
      });
    } catch (err) {
      // Error is already set by individual fetch functions
      console.error('Failed to refresh after retries:', err);
    } finally {
      setIsLoading(false);
    }
  }, [schoolId, retryOperation, fetchMetrics, fetchSchoolInfo, fetchActivities]);

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

    // Actions
    refreshAll,
    refreshAllWithRetry,
    loadMoreActivities,
    updateSchool,
    fetchMetrics,
    fetchActivities,
    retryOperation,

    // Clear error
    clearError: () => setError(null),
  };
};

export default useSchoolDashboard;
