import { renderHook, act, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';

import {
  multiSchoolScenarios,
  mockApiResponses,
  createMockApiClient,
  createMockSchoolMembership,
} from '../utils/multi-school-test-utils';

import apiClient from '@/api/apiClient';
import { useMultiSchool } from '@/hooks/useMultiSchool';

// Mock the API client
jest.mock('@/api/apiClient', () => ({
  default: {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
    put: jest.fn(),
  },
  __esModule: true,
}));
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

// Mock React Native Alert
jest.spyOn(Alert, 'alert');

describe('useMultiSchool Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Default successful responses
    mockedApiClient.get.mockImplementation((url: string) => {
      if (url.includes('/school-memberships/')) {
        return Promise.resolve({ data: mockApiResponses.memberships.success });
      }
      if (url.includes('/teacher-invitations/pending/')) {
        return Promise.resolve({ data: mockApiResponses.pendingInvitations.success });
      }
      if (url.includes('/stats/')) {
        return Promise.resolve({ data: mockApiResponses.schoolStats.success });
      }
      return Promise.resolve({ data: {} });
    });
    mockedApiClient.patch.mockResolvedValue({ data: mockApiResponses.switchSchool.success });
    mockedApiClient.delete.mockResolvedValue({ data: { success: true } });
  });

  describe('Initial State and Data Loading', () => {
    it('should initialize with empty state', () => {
      const { result } = renderHook(() => useMultiSchool());

      expect(result.current.memberships).toEqual([]);
      expect(result.current.pendingInvitations).toEqual([]);
      expect(result.current.currentSchool).toBeNull();
      expect(result.current.loading).toBe(true); // Loading on initial mount
      expect(result.current.error).toBeNull();
    });

    it('should fetch memberships and invitations on mount', async () => {
      renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(mockedApiClient.get).toHaveBeenCalledWith('/accounts/school-memberships/');
        expect(mockedApiClient.get).toHaveBeenCalledWith('/accounts/teacher-invitations/pending/');
      });
    });

    it('should set current school from active membership', async () => {
      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.currentSchool).toBeTruthy();
        expect(result.current.currentSchool?.school.name).toBe('Escola Vila Nova');
        expect(result.current.loading).toBe(false);
      });
    });

    it('should handle memberships response with results array', async () => {
      mockedApiClient.get.mockImplementation((url: string) => {
        if (url.includes('/school-memberships/')) {
          return Promise.resolve({
            data: { results: mockApiResponses.memberships.success.results },
          });
        }
        return Promise.resolve({ data: {} });
      });

      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.memberships).toHaveLength(2);
      });
    });
  });

  describe('School Switching', () => {
    it('should switch to different school successfully', async () => {
      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const newSchool = createMockSchoolMembership({
        id: 2,
        school: { id: 2, name: 'New School' },
        is_active: false,
      });

      await act(async () => {
        await result.current.switchSchool(newSchool);
      });

      expect(mockedApiClient.patch).toHaveBeenCalledWith('/accounts/school-memberships/2/', {
        is_active: true,
      });
      expect(result.current.currentSchool).toEqual(newSchool);
      expect(Alert.alert).toHaveBeenCalledWith(
        'Escola Alterada',
        'Você agora está visualizando New School',
        [{ text: 'OK' }],
      );
    });

    it('should update memberships active status after switching', async () => {
      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const newSchool = createMockSchoolMembership({
        id: 2,
        school: { id: 2, name: 'New School' },
        is_active: false,
      });

      await act(async () => {
        await result.current.switchSchool(newSchool);
      });

      // Verify memberships are updated with new active status
      const updatedMembership = result.current.memberships.find(m => m.id === 2);
      expect(updatedMembership?.is_active).toBe(true);
    });

    it('should handle switch school errors', async () => {
      mockedApiClient.patch.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const newSchool = createMockSchoolMembership({ id: 2 });

      await act(async () => {
        await result.current.switchSchool(newSchool);
      });

      expect(result.current.error).toEqual({
        code: 'SWITCH_SCHOOL_ERROR',
        message: 'Falha ao alterar escola. Tente novamente.',
        retryable: true,
      });
      expect(result.current.loading).toBe(false);
    });

    it('should show loading state while switching', async () => {
      let resolveSwitch: (value: any) => void;
      mockedApiClient.patch.mockImplementation(
        () =>
          new Promise(resolve => {
            resolveSwitch = resolve;
          }),
      );

      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const newSchool = createMockSchoolMembership({ id: 2 });

      act(() => {
        result.current.switchSchool(newSchool);
      });

      expect(result.current.loading).toBe(true);

      act(() => {
        resolveSwitch!({ data: { success: true } });
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });
  });

  describe('School Management', () => {
    it('should leave school with confirmation', async () => {
      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const schoolId = 1;
      const schoolName = 'Test School';

      // Mock Alert.alert to simulate user confirmation
      (Alert.alert as jest.Mock).mockImplementation((title, message, buttons) => {
        const confirmButton = buttons?.find((b: any) => b.style === 'destructive');
        if (confirmButton) {
          confirmButton.onPress();
        }
      });

      await act(async () => {
        await result.current.leaveSchool(schoolId, schoolName);
      });

      expect(Alert.alert).toHaveBeenCalledWith(
        'Sair da Escola',
        'Tem certeza de que deseja sair da escola "Test School"? Esta ação não pode ser desfeita.',
        expect.any(Array),
      );
      expect(mockedApiClient.delete).toHaveBeenCalledWith('/accounts/school-memberships/1/');
    });

    it('should handle leave school cancellation', async () => {
      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Mock Alert.alert to simulate user cancellation
      (Alert.alert as jest.Mock).mockImplementation((title, message, buttons) => {
        const cancelButton = buttons?.find((b: any) => b.style === 'cancel');
        if (cancelButton) {
          cancelButton.onPress();
        }
      });

      await act(async () => {
        await result.current.leaveSchool(1, 'Test School');
      });

      expect(mockedApiClient.delete).not.toHaveBeenCalled();
    });

    it('should update state after leaving school', async () => {
      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
        expect(result.current.memberships).toHaveLength(2);
      });

      // Mock Alert to confirm leaving
      (Alert.alert as jest.Mock).mockImplementation((title, message, buttons) => {
        const confirmButton = buttons?.find((b: any) => b.style === 'destructive');
        if (confirmButton) {
          confirmButton.onPress();
        }
      });

      await act(async () => {
        await result.current.leaveSchool(1, 'Test School');
      });

      expect(result.current.memberships).toHaveLength(1);
    });
  });

  describe('School Statistics', () => {
    it('should fetch school statistics successfully', async () => {
      const { result } = renderHook(() => useMultiSchool());

      let stats;
      await act(async () => {
        stats = await result.current.getSchoolStats(1);
      });

      expect(mockedApiClient.get).toHaveBeenCalledWith('/accounts/schools/1/stats/');
      expect(stats).toEqual(mockApiResponses.schoolStats.success);
    });

    it('should handle school statistics errors gracefully', async () => {
      mockedApiClient.get.mockImplementation((url: string) => {
        if (url.includes('/stats/')) {
          return Promise.reject(new Error('Stats error'));
        }
        return Promise.resolve({ data: mockApiResponses.memberships.success });
      });

      const { result } = renderHook(() => useMultiSchool());

      let stats;
      await act(async () => {
        stats = await result.current.getSchoolStats(1);
      });

      expect(stats).toBeNull();
    });
  });

  describe('Error Handling', () => {
    it('should handle memberships fetch errors', async () => {
      mockedApiClient.get.mockImplementation((url: string) => {
        if (url.includes('/school-memberships/')) {
          return Promise.reject({
            response: { data: { detail: 'Access denied' } },
          });
        }
        return Promise.resolve({ data: [] });
      });

      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.error).toEqual({
          code: 'FETCH_MEMBERSHIPS_ERROR',
          message: 'Access denied',
          retryable: true,
        });
        expect(result.current.loading).toBe(false);
      });
    });

    it('should handle invitations fetch errors silently', async () => {
      mockedApiClient.get.mockImplementation((url: string) => {
        if (url.includes('/teacher-invitations/pending/')) {
          return Promise.reject(new Error('Invitations error'));
        }
        if (url.includes('/school-memberships/')) {
          return Promise.resolve({ data: mockApiResponses.memberships.success });
        }
        return Promise.resolve({ data: {} });
      });

      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
        // Should not set error for invitations failure
        expect(result.current.error).toBeNull();
        expect(result.current.pendingInvitations).toEqual([]);
      });
    });

    it('should clear errors when requested', async () => {
      mockedApiClient.get.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('Data Refresh', () => {
    it('should refresh all data when requested', async () => {
      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Clear previous calls
      jest.clearAllMocks();

      await act(async () => {
        await result.current.refresh();
      });

      expect(mockedApiClient.get).toHaveBeenCalledWith('/accounts/school-memberships/');
      expect(mockedApiClient.get).toHaveBeenCalledWith('/accounts/teacher-invitations/pending/');
    });
  });

  describe('Computed Values', () => {
    it('should calculate hasMultipleSchools correctly', async () => {
      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.hasMultipleSchools).toBe(true); // Mock returns 2 schools
      });
    });

    it('should calculate hasPendingInvitations correctly', async () => {
      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.hasPendingInvitations).toBe(true); // Mock returns invitations
      });
    });

    it('should calculate totalSchools correctly', async () => {
      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.totalSchools).toBe(2);
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty memberships response', async () => {
      mockedApiClient.get.mockImplementation((url: string) => {
        if (url.includes('/school-memberships/')) {
          return Promise.resolve({ data: { results: [] } });
        }
        return Promise.resolve({ data: [] });
      });

      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.memberships).toEqual([]);
        expect(result.current.currentSchool).toBeNull();
        expect(result.current.hasMultipleSchools).toBe(false);
      });
    });

    it('should prioritize active membership for current school', async () => {
      const inactiveMembership = createMockSchoolMembership({
        id: 1,
        is_active: false,
        school: { id: 1, name: 'Inactive School' },
      });
      const activeMembership = createMockSchoolMembership({
        id: 2,
        is_active: true,
        school: { id: 2, name: 'Active School' },
      });

      mockedApiClient.get.mockImplementation((url: string) => {
        if (url.includes('/school-memberships/')) {
          return Promise.resolve({
            data: { results: [inactiveMembership, activeMembership] },
          });
        }
        return Promise.resolve({ data: [] });
      });

      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.currentSchool?.school.name).toBe('Active School');
      });
    });

    it('should handle switching to current school gracefully', async () => {
      const { result } = renderHook(() => useMultiSchool());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
        expect(result.current.currentSchool).toBeTruthy();
      });

      const currentSchool = result.current.currentSchool!;

      await act(async () => {
        await result.current.switchSchool(currentSchool);
      });

      // Should still work but no API call needed
      expect(result.current.currentSchool).toEqual(currentSchool);
    });
  });
});
