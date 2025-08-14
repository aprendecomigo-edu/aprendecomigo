import {
  CheckIcon,
  PlusIcon,
  TrashIcon,
  FlagIcon,
  CalendarIcon,
  AlertCircleIcon,
} from 'lucide-react-native';
import React, { useState, useMemo } from 'react';

import { Task as ApiTask } from '@/api/tasksApi';
import { Box } from '@/components/ui/box';
import { Button, ButtonIcon, ButtonText } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useTasks } from '@/hooks/useTasks';

// UI Task interface (mapped from API Task)
interface UITask {
  id: string;
  title: string;
  completed: boolean;
  priority: 'low' | 'medium' | 'high';
  dueDate?: string;
  createdAt: string;
}

// Helper function to map API task to UI task
const mapApiTaskToUITask = (apiTask: ApiTask): UITask => ({
  id: apiTask.id,
  title: apiTask.title,
  completed: apiTask.status === 'completed',
  priority: apiTask.priority,
  dueDate: apiTask.due_date,
  createdAt: apiTask.created_at,
});

type TaskPriority = UITask['priority'];

interface ToDoTaskListProps {
  maxHeight?: number;
  onTasksChange?: (tasks: UITask[]) => void;
}

const PRIORITY_CONFIG: Record<TaskPriority, { color: string; label: string; icon: any }> = {
  high: {
    color: 'red',
    label: 'Alta',
    icon: AlertCircleIcon,
  },
  medium: {
    color: 'yellow',
    label: 'Média',
    icon: FlagIcon,
  },
  low: {
    color: 'green',
    label: 'Baixa',
    icon: FlagIcon,
  },
};

const formatDueDate = (dateString: string): { text: string; isOverdue: boolean } => {
  const dueDate = new Date(dateString);
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(today.getDate() + 1);

  // Reset time to compare only dates
  const dueDateOnly = new Date(dueDate.getFullYear(), dueDate.getMonth(), dueDate.getDate());
  const todayOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate());

  const isOverdue = dueDateOnly < todayOnly;

  if (dueDateOnly.getTime() === todayOnly.getTime()) {
    return { text: 'Hoje', isOverdue: false };
  } else if (dueDateOnly.getTime() === tomorrow.getTime()) {
    return { text: 'Amanhã', isOverdue: false };
  } else {
    const text = dueDate.toLocaleDateString('pt-PT', {
      day: '2-digit',
      month: 'short',
    });
    return { text, isOverdue };
  }
};

const PriorityBadge: React.FC<{ priority: TaskPriority }> = ({ priority }) => {
  const config = PRIORITY_CONFIG[priority];

  return (
    <HStack
      space="xs"
      className={`px-2 py-1 rounded-full items-center bg-${config.color}-50 border border-${config.color}-200`}
    >
      <Icon as={config.icon} size="xs" className={`text-${config.color}-600`} />
      <Text className={`text-xs font-medium text-${config.color}-700`}>{config.label}</Text>
    </HStack>
  );
};

const TaskItem: React.FC<{
  task: UITask;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
  isLoading?: boolean;
}> = ({ task, onToggle, onDelete, isLoading = false }) => {
  const dueDateInfo = task.dueDate ? formatDueDate(task.dueDate) : null;

  return (
    <Box className={`glass-light p-4 rounded-lg ${task.completed ? 'opacity-60' : ''}`}>
      <HStack space="sm" className="items-start">
        {/* Checkbox */}
        <Pressable
          onPress={() => onToggle(task.id)}
          disabled={isLoading}
          className={`w-5 h-5 rounded border-2 items-center justify-center mt-0.5 ${
            isLoading ? 'opacity-50' : ''
          } ${task.completed ? 'bg-success-600 border-success-600' : 'border-gray-300 bg-white'}`}
        >
          {task.completed && <Icon as={CheckIcon} size="xs" className="text-white" />}
        </Pressable>

        {/* Task Content */}
        <VStack space="xs" className="flex-1 min-w-0">
          <Text
            className={`font-medium font-primary ${
              task.completed ? 'line-through text-gray-500' : 'text-gray-900'
            }`}
          >
            {task.title}
          </Text>

          {/* Meta information */}
          <HStack space="md" className="items-center flex-wrap">
            <PriorityBadge priority={task.priority} />

            {dueDateInfo && (
              <HStack space="xs" className="items-center">
                <Icon as={CalendarIcon} size="xs" className="text-gray-500" />
                <Text
                  className={`text-xs font-body ${
                    dueDateInfo.isOverdue && !task.completed
                      ? 'text-red-600 font-semibold'
                      : 'text-gray-600'
                  }`}
                >
                  {dueDateInfo.text}
                  {dueDateInfo.isOverdue && !task.completed && ' (Atrasada)'}
                </Text>
              </HStack>
            )}
          </HStack>
        </VStack>

        {/* Delete button */}
        <Pressable
          onPress={() => onDelete(task.id)}
          disabled={isLoading}
          className={`p-2 rounded-lg active:scale-95 transition-transform ${
            isLoading ? 'opacity-50' : ''
          }`}
        >
          <Icon as={TrashIcon} size="xs" className="text-gray-400" />
        </Pressable>
      </HStack>
    </Box>
  );
};

