import { useState, useEffect, useCallback } from 'react';
import { Alert } from 'react-native';

import InvitationApi, {
  TeacherInvitation,
  InvitationListResponse,
  BulkInvitationRequest,
  BulkInvitationResponse,
  InvitationStatus,
  SchoolRole,
} from '@/api/invitationApi';

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

  const fetchInvitations = useCallback(async (params?: {
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
      
      setInvitations(response.results);
      setPagination({
        count: response.count,
        next: response.next || null,
        previous: response.previous || null,
        currentPage: params?.page || 1,
      });
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch invitations';
      setError(errorMessage);
      console.error('Error fetching invitations:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshInvitations = useCallback(() => {
    fetchInvitations({ page: pagination.currentPage });
  }, [fetchInvitations, pagination.currentPage]);

  useEffect(() => {
    if (autoFetch) {
      fetchInvitations();
    }
  }, [autoFetch, fetchInvitations]);

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

  const inviteTeacher = useCallback(async (data: {
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
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.error || 
                          err.message || 
                          'Failed to send invitation';
      setError(errorMessage);
      Alert.alert('Error', errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

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
      const errorMessage = err.response?.data?.detail || 
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

// Hook for managing individual invitation actions
export const useInvitationActions = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cancelInvitation = useCallback(async (token: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await InvitationApi.cancelInvitation(token);
      Alert.alert('Success', 'Invitation cancelled successfully');
      return result;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to cancel invitation';
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
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to resend invitation';
      setError(errorMessage);
      Alert.alert('Error', errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const acceptInvitation = useCallback(async (token: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await InvitationApi.acceptInvitation(token);
      Alert.alert('Success', 'Invitation accepted successfully');
      return result;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to accept invitation';
      setError(errorMessage);
      Alert.alert('Error', errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getInvitationStatus = useCallback(async (token: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await InvitationApi.getInvitationStatus(token);
      return result;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to get invitation status';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    cancelInvitation,
    resendInvitation,
    acceptInvitation,
    getInvitationStatus,
    loading,
    error,
  };
};

// Hook for polling invitation status updates
export const useInvitationPolling = (
  refreshCallback: () => void,
  intervalMs = 30000 // 30 seconds
) => {
  const [isPolling, setIsPolling] = useState(false);

  const startPolling = useCallback(() => {
    if (isPolling) return;
    
    setIsPolling(true);
    const interval = setInterval(() => {
      refreshCallback();
    }, intervalMs);

    return () => {
      clearInterval(interval);
      setIsPolling(false);
    };
  }, [isPolling, refreshCallback, intervalMs]);

  const stopPolling = useCallback(() => {
    setIsPolling(false);
  }, []);

  return {
    isPolling,
    startPolling,
    stopPolling,
  };
};