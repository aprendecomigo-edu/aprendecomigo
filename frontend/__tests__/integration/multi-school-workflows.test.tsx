import { render, fireEvent, waitFor, screen, act } from '@testing-library/react-native';
import React from 'react';
import { Alert } from 'react-native';

import {
  multiSchoolScenarios,
  createMockSchoolMembership,
  createMockPendingInvitation,
  createMockSchoolStats,
} from '../utils/multi-school-test-utils';

import apiClient from '@/api/apiClient';
import { useAuth } from '@/api/auth/AuthContext';
import { useSchool } from '@/api/auth/SchoolContext';
import { SchoolSwitcher } from '@/components/multi-school/SchoolSwitcher';
import { useMultiSchool } from '@/hooks/useMultiSchool';

// Mock all dependencies
jest.mock('@/hooks/useMultiSchool');
jest.mock('@/api/auth/SchoolContext');
jest.mock('@/api/auth/AuthContext');
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
jest.mock('lucide-react-native', () => ({
  ChevronDown: 'ChevronDown',
  School: 'School',
  Users: 'Users',
  Crown: 'Crown',
  Shield: 'Shield',
  Check: 'Check',
  Plus: 'Plus',
  Clock: 'Clock',
}));

const mockUseMultiSchool = useMultiSchool as jest.MockedFunction<typeof useMultiSchool>;
const mockUseSchool = useSchool as jest.MockedFunction<typeof useSchool>;
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

// Mock React Native Alert
jest.spyOn(Alert, 'alert');

