import { useState, useEffect, useCallback } from 'react';

import {
  StudentProfile,
  StudentFilters,
  StudentListResponse,
  getStudents,
  getStudentById,
  createStudent,
  updateStudent,
  deleteStudent,
  updateStudentStatus,
  bulkImportStudents,
  getEducationalSystems,
  EducationalSystem,
  CreateStudentData,
  UpdateStudentData,
  BulkImportResult,
} from '@/api/userApi';
import ApiValidator from '@/utils/apiValidation';

interface UseStudentsOptions {
  initialFilters?: StudentFilters;
  autoLoad?: boolean;
}

interface UseStudentsReturn {
  // Data
  students: StudentProfile[];
  totalCount: number;
  educationalSystems: EducationalSystem[];

  // Pagination
  currentPage: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;

  // Loading states
  isLoading: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  isDeleting: boolean;
  isBulkImporting: boolean;

  // Error states
  error: string | null;

  // Filters
  filters: StudentFilters;

  // Actions
  loadStudents: (newFilters?: StudentFilters) => Promise<void>;
  loadMoreStudents: () => Promise<void>;
  refreshStudents: () => Promise<void>;
  createStudentRecord: (data: CreateStudentData) => Promise<StudentProfile>;
  updateStudentRecord: (id: number, data: UpdateStudentData) => Promise<StudentProfile>;
  deleteStudentRecord: (id: number) => Promise<void>;
  updateStudentStatusRecord: (
    id: number,
    status: 'active' | 'inactive' | 'graduated',
  ) => Promise<StudentProfile>;
  bulkImportStudentsFromCSV: (file: File) => Promise<BulkImportResult>;
  getStudentByIdRecord: (id: number) => Promise<StudentProfile>;

  // Filter management
  setFilters: (newFilters: StudentFilters) => void;
  clearFilters: () => void;
  setSearch: (search: string) => void;
  setStatusFilter: (status?: 'active' | 'inactive' | 'graduated') => void;
  setEducationalSystemFilter: (systemId?: number) => void;
  setSchoolYearFilter: (schoolYear?: string) => void;
  setSortOrder: (ordering?: string) => void;
}

