import React, { useMemo } from 'react';
import { ScrollView } from 'react-native';
import { ClassSchedule } from '@/api/schedulerApi';
import { Task } from '@/api/tasksApi';
import { validateDate, safeFormatTime } from './dateUtils';
import { Box } from '@/components/ui/box';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { HStack } from '@/components/ui/hstack';
import { Pressable } from '@/components/ui/pressable';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Icon } from '@/components/ui/icon';
import { Clock, User, MapPin } from 'lucide-react-native';
import { useWorkingDays } from '@/hooks/useWorkingDays';

interface WeekViewProps {
  currentDate: Date;
  classes: ClassSchedule[];
  tasks: Task[];
  onClassPress: (classSchedule: ClassSchedule) => void;
}

// Helper function to get week dates starting from Sunday
const getWeekDates = (date: Date): Date[] => {
  const week = [];
  const startOfWeek = new Date(date);
  const day = startOfWeek.getDay();
  const diff = startOfWeek.getDate() - day; // First day is Sunday
  startOfWeek.setDate(diff);

  for (let i = 0; i < 7; i++) {
    const day = new Date(startOfWeek);
    day.setDate(startOfWeek.getDate() + i);
    week.push(day);
  }
  return week;
};

// Helper function to get time slots (hourly from 8 AM to 8 PM)
const getTimeSlots = (): string[] => {
  const slots = [];
  for (let hour = 8; hour <= 20; hour++) {
    slots.push(`${hour.toString().padStart(2, '0')}:00`);
  }
  return slots;
};