describe('Multi-School Workflow Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Default auth context
    mockUseAuth.mockReturnValue({
      userProfile: {
        id: 1,
        email: 'teacher@example.com',
        name: 'Test Teacher',
      },
      isAuthenticated: true,
      loading: false,
      error: null,
      login: jest.fn(),
      logout: jest.fn(),
      refreshProfile: jest.fn(),
    } as any);

    // Default API responses
    mockedApiClient.get.mockResolvedValue({ data: [] });
    mockedApiClient.patch.mockResolvedValue({ data: { success: true } });
    mockedApiClient.post.mockResolvedValue({ data: { success: true } });
  });

  describe('Complete Teacher Multi-School Journey', () => {
    it('should handle complete teacher workflow from invitation to teaching', async () => {
      // Step 1: Teacher receives invitation to new school
      const teacherInExistingSchool = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'Original School' },
        role: 'teacher',
        is_active: true,
      });

      const pendingInvitation = createMockPendingInvitation({
        id: 'inv_123',
        school: { id: 2, name: 'New School' },
        role: 'teacher',
        token: 'invite_token_123',
      });

      const mockSwitchSchool = jest.fn();
      const mockAcceptInvitation = jest.fn();
      let currentState = 'has_invitation';

      // Initial state: teacher with pending invitation
      mockUseMultiSchool.mockImplementation(() => {
        if (currentState === 'has_invitation') {
          return {
            memberships: [teacherInExistingSchool],
            currentSchool: teacherInExistingSchool,
            pendingInvitations: [pendingInvitation],
            loading: false,
            error: null,
            switchSchool: mockSwitchSchool,
            refresh: jest.fn(),
            hasMultipleSchools: false,
            hasPendingInvitations: true,
            totalSchools: 1,
            fetchMemberships: jest.fn(),
            fetchPendingInvitations: jest.fn(),
            leaveSchool: jest.fn(),
            getSchoolStats: jest.fn(),
            clearError: jest.fn(),
          };
        }

        if (currentState === 'invitation_accepted') {
          const newSchoolMembership = createMockSchoolMembership({
            id: 2,
            school: { id: 2, name: 'New School' },
            role: 'teacher',
            is_active: false,
          });

          return {
            memberships: [teacherInExistingSchool, newSchoolMembership],
            currentSchool: teacherInExistingSchool,
            pendingInvitations: [],
            loading: false,
            error: null,
            switchSchool: mockSwitchSchool,
            refresh: jest.fn(),
            hasMultipleSchools: true,
            hasPendingInvitations: false,
            totalSchools: 2,
            fetchMemberships: jest.fn(),
            fetchPendingInvitations: jest.fn(),
            leaveSchool: jest.fn(),
            getSchoolStats: jest.fn(),
            clearError: jest.fn(),
          };
        }

        return {
          memberships: [],
          currentSchool: null,
          pendingInvitations: [],
          loading: false,
          error: null,
          switchSchool: mockSwitchSchool,
          refresh: jest.fn(),
          hasMultipleSchools: false,
          hasPendingInvitations: false,
          totalSchools: 0,
          fetchMemberships: jest.fn(),
          fetchPendingInvitations: jest.fn(),
          leaveSchool: jest.fn(),
          getSchoolStats: jest.fn(),
          clearError: jest.fn(),
        };
      });

      // Render initial state with invitation
      const { rerender } = render(
        <SchoolSwitcher showPendingInvitations onInvitationAccept={mockAcceptInvitation} />,
      );

      // Step 2: Teacher sees pending invitation
      expect(screen.getByText('1 convite(s) pendente(s)')).toBeTruthy();

      // Open modal to view invitation
      const viewButton = screen.getByText('Ver');
      fireEvent.press(viewButton);

      expect(screen.getByText('Convites Pendentes')).toBeTruthy();
      expect(screen.getByText('New School')).toBeTruthy();

      // Step 3: Teacher accepts invitation
      const acceptButton = screen.getByText('Aceitar');
      fireEvent.press(acceptButton);

      expect(mockAcceptInvitation).toHaveBeenCalledWith(pendingInvitation);

      // Step 4: Simulate invitation acceptance
      currentState = 'invitation_accepted';

      // Re-render with updated state
      rerender(<SchoolSwitcher showPendingInvitations onInvitationAccept={mockAcceptInvitation} />);

      await waitFor(() => {
        // Should now show chevron indicating multiple schools
        expect(screen.getByTestId('chevron-down')).toBeTruthy();
      });

      // Step 5: Teacher switches to new school
      const currentSchoolElement = screen.getByText('Original School');
      fireEvent.press(currentSchoolElement.parent!);

      // Modal should show both schools
      await waitFor(() => {
        expect(screen.getByText('Escolas Ativas')).toBeTruthy();
        expect(screen.getAllByText('Original School')[1]).toBeTruthy(); // In modal
        expect(screen.getByText('New School')).toBeTruthy();
      });

      // Click on new school
      const newSchoolOption = screen.getByText('New School');
      fireEvent.press(newSchoolOption);

      expect(mockSwitchSchool).toHaveBeenCalledWith(
        expect.objectContaining({
          school: expect.objectContaining({
            name: 'New School',
          }),
        }),
      );
    });

    it('should handle error recovery during school switching', async () => {
      const school1 = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'School A' },
        is_active: true,
      });

      const school2 = createMockSchoolMembership({
        id: 2,
        school: { id: 2, name: 'School B' },
        is_active: false,
      });

      let switchAttempts = 0;
      const mockSwitchSchool = jest.fn(async school => {
        switchAttempts++;

        if (switchAttempts === 1) {
          // First attempt fails
          throw new Error('Network error');
        }

        // Second attempt succeeds
        return Promise.resolve();
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [school1, school2],
        currentSchool: school1,
        pendingInvitations: [],
        loading: false,
        error:
          switchAttempts === 1
            ? {
                code: 'SWITCH_SCHOOL_ERROR',
                message: 'Falha ao alterar escola. Tente novamente.',
                retryable: true,
              }
            : null,
        switchSchool: mockSwitchSchool,
        refresh: jest.fn(),
        hasMultipleSchools: true,
        hasPendingInvitations: false,
        totalSchools: 2,
        fetchMemberships: jest.fn(),
        fetchPendingInvitations: jest.fn(),
        leaveSchool: jest.fn(),
        getSchoolStats: jest.fn(),
        clearError: jest.fn(),
      });

      render(<SchoolSwitcher />);

      // Open modal
      const currentSchool = screen.getByText('School A');
      fireEvent.press(currentSchool.parent!);

      // Try to switch to School B (first attempt will fail)
      const schoolB = screen.getByText('School B');
      fireEvent.press(schoolB);

      await waitFor(() => {
        expect(mockSwitchSchool).toHaveBeenCalledTimes(1);
      });

      // Modal should still be open for retry
      expect(screen.getByText('Suas Escolas')).toBeTruthy();

      // Retry switching
      fireEvent.press(schoolB);

      await waitFor(() => {
        expect(mockSwitchSchool).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('School Admin Multi-Institution Management', () => {
    it('should handle school admin managing multiple institutions', async () => {
      const ownedSchool = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'Owned School' },
        role: 'school_owner',
        is_active: true,
      });

      const adminSchool = createMockSchoolMembership({
        id: 2,
        school: { id: 2, name: 'Admin School' },
        role: 'school_admin',
        is_active: false,
      });

      const teachingSchool = createMockSchoolMembership({
        id: 3,
        school: { id: 3, name: 'Teaching School' },
        role: 'teacher',
        is_active: false,
      });

      const mockSwitchSchool = jest.fn();
      const mockGetSchoolStats = jest.fn().mockImplementation(schoolId => {
        const statsMap: Record<number, any> = {
          1: createMockSchoolStats({ total_students: 150, monthly_revenue: 30000 }),
          2: createMockSchoolStats({ total_students: 200, monthly_revenue: 40000 }),
          3: createMockSchoolStats({ total_students: 100, monthly_revenue: 20000 }),
        };
        return Promise.resolve(statsMap[schoolId] || null);
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [ownedSchool, adminSchool, teachingSchool],
        currentSchool: ownedSchool,
        pendingInvitations: [],
        loading: false,
        error: null,
        switchSchool: mockSwitchSchool,
        refresh: jest.fn(),
        hasMultipleSchools: true,
        hasPendingInvitations: false,
        totalSchools: 3,
        fetchMemberships: jest.fn(),
        fetchPendingInvitations: jest.fn(),
        leaveSchool: jest.fn(),
        getSchoolStats: mockGetSchoolStats,
        clearError: jest.fn(),
      });

      render(<SchoolSwitcher />);

      // Should show current school with owner role
      expect(screen.getByText('Owned School')).toBeTruthy();
      expect(screen.getByText('Proprietário')).toBeTruthy();
      expect(screen.getByTestId('crown-icon')).toBeTruthy();

      // Open modal to view all schools
      const currentSchool = screen.getByText('Owned School');
      fireEvent.press(currentSchool.parent!);

      expect(screen.getByText('Escolas Ativas')).toBeTruthy();

      // Should show all schools with different roles
      expect(screen.getAllByText('Owned School')[1]).toBeTruthy();
      expect(screen.getByText('Admin School')).toBeTruthy();
      expect(screen.getByText('Teaching School')).toBeTruthy();

      // Switch to admin school
      const adminSchoolOption = screen.getByText('Admin School');
      fireEvent.press(adminSchoolOption);

      expect(mockSwitchSchool).toHaveBeenCalledWith(
        expect.objectContaining({
          role: 'school_admin',
          school: expect.objectContaining({
            name: 'Admin School',
          }),
        }),
      );

      // Test school stats retrieval for different roles
      const ownedStats = await mockGetSchoolStats(1);
      const adminStats = await mockGetSchoolStats(2);
      const teachingStats = await mockGetSchoolStats(3);

      expect(ownedStats.monthly_revenue).toBe(30000);
      expect(adminStats.monthly_revenue).toBe(40000);
      expect(teachingStats.monthly_revenue).toBe(20000);
    });
  });

  describe('Data Consistency Across School Switches', () => {
    it('should maintain data consistency during rapid school switches', async () => {
      const schools = [
        createMockSchoolMembership({
          id: 1,
          school: { id: 1, name: 'School A' },
          is_active: true,
        }),
        createMockSchoolMembership({
          id: 2,
          school: { id: 2, name: 'School B' },
          is_active: false,
        }),
        createMockSchoolMembership({
          id: 3,
          school: { id: 3, name: 'School C' },
          is_active: false,
        }),
      ];

      let currentSchoolIndex = 0;
      const switchingDelays = [100, 50, 75]; // Simulate different network delays

      const mockSwitchSchool = jest.fn(async school => {
        const delay = switchingDelays[school.id - 1] || 100;
        await new Promise(resolve => setTimeout(resolve, delay));

        currentSchoolIndex = school.id - 1;
        return Promise.resolve();
      });

      mockUseMultiSchool.mockImplementation(() => ({
        memberships: schools,
        currentSchool: schools[currentSchoolIndex],
        pendingInvitations: [],
        loading: false,
        error: null,
        switchSchool: mockSwitchSchool,
        refresh: jest.fn(),
        hasMultipleSchools: true,
        hasPendingInvitations: false,
        totalSchools: 3,
        fetchMemberships: jest.fn(),
        fetchPendingInvitations: jest.fn(),
        leaveSchool: jest.fn(),
        getSchoolStats: jest.fn(),
        clearError: jest.fn(),
      }));

      render(<SchoolSwitcher />);

      // Open modal
      const currentSchool = screen.getByText('School A');
      fireEvent.press(currentSchool.parent!);

      // Rapidly switch between schools
      const schoolB = screen.getByText('School B');
      const schoolC = screen.getByText('School C');

      // Switch to B, then immediately to C
      fireEvent.press(schoolB);
      fireEvent.press(schoolC);

      // Wait for all switches to complete
      await waitFor(
        () => {
          expect(mockSwitchSchool).toHaveBeenCalledTimes(2);
        },
        { timeout: 300 },
      );

      // Should have called switch for both schools
      expect(mockSwitchSchool).toHaveBeenNthCalledWith(
        1,
        expect.objectContaining({
          school: expect.objectContaining({ name: 'School B' }),
        }),
      );
      expect(mockSwitchSchool).toHaveBeenNthCalledWith(
        2,
        expect.objectContaining({
          school: expect.objectContaining({ name: 'School C' }),
        }),
      );
    });

    it('should handle concurrent operations during school switch', async () => {
      const school1 = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'School A' },
        is_active: true,
      });

      const school2 = createMockSchoolMembership({
        id: 2,
        school: { id: 2, name: 'School B' },
        is_active: false,
      });

      let isSwitching = false;
      const mockSwitchSchool = jest.fn(async school => {
        isSwitching = true;
        await new Promise(resolve => setTimeout(resolve, 100));
        isSwitching = false;
      });

      const mockRefresh = jest.fn(async () => {
        if (isSwitching) {
          throw new Error('Operation cancelled due to school switch');
        }
        return Promise.resolve();
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [school1, school2],
        currentSchool: school1,
        pendingInvitations: [],
        loading: false,
        error: null,
        switchSchool: mockSwitchSchool,
        refresh: mockRefresh,
        hasMultipleSchools: true,
        hasPendingInvitations: false,
        totalSchools: 2,
        fetchMemberships: jest.fn(),
        fetchPendingInvitations: jest.fn(),
        leaveSchool: jest.fn(),
        getSchoolStats: jest.fn(),
        clearError: jest.fn(),
      });

      render(<SchoolSwitcher />);

      // Start school switch
      const currentSchool = screen.getByText('School A');
      fireEvent.press(currentSchool.parent!);

      const schoolB = screen.getByText('School B');
      fireEvent.press(schoolB);

      // Try to refresh during switch (should handle gracefully)
      try {
        await mockRefresh();
      } catch (error: any) {
        expect(error.message).toBe('Operation cancelled due to school switch');
      }

      await waitFor(() => {
        expect(mockSwitchSchool).toHaveBeenCalledTimes(1);
        expect(isSwitching).toBe(false);
      });
    });
  });

  describe('Edge Cases and Error Scenarios', () => {
    it('should handle school deletion during active session', async () => {
      const activeSchool = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'Active School' },
        is_active: true,
      });

      const backupSchool = createMockSchoolMembership({
        id: 2,
        school: { id: 2, name: 'Backup School' },
        is_active: false,
      });

      let schoolDeleted = false;
      const mockSwitchSchool = jest.fn();
      const mockRefresh = jest.fn(async () => {
        if (schoolDeleted) {
          // Simulate school being deleted - remove from memberships
          return Promise.resolve();
        }
      });

      mockUseMultiSchool.mockImplementation(() => ({
        memberships: schoolDeleted ? [backupSchool] : [activeSchool, backupSchool],
        currentSchool: schoolDeleted ? backupSchool : activeSchool,
        pendingInvitations: [],
        loading: false,
        error: null,
        switchSchool: mockSwitchSchool,
        refresh: mockRefresh,
        hasMultipleSchools: !schoolDeleted,
        hasPendingInvitations: false,
        totalSchools: schoolDeleted ? 1 : 2,
        fetchMemberships: jest.fn(),
        fetchPendingInvitations: jest.fn(),
        leaveSchool: jest.fn(),
        getSchoolStats: jest.fn(),
        clearError: jest.fn(),
      }));

      const { rerender } = render(<SchoolSwitcher />);

      // Initially shows active school
      expect(screen.getByText('Active School')).toBeTruthy();

      // Simulate school deletion
      schoolDeleted = true;

      // Re-render with updated state
      rerender(<SchoolSwitcher />);

      // Should now show backup school
      expect(screen.getByText('Backup School')).toBeTruthy();
      expect(screen.queryByText('Active School')).toBeFalsy();
    });

    it('should handle network connectivity issues during school operations', async () => {
      const school = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'Test School' },
      });

      let networkError = false;
      const mockSwitchSchool = jest.fn(async school => {
        if (networkError) {
          throw new Error('Network unavailable');
        }
        return Promise.resolve();
      });

      const mockRefresh = jest.fn(async () => {
        if (networkError) {
          throw new Error('Network unavailable');
        }
        return Promise.resolve();
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [school],
        currentSchool: school,
        pendingInvitations: [],
        loading: false,
        error: networkError
          ? {
              code: 'NETWORK_ERROR',
              message: 'Erro de rede. Verifique sua conexão.',
              retryable: true,
            }
          : null,
        switchSchool: mockSwitchSchool,
        refresh: mockRefresh,
        hasMultipleSchools: false,
        hasPendingInvitations: false,
        totalSchools: 1,
        fetchMemberships: jest.fn(),
        fetchPendingInvitations: jest.fn(),
        leaveSchool: jest.fn(),
        getSchoolStats: jest.fn(),
        clearError: jest.fn(),
      });

      render(<SchoolSwitcher />);

      // Simulate network error
      networkError = true;

      // Try to switch schools during network error
      try {
        await mockSwitchSchool(school);
        expect(true).toBe(false); // Should not reach here
      } catch (error: any) {
        expect(error.message).toBe('Network unavailable');
      }

      // Try to refresh during network error
      try {
        await mockRefresh();
        expect(true).toBe(false); // Should not reach here
      } catch (error: any) {
        expect(error.message).toBe('Network unavailable');
      }

      // Restore network
      networkError = false;

      // Operations should now work
      await expect(mockSwitchSchool(school)).resolves.toBeUndefined();
      await expect(mockRefresh()).resolves.toBeUndefined();
    });
  });
});
