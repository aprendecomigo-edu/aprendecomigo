import { useState, useEffect, useCallback, useMemo } from 'react';

import {
  TeacherProfile,
  TeacherFilters,
  TeacherListResponse,
  getTeachersEnhanced,
  getTeachers,
} from '@/api/userApi';

interface UseTeachersOptions {
  useEnhanced?: boolean;
  initialFilters?: TeacherFilters;
  autoFetch?: boolean;
}

interface UseTeachersReturn {
  teachers: TeacherProfile[];
  loading: boolean;
  error: string | null;
  filters: TeacherFilters;
  pagination: {
    count: number;
    next: string | null;
    previous: string | null;
    currentPage: number;
    totalPages: number;
  };

  // Actions
  fetchTeachers: () => Promise<void>;
  setFilters: (filters: Partial<TeacherFilters>) => void;
  clearFilters: () => void;
  refresh: () => Promise<void>;

  // Filtering helpers
  filteredTeachers: TeacherProfile[];
  getTeachersByCompletion: (status: 'complete' | 'incomplete' | 'critical') => TeacherProfile[];
  getTeachersByStatus: (status: 'active' | 'inactive' | 'pending') => TeacherProfile[];
  searchTeachers: (query: string) => TeacherProfile[];
}

export const useTeachers = (options: UseTeachersOptions = {}): UseTeachersReturn => {
  const { useEnhanced = true, initialFilters = {}, autoFetch = true } = options;

  const [teachers, setTeachers] = useState<TeacherProfile[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFiltersState] = useState<TeacherFilters>({
    page: 1,
    page_size: 20,
    ordering: '-profile_completion_score',
    ...initialFilters,
  });
  const [pagination, setPagination] = useState({
    count: 0,
    next: null as string | null,
    previous: null as string | null,
    currentPage: 1,
    totalPages: 1,
  });

  const fetchTeachers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      if (useEnhanced) {
        const response: TeacherListResponse = await getTeachersEnhanced(filters);
        setTeachers(response.results);
        setPagination({
          count: response.count,
          next: response.next,
          previous: response.previous,
          currentPage: filters.page || 1,
          totalPages: Math.ceil(response.count / (filters.page_size || 20)),
        });
      } else {
        // Fallback to legacy API
        const response = await getTeachers();
        setTeachers(response);
        setPagination({
          count: response.length,
          next: null,
          previous: null,
          currentPage: 1,
          totalPages: 1,
        });
      }
    } catch (err: any) {
      console.error('Error fetching teachers:', err);
      setError(err.message || 'Failed to load teachers');
    } finally {
      setLoading(false);
    }
  }, [filters, useEnhanced]);

  const setFilters = useCallback((newFilters: Partial<TeacherFilters>) => {
    setFiltersState(prev => ({
      ...prev,
      ...newFilters,
      page: newFilters.page || 1, // Reset to first page when filters change
    }));
  }, []);

  const clearFilters = useCallback(() => {
    setFiltersState({
      page: 1,
      page_size: 20,
      ordering: '-profile_completion_score',
    });
  }, []);

  const refresh = useCallback(async () => {
    await fetchTeachers();
  }, [fetchTeachers]);

  // Auto-fetch when filters change
  useEffect(() => {
    if (autoFetch) {
      fetchTeachers();
    }
  }, [fetchTeachers, autoFetch]);

  // Computed values for filtering
  const filteredTeachers = useMemo(() => {
    let result = [...teachers];

    // Local filtering for immediate feedback (server-side filtering is primary)
    if (filters.search) {
      const query = filters.search.toLowerCase();
      result = result.filter(
        teacher =>
          teacher.user.name.toLowerCase().includes(query) ||
          teacher.user.email.toLowerCase().includes(query) ||
          teacher.specialty?.toLowerCase().includes(query) ||
          teacher.bio?.toLowerCase().includes(query),
      );
    }

    return result;
  }, [teachers, filters.search]);

  const getTeachersByCompletion = useCallback(
    (status: 'complete' | 'incomplete' | 'critical') => {
      return teachers.filter(teacher => {
        const completionScore = teacher.profile_completion_score || 0;
        const hasProfileCompletion = teacher.profile_completion;
        const hasCriticalMissing =
          hasProfileCompletion && teacher.profile_completion!.missing_critical.length > 0;

        switch (status) {
          case 'complete':
            return teacher.is_profile_complete && completionScore >= 80;
          case 'critical':
            return hasCriticalMissing || completionScore < 30;
          case 'incomplete':
            return !teacher.is_profile_complete && completionScore < 80 && !hasCriticalMissing;
          default:
            return false;
        }
      });
    },
    [teachers],
  );

  const getTeachersByStatus = useCallback(
    (status: 'active' | 'inactive' | 'pending') => {
      return teachers.filter(teacher => teacher.status === status);
    },
    [teachers],
  );

  const searchTeachers = useCallback(
    (query: string) => {
      if (!query.trim()) return teachers;

      const searchQuery = query.toLowerCase();
      return teachers.filter(
        teacher =>
          teacher.user.name.toLowerCase().includes(searchQuery) ||
          teacher.user.email.toLowerCase().includes(searchQuery) ||
          teacher.specialty?.toLowerCase().includes(searchQuery) ||
          teacher.bio?.toLowerCase().includes(searchQuery) ||
          teacher.teacher_courses?.some(
            course =>
              course.course_name.toLowerCase().includes(searchQuery) ||
              course.subject_area.toLowerCase().includes(searchQuery),
          ),
      );
    },
    [teachers],
  );

  return {
    teachers,
    loading,
    error,
    filters,
    pagination,

    // Actions
    fetchTeachers,
    setFilters,
    clearFilters,
    refresh,

    // Filtering helpers
    filteredTeachers,
    getTeachersByCompletion,
    getTeachersByStatus,
    searchTeachers,
  };
};

export default useTeachers;
