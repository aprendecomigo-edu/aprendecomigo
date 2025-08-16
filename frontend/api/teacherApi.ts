import apiClient from './apiClient';

export interface TeacherInfo {
  id: number;
  name: string;
  email: string;
  specialty: string;
  hourly_rate: number;
  profile_completion_score: number;
  schools: {
    id: number;
    name: string;
    joined_at: string;
  }[];
  courses_taught: {
    id: number;
    name: string;
    code: string;
    hourly_rate: number;
  }[];
}

export interface StudentProgress {
  id: number;
  name: string;
  email: string;
  current_level: string;
  completion_percentage: number;
  last_session_date: string | null;
  recent_assessments: {
    id: number;
    title: string;
    assessment_type: string;
    percentage: number;
    assessment_date: string;
  }[];
  skills_mastered: string[];
}

export interface SessionInfo {
  id: number;
  date: string;
  start_time: string;
  end_time: string;
  session_type: string;
  grade_level: string;
  student_count: number;
  student_names: string[];
  status: string;
  notes: string;
  duration_hours: number;
}

export interface SessionsData {
  today: SessionInfo[];
  upcoming: SessionInfo[];
  recent_completed: SessionInfo[];
}

export interface ProgressMetrics {
  average_student_progress: number;
  total_assessments_given: number;
  students_improved_this_month: number;
  completion_rate_trend: number;
}

export interface RecentActivity {
  id: string;
  activity_type: string;
  description: string;
  timestamp: string;
  actor_name: string | null;
  school_name: string;
}

export interface EarningsData {
  current_month_total: number;
  last_month_total: number;
  pending_amount: number;
  total_hours_taught: number;
  recent_payments: {
    id: number;
    amount: number;
    date: string;
    session_info: string;
    hours: number;
  }[];
}

export interface QuickStats {
  total_students: number;
  sessions_today: number;
  sessions_this_week: number;
  completion_rate: number;
  average_rating: number | null;
}

export interface TeacherDashboardData {
  teacher_info: TeacherInfo;
  students: StudentProgress[];
  sessions: SessionsData;
  progress_metrics: ProgressMetrics;
  recent_activities: RecentActivity[];
  earnings: EarningsData;
  quick_stats: QuickStats;
}

/**
 * Get consolidated dashboard data for the authenticated teacher
 */
export const getTeacherDashboard = async (): Promise<TeacherDashboardData> => {
  try {
    const response = await apiClient.get('/api/accounts/teachers/consolidated_dashboard/');
    return response.data;
  } catch (error) {
    console.error('Error fetching teacher dashboard:', error);
    throw error;
  }
};

/**
 * Get student progress data with optional filtering
 */
export const getStudentProgress = async (
  schoolId?: number,
  searchQuery?: string,
): Promise<StudentProgress[]> => {
  try {
    const params: any = {};
    if (schoolId) params.school_id = schoolId;
    if (searchQuery) params.search = searchQuery;

    const response = await apiClient.get('/api/students/progress/', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching student progress:', error);
    throw error;
  }
};

/**
 * Get detailed student information
 */
export const getStudentDetail = async (studentId: number): Promise<StudentProgress> => {
  try {
    const response = await apiClient.get(`/api/students/${studentId}/progress/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching student detail:', error);
    throw error;
  }
};

/**
 * Update student progress
 */
export const updateStudentProgress = async (
  studentId: number,
  progressData: Partial<StudentProgress>,
): Promise<StudentProgress> => {
  try {
    const response = await apiClient.patch(`/api/students/${studentId}/progress/`, progressData);
    return response.data;
  } catch (error) {
    console.error('Error updating student progress:', error);
    throw error;
  }
};

/**
 * Schedule a new session
 */
export const scheduleSession = async (sessionData: {
  student_ids: number[];
  date: string;
  start_time: string;
  end_time: string;
  session_type: string;
  grade_level?: string;
  notes?: string;
}): Promise<SessionInfo> => {
  try {
    const response = await apiClient.post('/api/sessions/', sessionData);
    return response.data;
  } catch (error) {
    console.error('Error scheduling session:', error);
    throw error;
  }
};

/**
 * Get teacher analytics
 */
export const getTeacherAnalytics = async (timeframe: 'week' | 'month' | 'year' = 'month') => {
  try {
    const response = await apiClient.get(`/api/teachers/analytics/`, {
      params: { timeframe },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching teacher analytics:', error);
    throw error;
  }
};
