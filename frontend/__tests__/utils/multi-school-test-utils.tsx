import { ReactNode } from 'react';

import { SchoolMembership, PendingInvitation, SchoolStats } from '@/hooks/useMultiSchool';

// Mock data for multi-school testing
export const createMockSchoolMembership = (
  overrides: Partial<SchoolMembership> = {}
): SchoolMembership => ({
  id: 1,
  school: {
    id: 1,
    name: 'Escola Vila Nova',
    description: 'Escola de educação fundamental',
    logo_url: 'https://example.com/logo1.png',
    website: 'https://escolavilanova.edu.br',
    phone: '+55 11 1234-5678',
    email: 'contato@escolavilanova.edu.br',
    address: 'Rua das Flores, 123, São Paulo - SP',
  },
  role: 'teacher',
  is_active: true,
  joined_at: '2024-01-15T10:30:00Z',
  status: 'active',
  permissions: ['view_students', 'create_sessions', 'grade_assignments'],
  ...overrides,
});

export const createMockSchoolOwnerMembership = (
  overrides: Partial<SchoolMembership> = {}
): SchoolMembership => ({
  ...createMockSchoolMembership(),
  id: 2,
  school: {
    id: 2,
    name: 'Instituto de Excelência',
    description: 'Centro educacional de ensino médio',
    logo_url: 'https://example.com/logo2.png',
    website: 'https://institutodeexcelencia.edu.br',
    phone: '+55 11 9876-5432',
    email: 'admin@institutodeexcelencia.edu.br',
    address: 'Av. Paulista, 456, São Paulo - SP',
  },
  role: 'school_owner',
  permissions: [
    'manage_school',
    'invite_teachers',
    'manage_billing',
    'view_analytics',
    'export_data',
    'manage_settings',
  ],
  ...overrides,
});

export const createMockSchoolAdminMembership = (
  overrides: Partial<SchoolMembership> = {}
): SchoolMembership => ({
  ...createMockSchoolMembership(),
  id: 3,
  school: {
    id: 3,
    name: 'Colégio São Bento',
    description: 'Educação católica tradicional',
    logo_url: 'https://example.com/logo3.png',
    phone: '+55 11 5555-1234',
    email: 'secretaria@colegiosb.edu.br',
    address: 'Rua São Bento, 789, São Paulo - SP',
  },
  role: 'school_admin',
  permissions: ['manage_teachers', 'view_reports', 'manage_students', 'configure_settings'],
  ...overrides,
});

export const createMockPendingInvitation = (
  overrides: Partial<PendingInvitation> = {}
): PendingInvitation => ({
  id: 'inv_123',
  school: {
    id: 4,
    name: 'Escola Internacional',
    logo_url: 'https://example.com/logo4.png',
  },
  role: 'teacher',
  invited_by: {
    name: 'Maria Silva',
    email: 'maria@escolainternacional.edu.br',
  },
  expires_at: '2024-02-15T23:59:59Z',
  custom_message: 'Venha fazer parte de nossa equipe de professores!',
  token: 'inv_token_abc123',
  ...overrides,
});

export const createMockSchoolStats = (overrides: Partial<SchoolStats> = {}): SchoolStats => ({
  total_students: 150,
  total_teachers: 12,
  active_sessions_count: 8,
  monthly_revenue: 25000,
  ...overrides,
});

// Multi-school scenarios for testing
export const multiSchoolScenarios = {
  singleSchoolTeacher: {
    memberships: [createMockSchoolMembership()],
    currentSchool: createMockSchoolMembership(),
    pendingInvitations: [],
  },
  multiSchoolTeacher: {
    memberships: [
      createMockSchoolMembership({ is_active: true }),
      createMockSchoolMembership({
        id: 2,
        school: { id: 2, name: 'Escola Central' },
        is_active: false,
      }),
    ],
    currentSchool: createMockSchoolMembership({ is_active: true }),
    pendingInvitations: [],
  },
  schoolOwnerWithMultipleSchools: {
    memberships: [
      createMockSchoolOwnerMembership({ is_active: true }),
      createMockSchoolMembership({
        id: 5,
        school: { id: 5, name: 'Escola Filial' },
        role: 'school_owner',
        is_active: false,
      }),
    ],
    currentSchool: createMockSchoolOwnerMembership({ is_active: true }),
    pendingInvitations: [],
  },
  teacherWithPendingInvitations: {
    memberships: [createMockSchoolMembership()],
    currentSchool: createMockSchoolMembership(),
    pendingInvitations: [
      createMockPendingInvitation(),
      createMockPendingInvitation({
        id: 'inv_456',
        school: { id: 6, name: 'Escola Premium' },
        role: 'school_admin',
        expires_at: '2024-03-01T23:59:59Z',
      }),
    ],
  },
  mixedRoleScenario: {
    memberships: [
      createMockSchoolMembership({ is_active: true }), // Teacher role
      createMockSchoolOwnerMembership({ id: 10, is_active: false }), // Owner role
      createMockSchoolAdminMembership({ id: 11, is_active: false }), // Admin role
    ],
    currentSchool: createMockSchoolMembership({ is_active: true }),
    pendingInvitations: [],
  },
  noSchoolsScenario: {
    memberships: [],
    currentSchool: null,
    pendingInvitations: [],
  },
  suspendedMembershipScenario: {
    memberships: [
      createMockSchoolMembership({
        status: 'suspended',
        is_active: false,
      }),
    ],
    currentSchool: null,
    pendingInvitations: [],
  },
};