// Helper function to get status color
const getStatusColor = (status: string): string => {
  switch (status) {
    case 'scheduled':
      return 'bg-blue-100 text-blue-800';
    case 'confirmed':
      return 'bg-green-100 text-green-800';
    case 'completed':
      return 'bg-gray-100 text-gray-800';
    case 'cancelled':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

// Helper function to get priority color for tasks
const getPriorityColor = (priority: string): string => {
  switch (priority) {
    case 'high':
      return 'bg-red-100 text-red-800';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800';
    case 'low':
      return 'bg-green-100 text-green-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

// Mini class card for week view
const MiniClassCard: React.FC<{
  classSchedule: ClassSchedule;
  onPress: () => void;
}> = ({ classSchedule, onPress }) => {
  return (
    <Pressable onPress={onPress}>
      <Box className="bg-blue-50 border border-blue-200 rounded p-2 mb-1">
        <VStack space="xs">
          <Text className="text-xs font-medium text-blue-900 leading-tight" numberOfLines={1}>
            {classSchedule.title}
          </Text>
          <Text className="text-xs text-blue-700" numberOfLines={1}>
            {classSchedule.teacher_name}
          </Text>
          <HStack space="xs" className="items-center">
            <Icon as={Clock} size="xs" className="text-blue-600" />
            <Text className="text-xs text-blue-600">
              {classSchedule.start_time} - {classSchedule.end_time}
            </Text>
          </HStack>
          <Badge size="sm" className={getStatusColor(classSchedule.status)}>
            <BadgeText className="text-xs">{classSchedule.status_display}</BadgeText>
          </Badge>
        </VStack>
      </Box>
    </Pressable>
  );
};

// Mini task card for week view
const MiniTaskCard: React.FC<{
  task: Task;
}> = ({ task }) => {
  return (
    <Box className="bg-orange-50 border border-orange-200 rounded p-2 mb-1">
      <VStack space="xs">
        <Text className="text-xs font-medium text-orange-900 leading-tight" numberOfLines={1}>
          {task.title}
        </Text>
        <Text className="text-xs text-orange-700" numberOfLines={1}>
          {task.task_type}
        </Text>
        {task.due_date && (
          <HStack space="xs" className="items-center">
            <Icon as={Clock} size="xs" className="text-orange-600" />
            <Text className="text-xs text-orange-600">
              Due: {safeFormatTime(task.due_date)}
            </Text>
          </HStack>
        )}
        <HStack space="xs">
          <Badge size="sm" className={getPriorityColor(task.priority)}>
            <BadgeText className="text-xs">{task.priority.toUpperCase()}</BadgeText>
          </Badge>
          {task.is_urgent && (
            <Badge size="sm" className="bg-red-100 text-red-800">
              <BadgeText className="text-xs">URGENT</BadgeText>
            </Badge>
          )}
        </HStack>
      </VStack>
    </Box>
  );
};

// Day column component
const DayColumn: React.FC<{
  date: Date;
  classes: ClassSchedule[];
  tasks: Task[];
  onClassPress: (classSchedule: ClassSchedule) => void;
}> = ({ date, classes, tasks, onClassPress }) => {
  const isToday = date.toDateString() === new Date().toDateString();
  const dayName = date.toLocaleDateString('pt-PT', { weekday: 'short' });
  const dayNumber = date.getDate();
  
  return (
    <VStack className="flex-1 min-w-[120px]" space="xs">
      {/* Day header */}
      <Box className={`p-2 rounded-lg ${isToday ? 'bg-blue-100' : 'bg-gray-50'}`}>
        <VStack className="items-center" space="xs">
          <Text className={`text-xs font-medium ${isToday ? 'text-blue-900' : 'text-gray-600'}`}>
            {dayName.toUpperCase()}
          </Text>
          <Text className={`text-lg font-bold ${isToday ? 'text-blue-900' : 'text-gray-900'}`}>
            {dayNumber}
          </Text>
        </VStack>
      </Box>
      
      {/* Day content */}
      <ScrollView className="flex-1" showsVerticalScrollIndicator={false}>
        <VStack space="xs" className="p-1">
          {classes.map(classSchedule => (
            <MiniClassCard
              key={`class-${classSchedule.id}`}
              classSchedule={classSchedule}
              onPress={() => onClassPress(classSchedule)}
            />
          ))}
          {tasks.map(task => (
            <MiniTaskCard
              key={`task-${task.id}`}
              task={task}
            />
          ))}
          {classes.length === 0 && tasks.length === 0 && (
            <Box className="bg-gray-50 rounded p-3 mt-2">
              <Text className="text-xs text-gray-500 text-center">
                No events
              </Text>
            </Box>
          )}
        </VStack>
      </ScrollView>
    </VStack>
  );
};

export const WeekView: React.FC<WeekViewProps> = ({ 
  currentDate, 
  classes, 
  tasks, 
  onClassPress 
}) => {
  const { getWorkingWeekDates, isLoading } = useWorkingDays();
  
  // Add null check and default to empty array
  const safeClasses = classes || [];
  const safeTasks = tasks || [];

  // Get only working days for the week
  const workingWeekDates = useMemo(() => {
    return getWorkingWeekDates(currentDate);
  }, [currentDate, getWorkingWeekDates]);

  // Group events by date (only for working days)
  const eventsByDate = useMemo(() => {
    const grouped: { [key: string]: { classes: ClassSchedule[]; tasks: Task[] } } = {};
    
    workingWeekDates.forEach(date => {
      const dateStr = date.toISOString().split('T')[0];
      grouped[dateStr] = { classes: [], tasks: [] };
    });

    // Group classes by date
    safeClasses.forEach(classSchedule => {
      const validation = validateDate(classSchedule.scheduled_date);
      if (validation.isValid && validation.date) {
        const dateStr = validation.date.toISOString().split('T')[0];
        if (grouped[dateStr]) {
          grouped[dateStr].classes.push(classSchedule);
        }
      }
    });

    // Group tasks by date
    safeTasks.forEach(task => {
      if (!task.due_date) return;
      const validation = validateDate(task.due_date);
      if (validation.isValid && validation.date) {
        const dateStr = validation.date.toISOString().split('T')[0];
        if (grouped[dateStr]) {
          grouped[dateStr].tasks.push(task);
        }
      }
    });

    return grouped;
  }, [safeClasses, safeTasks, workingWeekDates]);

  if (isLoading) {
    return (
      <VStack className="flex-1 justify-center items-center" space="md">
        <Text className="text-gray-500">Loading working days...</Text>
      </VStack>
    );
  }

  return (
    <VStack className="flex-1" space="md">
      {/* Week header */}
      <Text className="text-lg font-semibold text-center text-gray-800">
        {workingWeekDates.length > 0 && workingWeekDates[0].toLocaleDateString('pt-PT', { month: 'long', year: 'numeric' })}
      </Text>
      
      {/* Week grid - only showing working days */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} className="flex-1">
        <HStack space="xs" className="flex-1 px-2">
          {workingWeekDates.map((date, index) => {
            const dateStr = date.toISOString().split('T')[0];
            const dayEvents = eventsByDate[dateStr] || { classes: [], tasks: [] };
            
            return (
              <DayColumn
                key={`${dateStr}-${index}`}
                date={date}
                classes={dayEvents.classes}
                tasks={dayEvents.tasks}
                onClassPress={onClassPress}
              />
            );
          })}
        </HStack>
      </ScrollView>
      
      {workingWeekDates.length === 0 && (
        <VStack className="flex-1 justify-center items-center" space="md">
          <Text className="text-gray-500 text-center">
            No working days configured for this week
          </Text>
          <Text className="text-sm text-gray-400 text-center">
            Contact your school administrator to configure working days
          </Text>
        </VStack>
      )}
    </VStack>
  );
};

export default WeekView;