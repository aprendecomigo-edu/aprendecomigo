import { useState, useEffect, useCallback } from 'react';

import { tasksApi, Task, CreateTaskData, UpdateTaskData, TaskSummary } from '@/api/tasksApi';

export interface UseTasksResult {
  tasks: Task[];
  loading: boolean;
  error: string | null;
  refreshTasks: () => Promise<void>;
  createTask: (data: CreateTaskData) => Promise<Task | null>;
  updateTask: (id: string, data: UpdateTaskData) => Promise<Task | null>;
  deleteTask: (id: string) => Promise<boolean>;
  toggleTaskCompletion: (id: string) => Promise<Task | null>;
  taskSummary: TaskSummary | null;
}

export const useTasks = (autoFetch: boolean = true): UseTasksResult => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [taskSummary, setTaskSummary] = useState<TaskSummary | null>(null);

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [tasksData, summaryData] = await Promise.all([
        tasksApi.getAllTasks(),
        tasksApi.getTaskSummary(),
      ]);

      setTasks(tasksData);
      setTaskSummary(summaryData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch tasks';
      setError(errorMessage);
      console.error('Error fetching tasks:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshTasks = useCallback(async () => {
    await fetchTasks();
  }, [fetchTasks]);

  const createTask = useCallback(async (data: CreateTaskData): Promise<Task | null> => {
    try {
      setError(null);
      const newTask = await tasksApi.createTask(data);
      setTasks(prev => [...prev, newTask]);

      // Refresh summary after creating
      try {
        const summary = await tasksApi.getTaskSummary();
        setTaskSummary(summary);
      } catch (summaryError) {
        console.warn('Failed to refresh task summary:', summaryError);
      }

      return newTask;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create task';
      setError(errorMessage);
      console.error('Error creating task:', err);
      return null;
    }
  }, []);

  const updateTask = useCallback(async (id: string, data: UpdateTaskData): Promise<Task | null> => {
    try {
      setError(null);
      const updatedTask = await tasksApi.partialUpdateTask(id, data);
      setTasks(prev => prev.map(task => (task.id === id ? updatedTask : task)));

      // Refresh summary after updating
      try {
        const summary = await tasksApi.getTaskSummary();
        setTaskSummary(summary);
      } catch (summaryError) {
        console.warn('Failed to refresh task summary:', summaryError);
      }

      return updatedTask;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update task';
      setError(errorMessage);
      console.error('Error updating task:', err);
      return null;
    }
  }, []);

  const deleteTask = useCallback(async (id: string): Promise<boolean> => {
    try {
      setError(null);
      await tasksApi.deleteTask(id);
      setTasks(prev => prev.filter(task => task.id !== id));

      // Refresh summary after deleting
      try {
        const summary = await tasksApi.getTaskSummary();
        setTaskSummary(summary);
      } catch (summaryError) {
        console.warn('Failed to refresh task summary:', summaryError);
      }

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete task';
      setError(errorMessage);
      console.error('Error deleting task:', err);
      return false;
    }
  }, []);

  const toggleTaskCompletion = useCallback(
    async (id: string): Promise<Task | null> => {
      try {
        setError(null);
        const currentTask = tasks.find(task => task.id === id);
        if (!currentTask) {
          throw new Error('Task not found');
        }

        let updatedTask: Task;
        if (currentTask.status === 'completed') {
          updatedTask = await tasksApi.reopenTask(id);
        } else {
          updatedTask = await tasksApi.completeTask(id);
        }

        setTasks(prev => prev.map(task => (task.id === id ? updatedTask : task)));

        // Refresh summary after toggling
        try {
          const summary = await tasksApi.getTaskSummary();
          setTaskSummary(summary);
        } catch (summaryError) {
          console.warn('Failed to refresh task summary:', summaryError);
        }

        return updatedTask;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to toggle task completion';
        setError(errorMessage);
        console.error('Error toggling task completion:', err);
        return null;
      }
    },
    [tasks]
  );

  useEffect(() => {
    if (autoFetch) {
      fetchTasks();
    }
  }, [autoFetch, fetchTasks]);

  return {
    tasks,
    loading,
    error,
    refreshTasks,
    createTask,
    updateTask,
    deleteTask,
    toggleTaskCompletion,
    taskSummary,
  };
};

export default useTasks;