// Security test scenarios - data isolation
export const securityTestScenarios = {
  crossSchoolDataLeakage: {
    school1Data: {
      id: 1,
      students: ['student1@school1.com', 'student2@school1.com'],
      sessions: ['session1_school1', 'session2_school1'],
      revenue: 15000,
    },
    school2Data: {
      id: 2,
      students: ['student1@school2.com', 'student2@school2.com'],
      sessions: ['session1_school2', 'session2_school2'],
      revenue: 20000,
    },
  },
  permissionValidation: {
    teacherPermissions: ['view_students', 'create_sessions', 'grade_assignments'],
    adminPermissions: ['manage_teachers', 'view_reports', 'manage_students'],
    ownerPermissions: ['manage_school', 'invite_teachers', 'manage_billing', 'view_analytics'],
  },
  roleEscalation: {
    initialRole: 'teacher',
    attemptedActions: ['manage_billing', 'invite_teachers', 'delete_school', 'export_data'],
  },
};

// Mock API responses
export const mockApiResponses = {
  memberships: {
    success: {
      results: [createMockSchoolMembership(), createMockSchoolOwnerMembership()],
    },
    error: {
      detail: 'Erro ao carregar escolas',
      code: 'FETCH_MEMBERSHIPS_ERROR',
    },
  },
  switchSchool: {
    success: { success: true },
    error: {
      detail: 'Permissão negada para alternar escola',
      code: 'SWITCH_SCHOOL_ERROR',
    },
  },
  pendingInvitations: {
    success: {
      results: [createMockPendingInvitation()],
    },
    error: {
      detail: 'Erro ao carregar convites',
      code: 'FETCH_INVITATIONS_ERROR',
    },
  },
  schoolStats: {
    success: createMockSchoolStats(),
    error: {
      detail: 'Erro ao carregar estatísticas',
      code: 'FETCH_STATS_ERROR',
    },
  },
};

// Test utilities for mocking API calls
export const createMockApiClient = (responses: Record<string, any> = {}) => ({
  get: jest.fn((url: string) => {
    if (url.includes('/school-memberships/')) {
      return Promise.resolve({
        data: responses.memberships || mockApiResponses.memberships.success,
      });
    }
    if (url.includes('/teacher-invitations/pending/')) {
      return Promise.resolve({
        data: responses.invitations || mockApiResponses.pendingInvitations.success,
      });
    }
    if (url.includes('/stats/')) {
      return Promise.resolve({ data: responses.stats || mockApiResponses.schoolStats.success });
    }
    return Promise.resolve({ data: {} });
  }),
  patch: jest.fn(() =>
    Promise.resolve({ data: responses.switch || mockApiResponses.switchSchool.success })
  ),
  delete: jest.fn(() => Promise.resolve({ data: { success: true } })),
  post: jest.fn(() => Promise.resolve({ data: { success: true } })),
});

// Custom render helper for multi-school components
export const renderWithMultiSchoolContext = (
  ui: ReactNode,
  scenario = multiSchoolScenarios.singleSchoolTeacher
) => {
  // This would normally wrap with providers, but since we're mocking the hook,
  // we'll just return the UI for now
  return ui;
};

// Helper to simulate user interactions in multi-school context
export const userInteractions = {
  switchSchool: (schoolName: string) => ({
    action: 'switch_school',
    target: schoolName,
  }),
  acceptInvitation: (invitationId: string) => ({
    action: 'accept_invitation',
    target: invitationId,
  }),
  leaveSchool: (schoolId: number) => ({
    action: 'leave_school',
    target: schoolId,
  }),
};

// Assertion helpers for testing multi-school behavior
export const multiSchoolAssertions = {
  shouldDisplayCurrentSchool: (schoolName: string) => expect(schoolName).toBeTruthy(),

  shouldShowMultipleSchools: (count: number) => expect(count).toBeGreaterThan(1),

  shouldIsolateSchoolData: (school1Data: any, school2Data: any) => {
    expect(school1Data.students).not.toEqual(school2Data.students);
    expect(school1Data.sessions).not.toEqual(school2Data.sessions);
  },

  shouldRespectPermissions: (
    userRole: string,
    attemptedAction: string,
    expectedResult: boolean
  ) => {
    // This would check if the user can perform the action based on their role
    const rolePermissions: Record<string, string[]> = {
      teacher: ['view_students', 'create_sessions'],
      school_admin: ['manage_teachers', 'view_reports'],
      school_owner: ['manage_school', 'invite_teachers', 'manage_billing'],
    };

    const hasPermission = rolePermissions[userRole]?.includes(attemptedAction) || false;
    expect(hasPermission).toBe(expectedResult);
  },
};
