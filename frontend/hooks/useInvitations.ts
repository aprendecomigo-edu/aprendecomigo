import { useState, useEffect, useCallback, useRef } from 'react';
import { Alert } from 'react-native';

import InvitationApi, {
  TeacherInvitation,
  InvitationListResponse,
  BulkInvitationRequest,
  BulkInvitationResponse,
  InvitationStatus,
  SchoolRole,
  TeacherProfileData,
} from '@/api/invitationApi';
import { INVITATION_CONSTANTS } from '@/constants/invitations';

// Enhanced error handling types
export interface InvitationError {
  code?: string;
  message: string;
  details?: Record<string, any>;
  timestamp?: string;
  path?: string;
  retryable?: boolean;
}

// Retry configuration
interface RetryConfig {
  maxAttempts: number;
  delay: number;
  backoffMultiplier: number;
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: INVITATION_CONSTANTS.DEFAULT_RETRY_ATTEMPTS,
  delay: INVITATION_CONSTANTS.RETRY_DELAY_MS,
  backoffMultiplier: INVITATION_CONSTANTS.RETRY_BACKOFF_MULTIPLIER,
};

// Enhanced error parsing
const parseInvitationError = (err: any): InvitationError => {
  const response = err.response;
  const data = response?.data;

  // Handle standardized backend error format
  if (data?.error) {
    return {
      code: data.error.code,
      message: data.error.message,
      details: data.error.details || {},
      timestamp: data.timestamp,
      path: data.path,
      retryable: isRetryableError(data.error.code),
    };
  }

  // Handle legacy error formats
  const message = data?.detail || data?.message || err.message || 'Unknown error';
  const code = getErrorCodeFromMessage(message, response?.status);

  return {
    code,
    message,
    retryable: isRetryableError(code),
    timestamp: new Date().toISOString(),
  };
};

// Determine error code from message and status
const getErrorCodeFromMessage = (message: string, status?: number): string => {
  if (status === 404) return 'INVITATION_NOT_FOUND';
  if (status === 401) return 'AUTHENTICATION_REQUIRED';
  if (status === 403) return 'PERMISSION_DENIED';
  if (status === 409) return 'DUPLICATE_MEMBERSHIP';
  if (status >= 500) return 'SERVER_ERROR';
  if (!navigator.onLine) return 'NETWORK_ERROR';

  // Check message content
  const lowerMessage = message.toLowerCase();
  if (lowerMessage.includes('expired')) return 'INVITATION_EXPIRED';
  if (lowerMessage.includes('not found')) return 'INVITATION_NOT_FOUND';
  if (lowerMessage.includes('already')) return 'INVITATION_ALREADY_PROCESSED';
  if (lowerMessage.includes('network')) return 'NETWORK_ERROR';

  return 'UNKNOWN_ERROR';
};

// Determine if error is retryable
const isRetryableError = (code?: string): boolean => {
  const retryableCodes = ['NETWORK_ERROR', 'SERVER_ERROR', 'TIMEOUT_ERROR', 'UNKNOWN_ERROR'];
  return retryableCodes.includes(code || '');
};

// Retry utility with exponential backoff
const retryWithBackoff = async <T>(
  fn: () => Promise<T>,
  config: RetryConfig = DEFAULT_RETRY_CONFIG,
): Promise<T> => {
  let lastError: any;

  for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      const parsedError = parseInvitationError(error);

      // Don't retry if error is not retryable
      if (!parsedError.retryable) {
        throw error;
      }

      // Don't retry on last attempt
      if (attempt === config.maxAttempts) {
        throw error;
      }

      // Calculate delay with exponential backoff
      const delay = config.delay * Math.pow(config.backoffMultiplier, attempt - 1);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError;
};

