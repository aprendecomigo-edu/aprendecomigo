import { useState, useEffect, useCallback } from 'react';
import { Alert } from 'react-native';

import { InvitationError } from './useInvitations';

import apiClient from '@/api/apiClient';

// Types for multi-school functionality
export interface SchoolMembership {
  id: number;
  school: {
    id: number;
    name: string;
    description?: string;
    logo_url?: string;
    website?: string;
    phone?: string;
    email?: string;
    address?: string;
  };
  role: 'teacher' | 'school_admin' | 'school_owner';
  is_active: boolean;
  joined_at: string;
  status: 'active' | 'inactive' | 'pending' | 'suspended';
  permissions: string[];
}

export interface PendingInvitation {
  id: string;
  school: {
    id: number;
    name: string;
    logo_url?: string;
  };
  role: 'teacher' | 'school_admin' | 'school_owner';
  invited_by: {
    name: string;
    email: string;
  };
  expires_at: string;
  custom_message?: string;
  token: string;
}

export interface SchoolStats {
  total_students: number;
  total_teachers: number;
  active_sessions_count: number;
  monthly_revenue?: number;
}

// Hook for managing multi-school functionality
export const useMultiSchool = () => {
  const [memberships, setMemberships] = useState<SchoolMembership[]>([]);
  const [pendingInvitations, setPendingInvitations] = useState<PendingInvitation[]>([]);
  const [currentSchool, setCurrentSchool] = useState<SchoolMembership | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<InvitationError | null>(null);

  // Fetch all school memberships for the current user
  const fetchMemberships = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.get('/accounts/school-memberships/');
      const membershipData = response.data.results || response.data;

      setMemberships(membershipData);

      // Set current school if none is selected
      if (!currentSchool && membershipData.length > 0) {
        const activeMembership =
          membershipData.find((m: SchoolMembership) => m.is_active) || membershipData[0];
        setCurrentSchool(activeMembership);
      }
    } catch (err: any) {
      const parsedError: InvitationError = {
        code: 'FETCH_MEMBERSHIPS_ERROR',
        message: err.response?.data?.detail || 'Falha ao carregar suas escolas',
        retryable: true,
      };
      setError(parsedError);
    } finally {
      setLoading(false);
    }
  }, [currentSchool]);

  // Fetch pending invitations for the current user
  const fetchPendingInvitations = useCallback(async () => {
    try {
      const response = await apiClient.get('/accounts/teacher-invitations/pending/');
      setPendingInvitations(response.data.results || response.data);
    } catch (err: any) {
      console.error('Failed to fetch pending invitations:', err);
      // Don't set error state for this as it's not critical
    }
  }, []);

  // Switch to a different school context
  const switchSchool = useCallback(async (membership: SchoolMembership) => {
    try {
      setLoading(true);
      setError(null);

      // Update user's active school on the backend
      await apiClient.patch(`/accounts/school-memberships/${membership.id}/`, {
        is_active: true,
      });

      // Update local state
      setCurrentSchool(membership);

      // Update all memberships to reflect new active status
      setMemberships(prev =>
        prev.map(m => ({
          ...m,
          is_active: m.id === membership.id,
        }))
      );

      Alert.alert('Escola Alterada', `Você agora está visualizando ${membership.school.name}`, [
        { text: 'OK' },
      ]);
    } catch (err: any) {
      const parsedError: InvitationError = {
        code: 'SWITCH_SCHOOL_ERROR',
        message: 'Falha ao alterar escola. Tente novamente.',
        retryable: true,
      };
      setError(parsedError);
    } finally {
      setLoading(false);
    }
  }, []);

  // Leave a school (with confirmation)
  const leaveSchool = useCallback(
    async (membershipId: number, schoolName: string) => {
      return new Promise<void>((resolve, reject) => {
        Alert.alert(
          'Sair da Escola',
          `Tem certeza de que deseja sair da escola "${schoolName}"? Esta ação não pode ser desfeita.`,
          [
            { text: 'Cancelar', style: 'cancel', onPress: () => resolve() },
            {
              text: 'Sair',
              style: 'destructive',
              onPress: async () => {
                try {
                  setLoading(true);
                  await apiClient.delete(`/accounts/school-memberships/${membershipId}/`);

                  // Remove from local state
                  setMemberships(prev => prev.filter(m => m.id !== membershipId));

                  // If this was the current school, switch to another one
                  if (currentSchool?.id === membershipId) {
                    const remainingMemberships = memberships.filter(m => m.id !== membershipId);
                    setCurrentSchool(remainingMemberships[0] || null);
                  }

                  Alert.alert('Sucesso', `Você saiu da escola "${schoolName}".`);
                  resolve();
                } catch (err: any) {
                  const parsedError: InvitationError = {
                    code: 'LEAVE_SCHOOL_ERROR',
                    message: 'Falha ao sair da escola. Tente novamente.',
                    retryable: true,
                  };
                  setError(parsedError);
                  reject(parsedError);
                } finally {
                  setLoading(false);
                }
              },
            },
          ]
        );
      });
    },
    [currentSchool, memberships]
  );

  // Get school statistics
  const getSchoolStats = useCallback(async (schoolId: number): Promise<SchoolStats | null> => {
    try {
      const response = await apiClient.get(`/accounts/schools/${schoolId}/stats/`);
      return response.data;
    } catch (err: any) {
      console.error('Failed to fetch school stats:', err);
      return null;
    }
  }, []);

  // Refresh all data
  const refresh = useCallback(async () => {
    await Promise.all([fetchMemberships(), fetchPendingInvitations()]);
  }, [fetchMemberships, fetchPendingInvitations]);

  // Clear error state
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Initialize data on mount
  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    // Data
    memberships,
    pendingInvitations,
    currentSchool,

    // State
    loading,
    error,

    // Actions
    fetchMemberships,
    fetchPendingInvitations,
    switchSchool,
    leaveSchool,
    getSchoolStats,
    refresh,
    clearError,

    // Computed values
    hasMultipleSchools: memberships.length > 1,
    hasPendingInvitations: pendingInvitations.length > 0,
    totalSchools: memberships.length,
  };
};

export default useMultiSchool;
