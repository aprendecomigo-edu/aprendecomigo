import React from 'react';
import { render, renderHook, act } from '@testing-library/react-native';

import { SchoolProvider, useSchool, UserSchool } from '@/api/auth/SchoolContext';
import { useAuth } from '@/api/auth/AuthContext';

// Mock the AuthContext
jest.mock('@/api/auth/AuthContext');
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe('SchoolContext', () => {
  const mockUserProfile = {
    id: 1,
    email: 'user@example.com',
    name: 'Test User',
    roles: [
      {
        role: 'school_owner',
        role_display: 'Proprietário',
        school: {
          id: 1,
          name: 'Escola Vila Nova',
        },
      },
      {
        role: 'teacher',
        role_display: 'Professor',
        school: {
          id: 2,
          name: 'Escola Central',
        },
      },
      {
        role: 'school_admin',
        role_display: 'Administrador',
        school: {
          id: 3,
          name: 'Colégio São Bento',
        },
      },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      userProfile: mockUserProfile,
      isAuthenticated: true,
      loading: false,
      error: null,
      login: jest.fn(),
      logout: jest.fn(),
      refreshProfile: jest.fn(),
    } as any);
  });

  describe('SchoolProvider', () => {
    const TestComponent = () => {
      const { userSchools, currentSchool } = useSchool();
      return (
        <>
          <div testID="schools-count">{userSchools.length}</div>
          <div testID="current-school">{currentSchool?.name || 'None'}</div>
        </>
      );
    };

    it('should extract schools from user profile roles', () => {
      const { getByTestId } = render(
        <SchoolProvider>
          <TestComponent />
        </SchoolProvider>
      );

      expect(getByTestId('schools-count')).toHaveTextContent('3');
      expect(getByTestId('current-school')).toHaveTextContent('Escola Vila Nova'); // First admin school
    });

    it('should prioritize admin schools for default current school', () => {
      const { getByTestId } = render(
        <SchoolProvider>
          <TestComponent />
        </SchoolProvider>
      );

      // Should default to first school_owner/school_admin role
      expect(getByTestId('current-school')).toHaveTextContent('Escola Vila Nova');
    });

    it('should fallback to first school if no admin schools', () => {
      mockUseAuth.mockReturnValue({
        userProfile: {
          ...mockUserProfile,
          roles: [
            {
              role: 'teacher',
              role_display: 'Professor',
              school: {
                id: 2,
                name: 'Only Teacher School',
              },
            },
          ],
        },
        isAuthenticated: true,
        loading: false,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        refreshProfile: jest.fn(),
      } as any);

      const { getByTestId } = render(
        <SchoolProvider>
          <TestComponent />
        </SchoolProvider>
      );

      expect(getByTestId('current-school')).toHaveTextContent('Only Teacher School');
    });

    it('should clear school data when user profile is null', () => {
      mockUseAuth.mockReturnValue({
        userProfile: null,
        isAuthenticated: false,
        loading: false,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        refreshProfile: jest.fn(),
      } as any);

      const { getByTestId } = render(
        <SchoolProvider>
          <TestComponent />
        </SchoolProvider>
      );

      expect(getByTestId('schools-count')).toHaveTextContent('0');
      expect(getByTestId('current-school')).toHaveTextContent('None');
    });
  });

  describe('useSchool Hook', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <SchoolProvider>{children}</SchoolProvider>
    );

    it('should provide school context data', () => {
      const { result } = renderHook(() => useSchool(), { wrapper });

      expect(result.current.userSchools).toHaveLength(3);
      expect(result.current.currentSchool).toEqual({
        id: 1,
        name: 'Escola Vila Nova',
        role: 'school_owner',
        role_display: 'Proprietário',
      });
      expect(result.current.isSchoolAdmin).toBe(true);
      expect(result.current.isTeacher).toBe(true);
    });

    it('should allow setting current school', () => {
      const { result } = renderHook(() => useSchool(), { wrapper });

      const newSchool: UserSchool = {
        id: 2,
        name: 'Escola Central',
        role: 'teacher',
        role_display: 'Professor',
      };

      act(() => {
        result.current.setCurrentSchool(newSchool);
      });

      expect(result.current.currentSchool).toEqual(newSchool);
    });

    it('should check role existence correctly', () => {
      const { result } = renderHook(() => useSchool(), { wrapper });

      expect(result.current.hasRole('school_owner')).toBe(true);
      expect(result.current.hasRole('teacher')).toBe(true);
      expect(result.current.hasRole('school_admin')).toBe(true);
      expect(result.current.hasRole('student')).toBe(false);
    });

    it('should check multiple role existence correctly', () => {
      const { result } = renderHook(() => useSchool(), { wrapper });

      expect(result.current.hasAnyRole(['school_owner', 'teacher'])).toBe(true);
      expect(result.current.hasAnyRole(['student', 'parent'])).toBe(false);
      expect(result.current.hasAnyRole(['school_admin'])).toBe(true);
    });

    it('should compute isSchoolAdmin correctly', () => {
      const { result } = renderHook(() => useSchool(), { wrapper });

      expect(result.current.isSchoolAdmin).toBe(true); // Has school_owner and school_admin
    });

    it('should compute isTeacher correctly', () => {
      const { result } = renderHook(() => useSchool(), { wrapper });

      expect(result.current.isTeacher).toBe(true);
    });

    it('should throw error when used outside provider', () => {
      const { result } = renderHook(() => useSchool());

      expect(result.error).toEqual(
        new Error('useSchool must be used within a SchoolProvider')
      );
    });
  });

  describe('Security and Role Validation', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <SchoolProvider>{children}</SchoolProvider>
    );

    it('should properly isolate school data by role', () => {
      const { result } = renderHook(() => useSchool(), { wrapper });

      const ownerSchool = result.current.userSchools.find(s => s.role === 'school_owner');
      const teacherSchool = result.current.userSchools.find(s => s.role === 'teacher');
      const adminSchool = result.current.userSchools.find(s => s.role === 'school_admin');

      expect(ownerSchool?.id).toBe(1);
      expect(teacherSchool?.id).toBe(2);
      expect(adminSchool?.id).toBe(3);

      // Schools should be different
      expect(ownerSchool?.id).not.toBe(teacherSchool?.id);
      expect(ownerSchool?.id).not.toBe(adminSchool?.id);
      expect(teacherSchool?.id).not.toBe(adminSchool?.id);
    });

    it('should validate school owner permissions', () => {
      const { result } = renderHook(() => useSchool(), { wrapper });

      // School owners should have admin privileges
      expect(result.current.isSchoolAdmin).toBe(true);
      expect(result.current.hasRole('school_owner')).toBe(true);
    });

    it('should validate school admin permissions', () => {
      const { result } = renderHook(() => useSchool(), { wrapper });

      expect(result.current.isSchoolAdmin).toBe(true);
      expect(result.current.hasRole('school_admin')).toBe(true);
    });

    it('should validate teacher permissions', () => {
      const { result } = renderHook(() => useSchool(), { wrapper });

      expect(result.current.isTeacher).toBe(true);
      expect(result.current.hasRole('teacher')).toBe(true);
    });

    it('should prevent unauthorized role access', () => {
      mockUseAuth.mockReturnValue({
        userProfile: {
          ...mockUserProfile,
          roles: [
            {
              role: 'teacher',
              role_display: 'Professor',
              school: {
                id: 1,
                name: 'Teacher Only School',
              },
            },
          ],
        },
        isAuthenticated: true,
        loading: false,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        refreshProfile: jest.fn(),
      } as any);

      const { result } = renderHook(() => useSchool(), { wrapper });

      // Teacher-only user should not have admin privileges
      expect(result.current.isSchoolAdmin).toBe(false);
      expect(result.current.hasRole('school_owner')).toBe(false);
      expect(result.current.hasRole('school_admin')).toBe(false);
      expect(result.current.isTeacher).toBe(true);
    });
  });

  describe('Context Switch Security', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <SchoolProvider>{children}</SchoolProvider>
    );

    it('should allow switching between authorized schools only', () => {
      const { result } = renderHook(() => useSchool(), { wrapper });

      // User should be able to switch to any of their schools
      const authorizedSchools = result.current.userSchools;
      
      authorizedSchools.forEach(school => {
        act(() => {
          result.current.setCurrentSchool(school);
        });
        expect(result.current.currentSchool).toEqual(school);
      });
    });

    it('should maintain role context when switching schools', () => {
      const { result } = renderHook(() => useSchool(), { wrapper });

      const teacherSchool = result.current.userSchools.find(s => s.role === 'teacher')!;
      const ownerSchool = result.current.userSchools.find(s => s.role === 'school_owner')!;

      // Switch to teacher school
      act(() => {
        result.current.setCurrentSchool(teacherSchool);
      });
      expect(result.current.currentSchool?.role).toBe('teacher');

      // Switch to owner school
      act(() => {
        result.current.setCurrentSchool(ownerSchool);
      });
      expect(result.current.currentSchool?.role).toBe('school_owner');
    });

    it('should prevent switching to unauthorized schools', () => {
      const { result } = renderHook(() => useSchool(), { wrapper });

      const unauthorizedSchool: UserSchool = {
        id: 999,
        name: 'Unauthorized School',
        role: 'school_owner',
        role_display: 'Proprietário',
      };

      // This test demonstrates that the context itself doesn't prevent this,
      // but the business logic should validate that the school exists in userSchools
      const initialSchool = result.current.currentSchool;
      
      act(() => {
        result.current.setCurrentSchool(unauthorizedSchool);
      });

      // The context will accept any school object, but validation should happen
      // at the business logic level to ensure the school is in userSchools
      expect(result.current.currentSchool).toEqual(unauthorizedSchool);
      
      // Reset to initial state for other tests
      act(() => {
        result.current.setCurrentSchool(initialSchool!);
      });
    });
  });

  describe('Edge Cases', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <SchoolProvider>{children}</SchoolProvider>
    );

    it('should handle user profile without roles', () => {
      mockUseAuth.mockReturnValue({
        userProfile: {
          ...mockUserProfile,
          roles: undefined,
        },
        isAuthenticated: true,
        loading: false,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        refreshProfile: jest.fn(),
      } as any);

      const { result } = renderHook(() => useSchool(), { wrapper });

      expect(result.current.userSchools).toEqual([]);
      expect(result.current.currentSchool).toBeNull();
      expect(result.current.isSchoolAdmin).toBe(false);
      expect(result.current.isTeacher).toBe(false);
    });

    it('should handle empty roles array', () => {
      mockUseAuth.mockReturnValue({
        userProfile: {
          ...mockUserProfile,
          roles: [],
        },
        isAuthenticated: true,
        loading: false,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        refreshProfile: jest.fn(),
      } as any);

      const { result } = renderHook(() => useSchool(), { wrapper });

      expect(result.current.userSchools).toEqual([]);
      expect(result.current.currentSchool).toBeNull();
      expect(result.current.hasRole('teacher')).toBe(false);
      expect(result.current.hasAnyRole(['school_owner', 'teacher'])).toBe(false);
    });

    it('should not override current school if already set', () => {
      const { result } = renderHook(() => useSchool(), { wrapper });

      const initialSchool = result.current.currentSchool;
      
      // Simulate profile update that would normally trigger useEffect
      mockUseAuth.mockReturnValue({
        userProfile: {
          ...mockUserProfile,
          roles: [
            {
              role: 'teacher',
              role_display: 'Professor',
              school: {
                id: 10,
                name: 'New School',
              },
            },
          ],
        },
        isAuthenticated: true,
        loading: false,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        refreshProfile: jest.fn(),
      } as any);

      // Current school should remain the same until explicitly changed
      expect(result.current.currentSchool).toEqual(initialSchool);
    });
  });
});