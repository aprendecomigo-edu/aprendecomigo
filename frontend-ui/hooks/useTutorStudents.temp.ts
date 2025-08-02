import { useState, useCallback } from 'react';

// Temporary mock implementation for testing
export interface TutorStudent {
  id: number;
  name: string;
  email: string;
  status: 'active' | 'inactive' | 'pending';
  progress?: {
    lastSessionDate?: string;
    completionRate?: number;
    totalSessions?: number;
  };
}

interface UseTutorStudentsResult {
  students: TutorStudent[];
  totalStudents: number;
  activeStudents: number;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

// Mock data for testing
const mockStudents: TutorStudent[] = [
  {
    id: 1,
    name: 'Maria Silva',
    email: 'maria.silva@example.com',
    status: 'active',
    progress: {
      lastSessionDate: '2025-07-30',
      completionRate: 0.85,
      totalSessions: 12,
    },
  },
  {
    id: 2,
    name: 'João Santos',
    email: 'joao.santos@example.com',
    status: 'active',
    progress: {
      lastSessionDate: '2025-07-29',
      completionRate: 0.72,
      totalSessions: 8,
    },
  },
  {
    id: 3,
    name: 'Ana Costa',
    email: 'ana.costa@example.com',
    status: 'pending',
    progress: {
      totalSessions: 0,
    },
  },
];

export const useTutorStudents = (schoolId?: number): UseTutorStudentsResult => {
  const [students] = useState<TutorStudent[]>(mockStudents);
  const [isLoading] = useState(false);
  const [error] = useState<string | null>(null);

  const totalStudents = students.length;
  const activeStudents = students.filter(s => s.status === 'active').length;

  const refresh = useCallback(async () => {
    // Mock refresh - no-op for testing
    console.log('Refreshing tutor students for school:', schoolId);
  }, [schoolId]);

  return {
    students,
    totalStudents,
    activeStudents,
    isLoading,
    error,
    refresh,
  };
};

export default useTutorStudents;