const AddTaskForm: React.FC<{
  onAdd: (title: string, priority: TaskPriority) => void;
  onCancel: () => void;
}> = ({ onAdd, onCancel }) => {
  const [title, setTitle] = useState('');
  const [priority, setPriority] = useState<TaskPriority>('medium');

  const handleSubmit = () => {
    if (title.trim()) {
      onAdd(title.trim(), priority);
      setTitle('');
      onCancel();
    }
  };

  return (
    <Box className="glass-light p-4 rounded-lg border border-primary-200">
      <VStack space="md">
        <Input variant="outline" size="sm">
          <InputField
            placeholder="Nova tarefa..."
            value={title}
            onChangeText={setTitle}
            onSubmitEditing={handleSubmit}
            autoFocus
          />
        </Input>

        {/* Priority Selector */}
        <VStack space="xs">
          <Text className="text-sm font-medium font-primary text-gray-700">Prioridade:</Text>
          <HStack space="xs" className="flex-wrap">
            {Object.entries(PRIORITY_CONFIG).map(([key, config]) => (
              <Pressable
                key={key}
                onPress={() => setPriority(key as TaskPriority)}
                className={`px-3 py-1.5 rounded-lg active:scale-98 transition-transform ${
                  priority === key ? 'bg-gradient-primary' : 'bg-gray-100'
                }`}
              >
                <Text
                  className={`text-sm font-medium font-primary ${
                    priority === key ? 'text-white' : 'text-gray-700'
                  }`}
                >
                  {config.label}
                </Text>
              </Pressable>
            ))}
          </HStack>
        </VStack>

        {/* Actions */}
        <HStack space="md" className="justify-end">
          <Button variant="outline" size="sm" onPress={onCancel}>
            <ButtonText>Cancelar</ButtonText>
          </Button>
          <Button variant="solid" size="sm" onPress={handleSubmit} isDisabled={!title.trim()}>
            <ButtonText>Adicionar</ButtonText>
          </Button>
        </HStack>
      </VStack>
    </Box>
  );
};

const EmptyState: React.FC<{ onAddTask: () => void }> = ({ onAddTask }) => (
  <VStack space="md" className="items-center py-8">
    <Icon as={CheckIcon} size="xl" className="text-gray-300" />
    <Text className="text-lg font-medium font-primary text-gray-600">Nenhuma tarefa</Text>
    <Text className="text-sm font-body text-gray-500 text-center max-w-sm">
      Organize suas atividades administrativas criando tarefas personalizadas
    </Text>
    <Button variant="outline" size="sm" onPress={onAddTask}>
      <ButtonIcon as={PlusIcon} />
      <ButtonText>Criar primeira tarefa</ButtonText>
    </Button>
  </VStack>
);

