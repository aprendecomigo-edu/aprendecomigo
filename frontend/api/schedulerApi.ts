import apiClient from './apiClient';

// Types for scheduler API
export interface TeacherAvailability {
  id: number;
  teacher: number;
  teacher_name: string;
  school: number;
  school_name: string;
  day_of_week: string;
  day_of_week_display: string;
  start_time: string;
  end_time: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TeacherUnavailability {
  id: number;
  teacher: number;
  teacher_name: string;
  school: number;
  school_name: string;
  date: string;
  start_time?: string;
  end_time?: string;
  reason: string;
  is_all_day: boolean;
  created_at: string;
}

export interface ClassSchedule {
  id: number;
  teacher: number;
  teacher_name: string;
  student: number;
  student_name: string;
  school: number;
  school_name: string;
  title: string;
  description: string;
  class_type: 'individual' | 'group' | 'trial';
  class_type_display: string;
  status: 'scheduled' | 'confirmed' | 'completed' | 'cancelled' | 'no_show';
  status_display: string;
  scheduled_date: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  booked_by: number;
  booked_by_name: string;
  booked_at: string;
  additional_students_names: string[];
  cancelled_at?: string;
  cancellation_reason?: string;
  completed_at?: string;
  teacher_notes: string;
  student_notes: string;
  can_be_cancelled: boolean;
  is_past: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateClassScheduleData {
  teacher: number;
  student: number;
  school: number;
  title: string;
  description?: string;
  class_type: 'individual' | 'group' | 'trial';
  scheduled_date: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  additional_students?: number[];
}

export interface RecurringClassSchedule {
  id: number;
  teacher: number;
  teacher_name: string;
  student: number;
  student_name: string;
  school: number;
  school_name: string;
  title: string;
  description: string;
  class_type: 'individual' | 'group' | 'trial';
  class_type_display: string;
  day_of_week: string;
  day_of_week_display: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  start_date: string;
  end_date?: string;
  is_active: boolean;
  created_by: number;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface AvailableTimeSlot {
  start_time: string;
  end_time: string;
  school_id: number;
  school_name: string;
}

export interface AvailableTimeSlotsResponse {
  teacher_id: number;
  date: string;
  available_slots: AvailableTimeSlot[];
}

// Scheduler API functions
export const schedulerApi = {
  // Teacher Availability
  getTeacherAvailability: async (teacherId?: number): Promise<TeacherAvailability[]> => {
    const params = teacherId ? { teacher_id: teacherId } : {};
    const response = await apiClient.get('/scheduler/api/availability/', { params });

    // Handle paginated response - extract results
    if (response.data && Array.isArray(response.data.results)) {
      return response.data.results;
    } else if (Array.isArray(response.data)) {
      // Fallback for non-paginated response
      return response.data;
    } else {
      if (__DEV__) {
        console.warn('API did not return expected format:', response.data);
      }
      return [];
    }
  },

  createTeacherAvailability: async (
    data: Omit<
      TeacherAvailability,
      'id' | 'teacher_name' | 'school_name' | 'day_of_week_display' | 'created_at' | 'updated_at'
    >
  ): Promise<TeacherAvailability> => {
    const response = await apiClient.post('/scheduler/api/availability/', data);
    return response.data;
  },

  updateTeacherAvailability: async (
    id: number,
    data: Partial<TeacherAvailability>
  ): Promise<TeacherAvailability> => {
    const response = await apiClient.patch(`/scheduler/api/availability/${id}/`, data);
    return response.data;
  },

  deleteTeacherAvailability: (id: number): Promise<void> => {
    return apiClient.delete(`/scheduler/api/availability/${id}/`);
  },

  // Teacher Unavailability
  getTeacherUnavailability: async (teacherId?: number): Promise<TeacherUnavailability[]> => {
    const params = teacherId ? { teacher_id: teacherId } : {};
    const response = await apiClient.get('/scheduler/api/unavailability/', { params });

    // Handle paginated response - extract results
    if (response.data && Array.isArray(response.data.results)) {
      return response.data.results;
    } else if (Array.isArray(response.data)) {
      // Fallback for non-paginated response
      return response.data;
    } else {
      if (__DEV__) {
        console.warn('API did not return expected format:', response.data);
      }
      return [];
    }
  },

  createTeacherUnavailability: async (
    data: Omit<TeacherUnavailability, 'id' | 'teacher_name' | 'school_name' | 'created_at'>
  ): Promise<TeacherUnavailability> => {
    const response = await apiClient.post('/scheduler/api/unavailability/', data);
    return response.data;
  },

  updateTeacherUnavailability: async (
    id: number,
    data: Partial<TeacherUnavailability>
  ): Promise<TeacherUnavailability> => {
    const response = await apiClient.patch(`/scheduler/api/unavailability/${id}/`, data);
    return response.data;
  },

  deleteTeacherUnavailability: (id: number): Promise<void> => {
    return apiClient.delete(`/scheduler/api/unavailability/${id}/`);
  },

  // Class Schedules
  getClassSchedules: async (params?: {
    start_date?: string;
    end_date?: string;
    status?: string;
    teacher_id?: number;
    student_id?: number;
  }): Promise<ClassSchedule[]> => {
    const response = await apiClient.get('/scheduler/api/schedules/', { params });

    // Handle paginated response - extract results
    if (response.data && Array.isArray(response.data.results)) {
      return response.data.results;
    } else if (Array.isArray(response.data)) {
      // Fallback for non-paginated response
      return response.data;
    } else {
      if (__DEV__) {
        console.warn('API did not return expected format:', response.data);
      }
      return [];
    }
  },

  getClassSchedule: async (id: number): Promise<ClassSchedule> => {
    const response = await apiClient.get(`/scheduler/api/schedules/${id}/`);
    return response.data;
  },

  createClassSchedule: async (data: CreateClassScheduleData): Promise<ClassSchedule> => {
    const response = await apiClient.post('/scheduler/api/schedules/', data);
    return response.data;
  },

  updateClassSchedule: async (
    id: number,
    data: Partial<CreateClassScheduleData>
  ): Promise<ClassSchedule> => {
    const response = await apiClient.patch(`/scheduler/api/schedules/${id}/`, data);
    return response.data;
  },

  deleteClassSchedule: (id: number): Promise<void> => {
    return apiClient.delete(`/scheduler/api/schedules/${id}/`);
  },

  // Class Schedule Actions
  cancelClass: async (id: number, reason?: string): Promise<{ message: string }> => {
    const response = await apiClient.post(`/scheduler/api/schedules/${id}/cancel/`, { reason });
    return response.data;
  },

  confirmClass: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.post(`/scheduler/api/schedules/${id}/confirm/`);
    return response.data;
  },

