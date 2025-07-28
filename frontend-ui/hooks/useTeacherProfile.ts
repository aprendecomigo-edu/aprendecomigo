import { useState, useEffect, useCallback } from 'react';
import { 
  TeacherProfile, 
  UpdateTeacherData,
  getTeacherProfileDetailed,
  updateTeacherProfileAdmin
} from '@/api/userApi';

interface UseTeacherProfileOptions {
  teacherId?: number;
  autoFetch?: boolean;
}

interface UseTeacherProfileReturn {
  profile: TeacherProfile | null;
  loading: boolean;
  error: string | null;
  updating: boolean;
  
  // Actions
  fetchProfile: (id?: number) => Promise<void>;
  updateProfile: (data: UpdateTeacherData) => Promise<void>;
  refresh: () => Promise<void>;
  
  // Profile analysis helpers
  getCompletionStatus: () => 'complete' | 'incomplete' | 'critical';
  getMissingCriticalFields: () => string[];
  getMissingOptionalFields: () => string[];
  getRecommendations: () => Array<{ text: string; priority: 'high' | 'medium' | 'low' }>;
  getCompletionPercentage: () => number;
  
  // Course helpers
  getActiveCourses: () => any[];
  getCoursesCount: () => number;
  getSubjectAreas: () => string[];
  
  // Status helpers
  isActive: () => boolean;
  hasCalendarIntegration: () => boolean;
  hasContactInfo: () => boolean;
}

export const useTeacherProfile = (options: UseTeacherProfileOptions = {}): UseTeacherProfileReturn => {
  const { teacherId, autoFetch = true } = options;
  
  const [profile, setProfile] = useState<TeacherProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);

  const fetchProfile = useCallback(async (id?: number) => {
    const targetId = id || teacherId;
    if (!targetId) {
      setError('No teacher ID provided');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const profileData = await getTeacherProfileDetailed(targetId);
      setProfile(profileData);
    } catch (err: any) {
      console.error('Error fetching teacher profile:', err);
      setError(err.message || 'Failed to load teacher profile');
    } finally {
      setLoading(false);
    }
  }, [teacherId]);

  const updateProfile = useCallback(async (data: UpdateTeacherData) => {
    if (!profile?.id) {
      throw new Error('No profile loaded');
    }

    try {
      setUpdating(true);
      setError(null);
      
      const updatedProfile = await updateTeacherProfileAdmin(profile.id, data);
      setProfile(updatedProfile);
    } catch (err: any) {
      console.error('Error updating teacher profile:', err);
      const errorMessage = err.message || 'Failed to update teacher profile';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setUpdating(false);
    }
  }, [profile?.id]);

  const refresh = useCallback(async () => {
    if (profile?.id) {
      await fetchProfile(profile.id);
    }
  }, [profile?.id, fetchProfile]);

  // Auto-fetch on mount or when teacherId changes
  useEffect(() => {
    if (autoFetch && teacherId) {
      fetchProfile(teacherId);
    }
  }, [autoFetch, teacherId, fetchProfile]);

  // Profile analysis helpers
  const getCompletionStatus = useCallback((): 'complete' | 'incomplete' | 'critical' => {
    if (!profile) return 'incomplete';
    
    const completionScore = profile.profile_completion_score || 0;
    const hasCriticalMissing = profile.profile_completion?.missing_critical?.length > 0;
    
    if (hasCriticalMissing || completionScore < 30) {
      return 'critical';
    } else if (profile.is_profile_complete && completionScore >= 80) {
      return 'complete';
    } else {
      return 'incomplete';
    }
  }, [profile]);

  const getMissingCriticalFields = useCallback((): string[] => {
    return profile?.profile_completion?.missing_critical || [];
  }, [profile]);

  const getMissingOptionalFields = useCallback((): string[] => {
    return profile?.profile_completion?.missing_optional || [];
  }, [profile]);

  const getRecommendations = useCallback(() => {
    return profile?.profile_completion?.recommendations || [];
  }, [profile]);

  const getCompletionPercentage = useCallback((): number => {
    return profile?.profile_completion?.completion_percentage || profile?.profile_completion_score || 0;
  }, [profile]);

  // Course helpers
  const getActiveCourses = useCallback(() => {
    return profile?.teacher_courses?.filter(course => course.is_active) || [];
  }, [profile]);

  const getCoursesCount = useCallback((): number => {
    return getActiveCourses().length;
  }, [getActiveCourses]);

  const getSubjectAreas = useCallback((): string[] => {
    const courses = getActiveCourses();
    const areas = courses.map(course => course.subject_area);
    return [...new Set(areas)].filter(Boolean);
  }, [getActiveCourses]);

  // Status helpers
  const isActive = useCallback((): boolean => {
    return profile?.status === 'active' || !profile?.status; // Default to active if no status
  }, [profile]);

  const hasCalendarIntegration = useCallback((): boolean => {
    return Boolean(profile?.calendar_iframe?.trim());
  }, [profile]);

  const hasContactInfo = useCallback((): boolean => {
    const hasPhone = Boolean(profile?.phone_number?.trim());
    const hasAddress = Boolean(profile?.address?.trim());
    return hasPhone || hasAddress;
  }, [profile]);

  return {
    profile,
    loading,
    error,
    updating,
    
    // Actions
    fetchProfile,
    updateProfile,
    refresh,
    
    // Profile analysis helpers
    getCompletionStatus,
    getMissingCriticalFields,
    getMissingOptionalFields,
    getRecommendations,
    getCompletionPercentage,
    
    // Course helpers
    getActiveCourses,
    getCoursesCount,
    getSubjectAreas,
    
    // Status helpers
    isActive,
    hasCalendarIntegration,
    hasContactInfo
  };
};

export default useTeacherProfile;