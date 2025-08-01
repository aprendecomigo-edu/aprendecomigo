import { useState, useCallback } from 'react';

// Temporary mock implementation for testing
export interface TutorAnalytics {
  total_hours_taught: number;
  total_students: number;
  average_rating: number;
  total_earnings: number;
  monthly_growth: {
    hours: number;
    students: number;
    earnings: number;
  };
  subject_breakdown: Array<{
    subject: string;
    hours_taught: number;
    students: number;
    earnings: number;
  }>;
  rating_distribution: {
    '5_star': number;
    '4_star': number;
    '3_star': number;
    '2_star': number;
    '1_star': number;
  };
  performance_metrics: {
    completion_rate: number;
    on_time_rate: number;
    student_retention: number;
  };
}

interface UseTutorAnalyticsResult {
  analytics: TutorAnalytics | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

// Mock data for testing
const mockAnalytics: TutorAnalytics = {
  total_hours_taught: 120,
  total_students: 15,
  average_rating: 4.8,
  total_earnings: 2400,
  monthly_growth: {
    hours: 15,
    students: 25,
    earnings: 20,
  },
  subject_breakdown: [
    { subject: 'Mathematics', hours_taught: 60, students: 8, earnings: 1200 },
    { subject: 'Physics', hours_taught: 40, students: 5, earnings: 800 },
    { subject: 'Chemistry', hours_taught: 20, students: 2, earnings: 400 },
  ],
  rating_distribution: {
    '5_star': 12,
    '4_star': 2,
    '3_star': 1,
    '2_star': 0,
    '1_star': 0,
  },
  performance_metrics: {
    completion_rate: 0.95,
    on_time_rate: 0.98,
    student_retention: 0.90,
  },
};

export const useTutorAnalytics = (schoolId?: number): UseTutorAnalyticsResult => {
  const [analytics] = useState<TutorAnalytics | null>(mockAnalytics);
  const [isLoading] = useState(false);
  const [error] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    // Mock refresh - no-op for testing
    console.log('Refreshing tutor analytics for school:', schoolId);
  }, [schoolId]);

  return {
    analytics,
    isLoading,
    error,
    refresh,
  };
};

export default useTutorAnalytics;