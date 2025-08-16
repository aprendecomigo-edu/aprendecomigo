import apiClient from './apiClient';

export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed';
  priority: 'low' | 'medium' | 'high';
  task_type: 'onboarding' | 'assignment' | 'personal' | 'system';
  due_date?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
  is_urgent: boolean;
  is_system_generated: boolean;
  is_overdue: boolean;
  days_until_due?: number;
}

export interface CreateTaskData {
  title: string;
  description?: string;
  priority: 'low' | 'medium' | 'high';
  task_type: 'onboarding' | 'assignment' | 'personal' | 'system';
  due_date?: string;
  is_urgent?: boolean;
}

export interface UpdateTaskData {
  title?: string;
  description?: string;
  status?: 'pending' | 'in_progress' | 'completed';
  priority?: 'low' | 'medium' | 'high';
  task_type?: 'onboarding' | 'assignment' | 'personal' | 'system';
  due_date?: string;
  is_urgent?: boolean;
}

export interface TaskSummary {
  total_tasks: number;
  pending_tasks: number;
  in_progress_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  urgent_tasks: number;
  tasks_due_today: number;
  tasks_due_this_week: number;
}

class TasksApi {
  async getAllTasks(): Promise<Task[]> {
    const response = await apiClient.get('/tasks/');
    return response.data.results || response.data;
  }

  async getTask(id: string): Promise<Task> {
    const response = await apiClient.get(`/tasks/${id}/`);
    return response.data;
  }

  async createTask(data: CreateTaskData): Promise<Task> {
    const response = await apiClient.post('/tasks/', data);
    return response.data;
  }

  async updateTask(id: string, data: UpdateTaskData): Promise<Task> {
    const response = await apiClient.put(`/tasks/${id}/`, data);
    return response.data;
  }

  async partialUpdateTask(id: string, data: Partial<UpdateTaskData>): Promise<Task> {
    const response = await apiClient.patch(`/tasks/${id}/`, data);
    return response.data;
  }

  async deleteTask(id: string): Promise<void> {
    await apiClient.delete(`/tasks/${id}/`);
  }

  async completeTask(id: string): Promise<Task> {
    const response = await apiClient.post(`/tasks/${id}/complete/`, {});
    return response.data;
  }

  async reopenTask(id: string): Promise<Task> {
    const response = await apiClient.post(`/tasks/${id}/reopen/`, {});
    return response.data;
  }

  async getTaskSummary(): Promise<TaskSummary> {
    const response = await apiClient.get('/tasks/summary/');
    return response.data;
  }

  async getPendingTasks(): Promise<Task[]> {
    const response = await apiClient.get('/tasks/pending/');
    return response.data.results || response.data;
  }

  async getOverdueTasks(): Promise<Task[]> {
    const response = await apiClient.get('/tasks/overdue/');
    return response.data.results || response.data;
  }

  async getTasksDueToday(): Promise<Task[]> {
    const response = await apiClient.get('/tasks/due_today/');
    return response.data.results || response.data;
  }

  async getTasksForCalendar(startDate?: string, endDate?: string): Promise<Task[]> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await apiClient.get(
      `/tasks/calendar/${params.toString() ? '?' + params.toString() : ''}`,
    );
    return response.data.results || response.data;
  }
}

export const tasksApi = new TasksApi();