  completeClass: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.post(`/scheduler/api/schedules/${id}/complete/`);
    return response.data;
  },

  // Get user's classes
  getMyClasses: async (): Promise<ClassSchedule[]> => {
    const response = await apiClient.get('/scheduler/api/schedules/my_classes/');

    // Handle paginated response - extract results
    if (response.data && Array.isArray(response.data.results)) {
      return response.data.results;
    } else if (Array.isArray(response.data)) {
      // Fallback for non-paginated response
      return response.data;
    } else {
      if (__DEV__) {
        console.warn('API did not return expected format:', response.data);
      }
      return [];
    }
  },

  // Get available time slots
  getAvailableTimeSlots: async (
    teacherId: number,
    date: string
  ): Promise<AvailableTimeSlotsResponse> => {
    const response = await apiClient.get('/scheduler/api/schedules/available_slots/', {
      params: { teacher_id: teacherId, date },
    });
    return response.data;
  },

  // Recurring Schedules
  getRecurringSchedules: async (): Promise<RecurringClassSchedule[]> => {
    const response = await apiClient.get('/scheduler/api/recurring/');

    // Handle paginated response - extract results
    if (response.data && Array.isArray(response.data.results)) {
      return response.data.results;
    } else if (Array.isArray(response.data)) {
      // Fallback for non-paginated response
      return response.data;
    } else {
      if (__DEV__) {
        console.warn('API did not return expected format:', response.data);
      }
      return [];
    }
  },

  createRecurringSchedule: async (
    data: Omit<
      RecurringClassSchedule,
      | 'id'
      | 'teacher_name'
      | 'student_name'
      | 'school_name'
      | 'created_by_name'
      | 'day_of_week_display'
      | 'class_type_display'
      | 'created_at'
      | 'updated_at'
    >
  ): Promise<RecurringClassSchedule> => {
    const response = await apiClient.post('/scheduler/api/recurring/', data);
    return response.data;
  },

  updateRecurringSchedule: async (
    id: number,
    data: Partial<RecurringClassSchedule>
  ): Promise<RecurringClassSchedule> => {
    const response = await apiClient.patch(`/scheduler/api/recurring/${id}/`, data);
    return response.data;
  },

  deleteRecurringSchedule: (id: number): Promise<void> => {
    return apiClient.delete(`/scheduler/api/recurring/${id}/`);
  },

  generateSchedulesFromRecurring: async (
    id: number,
    weeksAhead?: number
  ): Promise<{ message: string; schedules: ClassSchedule[] }> => {
    const response = await apiClient.post(`/scheduler/api/recurring/${id}/generate_schedules/`, {
      weeks_ahead: weeksAhead || 4,
    });
    return response.data;
  },
};

export default schedulerApi;
