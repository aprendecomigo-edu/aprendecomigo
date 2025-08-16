import {
  Plus,
  CheckCircle,
  Circle,
  Calendar,
  Clock,
  AlertTriangle,
  Edit3,
  Trash2,
  ChevronDown,
  Filter,
  SortAsc,
  SortDesc,
} from 'lucide-react-native';
import React, { useState, useEffect } from 'react';

import { Task, CreateTaskData, UpdateTaskData, tasksApi } from '../../api/tasksApi';

import {
  AlertDialog,
  AlertDialogBody,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogBackdrop,
  AlertDialogCloseButton,
} from '@/components/ui/alert-dialog';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import {
  FormControl,
  FormControlLabel,
  FormControlLabelText,
  FormControlError,
  FormControlErrorText,
} from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import {
  Select,
  SelectTrigger,
  SelectInput,
  SelectIcon,
  SelectPortal,
  SelectBackdrop,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import { Spinner } from '@/components/ui/spinner';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/toast';
import { VStack } from '@/components/ui/vstack';

interface TasksTableProps {
  tasks: Task[];
  onTasksChange?: () => void;
  showAddButton?: boolean;
  title?: string;
}

interface TaskDialogProps {
  task?: Task;
  isOpen: boolean;
  onClose: () => void;
  onSave: (task: Task) => void;
}

const TaskDialog: React.FC<TaskDialogProps> = ({ task, isOpen, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    title: task?.title || '',
    description: task?.description || '',
    priority: task?.priority || 'medium',
    task_type: task?.task_type || 'personal',
    due_date: task?.due_date ? new Date(task.due_date).toISOString().split('T')[0] : '',
    is_urgent: task?.is_urgent || false,
  });
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  const handleSave = async () => {
    if (!formData.title.trim()) {
      toast.showToast('error', 'Title is required');
      return;
    }

    setIsLoading(true);
    try {
      let savedTask: Task;

      if (task) {
        // Update existing task
        const updateData: UpdateTaskData = {
          title: formData.title,
          description: formData.description,
          priority: formData.priority as 'low' | 'medium' | 'high',
          task_type: formData.task_type as 'onboarding' | 'assignment' | 'personal' | 'system',
          due_date: formData.due_date || undefined,
          is_urgent: formData.is_urgent,
        };
        savedTask = await tasksApi.updateTask(task.id, updateData);
      } else {
        // Create new task
        const createData: CreateTaskData = {
          title: formData.title,
          description: formData.description,
          priority: formData.priority as 'low' | 'medium' | 'high',
          task_type: formData.task_type as 'onboarding' | 'assignment' | 'personal' | 'system',
          due_date: formData.due_date || undefined,
          is_urgent: formData.is_urgent,
        };
        savedTask = await tasksApi.createTask(createData);
      }

      onSave(savedTask);
      onClose();

      toast.showToast('success', `Task ${task ? 'updated' : 'created'} successfully`);
    } catch (error) {
      if (__DEV__) {
        console.error('Error saving task:', error); // TODO: Review for sensitive data
      }
      toast.showToast('error', `Failed to ${task ? 'update' : 'create'} task`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AlertDialog isOpen={isOpen} onClose={onClose}>
      <AlertDialogBackdrop />
      <AlertDialogContent>
        <AlertDialogHeader>
          <Heading size="md">{task ? 'Edit Task' : 'Create New Task'}</Heading>
          <AlertDialogCloseButton />
        </AlertDialogHeader>
        <AlertDialogBody>
          <VStack space="md">
            <FormControl isRequired>
              <FormControlLabel>
                <FormControlLabelText>Title</FormControlLabelText>
              </FormControlLabel>
              <Input>
                <InputField
                  value={formData.title}
                  onChangeText={value => setFormData({ ...formData, title: value })}
                  placeholder="Enter task title"
                />
              </Input>
            </FormControl>

            <FormControl>
              <FormControlLabel>
                <FormControlLabelText>Description</FormControlLabelText>
              </FormControlLabel>
              <Textarea>
                <TextareaInput
                  value={formData.description}
                  onChangeText={value => setFormData({ ...formData, description: value })}
                  placeholder="Enter task description"
                />
              </Textarea>
            </FormControl>

            <HStack space="md">
              <FormControl flex={1}>
                <FormControlLabel>
                  <FormControlLabelText>Priority</FormControlLabelText>
                </FormControlLabel>
                <Select
                  selectedValue={formData.priority}
                  onValueChange={value => setFormData({ ...formData, priority: value })}
                >
                  <SelectTrigger>
                    <SelectInput placeholder="Select priority" />
                    <SelectIcon as={ChevronDown} />
                  </SelectTrigger>
                  <SelectPortal>
                    <SelectBackdrop />
                    <SelectContent>
                      <SelectItem label="Low" value="low" />
                      <SelectItem label="Medium" value="medium" />
                      <SelectItem label="High" value="high" />
                    </SelectContent>
                  </SelectPortal>
                </Select>
              </FormControl>

              <FormControl flex={1}>
                <FormControlLabel>
                  <FormControlLabelText>Type</FormControlLabelText>
                </FormControlLabel>
                <Select
                  selectedValue={formData.task_type}
                  onValueChange={value => setFormData({ ...formData, task_type: value })}
                >
                  <SelectTrigger>
                    <SelectInput placeholder="Select type" />
                    <SelectIcon as={ChevronDown} />
                  </SelectTrigger>
                  <SelectPortal>
                    <SelectBackdrop />
                    <SelectContent>
                      <SelectItem label="Personal" value="personal" />
                      <SelectItem label="Assignment" value="assignment" />
                      <SelectItem label="Onboarding" value="onboarding" />
                      <SelectItem label="System" value="system" />
                    </SelectContent>
                  </SelectPortal>
                </Select>
              </FormControl>
            </HStack>

            <FormControl>
              <FormControlLabel>
                <FormControlLabelText>Due Date</FormControlLabelText>
              </FormControlLabel>
              <Input>
                <InputField
                  value={formData.due_date}
                  onChangeText={value => setFormData({ ...formData, due_date: value })}
                  placeholder="YYYY-MM-DD"
                />
              </Input>
            </FormControl>

            <HStack space="md" className="items-center">
              <FormControlLabelText>Mark as urgent</FormControlLabelText>
              <Switch
                value={formData.is_urgent}
                onValueChange={value => setFormData({ ...formData, is_urgent: value })}
              />
            </HStack>
          </VStack>
        </AlertDialogBody>
        <AlertDialogFooter>
          <Button variant="outline" onPress={onClose}>
            <ButtonText>Cancel</ButtonText>
          </Button>
          <Button onPress={handleSave} disabled={isLoading}>
            {isLoading ? <Spinner size="small" /> : <ButtonText>Save</ButtonText>}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

const TasksTable: React.FC<TasksTableProps> = ({
  tasks,
  onTasksChange,
  showAddButton = true,
  title = 'Tarefas Pendentes',
}) => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const [sortBy, setSortBy] = useState<'due_date' | 'priority' | 'created_at' | 'title'>(
    'due_date',
  );
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [filterStatus, setFilterStatus] = useState<'all' | 'pending' | 'completed'>('all');
  const [filterPriority, setFilterPriority] = useState<'all' | 'high' | 'medium' | 'low'>('all');
  const [showFilters, setShowFilters] = useState(false);
  const toast = useToast();

  // Sort and filter tasks
  const sortedAndFilteredTasks = React.useMemo(() => {
    let filteredTasks = [...tasks];

    // Apply status filter
    if (filterStatus !== 'all') {
      if (filterStatus === 'pending') {
        filteredTasks = filteredTasks.filter(
          task => task.status === 'pending' || task.status === 'in_progress',
        );
      } else {
        filteredTasks = filteredTasks.filter(task => task.status === filterStatus);
      }
    }

    // Apply priority filter
    if (filterPriority !== 'all') {
      filteredTasks = filteredTasks.filter(task => task.priority === filterPriority);
    }

    // Apply sorting
    filteredTasks.sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case 'due_date':
          const aDate = a.due_date ? new Date(a.due_date).getTime() : Number.MAX_VALUE;
          const bDate = b.due_date ? new Date(b.due_date).getTime() : Number.MAX_VALUE;
          comparison = aDate - bDate;
          break;
        case 'priority':
          const priorityOrder = { high: 3, medium: 2, low: 1 };
          comparison =
            priorityOrder[a.priority as keyof typeof priorityOrder] -
            priorityOrder[b.priority as keyof typeof priorityOrder];
          break;
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'title':
          comparison = a.title.localeCompare(b.title);
          break;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return filteredTasks;
  }, [tasks, sortBy, sortOrder, filterStatus, filterPriority]);

  const handleSort = (field: typeof sortBy) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-500';
      case 'medium':
        return 'bg-yellow-500';
      case 'low':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getPriorityBorderColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'border-l-red-500';
      case 'medium':
        return 'border-l-yellow-500';
      case 'low':
        return 'border-l-green-500';
      default:
        return 'border-l-gray-500';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-50 border-green-200';
      case 'in_progress':
        return 'bg-blue-50 border-blue-200';
      case 'pending':
        return 'bg-gray-50 border-gray-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const handleToggleComplete = async (task: Task) => {
    setIsLoading(true);
    try {
      if (task.status === 'completed') {
        await tasksApi.reopenTask(task.id);
      } else {
        await tasksApi.completeTask(task.id);
      }
      onTasksChange?.();

      toast.showToast('success', `Task ${task.status === 'completed' ? 'reopened' : 'completed'}`);
    } catch (error) {
      if (__DEV__) {
        console.error('Error toggling task completion:', error); // TODO: Review for sensitive data
      }
      toast.showToast('error', 'Failed to update task');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteTask = async (task: Task) => {
    setIsLoading(true);
    try {
      await tasksApi.deleteTask(task.id);
      onTasksChange?.();

      toast.showToast('success', 'Task deleted successfully');
    } catch (error) {
      if (__DEV__) {
        console.error('Error deleting task:', error); // TODO: Review for sensitive data
      }
      toast.showToast('error', 'Failed to delete task');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditTask = (task: Task) => {
    setEditingTask(task);
    setIsDialogOpen(true);
  };

  const handleAddTask = () => {
    setEditingTask(undefined);
    setIsDialogOpen(true);
  };

  const handleTaskSaved = () => {
    onTasksChange?.();
  };

  const formatDueDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) return 'Overdue';
    if (diffDays === 0) return 'Due today';
    if (diffDays === 1) return 'Due tomorrow';
    return `Due in ${diffDays} days`;
  };

  return (
    <VStack space="md">
      <HStack className="justify-between items-center">
        <Heading className="text-xl font-bold text-gray-900">{title}</Heading>
        <HStack space="sm">
          <Button size="sm" variant="outline" onPress={() => setShowFilters(!showFilters)}>
            <Icon as={Filter} size="sm" />
            <ButtonText className="ml-1">Filter</ButtonText>
          </Button>
          {showAddButton && (
            <Button size="sm" onPress={handleAddTask}>
              <Icon as={Plus} size="sm" />
              <ButtonText className="ml-2">Add Task</ButtonText>
            </Button>
          )}
        </HStack>
      </HStack>

      {/* Sorting and Filtering Controls */}
      {showFilters && (
        <VStack space="md" className="bg-gray-50 p-4 rounded-lg">
          {/* Sort Controls */}
          <HStack space="sm" className="flex-wrap">
            <Text className="font-medium text-gray-700 mr-2">Sort by:</Text>
            <Button
              size="xs"
              variant={sortBy === 'due_date' ? 'solid' : 'outline'}
              onPress={() => handleSort('due_date')}
            >
              <ButtonText className="text-xs">Due Date</ButtonText>
              {sortBy === 'due_date' && (
                <Icon as={sortOrder === 'asc' ? SortAsc : SortDesc} size="xs" className="ml-1" />
              )}
            </Button>
            <Button
              size="xs"
              variant={sortBy === 'priority' ? 'solid' : 'outline'}
              onPress={() => handleSort('priority')}
            >
              <ButtonText className="text-xs">Priority</ButtonText>
              {sortBy === 'priority' && (
                <Icon as={sortOrder === 'asc' ? SortAsc : SortDesc} size="xs" className="ml-1" />
              )}
            </Button>
            <Button
              size="xs"
              variant={sortBy === 'created_at' ? 'solid' : 'outline'}
              onPress={() => handleSort('created_at')}
            >
              <ButtonText className="text-xs">Created</ButtonText>
              {sortBy === 'created_at' && (
                <Icon as={sortOrder === 'asc' ? SortAsc : SortDesc} size="xs" className="ml-1" />
              )}
            </Button>
            <Button
              size="xs"
              variant={sortBy === 'title' ? 'solid' : 'outline'}
              onPress={() => handleSort('title')}
            >
              <ButtonText className="text-xs">Title</ButtonText>
              {sortBy === 'title' && (
                <Icon as={sortOrder === 'asc' ? SortAsc : SortDesc} size="xs" className="ml-1" />
              )}
            </Button>
          </HStack>

          {/* Filter Controls */}
          <HStack space="md" className="flex-wrap">
            <VStack space="sm" className="flex-1">
              <Text className="font-medium text-gray-700 text-sm">Status:</Text>
              <Select
                selectedValue={filterStatus}
                onValueChange={value => setFilterStatus(value as any)}
              >
                <SelectTrigger size="sm">
                  <SelectInput placeholder="Filter by status" />
                  <SelectIcon as={ChevronDown} />
                </SelectTrigger>
                <SelectPortal>
                  <SelectBackdrop />
                  <SelectContent>
                    <SelectItem label="All" value="all" />
                    <SelectItem label="Pending" value="pending" />
                    <SelectItem label="Completed" value="completed" />
                  </SelectContent>
                </SelectPortal>
              </Select>
            </VStack>

            <VStack space="sm" className="flex-1">
              <Text className="font-medium text-gray-700 text-sm">Priority:</Text>
              <Select
                selectedValue={filterPriority}
                onValueChange={value => setFilterPriority(value as any)}
              >
                <SelectTrigger size="sm">
                  <SelectInput placeholder="Filter by priority" />
                  <SelectIcon as={ChevronDown} />
                </SelectTrigger>
                <SelectPortal>
                  <SelectBackdrop />
                  <SelectContent>
                    <SelectItem label="All" value="all" />
                    <SelectItem label="High" value="high" />
                    <SelectItem label="Medium" value="medium" />
                    <SelectItem label="Low" value="low" />
                  </SelectContent>
                </SelectPortal>
              </Select>
            </VStack>
          </HStack>
        </VStack>
      )}

      {/* Task Statistics */}
      <HStack space="md" className="bg-blue-50 p-3 rounded-lg">
        <VStack space="xs" className="flex-1">
          <Text className="text-blue-600 font-semibold text-sm">Total Tasks</Text>
          <Text className="text-blue-900 font-bold text-lg">{tasks.length}</Text>
        </VStack>
        <VStack space="xs" className="flex-1">
          <Text className="text-green-600 font-semibold text-sm">Completed</Text>
          <Text className="text-green-900 font-bold text-lg">
            {tasks.filter(task => task.status === 'completed').length}
          </Text>
        </VStack>
        <VStack space="xs" className="flex-1">
          <Text className="text-red-600 font-semibold text-sm">Overdue</Text>
          <Text className="text-red-900 font-bold text-lg">
            {tasks.filter(task => task.is_overdue).length}
          </Text>
        </VStack>
      </HStack>

      <VStack space="xs">
        {sortedAndFilteredTasks.map(task => (
          <Box
            key={task.id}
            className={`rounded-lg p-4 border-l-4 ${getPriorityBorderColor(
              task.priority,
            )} ${getStatusColor(task.status)}`}
          >
            <HStack className="justify-between items-start">
              <HStack space="md" className="flex-1">
                <Pressable onPress={() => handleToggleComplete(task)}>
                  <Icon
                    as={task.status === 'completed' ? CheckCircle : Circle}
                    size="lg"
                    className={task.status === 'completed' ? 'text-green-600' : 'text-gray-400'}
                  />
                </Pressable>

                <VStack space="xs" className="flex-1">
                  <HStack className="justify-between items-start">
                    <Text
                      className={`font-semibold ${
                        task.status === 'completed' ? 'line-through text-gray-500' : 'text-gray-900'
                      }`}
                    >
                      {task.title}
                    </Text>
                    <HStack space="xs">
                      <Badge variant="solid" className={getPriorityColor(task.priority)}>
                        <BadgeText className="text-white text-xs">
                          {task.priority.toUpperCase()}
                        </BadgeText>
                      </Badge>
                      {task.is_urgent && (
                        <Badge variant="solid" className="bg-red-600">
                          <BadgeText className="text-white text-xs">URGENT</BadgeText>
                        </Badge>
                      )}
                    </HStack>
                  </HStack>

                  {task.description && (
                    <Text className="text-gray-600 text-sm">{task.description}</Text>
                  )}

                  <HStack space="md" className="items-center">
                    <HStack space="xs" className="items-center">
                      <Icon as={Calendar} size="xs" className="text-gray-500" />
                      <Text className="text-gray-500 text-xs">{task.task_type}</Text>
                    </HStack>

                    {task.due_date && (
                      <HStack space="xs" className="items-center">
                        <Icon
                          as={task.is_overdue ? AlertTriangle : Clock}
                          size="xs"
                          className={task.is_overdue ? 'text-red-500' : 'text-gray-500'}
                        />
                        <Text
                          className={`text-xs ${
                            task.is_overdue ? 'text-red-500' : 'text-gray-500'
                          }`}
                        >
                          {formatDueDate(task.due_date)}
                        </Text>
                      </HStack>
                    )}
                  </HStack>
                </VStack>
              </HStack>

              <HStack space="xs">
                <Pressable onPress={() => handleEditTask(task)}>
                  <Icon as={Edit3} size="sm" className="text-gray-500" />
                </Pressable>
                {!task.is_system_generated && (
                  <Pressable onPress={() => handleDeleteTask(task)}>
                    <Icon as={Trash2} size="sm" className="text-red-500" />
                  </Pressable>
                )}
              </HStack>
            </HStack>
          </Box>
        ))}

        {sortedAndFilteredTasks.length === 0 && (
          <Box className="text-center py-12">
            <VStack space="md" className="items-center">
              <Icon as={tasks.length === 0 ? Plus : Filter} size="3xl" className="text-gray-300" />
              <VStack space="sm" className="items-center">
                <Text className="text-lg font-semibold text-gray-600">
                  {tasks.length === 0 ? 'No tasks yet!' : 'No tasks match your filters'}
                </Text>
                <Text className="text-gray-500 text-center max-w-xs">
                  {tasks.length === 0
                    ? 'Click "Add Task" to create your first task and start organizing your work.'
                    : 'Try adjusting your filters or add a new task.'}
                </Text>
              </VStack>
              {showAddButton && (
                <Button size="lg" onPress={handleAddTask} className="mt-4">
                  <Icon as={Plus} size="sm" />
                  <ButtonText className="ml-2">
                    {tasks.length === 0 ? 'Add Your First Task' : 'Add Task'}
                  </ButtonText>
                </Button>
              )}
            </VStack>
          </Box>
        )}
      </VStack>

      <TaskDialog
        task={editingTask}
        isOpen={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
        onSave={handleTaskSaved}
      />
    </VStack>
  );
};

export default TasksTable;
