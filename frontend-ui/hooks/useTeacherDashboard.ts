import { useEffect, useState, useCallback } from 'react';

import {
  getTeacherDashboard,
  TeacherDashboardData,
  StudentProgress,
  getStudentProgress,
  getStudentDetail,
} from '@/api/teacherApi';

export interface UseTeacherDashboardResult {
  data: TeacherDashboardData | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  lastUpdated: Date | null;
}

export const useTeacherDashboard = (): UseTeacherDashboardResult => {
  const [data, setData] = useState<TeacherDashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadDashboard = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const dashboardData = await getTeacherDashboard();
      setData(dashboardData);
      setLastUpdated(new Date());
    } catch (err: any) {
      console.error('Failed to load teacher dashboard:', err);
      setError(err?.response?.data?.detail || err?.message || 'Erro ao carregar dashboard');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    await loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  return {
    data,
    isLoading,
    error,
    refresh,
    lastUpdated,
  };
};

export interface UseTeacherStudentsResult {
  students: StudentProgress[];
  filteredStudents: StudentProgress[];
  isLoading: boolean;
  error: string | null;
  searchQuery: string;
  filterBy: 'all' | 'active' | 'needs_attention';
  setSearchQuery: (query: string) => void;
  setFilterBy: (filter: 'all' | 'active' | 'needs_attention') => void;
  refresh: () => Promise<void>;
  getStudentById: (id: number) => StudentProgress | undefined;
}

export const useTeacherStudents = (): UseTeacherStudentsResult => {
  const [students, setStudents] = useState<StudentProgress[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterBy, setFilterBy] = useState<'all' | 'active' | 'needs_attention'>('all');

  const loadStudents = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const studentsData = await getStudentProgress();
      setStudents(studentsData);
    } catch (err: any) {
      console.error('Failed to load students:', err);
      setError(err?.response?.data?.detail || err?.message || 'Erro ao carregar estudantes');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    await loadStudents();
  }, [loadStudents]);

  const getStudentById = useCallback(
    (id: number) => {
      return students.find(student => student.id === id);
    },
    [students]
  );

  // Filter students based on search query and filter criteria
  const filteredStudents = useCallback(() => {
    let filtered = students;

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      filtered = filtered.filter(
        student =>
          student.name.toLowerCase().includes(query) || student.email.toLowerCase().includes(query)
      );
    }

    // Apply category filter
    switch (filterBy) {
      case 'active':
        filtered = filtered.filter(
          student =>
            student.last_session_date &&
            new Date(student.last_session_date) >= new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) // Last 7 days
        );
        break;
      case 'needs_attention':
        filtered = filtered.filter(
          student =>
            student.completion_percentage < 50 ||
            !student.last_session_date ||
            new Date(student.last_session_date) < new Date(Date.now() - 14 * 24 * 60 * 60 * 1000) // More than 14 days ago
        );
        break;
      case 'all':
      default:
        // No additional filtering
        break;
    }

    return filtered;
  }, [students, searchQuery, filterBy])();

  useEffect(() => {
    loadStudents();
  }, [loadStudents]);

  return {
    students,
    filteredStudents,
    isLoading,
    error,
    searchQuery,
    filterBy,
    setSearchQuery,
    setFilterBy,
    refresh,
    getStudentById,
  };
};

export interface UseStudentDetailResult {
  student: StudentProgress | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export const useStudentDetail = (studentId: number): UseStudentDetailResult => {
  const [student, setStudent] = useState<StudentProgress | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStudent = useCallback(async () => {
    if (!studentId) return;

    try {
      setIsLoading(true);
      setError(null);

      const studentData = await getStudentDetail(studentId);
      setStudent(studentData);
    } catch (err: any) {
      console.error('Failed to load student detail:', err);
      setError(
        err?.response?.data?.detail || err?.message || 'Erro ao carregar detalhes do estudante'
      );
    } finally {
      setIsLoading(false);
    }
  }, [studentId]);

  const refresh = useCallback(async () => {
    await loadStudent();
  }, [loadStudent]);

  useEffect(() => {
    loadStudent();
  }, [loadStudent]);

  return {
    student,
    isLoading,
    error,
    refresh,
  };
};
