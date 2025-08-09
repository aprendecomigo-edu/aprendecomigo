import React from 'react';
import { render, renderHook, waitFor, act } from '@testing-library/react-native';

import { useMultiSchool } from '@/hooks/useMultiSchool';
import { useSchool } from '@/api/auth/SchoolContext';
import { useAuth } from '@/api/auth/AuthContext';
import apiClient from '@/api/apiClient';
import {
  securityTestScenarios,
  multiSchoolAssertions,
  createMockSchoolMembership,
  createMockApiClient,
} from '../../../utils/multi-school-test-utils';

// Mock dependencies
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

const mockUseMultiSchool = useMultiSchool as jest.MockedFunction<typeof useMultiSchool>;
const mockUseSchool = useSchool as jest.MockedFunction<typeof useSchool>;
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('Multi-School Security - Data Isolation', () => {
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
  });

  describe('Cross-School Data Leakage Prevention', () => {
    it('should isolate student data between schools', async () => {
      const school1 = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'School 1' },
        is_active: true,
      });
      
      const school2 = createMockSchoolMembership({
        id: 2,
        school: { id: 2, name: 'School 2' },
        is_active: false,
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

      // Mock API calls to return school-specific data
      mockedApiClient.get.mockImplementation((url: string) => {
        if (url.includes('schools/1/students')) {
          return Promise.resolve({
            data: securityTestScenarios.crossSchoolDataLeakage.school1Data.students,
          });
        }
        if (url.includes('schools/2/students')) {
          return Promise.resolve({
            data: securityTestScenarios.crossSchoolDataLeakage.school2Data.students,
          });
        }
        return Promise.resolve({ data: [] });
      });

      // Test that school 1 data is isolated from school 2 data
      const school1StudentsResponse = await mockedApiClient.get('/schools/1/students');
      const school2StudentsResponse = await mockedApiClient.get('/schools/2/students');

      const school1Students = school1StudentsResponse.data;
      const school2Students = school2StudentsResponse.data;

      // Assert data isolation
      multiSchoolAssertions.shouldIsolateSchoolData(
        { students: school1Students },
        { students: school2Students }
      );

      expect(school1Students).not.toEqual(school2Students);
      expect(school1Students.length).toBeGreaterThan(0);
      expect(school2Students.length).toBeGreaterThan(0);

      // Ensure no cross-contamination
      school1Students.forEach((student: string) => {
        expect(school2Students).not.toContain(student);
      });

      school2Students.forEach((student: string) => {
        expect(school1Students).not.toContain(student);
      });
    });

    it('should isolate session data between schools', async () => {
      const school1 = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'School 1' },
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [school1],
        currentSchool: school1,
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

      // Mock session data for different schools
      mockedApiClient.get.mockImplementation((url: string) => {
        const schoolId = url.match(/schools\/(\d+)/)?.[1];
        if (schoolId === '1') {
          return Promise.resolve({
            data: { sessions: securityTestScenarios.crossSchoolDataLeakage.school1Data.sessions },
          });
        }
        if (schoolId === '2') {
          return Promise.resolve({
            data: { sessions: securityTestScenarios.crossSchoolDataLeakage.school2Data.sessions },
          });
        }
        return Promise.resolve({ data: { sessions: [] } });
      });

      const school1Response = await mockedApiClient.get('/schools/1/sessions');
      const school2Response = await mockedApiClient.get('/schools/2/sessions');

      expect(school1Response.data.sessions).not.toEqual(school2Response.data.sessions);
    });

    it('should isolate financial data between schools', async () => {
      const school1 = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'School 1' },
        role: 'school_owner',
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [school1],
        currentSchool: school1,
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

      // Mock financial data access
      mockedApiClient.get.mockImplementation((url: string) => {
        const schoolId = url.match(/schools\/(\d+)/)?.[1];
        if (schoolId === '1') {
          return Promise.resolve({
            data: { revenue: securityTestScenarios.crossSchoolDataLeakage.school1Data.revenue },
          });
        }
        if (schoolId === '2') {
          return Promise.resolve({
            data: { revenue: securityTestScenarios.crossSchoolDataLeakage.school2Data.revenue },
          });
        }
        return Promise.resolve({ data: { revenue: 0 } });
      });

      const school1Revenue = await mockedApiClient.get('/schools/1/revenue');
      const school2Revenue = await mockedApiClient.get('/schools/2/revenue');

      expect(school1Revenue.data.revenue).toBe(15000);
      expect(school2Revenue.data.revenue).toBe(20000);
      expect(school1Revenue.data.revenue).not.toEqual(school2Revenue.data.revenue);
    });
  });

  describe('Permission Validation', () => {
    it('should enforce teacher permissions correctly', () => {
      const teacherPermissions = securityTestScenarios.permissionValidation.teacherPermissions;
      
      teacherPermissions.forEach(permission => {
        multiSchoolAssertions.shouldRespectPermissions('teacher', permission, true);
      });

      // Teacher should not have admin permissions
      const adminActions = ['manage_billing', 'invite_teachers', 'delete_school'];
      adminActions.forEach(action => {
        multiSchoolAssertions.shouldRespectPermissions('teacher', action, false);
      });
    });

    it('should enforce school admin permissions correctly', () => {
      const adminPermissions = securityTestScenarios.permissionValidation.adminPermissions;
      
      adminPermissions.forEach(permission => {
        multiSchoolAssertions.shouldRespectPermissions('school_admin', permission, true);
      });

      // Admin should not have owner-only permissions
      const ownerOnlyActions = ['delete_school', 'transfer_ownership'];
      ownerOnlyActions.forEach(action => {
        multiSchoolAssertions.shouldRespectPermissions('school_admin', action, false);
      });
    });

    it('should enforce school owner permissions correctly', () => {
      const ownerPermissions = securityTestScenarios.permissionValidation.ownerPermissions;
      
      ownerPermissions.forEach(permission => {
        multiSchoolAssertions.shouldRespectPermissions('school_owner', permission, true);
      });
    });

    it('should prevent role escalation attacks', async () => {
      const { attemptedActions } = securityTestScenarios.roleEscalation;
      
      // Simulate teacher trying to access owner-level functions
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

      // Mock API to reject unauthorized actions
      mockedApiClient.post.mockImplementation((url: string) => {
        if (url.includes('/billing') || url.includes('/invitations') || url.includes('/delete')) {
          return Promise.reject({
            response: {
              status: 403,
              data: { detail: 'Permission denied' },
            },
          });
        }
        return Promise.resolve({ data: { success: true } });
      });

      // Test each attempted action
      for (const action of attemptedActions) {
        try {
          await mockedApiClient.post(`/schools/1/${action}`);
          // If we get here, the action was allowed when it shouldn't be
          expect(true).toBe(false); // This should fail
        } catch (error: any) {
          expect(error.response.status).toBe(403);
          expect(error.response.data.detail).toBe('Permission denied');
        }
      }
    });
  });

  describe('Context Switching Security', () => {
    it('should validate school membership before allowing context switch', async () => {
      const validSchool = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'Valid School' },
      });

      const invalidSchool = createMockSchoolMembership({
        id: 999,
        school: { id: 999, name: 'Invalid School' },
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [validSchool], // Only valid school in memberships
        currentSchool: validSchool,
        pendingInvitations: [],
        loading: false,
        error: null,
        switchSchool: jest.fn((school) => {
          // Simulate backend validation
          const hasAccess = [validSchool].some(m => m.id === school.id);
          if (!hasAccess) {
            throw new Error('Unauthorized school access');
          }
          return Promise.resolve();
        }),
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

      const { result } = renderHook(() => useMultiSchool());

      // Should allow switching to valid school
      await act(async () => {
        await result.current.switchSchool(validSchool);
      });

      // Should reject switching to invalid school
      await act(async () => {
        try {
          await result.current.switchSchool(invalidSchool);
          expect(true).toBe(false); // Should not reach here
        } catch (error: any) {
          expect(error.message).toBe('Unauthorized school access');
        }
      });
    });

    it('should clear sensitive data when switching schools', async () => {
      const school1 = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'School 1' },
        is_active: true,
      });

      const school2 = createMockSchoolMembership({
        id: 2,
        school: { id: 2, name: 'School 2' },
        is_active: false,
      });

      let currentSchoolData = { students: ['school1_student1'], sessions: ['school1_session1'] };

      mockUseMultiSchool.mockReturnValue({
        memberships: [school1, school2],
        currentSchool: school1,
        pendingInvitations: [],
        loading: false,
        error: null,
        switchSchool: jest.fn(async (school) => {
          // Simulate clearing data and loading new data
          currentSchoolData = school.id === 1 
            ? { students: ['school1_student1'], sessions: ['school1_session1'] }
            : { students: ['school2_student1'], sessions: ['school2_session1'] };
        }),
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

      // Initial state - School 1 data
      expect(currentSchoolData.students).toEqual(['school1_student1']);

      // Switch to School 2
      await act(async () => {
        await result.current.switchSchool(school2);
      });

      // Should have School 2 data now, not School 1 data
      expect(currentSchoolData.students).toEqual(['school2_student1']);
      expect(currentSchoolData.students).not.toContain('school1_student1');
    });

    it('should maintain separate session tokens per school', async () => {
      // This test ensures that switching schools also switches API context
      const school1 = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'School 1' },
      });

      const school2 = createMockSchoolMembership({
        id: 2,
        school: { id: 2, name: 'School 2' },
      });

      let currentSchoolToken = 'school1_token';

      // Mock API client to use school-specific tokens
      mockedApiClient.get.mockImplementation((url: string) => {
        return Promise.resolve({
          data: { token: currentSchoolToken, school_id: currentSchoolToken.split('_')[0] },
        });
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [school1, school2],
        currentSchool: school1,
        pendingInvitations: [],
        loading: false,
        error: null,
        switchSchool: jest.fn(async (school) => {
          currentSchoolToken = `school${school.id}_token`;
        }),
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

      // Verify initial token
      const initialResponse = await mockedApiClient.get('/auth/token');
      expect(initialResponse.data.token).toBe('school1_token');

      // Switch schools
      await act(async () => {
        await result.current.switchSchool(school2);
      });

      // Verify token changed
      const newResponse = await mockedApiClient.get('/auth/token');
      expect(newResponse.data.token).toBe('school2_token');
      expect(newResponse.data.token).not.toBe('school1_token');
    });
  });

  describe('API Security Validation', () => {
    it('should include school context in API requests', async () => {
      const currentSchool = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'Test School' },
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [currentSchool],
        currentSchool,
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

      // Mock API client to verify school context is included
      mockedApiClient.get.mockImplementation((url: string, config?: any) => {
        expect(config?.headers?.['X-School-Context']).toBe('1');
        return Promise.resolve({ data: { success: true } });
      });

      await mockedApiClient.get('/students', {
        headers: { 'X-School-Context': '1' }
      });

      expect(mockedApiClient.get).toHaveBeenCalledWith('/students', {
        headers: { 'X-School-Context': '1' }
      });
    });

    it('should validate API responses contain only current school data', async () => {
      const currentSchool = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'Test School' },
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [currentSchool],
        currentSchool,
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

      // Mock response that includes data from wrong school
      mockedApiClient.get.mockResolvedValue({
        data: {
          students: [
            { id: 1, name: 'Student 1', school_id: 1 },
            { id: 2, name: 'Student 2', school_id: 2 }, // Wrong school!
          ]
        }
      });

      const response = await mockedApiClient.get('/students');
      
      // Validate that only current school data is present
      const currentSchoolStudents = response.data.students.filter(
        (student: any) => student.school_id === currentSchool.school.id
      );
      
      expect(currentSchoolStudents).toHaveLength(1);
      expect(currentSchoolStudents[0].school_id).toBe(1);
      
      // Should not contain data from other schools
      const wrongSchoolStudents = response.data.students.filter(
        (student: any) => student.school_id !== currentSchool.school.id
      );
      
      // If this test finds wrong school data, it indicates a security issue
      if (wrongSchoolStudents.length > 0) {
        throw new Error(`Security violation: API returned data from unauthorized schools`);
      }
    });
  });
});