const ToDoTaskList: React.FC<ToDoTaskListProps> = ({ onTasksChange, maxHeight = 500 }) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Use the API hook
  const {
    tasks: apiTasks,
    loading,
    error,
    createTask,
    updateTask,
    deleteTask,
    toggleTaskCompletion,
    refreshTasks,
  } = useTasks();

  // Convert API tasks to UI tasks
  const tasks = useMemo(() => {
    return apiTasks.map(mapApiTaskToUITask);
  }, [apiTasks]);

  const { pendingTasks, completedTasks } = useMemo(() => {
    const pending = tasks
      .filter(task => !task.completed)
      .sort((a, b) => {
        // Sort by priority (high -> medium -> low) then by due date
        const priorityOrder = { high: 0, medium: 1, low: 2 };
        const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority];

        if (priorityDiff !== 0) return priorityDiff;

        if (a.dueDate && b.dueDate) {
          return new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime();
        }
        if (a.dueDate) return -1;
        if (b.dueDate) return 1;

        return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
      });

    const completed = tasks.filter(task => task.completed);

    return { pendingTasks: pending, completedTasks: completed };
  }, [tasks]);

  // Update parent component when tasks change
  React.useEffect(() => {
    onTasksChange?.(tasks);
  }, [tasks, onTasksChange]);

  const handleToggleTask = async (id: string) => {
    setActionLoading(id);
    try {
      await toggleTaskCompletion(id);
    } catch (err) {
      console.error('Failed to toggle task:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteTask = async (id: string) => {
    setActionLoading(id);
    try {
      await deleteTask(id);
    } catch (err) {
      console.error('Failed to delete task:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleAddTask = async (title: string, priority: TaskPriority) => {
    try {
      await createTask({
        title,
        priority,
        task_type: 'personal', // Default to personal tasks
        description: '', // Optional field
      });
      setShowAddForm(false);
    } catch (err) {
      console.error('Failed to create task:', err);
    }
  };

  return (
    <Box className="glass-container p-6 rounded-xl">
      <VStack space="md">
        {/* Header */}
        <HStack className="justify-between items-center">
          <VStack space="xs">
            <Heading size="md" className="font-primary text-gray-900">
              <Text className="bg-gradient-accent">Tarefas Pessoais</Text>
            </Heading>
            <Text className="text-sm font-body text-gray-600">
              {pendingTasks.length} pendentes, {completedTasks.length} concluídas
            </Text>
          </VStack>

          {!showAddForm && (
            <Button variant="outline" size="sm" onPress={() => setShowAddForm(true)}>
              <ButtonIcon as={PlusIcon} />
              <ButtonText>Nova</ButtonText>
            </Button>
          )}
        </HStack>

        {/* Loading State */}
        {loading && (
          <VStack space="md" className="items-center py-8">
            <Text className="text-center font-body text-gray-500">Carregando tarefas...</Text>
          </VStack>
        )}

        {/* Error State */}
        {error && (
          <VStack space="md" className="items-center py-4">
            <Text className="text-center font-body text-red-600">Erro: {error}</Text>
            <Button variant="outline" size="sm" onPress={refreshTasks}>
              <ButtonText>Tentar Novamente</ButtonText>
            </Button>
          </VStack>
        )}

        {/* Add Task Form */}
        {showAddForm && (
          <AddTaskForm onAdd={handleAddTask} onCancel={() => setShowAddForm(false)} />
        )}

        {/* Tasks List */}
        {!loading && !error && tasks.length === 0 && !showAddForm ? (
          <EmptyState onAddTask={() => setShowAddForm(true)} />
        ) : (
          <ScrollView showsVerticalScrollIndicator={false} style={{ maxHeight }}>
            <VStack space="md">
              {/* Pending Tasks */}
              {pendingTasks.length > 0 && (
                <VStack space="sm">
                  <Text className="text-sm font-semibold font-primary text-gray-700 px-2">
                    Pendentes ({pendingTasks.length})
                  </Text>
                  <VStack space="sm">
                    {pendingTasks.map(task => (
                      <TaskItem
                        key={task.id}
                        task={task}
                        onToggle={handleToggleTask}
                        onDelete={handleDeleteTask}
                        isLoading={actionLoading === task.id}
                      />
                    ))}
                  </VStack>
                </VStack>
              )}

              {/* Completed Tasks */}
              {completedTasks.length > 0 && (
                <VStack space="sm">
                  <Text className="text-sm font-semibold font-primary text-gray-700 px-2">
                    Concluídas ({completedTasks.length})
                  </Text>
                  <VStack space="sm">
                    {completedTasks.map(task => (
                      <TaskItem
                        key={task.id}
                        task={task}
                        onToggle={handleToggleTask}
                        onDelete={handleDeleteTask}
                        isLoading={actionLoading === task.id}
                      />
                    ))}
                  </VStack>
                </VStack>
              )}
            </VStack>
          </ScrollView>
        )}
      </VStack>
    </Box>
  );
};

export { ToDoTaskList };
export default ToDoTaskList;