// Hook for managing teacher invitations (admin view)
export const useInvitations = (autoFetch = true) => {
  const [invitations, setInvitations] = useState<TeacherInvitation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null as string | null,
    previous: null as string | null,
    currentPage: 1,
  });

  // Use ref to store current page to prevent re-render loops
  const currentPageRef = useRef(1);
  // Use ref to store autoFetch value to prevent re-render loops
  const autoFetchRef = useRef(autoFetch);
  autoFetchRef.current = autoFetch;

  const fetchInvitations = useCallback(
    async (params?: {
      page?: number;
      status?: InvitationStatus;
      email?: string;
      role?: SchoolRole;
      ordering?: string;
    }) => {
      try {
        setLoading(true);
        setError(null);

        const response = await InvitationApi.getSchoolInvitations(params);

        const currentPage = params?.page || 1;
        currentPageRef.current = currentPage;

        setInvitations(response.results);
        setPagination({
          count: response.count,
          next: response.next || null,
          previous: response.previous || null,
          currentPage,
        });
      } catch (err: any) {
        const errorMessage =
          err.response?.data?.detail || err.message || 'Failed to fetch invitations';
        setError(errorMessage);
        console.error('Error fetching invitations:', err);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const refreshInvitations = useCallback(() => {
    fetchInvitations({ page: currentPageRef.current });
  }, [fetchInvitations]);

  // Fixed: Remove fetchInvitations from dependency array to prevent infinite loop
  useEffect(() => {
    if (autoFetchRef.current) {
      fetchInvitations();
    }
  }, []); // Only run once on mount

  return {
    invitations,
    loading,
    error,
    pagination,
    fetchInvitations,
    refreshInvitations,
  };
};

// Hook for inviting a single teacher
export const useInviteTeacher = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const inviteTeacher = useCallback(
    async (data: {
      email: string;
      school_id: number;
      role: SchoolRole;
      custom_message?: string;
    }) => {
      try {
        setLoading(true);
        setError(null);

        const invitation = await InvitationApi.inviteExistingTeacher(data);
        return invitation;
      } catch (err: any) {
        const errorMessage =
          err.response?.data?.detail ||
          err.response?.data?.error ||
          err.message ||
          'Failed to send invitation';
        setError(errorMessage);
        Alert.alert('Error', errorMessage);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  return {
    inviteTeacher,
    loading,
    error,
  };
};

// Hook for bulk invitations
export const useBulkInvitations = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<{
    total: number;
    completed: number;
    failed: number;
  }>({ total: 0, completed: 0, failed: 0 });

  const sendBulkInvitations = useCallback(async (data: BulkInvitationRequest) => {
    try {
      setLoading(true);
      setError(null);
      setProgress({ total: data.invitations.length, completed: 0, failed: 0 });

      const response = await InvitationApi.sendBulkInvitations(data);

      setProgress({
        total: response.summary.total_requested,
        completed: response.summary.total_created,
        failed: response.summary.total_errors,
      });

      return response;
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        err.response?.data?.error ||
        err.message ||
        'Failed to send bulk invitations';
      setError(errorMessage);
      Alert.alert('Error', errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const resetProgress = useCallback(() => {
    setProgress({ total: 0, completed: 0, failed: 0 });
    setError(null);
  }, []);

  return {
    sendBulkInvitations,
    loading,
    error,
    progress,
    resetProgress,
  };
};

// Hook for managing individual invitation actions with enhanced error handling
export const useInvitationActions = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<InvitationError | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const cancelInvitation = useCallback(async (token: string) => {
    try {
      setLoading(true);
      setError(null);

      const result = await InvitationApi.cancelInvitation(token);
      Alert.alert('Success', 'Invitation cancelled successfully');
      return result;
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || 'Failed to cancel invitation';
      setError(errorMessage);
      Alert.alert('Error', errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const resendInvitation = useCallback(async (token: string) => {
    try {
      setLoading(true);
      setError(null);

      const result = await InvitationApi.resendInvitation(token);
      Alert.alert('Success', 'Invitation resent successfully');
      return result;
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || 'Failed to resend invitation';
      setError(errorMessage);
      Alert.alert('Error', errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const acceptInvitation = useCallback(
    async (token: string, profileData?: TeacherProfileData, retryConfig?: Partial<RetryConfig>) => {
      try {
        setLoading(true);
        setError(null);
        setRetryCount(0);

        const result = await retryWithBackoff(
          () => InvitationApi.acceptInvitation(token, profileData),
          { ...DEFAULT_RETRY_CONFIG, ...retryConfig },
        );

        return result;
      } catch (err: any) {
        const parsedError = parseInvitationError(err);
        setError(parsedError);

        // Only show alert for non-retryable errors or final failure
        if (!parsedError.retryable) {
          Alert.alert('Erro', parsedError.message);
        }

        throw parsedError;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const declineInvitation = useCallback(
    async (token: string, retryConfig?: Partial<RetryConfig>) => {
      try {
        setLoading(true);
        setError(null);
        setRetryCount(0);

        const result = await retryWithBackoff(() => InvitationApi.declineInvitation(token), {
          ...DEFAULT_RETRY_CONFIG,
          ...retryConfig,
        });

        return result;
      } catch (err: any) {
        const parsedError = parseInvitationError(err);
        setError(parsedError);
        Alert.alert('Erro', parsedError.message);
        throw parsedError;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const getInvitationStatus = useCallback(
    async (token: string, retryConfig?: Partial<RetryConfig>) => {
      try {
        setLoading(true);
        setError(null);
        setRetryCount(0);

        const result = await retryWithBackoff(() => InvitationApi.getInvitationStatus(token), {
          ...DEFAULT_RETRY_CONFIG,
          ...retryConfig,
        });

        return result;
      } catch (err: any) {
        const parsedError = parseInvitationError(err);
        setError(parsedError);
        throw parsedError;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  // Retry last failed operation
  const retryLastOperation = useCallback(async () => {
    if (!error?.retryable) {
      throw new Error('Last operation is not retryable');
    }
    setRetryCount(prev => prev + 1);
    // The specific retry logic would depend on which operation failed
    // This is a placeholder for the retry mechanism
  }, [error]);

  // Clear error state
  const clearError = useCallback(() => {
    setError(null);
    setRetryCount(0);
  }, []);

  return {
    cancelInvitation,
    resendInvitation,
    acceptInvitation,
    declineInvitation,
    getInvitationStatus,
    retryLastOperation,
    clearError,
    loading,
    error,
    retryCount,
    canRetry: error?.retryable ?? false,
  };
};

// Hook for polling invitation status updates
export const useInvitationPolling = (
  refreshCallback: () => void,
  intervalMs = INVITATION_CONSTANTS.STATUS_POLLING_INTERVAL,
) => {
  const [isPolling, setIsPolling] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const refreshCallbackRef = useRef(refreshCallback);

  // Update callback ref without causing re-renders
  refreshCallbackRef.current = refreshCallback;

  const startPolling = useCallback(() => {
    if (intervalRef.current) return; // Already polling

    setIsPolling(true);
    intervalRef.current = setInterval(() => {
      refreshCallbackRef.current();
    }, intervalMs);
  }, [intervalMs]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    isPolling,
    startPolling,
    stopPolling,
  };
};
