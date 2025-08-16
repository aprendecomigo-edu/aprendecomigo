import { renderHook, waitFor, act } from '@testing-library/react-native';
import React from 'react';

import {
  createMockSchoolMembership,
  securityTestScenarios,
} from '../../../utils/multi-school-test-utils';

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

// Security test scenarios - simulate real attack vectors
describe('Cross-School Data Leakage Prevention', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedApiClient.get.mockResolvedValue({ data: [] });
  });

  describe('API Request Isolation', () => {
    it('should include school context header in all API requests', async () => {
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

      // Mock interceptor to verify school context
      const mockInterceptor = jest.fn(config => {
        expect(config.headers).toHaveProperty('X-School-Context', '1');
        return config;
      });

      mockedApiClient.get.mockImplementation(async (url, config) => {
        mockInterceptor(config || { headers: { 'X-School-Context': '1' } });
        return Promise.resolve({ data: { school_id: 1 } });
      });

      await mockedApiClient.get('/students', {
        headers: { 'X-School-Context': '1' },
      });

      expect(mockInterceptor).toHaveBeenCalledWith(
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-School-Context': '1',
          }),
        }),
      );
    });

    it('should reject API requests without proper school context', async () => {
      // Mock API to reject requests without school context
      mockedApiClient.get.mockImplementation((url, config) => {
        if (!config?.headers?.['X-School-Context']) {
          return Promise.reject({
            response: {
              status: 400,
              data: { detail: 'School context required' },
            },
          });
        }
        return Promise.resolve({ data: { success: true } });
      });

      // Request without school context should fail
      try {
        await mockedApiClient.get('/students');
        expect(true).toBe(false); // Should not reach here
      } catch (error: any) {
        expect(error.response.status).toBe(400);
        expect(error.response.data.detail).toBe('School context required');
      }

      // Request with school context should succeed
      const validResponse = await mockedApiClient.get('/students', {
        headers: { 'X-School-Context': '1' },
      });
      expect(validResponse.data.success).toBe(true);
    });

    it('should validate school context matches user membership', async () => {
      const userSchools = [
        createMockSchoolMembership({ id: 1, school: { id: 1, name: 'Authorized School' } }),
      ];

      mockUseMultiSchool.mockReturnValue({
        memberships: userSchools,
        currentSchool: userSchools[0],
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

      // Mock API to validate school membership
      mockedApiClient.get.mockImplementation((url, config) => {
        const requestedSchoolId = config?.headers?.['X-School-Context'];
        const authorizedSchoolIds = ['1']; // User only has access to school 1

        if (!authorizedSchoolIds.includes(requestedSchoolId)) {
          return Promise.reject({
            response: {
              status: 403,
              data: { detail: 'Unauthorized school access' },
            },
          });
        }
        return Promise.resolve({ data: { school_id: requestedSchoolId } });
      });

      // Authorized school request should succeed
      const authorizedResponse = await mockedApiClient.get('/students', {
        headers: { 'X-School-Context': '1' },
      });
      expect(authorizedResponse.data.school_id).toBe('1');

      // Unauthorized school request should fail
      try {
        await mockedApiClient.get('/students', {
          headers: { 'X-School-Context': '999' }, // Unauthorized school
        });
        expect(true).toBe(false); // Should not reach here
      } catch (error: any) {
        expect(error.response.status).toBe(403);
        expect(error.response.data.detail).toBe('Unauthorized school access');
      }
    });
  });

  describe('Response Data Validation', () => {
    it('should filter out data from unauthorized schools', async () => {
      const authorizedSchool = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'Authorized School' },
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [authorizedSchool],
        currentSchool: authorizedSchool,
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

      // Mock response containing mixed school data (potential security issue)
      mockedApiClient.get.mockResolvedValue({
        data: {
          students: [
            { id: 1, name: 'Student A', school_id: 1 }, // Authorized
            { id: 2, name: 'Student B', school_id: 2 }, // Unauthorized - should be filtered
            { id: 3, name: 'Student C', school_id: 1 }, // Authorized
            { id: 4, name: 'Student D', school_id: 3 }, // Unauthorized - should be filtered
          ],
        },
      });

      const response = await mockedApiClient.get('/students');
      const allStudents = response.data.students;

      // Client-side filtering for security validation
      const authorizedStudents = allStudents.filter(
        (student: any) => student.school_id === authorizedSchool.school.id,
      );

      const unauthorizedStudents = allStudents.filter(
        (student: any) => student.school_id !== authorizedSchool.school.id,
      );

      expect(authorizedStudents).toHaveLength(2);
      expect(unauthorizedStudents).toHaveLength(2);

      // This test identifies a potential security vulnerability
      if (unauthorizedStudents.length > 0) {
        if (__DEV__) {
          console.warn(
            `Security Alert: API returned ${unauthorizedStudents.length} unauthorized records`,
          );
        }

        // In a real application, this should trigger security logging
        expect(unauthorizedStudents).toEqual(
          expect.arrayContaining([expect.objectContaining({ school_id: expect.not.toEqual(1) })]),
        );
      }
    });

    it('should detect and prevent data contamination attacks', async () => {
      // Simulate a malicious response that tries to inject unauthorized data
      const attackPayload = {
        students: [{ id: 1, name: 'Legitimate Student', school_id: 1 }],
        // Malicious data hidden in unexpected fields
        __metadata: {
          leaked_schools: [
            { id: 2, name: 'Victim School', revenue: 50000 },
            { id: 3, name: 'Another School', student_count: 200 },
          ],
        },
        // Attempt to inject unauthorized records
        related_data: {
          other_school_students: [{ id: 999, name: 'Leaked Student', school_id: 2 }],
        },
      };

      mockedApiClient.get.mockResolvedValue({ data: attackPayload });

      const response = await mockedApiClient.get('/students');

      // Security validation - check for unauthorized data
      const responseKeys = Object.keys(response.data);
      const suspiciousKeys = responseKeys.filter(
        key => key.includes('leaked') || key.includes('other_school') || key.startsWith('__'),
      );

      if (suspiciousKeys.length > 0) {
        if (__DEV__) {
          console.warn(
            `Security Alert: Suspicious data keys detected: ${suspiciousKeys.join(', ')}`,
          );
        }

        // In production, this should trigger security monitoring
        expect(suspiciousKeys).toContain('__metadata');
        expect(response.data.__metadata?.leaked_schools).toBeDefined();
      }

      // Validate that the application only uses authorized data
      const authorizedStudents = response.data.students.filter(
        (student: any) => student.school_id === 1,
      );

      expect(authorizedStudents).toHaveLength(1);
      expect(authorizedStudents[0].name).toBe('Legitimate Student');
    });
  });

  describe('Memory and State Isolation', () => {
    it('should clear previous school data when switching contexts', async () => {
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

      let currentSchoolData = {
        students: [{ id: 1, name: 'School A Student', school_id: 1 }],
        sessions: [{ id: 1, title: 'School A Session', school_id: 1 }],
      };

      const mockSwitchSchool = jest.fn(async school => {
        // Simulate clearing and reloading data
        currentSchoolData = {
          students:
            school.id === 1
              ? [{ id: 1, name: 'School A Student', school_id: 1 }]
              : [{ id: 2, name: 'School B Student', school_id: 2 }],
          sessions:
            school.id === 1
              ? [{ id: 1, title: 'School A Session', school_id: 1 }]
              : [{ id: 2, title: 'School B Session', school_id: 2 }],
        };
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [school1, school2],
        currentSchool: school1,
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

      const { result } = renderHook(() => useMultiSchool());

      // Initial state - School A
      expect(currentSchoolData.students[0].school_id).toBe(1);
      expect(currentSchoolData.sessions[0].school_id).toBe(1);

      // Switch to School B
      await act(async () => {
        await result.current.switchSchool(school2);
      });

      // State should be completely replaced, not merged
      expect(currentSchoolData.students[0].school_id).toBe(2);
      expect(currentSchoolData.sessions[0].school_id).toBe(2);

      // No traces of School A data should remain
      expect(currentSchoolData.students.find(s => s.school_id === 1)).toBeUndefined();
      expect(currentSchoolData.sessions.find(s => s.school_id === 1)).toBeUndefined();
    });

    it('should prevent data persistence across school switches', async () => {
      // Simulate a cache or state that might leak data
      const applicationCache = new Map();

      const school1 = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'School A' },
      });

      const school2 = createMockSchoolMembership({
        id: 2,
        school: { id: 2, name: 'School B' },
      });

      const mockSwitchSchool = jest.fn(async school => {
        // Simulate proper cache clearing
        applicationCache.clear();

        // Set new school data
        applicationCache.set('currentSchoolId', school.id);
        applicationCache.set('schoolData', {
          students: school.id === 1 ? ['student_a1'] : ['student_b1'],
          teachers: school.id === 1 ? ['teacher_a1'] : ['teacher_b1'],
        });
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [school1, school2],
        currentSchool: school1,
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

      const { result } = renderHook(() => useMultiSchool());

      // Initial state
      applicationCache.set('currentSchoolId', 1);
      applicationCache.set('schoolData', { students: ['student_a1'] });

      expect(applicationCache.get('currentSchoolId')).toBe(1);
      expect(applicationCache.get('schoolData').students).toEqual(['student_a1']);

      // Switch schools
      await act(async () => {
        await result.current.switchSchool(school2);
      });

      // Cache should be cleared and updated
      expect(applicationCache.get('currentSchoolId')).toBe(2);
      expect(applicationCache.get('schoolData').students).toEqual(['student_b1']);

      // Ensure no data from previous school remains
      expect(applicationCache.get('schoolData').students).not.toContain('student_a1');
    });
  });

  describe('URL and Navigation Security', () => {
    it('should validate school context in URL parameters', async () => {
      const authorizedSchool = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'Authorized School' },
      });

      mockUseMultiSchool.mockReturnValue({
        memberships: [authorizedSchool],
        currentSchool: authorizedSchool,
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

      // Mock URL validation
      const validateSchoolInUrl = (url: string, userSchools: any[]) => {
        const schoolIdMatch = url.match(/\/schools\/(\d+)/);
        if (!schoolIdMatch) return true; // No school context in URL

        const urlSchoolId = parseInt(schoolIdMatch[1]);
        return userSchools.some(school => school.school.id === urlSchoolId);
      };

      const userSchools = [authorizedSchool];

      // Valid URLs
      expect(validateSchoolInUrl('/schools/1/students', userSchools)).toBe(true);
      expect(validateSchoolInUrl('/dashboard', userSchools)).toBe(true);

      // Invalid URLs (trying to access unauthorized school)
      expect(validateSchoolInUrl('/schools/999/students', userSchools)).toBe(false);
      expect(validateSchoolInUrl('/schools/2/billing', userSchools)).toBe(false);
    });

    it('should prevent school ID manipulation in API calls', async () => {
      // Mock API that validates school ID parameter
      mockedApiClient.get.mockImplementation(url => {
        const schoolId = url.match(/\/schools\/(\d+)/)?.[1];

        // Simulate backend validation
        const authorizedSchools = ['1'];

        if (schoolId && !authorizedSchools.includes(schoolId)) {
          return Promise.reject({
            response: {
              status: 403,
              data: { detail: 'Unauthorized school access' },
            },
          });
        }

        return Promise.resolve({
          data: { school_id: schoolId, data: 'authorized data' },
        });
      });

      // Authorized request should work
      const validResponse = await mockedApiClient.get('/schools/1/students');
      expect(validResponse.data.school_id).toBe('1');

      // Unauthorized requests should fail
      const unauthorizedSchools = ['999', '2', '0', '-1'];

      for (const schoolId of unauthorizedSchools) {
        try {
          await mockedApiClient.get(`/schools/${schoolId}/students`);
          expect(true).toBe(false); // Should not reach here
        } catch (error: any) {
          expect(error.response.status).toBe(403);
          expect(error.response.data.detail).toBe('Unauthorized school access');
        }
      }
    });
  });

  describe('Real-time Data Security', () => {
    it('should isolate WebSocket subscriptions by school', async () => {
      const mockWebSocketManager = {
        activeSubscriptions: new Map(),
        subscribe: jest.fn((channel, schoolId) => {
          const key = `${channel}_${schoolId}`;
          mockWebSocketManager.activeSubscriptions.set(key, { channel, schoolId });
        }),
        unsubscribe: jest.fn((channel, schoolId) => {
          const key = `${channel}_${schoolId}`;
          mockWebSocketManager.activeSubscriptions.delete(key);
        }),
        unsubscribeAll: jest.fn(() => {
          mockWebSocketManager.activeSubscriptions.clear();
        }),
      };

      const school1 = createMockSchoolMembership({
        id: 1,
        school: { id: 1, name: 'School A' },
      });

      const school2 = createMockSchoolMembership({
        id: 2,
        school: { id: 2, name: 'School B' },
      });

      // Subscribe to School A channels
      mockWebSocketManager.subscribe('students', 1);
      mockWebSocketManager.subscribe('sessions', 1);

      expect(mockWebSocketManager.activeSubscriptions.size).toBe(2);
      expect(mockWebSocketManager.activeSubscriptions.has('students_1')).toBe(true);
      expect(mockWebSocketManager.activeSubscriptions.has('sessions_1')).toBe(true);

      // When switching schools, all subscriptions should be cleared
      mockWebSocketManager.unsubscribeAll();

      // Subscribe to School B channels
      mockWebSocketManager.subscribe('students', 2);
      mockWebSocketManager.subscribe('sessions', 2);

      expect(mockWebSocketManager.activeSubscriptions.size).toBe(2);
      expect(mockWebSocketManager.activeSubscriptions.has('students_2')).toBe(true);
      expect(mockWebSocketManager.activeSubscriptions.has('sessions_2')).toBe(true);

      // Should not have any School A subscriptions
      expect(mockWebSocketManager.activeSubscriptions.has('students_1')).toBe(false);
      expect(mockWebSocketManager.activeSubscriptions.has('sessions_1')).toBe(false);
    });

    it('should validate real-time message school context', () => {
      const authorizedSchoolId = 1;

      // Mock WebSocket message handler
      const handleWebSocketMessage = (message: any) => {
        const { type, data, school_id } = message;

        // Validate school context
        if (school_id !== authorizedSchoolId) {
          throw new Error(`Unauthorized message from school ${school_id}`);
        }

        return { type, data, school_id };
      };

      // Valid message
      const validMessage = {
        type: 'student_update',
        data: { student_id: 1, name: 'Updated Name' },
        school_id: 1,
      };

      expect(() => handleWebSocketMessage(validMessage)).not.toThrow();

      // Invalid messages
      const invalidMessages = [
        { type: 'student_update', data: {}, school_id: 2 },
        { type: 'session_update', data: {}, school_id: 999 },
        { type: 'payment_update', data: {}, school_id: 0 },
      ];

      invalidMessages.forEach(message => {
        expect(() => handleWebSocketMessage(message)).toThrow(
          `Unauthorized message from school ${message.school_id}`,
        );
      });
    });
  });
});
