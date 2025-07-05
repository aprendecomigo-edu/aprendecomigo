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
  getTeacherAvailability: (teacherId?: number): Promise<TeacherAvailability[]> => {
    const params = teacherId ? { teacher_id: teacherId } : {};
    return apiClient.get('/scheduler/api/availability/', { params });
  },

  createTeacherAvailability: (
    data: Omit<
      TeacherAvailability,
      'id' | 'teacher_name' | 'school_name' | 'day_of_week_display' | 'created_at' | 'updated_at'
    >
  ): Promise<TeacherAvailability> => {
    return apiClient.post('/scheduler/api/availability/', data);
  },

  updateTeacherAvailability: (
    id: number,
    data: Partial<TeacherAvailability>
  ): Promise<TeacherAvailability> => {
    return apiClient.patch(`/scheduler/api/availability/${id}/`, data);
  },

  deleteTeacherAvailability: (id: number): Promise<void> => {
    return apiClient.delete(`/scheduler/api/availability/${id}/`);
  },

  // Teacher Unavailability
  getTeacherUnavailability: (teacherId?: number): Promise<TeacherUnavailability[]> => {
    const params = teacherId ? { teacher_id: teacherId } : {};
    return apiClient.get('/scheduler/api/unavailability/', { params });
  },

  createTeacherUnavailability: (
    data: Omit<TeacherUnavailability, 'id' | 'teacher_name' | 'school_name' | 'created_at'>
  ): Promise<TeacherUnavailability> => {
    return apiClient.post('/scheduler/api/unavailability/', data);
  },

  updateTeacherUnavailability: (
    id: number,
    data: Partial<TeacherUnavailability>
  ): Promise<TeacherUnavailability> => {
    return apiClient.patch(`/scheduler/api/unavailability/${id}/`, data);
  },

  deleteTeacherUnavailability: (id: number): Promise<void> => {
    return apiClient.delete(`/scheduler/api/unavailability/${id}/`);
  },

  // Class Schedules
  getClassSchedules: (params?: {
    start_date?: string;
    end_date?: string;
    status?: string;
    teacher_id?: number;
    student_id?: number;
  }): Promise<ClassSchedule[]> => {
    return apiClient.get('/scheduler/api/schedules/', { params });
  },

  getClassSchedule: (id: number): Promise<ClassSchedule> => {
    return apiClient.get(`/scheduler/api/schedules/${id}/`);
  },

  createClassSchedule: (data: CreateClassScheduleData): Promise<ClassSchedule> => {
    return apiClient.post('/scheduler/api/schedules/', data);
  },

  updateClassSchedule: (
    id: number,
    data: Partial<CreateClassScheduleData>
  ): Promise<ClassSchedule> => {
    return apiClient.patch(`/scheduler/api/schedules/${id}/`, data);
  },

  deleteClassSchedule: (id: number): Promise<void> => {
    return apiClient.delete(`/scheduler/api/schedules/${id}/`);
  },

  // Class Schedule Actions
  cancelClass: (id: number, reason?: string): Promise<{ message: string }> => {
    return apiClient.post(`/scheduler/api/schedules/${id}/cancel/`, { reason });
  },

  confirmClass: (id: number): Promise<{ message: string }> => {
    return apiClient.post(`/scheduler/api/schedules/${id}/confirm/`);
  },

  completeClass: (id: number): Promise<{ message: string }> => {
    return apiClient.post(`/scheduler/api/schedules/${id}/complete/`);
  },

  // Get user's classes
  getMyClasses: (): Promise<ClassSchedule[]> => {
    return apiClient.get('/scheduler/api/schedules/my_classes/');
  },

  // Get available time slots
  getAvailableTimeSlots: (teacherId: number, date: string): Promise<AvailableTimeSlotsResponse> => {
    return apiClient.get('/scheduler/api/schedules/available_slots/', {
      params: { teacher_id: teacherId, date },
    });
  },

  // Recurring Schedules
  getRecurringSchedules: (): Promise<RecurringClassSchedule[]> => {
    return apiClient.get('/scheduler/api/recurring/');
  },

  createRecurringSchedule: (
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
    return apiClient.post('/scheduler/api/recurring/', data);
  },

  updateRecurringSchedule: (
    id: number,
    data: Partial<RecurringClassSchedule>
  ): Promise<RecurringClassSchedule> => {
    return apiClient.patch(`/scheduler/api/recurring/${id}/`, data);
  },

  deleteRecurringSchedule: (id: number): Promise<void> => {
    return apiClient.delete(`/scheduler/api/recurring/${id}/`);
  },

  generateSchedulesFromRecurring: (
    id: number,
    weeksAhead?: number
  ): Promise<{ message: string; schedules: ClassSchedule[] }> => {
    return apiClient.post(`/scheduler/api/recurring/${id}/generate_schedules/`, {
      weeks_ahead: weeksAhead || 4,
    });
  },
};

export default schedulerApi;