export const useStudents = (options: UseStudentsOptions = {}): UseStudentsReturn => {
  const { initialFilters = {}, autoLoad = true } = options;

  // State management
  const [students, setStudents] = useState<StudentProfile[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [educationalSystems, setEducationalSystems] = useState<EducationalSystem[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [hasPreviousPage, setHasPreviousPage] = useState(false);

  // Loading states
  const [isLoading, setIsLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isBulkImporting, setIsBulkImporting] = useState(false);

  // Error state
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [filters, setFiltersState] = useState<StudentFilters>({
    page: 1,
    page_size: 20,
    ...initialFilters,
  });

  // Load educational systems on mount
  useEffect(() => {
    const loadEducationalSystems = async () => {
      try {
        const systems = await getEducationalSystems();
        setEducationalSystems(systems);
      } catch (err: any) {
        console.error('Failed to load educational systems:', err);
      }
    };

    loadEducationalSystems();
  }, []);

  // Helper function to get specific error message based on HTTP status
  const getErrorMessage = (error: any, defaultMessage: string): string => {
    if (error.response?.status === 401) {
      return 'Sua sessão expirou. Faça login novamente para continuar.';
    } else if (error.response?.status === 403) {
      return 'Você não tem permissão para acessar estes dados.';
    } else if (error.response?.status === 404) {
      return 'Os dados solicitados não foram encontrados.';
    } else if (error.response?.status === 422) {
      return 'Dados inválidos enviados ao servidor. Verifique os filtros aplicados.';
    } else if (error.response?.status >= 500) {
      return 'Erro interno do servidor. Tente novamente em alguns minutos.';
    } else if (error.response?.status === 0 || error.code === 'NETWORK_ERROR') {
      return 'Erro de conexão. Verifique sua internet e tente novamente.';
    } else if (error.response?.data?.message) {
      return error.response.data.message;
    } else if (error.response?.data?.detail) {
      return error.response.data.detail;
    } else if (error.message) {
      return error.message;
    }
    return defaultMessage;
  };

  // Load students function
  const loadStudents = useCallback(
    async (newFilters?: StudentFilters) => {
      try {
        setIsLoading(true);
        setError(null);

        const filtersToUse = newFilters || filters;

        // Validate filters before sending request
        const validation = ApiValidator.validateStudentFilters(filtersToUse);
        if (!validation.isValid) {
          throw new Error(`Filtros inválidos: ${validation.errors.join(', ')}`);
        }

        const response: StudentListResponse = await getStudents(filtersToUse);

        setStudents(response.results);
        setTotalCount(response.count);
        setCurrentPage(filtersToUse.page || 1);
        setHasNextPage(!!response.next);
        setHasPreviousPage(!!response.previous);

        if (newFilters) {
          setFiltersState(filtersToUse);
        }
      } catch (err: any) {
        console.error('Failed to load students:', err);
        const errorMessage = getErrorMessage(
          err,
          'Erro ao carregar lista de alunos. Tente novamente.',
        );
        setError(errorMessage);
        setStudents([]);
        setTotalCount(0);
      } finally {
        setIsLoading(false);
      }
    },
    [filters],
  );

  // Load more students (pagination)
  const loadMoreStudents = useCallback(async () => {
    if (!hasNextPage || isLoading) return;

    const nextPage = currentPage + 1;
    const newFilters = { ...filters, page: nextPage };

    try {
      setIsLoading(true);
      setError(null);

      const response: StudentListResponse = await getStudents(newFilters);

      // Append new results to existing students
      setStudents(prev => [...prev, ...response.results]);
      setCurrentPage(nextPage);
      setHasNextPage(!!response.next);
      setHasPreviousPage(!!response.previous);
      setFiltersState(newFilters);
    } catch (err: any) {
      console.error('Failed to load more students:', err);
      const errorMessage = getErrorMessage(err, 'Erro ao carregar mais alunos. Tente novamente.');
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [hasNextPage, isLoading, currentPage, filters]);

  // Refresh students
  const refreshStudents = useCallback(async () => {
    await loadStudents(filters);
  }, [loadStudents, filters]);

  // CRUD operations
  const createStudentRecord = useCallback(
    async (data: CreateStudentData): Promise<StudentProfile> => {
      try {
        setIsCreating(true);
        setError(null);

        // Validate and sanitize data before sending
        const sanitizedData = ApiValidator.sanitizeStudentData(data);
        const validation = ApiValidator.validateStudentData(sanitizedData);
        if (!validation.isValid) {
          throw new Error(`Dados inválidos: ${validation.errors.join(', ')}`);
        }

        const newStudent = await createStudent(sanitizedData);

        // Add to the beginning of the list
        setStudents(prev => [newStudent, ...prev]);
        setTotalCount(prev => prev + 1);

        return newStudent;
      } catch (err: any) {
        console.error('Failed to create student:', err);
        const errorMessage = getErrorMessage(err, 'Erro ao criar aluno. Tente novamente.');
        setError(errorMessage);
        throw new Error(errorMessage);
      } finally {
        setIsCreating(false);
      }
    },
    [],
  );

  const updateStudentRecord = useCallback(
    async (id: number, data: UpdateStudentData): Promise<StudentProfile> => {
      try {
        setIsUpdating(true);
        setError(null);

        const updatedStudent = await updateStudent(id, data);

        // Update in the list
        setStudents(prev => prev.map(student => (student.id === id ? updatedStudent : student)));

        return updatedStudent;
      } catch (err: any) {
        console.error('Failed to update student:', err);
        const errorMessage = getErrorMessage(err, 'Erro ao atualizar aluno. Tente novamente.');
        setError(errorMessage);
        throw new Error(errorMessage);
      } finally {
        setIsUpdating(false);
      }
    },
    [],
  );

  const deleteStudentRecord = useCallback(async (id: number): Promise<void> => {
    try {
      setIsDeleting(true);
      setError(null);

      await deleteStudent(id);

      // Remove from the list
      setStudents(prev => prev.filter(student => student.id !== id));
      setTotalCount(prev => prev - 1);
    } catch (err: any) {
      console.error('Failed to delete student:', err);
      const errorMessage = getErrorMessage(err, 'Erro ao excluir aluno. Tente novamente.');
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsDeleting(false);
    }
  }, []);

  const updateStudentStatusRecord = useCallback(
    async (id: number, status: 'active' | 'inactive' | 'graduated'): Promise<StudentProfile> => {
      try {
        setIsUpdating(true);
        setError(null);

        // Validate status update data
        const validation = ApiValidator.validateStudentStatusUpdate(id, status);
        if (!validation.isValid) {
          throw new Error(`Parâmetros inválidos: ${validation.errors.join(', ')}`);
        }

        const updatedStudent = await updateStudentStatus(id, status);

        // Update in the list
        setStudents(prev => prev.map(student => (student.id === id ? updatedStudent : student)));

        return updatedStudent;
      } catch (err: any) {
        console.error('Failed to update student status:', err);
        const errorMessage = getErrorMessage(
          err,
          'Erro ao atualizar status do aluno. Tente novamente.',
        );
        setError(errorMessage);
        throw new Error(errorMessage);
      } finally {
        setIsUpdating(false);
      }
    },
    [],
  );

  const bulkImportStudentsFromCSV = useCallback(
    async (file: File): Promise<BulkImportResult> => {
      try {
        setIsBulkImporting(true);
        setError(null);

        const result = await bulkImportStudents(file);

        // Refresh the student list after import
        if (result.success && result.created_count > 0) {
          await refreshStudents();
        }

        return result;
      } catch (err: any) {
        console.error('Failed to bulk import students:', err);
        const errorMessage = getErrorMessage(
          err,
          'Erro ao importar alunos do CSV. Tente novamente.',
        );
        setError(errorMessage);
        throw new Error(errorMessage);
      } finally {
        setIsBulkImporting(false);
      }
    },
    [refreshStudents],
  );

  const getStudentByIdRecord = useCallback(async (id: number): Promise<StudentProfile> => {
    try {
      setError(null);
      return await getStudentById(id);
    } catch (err: any) {
      console.error('Failed to get student:', err);
      const errorMessage = getErrorMessage(err, 'Erro ao buscar dados do aluno. Tente novamente.');
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  // Filter management
  const setFilters = useCallback(
    (newFilters: StudentFilters) => {
      const updatedFilters = { ...filters, ...newFilters, page: 1 };
      setFiltersState(updatedFilters);
      loadStudents(updatedFilters);
    },
    [filters, loadStudents],
  );

  const clearFilters = useCallback(() => {
    const clearedFilters: StudentFilters = {
      page: 1,
      page_size: filters.page_size || 20,
    };
    setFiltersState(clearedFilters);
    loadStudents(clearedFilters);
  }, [filters.page_size, loadStudents]);

  const setSearch = useCallback(
    (search: string) => {
      setFilters({ search: search || undefined });
    },
    [setFilters],
  );

  const setStatusFilter = useCallback(
    (status?: 'active' | 'inactive' | 'graduated') => {
      setFilters({ status });
    },
    [setFilters],
  );

  const setEducationalSystemFilter = useCallback(
    (systemId?: number) => {
      setFilters({ educational_system: systemId });
    },
    [setFilters],
  );

  const setSchoolYearFilter = useCallback(
    (schoolYear?: string) => {
      setFilters({ school_year: schoolYear });
    },
    [setFilters],
  );

  const setSortOrder = useCallback(
    (ordering?: string) => {
      setFilters({ ordering });
    },
    [setFilters],
  );

  // Auto-load on mount
  useEffect(() => {
    if (autoLoad) {
      loadStudents();
    }
  }, [autoLoad, loadStudents]);

  return {
    // Data
    students,
    totalCount,
    educationalSystems,

    // Pagination
    currentPage,
    hasNextPage,
    hasPreviousPage,

    // Loading states
    isLoading,
    isCreating,
    isUpdating,
    isDeleting,
    isBulkImporting,

    // Error state
    error,

    // Filters
    filters,

    // Actions
    loadStudents,
    loadMoreStudents,
    refreshStudents,
    createStudentRecord,
    updateStudentRecord,
    deleteStudentRecord,
    updateStudentStatusRecord,
    bulkImportStudentsFromCSV,
    getStudentByIdRecord,

    // Filter management
    setFilters,
    clearFilters,
    setSearch,
    setStatusFilter,
    setEducationalSystemFilter,
    setSchoolYearFilter,
    setSortOrder,
  };
};
