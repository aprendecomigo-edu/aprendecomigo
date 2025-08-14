/**
 * Tasks API Service
 * Handles all task-related API operations using dependency injection
 */

import { ApiClient } from '../client/ApiClient';

export interface Task {
  id: number;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high';
  assigned_to?: number;
  assigned_by?: number;
  due_date?: string;
  created_at: string;
  updated_at: string;
  school_id?: number;
}

export interface CreateTaskData {
  title: string;
  description?: string;
  priority?: 'low' | 'medium' | 'high';
  assigned_to?: number;
  due_date?: string;
  school_id?: number;
}

export interface UpdateTaskData {
  title?: string;
  description?: string;
  status?: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority?: 'low' | 'medium' | 'high';
  assigned_to?: number;
  due_date?: string;
}

export interface TaskFilters {
  status?: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority?: 'low' | 'medium' | 'high';
  assigned_to?: number;
  school_id?: number;
  due_date_from?: string;
  due_date_to?: string;
}

export class TasksApiService {
  constructor(private readonly apiClient: ApiClient) {}

  /**
   * Get all tasks
   */
  async getTasks(filters?: TaskFilters): Promise<Task[]> {
    const params = new URLSearchParams();

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }

    const url = `/tasks/${params.toString() ? `?${params}` : ''}`;
    const response = await this.apiClient.get<Task[]>(url);
    return response.data;
  }

  /**
   * Get a specific task
   */
  async getTask(taskId: number): Promise<Task> {
    const response = await this.apiClient.get<Task>(`/tasks/${taskId}/`);
    return response.data;
  }

  /**
   * Create a new task
   */
  async createTask(data: CreateTaskData): Promise<Task> {
    const response = await this.apiClient.post<Task>('/tasks/', data);
    return response.data;
  }

  /**
   * Update an existing task
   */
  async updateTask(taskId: number, data: UpdateTaskData): Promise<Task> {
    const response = await this.apiClient.patch<Task>(`/tasks/${taskId}/`, data);
    return response.data;
  }

  /**
   * Delete a task
   */
  async deleteTask(taskId: number): Promise<void> {
    await this.apiClient.delete(`/tasks/${taskId}/`);
  }

  /**
   * Mark task as completed
   */
  async completeTask(taskId: number): Promise<Task> {
    const response = await this.apiClient.patch<Task>(`/tasks/${taskId}/`, {
      status: 'completed',
    });
    return response.data;
  }
}
