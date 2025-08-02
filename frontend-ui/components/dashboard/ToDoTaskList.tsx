import {
  CheckIcon,
  PlusIcon,
  TrashIcon,
  FlagIcon,
  CalendarIcon,
  AlertCircleIcon,
} from 'lucide-react-native';
import React, { useState, useMemo } from 'react';

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

// Task types
interface Task {
  id: string;
  title: string;
  completed: boolean;
  priority: 'low' | 'medium' | 'high';
  dueDate?: string;
  createdAt: string;
}

type TaskPriority = Task['priority'];

interface ToDoTaskListProps {
  // Future props for real data integration
  initialTasks?: Task[];
  onTasksChange?: (tasks: Task[]) => void;
  maxHeight?: number;
}

// Mock initial tasks for demonstration
const INITIAL_TASKS: Task[] = [
  {
    id: '1',
    title: 'Revisar convites de professores pendentes',
    completed: false,
    priority: 'high',
    dueDate: '2025-08-02',
    createdAt: '2025-08-01T10:00:00Z',
  },
  {
    id: '2',
    title: 'Atualizar informações da escola no perfil',
    completed: false,
    priority: 'medium',
    createdAt: '2025-08-01T14:30:00Z',
  },
  {
    id: '3',
    title: 'Configurar templates de email para comunicação',
    completed: true,
    priority: 'low',
    createdAt: '2025-07-30T09:15:00Z',
  },
  {
    id: '4',
    title: 'Verificar horários disponíveis dos professores',
    completed: false,
    priority: 'medium',
    dueDate: '2025-08-03',
    createdAt: '2025-08-01T16:45:00Z',
  },
];

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
  task: Task;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
}> = ({ task, onToggle, onDelete }) => {
  const dueDateInfo = task.dueDate ? formatDueDate(task.dueDate) : null;

  return (
    <Box className={`glass-light p-4 rounded-lg ${task.completed ? 'opacity-60' : ''}`}>
      <HStack space="sm" className="items-start">
        {/* Checkbox */}
        <Pressable
          onPress={() => onToggle(task.id)}
          className={`w-5 h-5 rounded border-2 items-center justify-center mt-0.5 ${
            task.completed ? 'bg-success-600 border-success-600' : 'border-gray-300 bg-white'
          }`}
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
          className="p-2 rounded-lg active:scale-95 transition-transform"
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

const ToDoTaskList: React.FC<ToDoTaskListProps> = ({
  initialTasks = INITIAL_TASKS,
  onTasksChange,
  maxHeight = 500,
}) => {
  const [tasks, setTasks] = useState<Task[]>(initialTasks);
  const [showAddForm, setShowAddForm] = useState(false);

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

  const updateTasks = (newTasks: Task[]) => {
    setTasks(newTasks);
    onTasksChange?.(newTasks);
  };

  const handleToggleTask = (id: string) => {
    updateTasks(
      tasks.map(task => (task.id === id ? { ...task, completed: !task.completed } : task))
    );
  };

  const handleDeleteTask = (id: string) => {
    updateTasks(tasks.filter(task => task.id !== id));
  };

  const handleAddTask = (title: string, priority: TaskPriority) => {
    const newTask: Task = {
      id: Date.now().toString(),
      title,
      completed: false,
      priority,
      createdAt: new Date().toISOString(),
    };
    updateTasks([...tasks, newTask]);
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

        {/* Add Task Form */}
        {showAddForm && (
          <AddTaskForm onAdd={handleAddTask} onCancel={() => setShowAddForm(false)} />
        )}

        {/* Tasks List */}
        {tasks.length === 0 && !showAddForm ? (
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
