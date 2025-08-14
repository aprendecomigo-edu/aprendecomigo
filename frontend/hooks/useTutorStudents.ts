import { useCallback, useEffect, useState } from 'react';

import { useUserProfile } from '@/api/auth';
import { getStudents, StudentProfile } from '@/api/userApi';

interface TutorStudent extends StudentProfile {
  progress?: {
    completedSessions: number;
    totalPlannedSessions: number;
    completionRate: number;
    lastSessionDate?: string;
    nextSessionDate?: string;
  };
  acquisition?: {
    invitationDate?: string;
    invitationMethod?: string;
    conversionDays?: number;
  };
}

interface UseTutorStudentsResult {
  students: TutorStudent[];
  isLoading: boolean;
  error: string | null;
  totalStudents: number;
  activeStudents: number;
  refresh: () => Promise<void>;
}

const useTutorStudents = (schoolId?: number): UseTutorStudentsResult => {
  const { userProfile } = useUserProfile();
  const [students, setStudents] = useState<TutorStudent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStudents = useCallback(async () => {
    if (!schoolId) return;

    try {
      setIsLoading(true);
      setError(null);

      const response = await getStudents();

      // Enhance students with tutor-specific data
      const enhancedStudents: TutorStudent[] = response.results.map(student => ({
        ...student,
        progress: {
          completedSessions: Math.floor(Math.random() * 20), // Mock data
          totalPlannedSessions: Math.floor(Math.random() * 25) + 5,
          completionRate: Math.random() * 0.4 + 0.6, // 60-100%
          lastSessionDate: new Date(
            Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000
          ).toISOString(),
          nextSessionDate: new Date(
            Date.now() + Math.random() * 7 * 24 * 60 * 60 * 1000
          ).toISOString(),
        },
        acquisition: {
          invitationDate: new Date(
            Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000
          ).toISOString(),
          invitationMethod: ['email', 'link', 'referral'][Math.floor(Math.random() * 3)],
          conversionDays: Math.floor(Math.random() * 14) + 1,
        },
      }));

      setStudents(enhancedStudents);
    } catch (err) {
      console.error('Error fetching tutor students:', err);
      setError('Falha ao carregar estudantes');
    } finally {
      setIsLoading(false);
    }
  }, [schoolId]);

  const refresh = useCallback(async () => {
    await fetchStudents();
  }, [fetchStudents]);

  useEffect(() => {
    if (userProfile && schoolId) {
      fetchStudents();
    }
  }, [userProfile, schoolId, fetchStudents]);

  const totalStudents = students.length;
  const activeStudents = students.filter(student => {
    const lastSessionDate = student.progress?.lastSessionDate;
    if (!lastSessionDate) return false;
    const daysSinceLastSession =
      (Date.now() - new Date(lastSessionDate).getTime()) / (1000 * 60 * 60 * 24);
    return daysSinceLastSession <= 7; // Active if had session in last 7 days
  }).length;

  return {
    students,
    isLoading,
    error,
    totalStudents,
    activeStudents,
    refresh,
  };
};

// Export both named and default exports for compatibility
export { useTutorStudents };
export default useTutorStudents;
