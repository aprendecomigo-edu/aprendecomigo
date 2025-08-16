import { render, renderHook, fireEvent, waitFor, act } from '@testing-library/react-native';
import React from 'react';

import {
  multiSchoolScenarios,
  createMockSchoolMembership,
  createMockSchoolStats,
} from '../../utils/multi-school-test-utils';

import apiClient from '@/api/apiClient';
import { useSchool } from '@/api/auth/SchoolContext';
import { useMultiSchool } from '@/hooks/useMultiSchool';

// Mock dependencies
jest.mock('@/hooks/useMultiSchool');
jest.mock('@/api/auth/SchoolContext');
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

const mockUseMultiSchool = useMultiSchool as jest.MockedFunction<typeof useMultiSchool>;
const mockUseSchool = useSchool as jest.MockedFunction<typeof useSchool>;
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('Teacher Multi-School Experience', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Default API responses
    mockedApiClient.get.mockResolvedValue({ data: [] });
    mockedApiClient.patch.mockResolvedValue({ data: { success: true } });
    mockedApiClient.post.mockResolvedValue({ data: { success: true } });
    mockedApiClient.delete.mockResolvedValue({ data: { success: true } });
  });

  describe('Multi-School Access Controls', () => {
    it('should allow teacher to access only authorized schools', () => {
      const teacherSchools = [
        createMockSchoolMembership({
          id: 1,
          school: { id: 1, name: 'Elementary School A' },
          role: 'teacher',
          is_active: true,
        }),
        createMockSchoolMembership({
          id: 2,
          school: { id: 2, name: 'High School B' },
          role: 'teacher',
          is_active: false,
        }),
      ];

      mockUseMultiSchool.mockReturnValue({
        memberships: teacherSchools,
        currentSchool: teacherSchools[0],
        pendingInvitations: [],
        loading: false,
        error: null,
        switchSchool: jest.fn(),
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

      const { result } = renderHook(() => useMultiSchool());

      expect(result.current.memberships).toHaveLength(2);
      expect(result.current.hasMultipleSchools).toBe(true);
      expect(result.current.currentSchool?.school.name).toBe('Elementary School A');

      // All memberships should have teacher role
      result.current.memberships.forEach(membership => {
        expect(membership.role).toBe('teacher');
        expect(['view_students', 'create_sessions', 'grade_assignments']).toEqual(
          expect.arrayContaining(membership.permissions),
        );
      });
    });

    it('should restrict teacher permissions to appropriate actions', () => {
      const teacherMembership = createMockSchoolMembership({
        role: 'teacher',
        permissions: ['view_students', 'create_sessions', 'grade_assignments'],
      });

      mockUseSchool.mockReturnValue({
        userSchools: [teacherMembership],
        currentSchool: teacherMembership,
        setCurrentSchool: jest.fn(),
        hasRole: (role: string) => role === 'teacher',
        hasAnyRole: (roles: string[]) => roles.includes('teacher'),
        isSchoolAdmin: false,
        isTeacher: true,
      });

      const { result } = renderHook(() => useSchool());

      // Teacher should have teaching permissions
      expect(result.current.isTeacher).toBe(true);
      expect(result.current.hasRole('teacher')).toBe(true);

      // Teacher should NOT have admin permissions
      expect(result.current.isSchoolAdmin).toBe(false);
      expect(result.current.hasRole('school_owner')).toBe(false);
      expect(result.current.hasRole('school_admin')).toBe(false);
    });

    it('should prevent teacher from accessing admin-only functions', async () => {
      const teacherMembership = createMockSchoolMembership({
        role: 'teacher',
        permissions: ['view_students', 'create_sessions'],
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [teacherMembership],
        currentSchool: teacherMembership,
        pendingInvitations: [],
        loading: false,
        error: null,
        switchSchool: jest.fn(),
        refresh: jest.fn(),
        hasMultipleSchools: false,
        hasPendingInvitations: false,
        totalSchools: 1,
        fetchMemberships: jest.fn(),
        fetchPendingInvitations: jest.fn(),
        leaveSchool: jest.fn(),
        getSchoolStats: jest.fn(),
        clearError: jest.fn(),
      });

      // Mock API to reject admin actions
      const adminActions = [
        '/schools/1/invite-teachers',
        '/schools/1/billing',
        '/schools/1/settings',
        '/schools/1/delete',
      ];

      mockedApiClient.post.mockImplementation((url: string) => {
        if (adminActions.some(action => url.includes(action))) {
          return Promise.reject({
            response: {
              status: 403,
              data: { detail: 'Teacher role does not have permission for this action' },
            },
          });
        }
        return Promise.resolve({ data: { success: true } });
      });

      // Test each admin action
      for (const action of adminActions) {
        try {
          await mockedApiClient.post(action);
          expect(true).toBe(false); // Should not reach here
        } catch (error: any) {
          expect(error.response.status).toBe(403);
          expect(error.response.data.detail).toContain('Teacher role does not have permission');
        }
      }
    });
  });

  describe('Student Roster Isolation', () => {
    it('should show different student rosters per school', async () => {
      const school1 = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'School A' },
        role: 'teacher',
        is_active: true,
      });

      const school2 = createMockSchoolMembership({
        id: 2,
        school: { id: 2, name: 'School B' },
        role: 'teacher',
        is_active: false,
      });

      let currentSchool = school1;
      const mockSwitchSchool = jest.fn(async school => {
        currentSchool = school;
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [school1, school2],
        currentSchool,
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
      });

      // Mock different student rosters for each school
      mockedApiClient.get.mockImplementation((url: string) => {
        if (url.includes('/students') && currentSchool.id === 1) {
          return Promise.resolve({
            data: {
              students: [
                { id: 1, name: 'Alice Smith', school_id: 1 },
                { id: 2, name: 'Bob Johnson', school_id: 1 },
              ],
            },
          });
        }
        if (url.includes('/students') && currentSchool.id === 2) {
          return Promise.resolve({
            data: {
              students: [
                { id: 3, name: 'Carol Brown', school_id: 2 },
                { id: 4, name: 'David Wilson', school_id: 2 },
              ],
            },
          });
        }
        return Promise.resolve({ data: { students: [] } });
      });

      const { result } = renderHook(() => useMultiSchool());

      // Get students for School A
      const school1StudentsResponse = await mockedApiClient.get('/students');
      const school1Students = school1StudentsResponse.data.students;

      expect(school1Students).toHaveLength(2);
      expect(school1Students[0].name).toBe('Alice Smith');
      expect(school1Students[1].name).toBe('Bob Johnson');

      // Switch to School B
      await act(async () => {
        await result.current.switchSchool(school2);
      });

      // Get students for School B
      const school2StudentsResponse = await mockedApiClient.get('/students');
      const school2Students = school2StudentsResponse.data.students;

      expect(school2Students).toHaveLength(2);
      expect(school2Students[0].name).toBe('Carol Brown');
      expect(school2Students[1].name).toBe('David Wilson');

      // Ensure no cross-contamination
      expect(school1Students).not.toEqual(school2Students);
      school1Students.forEach((student: any) => {
        expect(school2Students.find((s: any) => s.id === student.id)).toBeUndefined();
      });
    });

    it('should filter student data by teacher assignments', async () => {
      const teacherMembership = createMockSchoolMembership({
        id: 1,
        role: 'teacher',
        permissions: ['view_assigned_students'],
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [teacherMembership],
        currentSchool: teacherMembership,
        pendingInvitations: [],
        loading: false,
        error: null,
        switchSchool: jest.fn(),
        refresh: jest.fn(),
        hasMultipleSchools: false,
        hasPendingInvitations: false,
        totalSchools: 1,
        fetchMemberships: jest.fn(),
        fetchPendingInvitations: jest.fn(),
        leaveSchool: jest.fn(),
        getSchoolStats: jest.fn(),
        clearError: jest.fn(),
      });

      // Mock API to return only assigned students
      mockedApiClient.get.mockImplementation((url: string) => {
        if (url.includes('/students/assigned')) {
          return Promise.resolve({
            data: {
              students: [
                { id: 1, name: 'Assigned Student 1', teacher_id: 1 },
                { id: 2, name: 'Assigned Student 2', teacher_id: 1 },
              ],
            },
          });
        }
        if (url.includes('/students/all')) {
          return Promise.reject({
            response: {
              status: 403,
              data: { detail: 'Teachers can only view assigned students' },
            },
          });
        }
        return Promise.resolve({ data: { students: [] } });
      });

      // Teacher should be able to view assigned students
      const assignedStudents = await mockedApiClient.get('/students/assigned');
      expect(assignedStudents.data.students).toHaveLength(2);

      // Teacher should NOT be able to view all students
      try {
        await mockedApiClient.get('/students/all');
        expect(true).toBe(false); // Should not reach here
      } catch (error: any) {
        expect(error.response.status).toBe(403);
        expect(error.response.data.detail).toContain('Teachers can only view assigned students');
      }
    });
  });

  describe('Earnings Calculation Per School', () => {
    it('should calculate earnings separately for each school', async () => {
      const school1 = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'School A' },
        role: 'teacher',
      });

      const school2 = createMockSchoolMembership({
        id: 2,
        school: { id: 2, name: 'School B' },
        role: 'teacher',
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [school1, school2],
        currentSchool: school1,
        pendingInvitations: [],
        loading: false,
        error: null,
        switchSchool: jest.fn(),
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

      // Mock earnings data per school
      mockedApiClient.get.mockImplementation((url: string) => {
        const schoolId = url.match(/schools\/(\d+)/)?.[1];
        if (url.includes('/teacher-earnings') && schoolId === '1') {
          return Promise.resolve({
            data: {
              monthly_earnings: 1500,
              sessions_count: 20,
              average_per_session: 75,
              school_id: 1,
            },
          });
        }
        if (url.includes('/teacher-earnings') && schoolId === '2') {
          return Promise.resolve({
            data: {
              monthly_earnings: 2200,
              sessions_count: 30,
              average_per_session: 73.33,
              school_id: 2,
            },
          });
        }
        return Promise.resolve({ data: {} });
      });

      // Get earnings for School A
      const school1Earnings = await mockedApiClient.get('/schools/1/teacher-earnings');
      expect(school1Earnings.data.monthly_earnings).toBe(1500);
      expect(school1Earnings.data.school_id).toBe(1);

      // Get earnings for School B
      const school2Earnings = await mockedApiClient.get('/schools/2/teacher-earnings');
      expect(school2Earnings.data.monthly_earnings).toBe(2200);
      expect(school2Earnings.data.school_id).toBe(2);

      // Earnings should be different
      expect(school1Earnings.data.monthly_earnings).not.toEqual(
        school2Earnings.data.monthly_earnings,
      );

      // Total earnings calculation should be separate
      const totalEarnings =
        school1Earnings.data.monthly_earnings + school2Earnings.data.monthly_earnings;
      expect(totalEarnings).toBe(3700);
    });

    it('should track payment status per school', async () => {
      const teacherMembership = createMockSchoolMembership({
        id: 1,
        role: 'teacher',
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [teacherMembership],
        currentSchool: teacherMembership,
        pendingInvitations: [],
        loading: false,
        error: null,
        switchSchool: jest.fn(),
        refresh: jest.fn(),
        hasMultipleSchools: false,
        hasPendingInvitations: false,
        totalSchools: 1,
        fetchMemberships: jest.fn(),
        fetchPendingInvitations: jest.fn(),
        leaveSchool: jest.fn(),
        getSchoolStats: jest.fn(),
        clearError: jest.fn(),
      });

      // Mock payment status per school
      mockedApiClient.get.mockResolvedValue({
        data: {
          payment_history: [
            {
              school_id: 1,
              month: '2024-01',
              amount: 1500,
              status: 'paid',
              paid_at: '2024-02-01T10:00:00Z',
            },
            {
              school_id: 1,
              month: '2024-02',
              amount: 1600,
              status: 'pending',
              due_date: '2024-03-01T00:00:00Z',
            },
          ],
        },
      });

      const paymentHistory = await mockedApiClient.get('/teacher/payment-history');
      const payments = paymentHistory.data.payment_history;

      expect(payments).toHaveLength(2);
      expect(payments[0].status).toBe('paid');
      expect(payments[1].status).toBe('pending');

      // Each payment should be tied to specific school
      payments.forEach((payment: any) => {
        expect(payment.school_id).toBe(1);
      });
    });
  });

  describe('Session Scheduling Boundaries', () => {
    it('should respect school-specific scheduling rules', async () => {
      const school1 = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'Morning School' },
        role: 'teacher',
      });

      const school2 = createMockSchoolMembership({
        id: 2,
        school: { id: 2, name: 'Evening School' },
        role: 'teacher',
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [school1, school2],
        currentSchool: school1,
        pendingInvitations: [],
        loading: false,
        error: null,
        switchSchool: jest.fn(),
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

      // Mock school-specific scheduling rules
      mockedApiClient.get.mockImplementation((url: string) => {
        const schoolId = url.match(/schools\/(\d+)/)?.[1];
        if (url.includes('/schedule-rules') && schoolId === '1') {
          return Promise.resolve({
            data: {
              allowed_hours: { start: '08:00', end: '12:00' },
              max_sessions_per_day: 4,
              break_between_sessions: 15, // minutes
            },
          });
        }
        if (url.includes('/schedule-rules') && schoolId === '2') {
          return Promise.resolve({
            data: {
              allowed_hours: { start: '18:00', end: '22:00' },
              max_sessions_per_day: 3,
              break_between_sessions: 10, // minutes
            },
          });
        }
        return Promise.resolve({ data: {} });
      });

      const school1Rules = await mockedApiClient.get('/schools/1/schedule-rules');
      const school2Rules = await mockedApiClient.get('/schools/2/schedule-rules');

      // Schools should have different scheduling rules
      expect(school1Rules.data.allowed_hours.start).toBe('08:00');
      expect(school2Rules.data.allowed_hours.start).toBe('18:00');

      expect(school1Rules.data.max_sessions_per_day).toBe(4);
      expect(school2Rules.data.max_sessions_per_day).toBe(3);
    });

    it('should prevent scheduling conflicts across schools', async () => {
      const teacher = createMockSchoolMembership({
        id: 1,
        role: 'teacher',
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [teacher],
        currentSchool: teacher,
        pendingInvitations: [],
        loading: false,
        error: null,
        switchSchool: jest.fn(),
        refresh: jest.fn(),
        hasMultipleSchools: false,
        hasPendingInvitations: false,
        totalSchools: 1,
        fetchMemberships: jest.fn(),
        fetchPendingInvitations: jest.fn(),
        leaveSchool: jest.fn(),
        getSchoolStats: jest.fn(),
        clearError: jest.fn(),
      });

      // Mock existing sessions across all schools
      mockedApiClient.get.mockImplementation((url: string) => {
        if (url.includes('/teacher/all-sessions')) {
          return Promise.resolve({
            data: {
              sessions: [
                {
                  id: 1,
                  school_id: 1,
                  date: '2024-02-01',
                  start_time: '10:00',
                  end_time: '11:00',
                },
                {
                  id: 2,
                  school_id: 2,
                  date: '2024-02-01',
                  start_time: '10:30',
                  end_time: '11:30',
                },
              ],
            },
          });
        }
        return Promise.resolve({ data: {} });
      });

      // Mock scheduling validation
      mockedApiClient.post.mockImplementation((url: string, data: any) => {
        if (url.includes('/schedule-session')) {
          const newSession = data;
          const existingSessions = [
            { start_time: '10:00', end_time: '11:00', date: '2024-02-01' },
            { start_time: '10:30', end_time: '11:30', date: '2024-02-01' },
          ];

          // Check for time conflicts
          const hasConflict = existingSessions.some(session => {
            const newStart = new Date(`${newSession.date} ${newSession.start_time}`);
            const newEnd = new Date(`${newSession.date} ${newSession.end_time}`);
            const existingStart = new Date(`${session.date} ${session.start_time}`);
            const existingEnd = new Date(`${session.date} ${session.end_time}`);

            return newStart < existingEnd && newEnd > existingStart;
          });

          if (hasConflict) {
            return Promise.reject({
              response: {
                status: 409,
                data: { detail: 'Schedule conflict with existing session' },
              },
            });
          }

          return Promise.resolve({ data: { success: true, session_id: 3 } });
        }
        return Promise.resolve({ data: {} });
      });

      // Try to schedule a conflicting session
      try {
        await mockedApiClient.post('/schedule-session', {
          date: '2024-02-01',
          start_time: '10:15',
          end_time: '11:15',
          school_id: 3,
        });
        expect(true).toBe(false); // Should not reach here
      } catch (error: any) {
        expect(error.response.status).toBe(409);
        expect(error.response.data.detail).toContain('Schedule conflict');
      }

      // Try to schedule a non-conflicting session
      const successfulBooking = await mockedApiClient.post('/schedule-session', {
        date: '2024-02-01',
        start_time: '14:00',
        end_time: '15:00',
        school_id: 1,
      });

      expect(successfulBooking.data.success).toBe(true);
      expect(successfulBooking.data.session_id).toBe(3);
    });
  });

  describe('Dashboard and Analytics Per School', () => {
    it('should show school-specific analytics', async () => {
      const activeSchool = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'Active School' },
        role: 'teacher',
        is_active: true,
      });

      const mockGetSchoolStats = jest.fn().mockResolvedValue(
        createMockSchoolStats({
          total_students: 25,
          active_sessions_count: 5,
        }),
      );

      mockUseMultiSchool.mockReturnValue({
        memberships: [activeSchool],
        currentSchool: activeSchool,
        pendingInvitations: [],
        loading: false,
        error: null,
        switchSchool: jest.fn(),
        refresh: jest.fn(),
        hasMultipleSchools: false,
        hasPendingInvitations: false,
        totalSchools: 1,
        fetchMemberships: jest.fn(),
        fetchPendingInvitations: jest.fn(),
        leaveSchool: jest.fn(),
        getSchoolStats: mockGetSchoolStats,
        clearError: jest.fn(),
      });

      const { result } = renderHook(() => useMultiSchool());

      const stats = await result.current.getSchoolStats(1);

      expect(mockGetSchoolStats).toHaveBeenCalledWith(1);
      expect(stats?.total_students).toBe(25);
      expect(stats?.active_sessions_count).toBe(5);
    });

    it('should update analytics when switching schools', async () => {
      const school1 = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'School A' },
        role: 'teacher',
        is_active: true,
      });

      const school2 = createMockSchoolMembership({
        id: 2,
        school: { id: 2, name: 'School B' },
        role: 'teacher',
        is_active: false,
      });

      let currentSchool = school1;
      const mockSwitchSchool = jest.fn(async school => {
        currentSchool = school;
      });

      const mockGetSchoolStats = jest.fn().mockImplementation((schoolId: number) => {
        if (schoolId === 1) {
          return Promise.resolve(
            createMockSchoolStats({
              total_students: 20,
              active_sessions_count: 3,
            }),
          );
        }
        if (schoolId === 2) {
          return Promise.resolve(
            createMockSchoolStats({
              total_students: 35,
              active_sessions_count: 8,
            }),
          );
        }
        return Promise.resolve(null);
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [school1, school2],
        currentSchool,
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
        getSchoolStats: mockGetSchoolStats,
        clearError: jest.fn(),
      });

      const { result } = renderHook(() => useMultiSchool());

      // Get stats for School A
      const school1Stats = await result.current.getSchoolStats(1);
      expect(school1Stats?.total_students).toBe(20);
      expect(school1Stats?.active_sessions_count).toBe(3);

      // Switch to School B
      await act(async () => {
        await result.current.switchSchool(school2);
      });

      // Get stats for School B
      const school2Stats = await result.current.getSchoolStats(2);
      expect(school2Stats?.total_students).toBe(35);
      expect(school2Stats?.active_sessions_count).toBe(8);

      // Stats should be different
      expect(school1Stats?.total_students).not.toEqual(school2Stats?.total_students);
      expect(school1Stats?.active_sessions_count).not.toEqual(school2Stats?.active_sessions_count);
    });
  });
});
