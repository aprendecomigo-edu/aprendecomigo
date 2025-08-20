import { router } from 'expo-router';
import { Plus, CalendarDays, Clock, User, MapPin } from 'lucide-react-native';
import React, { useState, useEffect, useCallback } from 'react';
import { Alert } from 'react-native';
import { DateData } from 'react-native-calendars';

import apiClient from '@/api/apiClient';
import { useUserProfile } from '@/api/auth';
import schedulerApi, { ClassSchedule } from '@/api/schedulerApi';
import { Task } from '@/api/tasksApi';
import MonthView from '@/components/calendar/MonthView';
import MainLayout from '@/components/layouts/MainLayout';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Calendar view types
type CalendarView = 'list' | 'week' | 'month';

// Helper function to get week dates
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

// Helper function to format date
// Helper function to format date (currently unused)
// const formatDate = (date: Date): string => {
//   return date.toLocaleDateString('pt-PT', {
//     day: '2-digit',
//     month: '2-digit',
//     year: 'numeric',
//   });
// };

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

// Task card component for calendar view
const TaskCard: React.FC<{
  task: Task;
  showDate?: boolean;
}> = ({ task, showDate = false }) => {
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

  const formatDueDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-PT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  return (
    <Box className="bg-white rounded-lg border border-l-4 border-l-orange-500 border-gray-200 p-4 mb-3 shadow-sm">
      <VStack space="sm">
        {/* Header */}
        <HStack className="justify-between items-start">
          <VStack className="flex-1">
            <Text className="font-bold text-lg">{task.title}</Text>
            <Text className="text-gray-600">{task.task_type}</Text>
          </VStack>
          <HStack space="xs">
            <Badge className={getPriorityColor(task.priority)}>
              <BadgeText>{task.priority.toUpperCase()}</BadgeText>
            </Badge>
            {task.is_urgent && (
              <Badge className="bg-red-100 text-red-800">
                <BadgeText>URGENT</BadgeText>
              </Badge>
            )}
          </HStack>
        </HStack>

        {/* Date and Time */}
        <HStack space="md" className="flex-wrap">
          {showDate && task.due_date && (
            <HStack space="xs" className="items-center">
              <Icon as={CalendarDays} size="sm" className="text-gray-500" />
              <Text className="text-sm text-gray-600">{formatDueDate(task.due_date)}</Text>
            </HStack>
          )}
          {task.due_date && (
            <HStack space="xs" className="items-center">
              <Icon as={Clock} size="sm" className="text-gray-500" />
              <Text className="text-sm text-gray-600">
                Due:{' '}
                {new Date(task.due_date).toLocaleTimeString('pt-PT', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </Text>
            </HStack>
          )}
        </HStack>

        {/* Description */}
        {task.description && <Text className="text-sm text-gray-600">{task.description}</Text>}
      </VStack>
    </Box>
  );
};

// Class card component
const ClassCard: React.FC<{
  classSchedule: ClassSchedule;
  onPress: () => void;
  showDate?: boolean;
}> = ({ classSchedule, onPress, showDate = false }) => {
  const { userProfile } = useUserProfile();
  const isTeacher = userProfile?.user_type === 'teacher';

  return (
    <Pressable onPress={onPress}>
      <Box className="bg-white rounded-lg border border-gray-200 p-4 mb-3 shadow-sm">
        <VStack space="sm">
          {/* Header */}
          <HStack className="justify-between items-start">
            <VStack className="flex-1">
              <Text className="font-bold text-lg">{classSchedule.title}</Text>
              <Text className="text-gray-600">
                {isTeacher
                  ? `Student: ${classSchedule.student_name}`
                  : `Teacher: ${classSchedule.teacher_name}`}
              </Text>
            </VStack>
            <Badge className={getStatusColor(classSchedule.status)}>
              <BadgeText>{classSchedule.status_display}</BadgeText>
            </Badge>
          </HStack>

          {/* Date and Time */}
          <HStack space="md" className="flex-wrap">
            {showDate && (
              <HStack space="xs" className="items-center">
                <Icon as={CalendarDays} size="sm" className="text-gray-500" />
                <Text className="text-sm text-gray-600">{classSchedule.scheduled_date}</Text>
              </HStack>
            )}
            <HStack space="xs" className="items-center">
              <Icon as={Clock} size="sm" className="text-gray-500" />
              <Text className="text-sm text-gray-600">
                {classSchedule.start_time} - {classSchedule.end_time}
              </Text>
            </HStack>
            <HStack space="xs" className="items-center">
              <Icon as={MapPin} size="sm" className="text-gray-500" />
              <Text className="text-sm text-gray-600">{classSchedule.school_name}</Text>
            </HStack>
          </HStack>

          {/* Description */}
          {classSchedule.description && (
            <Text className="text-sm text-gray-600">{classSchedule.description}</Text>
          )}

          {/* Additional students for group classes */}
          {classSchedule.additional_students_names.length > 0 && (
            <HStack space="xs" className="items-center">
              <Icon as={User} size="sm" className="text-gray-500" />
              <Text className="text-sm text-gray-600">
                Group: {classSchedule.additional_students_names.join(', ')}
              </Text>
            </HStack>
          )}
        </VStack>
      </Box>
    </Pressable>
  );
};

// Week view component
const WeekView: React.FC<{
  currentDate: Date;
  classes: ClassSchedule[];
  tasks: Task[];
  onClassPress: (classSchedule: ClassSchedule) => void;
}> = ({ currentDate, classes, tasks, onClassPress }) => {
  // Add null check and default to empty array
  const safeClasses = classes || [];
  const safeTasks = tasks || [];

  const weekDates = getWeekDates(currentDate);

  return (
    <VStack className="flex-1" space="md">
      <ScrollView>
        <VStack space="lg">
          {weekDates.map((date, index) => {
            const dateStr = date.toISOString().split('T')[0];
            const dayClasses = safeClasses.filter(c => c.scheduled_date === dateStr);
            const dayTasks = safeTasks.filter(
              t => t.due_date && t.due_date.split('T')[0] === dateStr,
            );

            const hasContent = dayClasses.length > 0 || dayTasks.length > 0;

            return (
              <VStack key={index} space="sm">
                <Text className="font-medium text-gray-700">
                  {date.toLocaleDateString('pt-PT', {
                    weekday: 'long',
                    day: 'numeric',
                    month: 'long',
                  })}
                </Text>
                {hasContent ? (
                  <VStack space="xs">
                    {dayClasses.map(classSchedule => (
                      <ClassCard
                        key={`class-${classSchedule.id}`}
                        classSchedule={classSchedule}
                        onPress={() => onClassPress(classSchedule)}
                      />
                    ))}
                    {dayTasks.map(task => (
                      <TaskCard key={`task-${task.id}`} task={task} />
                    ))}
                  </VStack>
                ) : (
                  <Box className="bg-gray-50 rounded-lg p-4">
                    <Text className="text-gray-500 text-center">No classes or tasks scheduled</Text>
                  </Box>
                )}
              </VStack>
            );
          })}
        </VStack>
      </ScrollView>
    </VStack>
  );
};

// List view component
const ListView: React.FC<{
  classes: ClassSchedule[];
  tasks: Task[];
  onClassPress: (classSchedule: ClassSchedule) => void;
}> = ({ classes, tasks, onClassPress }) => {
  // Add null check and default to empty array
  const safeClasses = classes || [];
  const safeTasks = tasks || [];

  const hasContent = safeClasses.length > 0 || safeTasks.length > 0;

  if (!hasContent) {
    return (
      <Center className="flex-1 py-12">
        <Icon as={CalendarDays} size="xl" className="text-gray-300 mb-4" />
        <Text className="text-lg font-medium text-gray-600 mb-2">
          No classes or tasks scheduled
        </Text>
        <Text className="text-gray-500 text-center max-w-sm">
          Your upcoming classes and tasks will appear here
        </Text>
      </Center>
    );
  }

  return (
    <ScrollView>
      <VStack space="md">
        {safeClasses.map(classSchedule => (
          <ClassCard
            key={`class-${classSchedule.id}`}
            classSchedule={classSchedule}
            onPress={() => onClassPress(classSchedule)}
            showDate={true}
          />
        ))}
        {safeTasks.map(task => (
          <TaskCard key={`task-${task.id}`} task={task} showDate={true} />
        ))}
      </VStack>
    </ScrollView>
  );
};

// Main calendar component
const CalendarScreen: React.FC = () => {
  const { userProfile } = useUserProfile();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<CalendarView>('list');
  const [classes, setClasses] = useState<ClassSchedule[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  // Check if user can schedule classes based on their role
  // Teachers should not be able to schedule classes
  const canSchedule = userProfile?.user_type !== 'teacher';

  const loadClasses = useCallback(async () => {
    try {
      setLoading(true);
      const classes = await schedulerApi.getClassSchedules();
      // API now returns the array directly
      setClasses(Array.isArray(classes) ? classes : []);
    } catch (error) {
      if (__DEV__) {
        console.error('Error loading classes:', error); // TODO: Review for sensitive data
      }
      // Set empty array on error to prevent crashes
      setClasses([]);
      Alert.alert('Error', 'Failed to load classes');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadTasks = useCallback(async () => {
    try {
      // Calculate start and end dates for the current view
      let startDate: string, endDate: string;
      const start = new Date(currentDate);
      const end = new Date(currentDate);

      if (view === 'week') {
        const weekDates = getWeekDates(currentDate);
        start.setTime(weekDates[0].getTime());
        end.setTime(weekDates[6].getTime());
      } else {
        // For list view, show tasks for the next 30 days
        end.setDate(start.getDate() + 30);
      }

      startDate = start.toISOString();
      endDate = end.toISOString();

      // Use direct API call instead of tasksApi (which has issues)
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      const response = await apiClient.get(
        `/tasks/calendar/${params.toString() ? '?' + params.toString() : ''}`,
      );
      const calendarTasks = response.data;

      setTasks(calendarTasks || []);
    } catch (error) {
      if (__DEV__) {
        console.error('Error loading tasks:', error); // TODO: Review for sensitive data
      }
      setTasks([]);
    }
  }, [currentDate, view]);

  useEffect(() => {
    // Load data when component mounts
    const initializeData = async () => {
      try {
        await loadClasses();
        await loadTasks();
      } catch (error) {
        if (__DEV__) {
          console.error('Error in initializeData:', error); // TODO: Review for sensitive data
        }
      }
    };
    initializeData();
  }, [loadClasses, loadTasks]);

  const handleClassPress = (classSchedule: ClassSchedule) => {
    router.push(`/calendar/${classSchedule.id}`);
  };

  const handleNewClass = () => {
    router.push('/calendar/book');
  };

  const handleDayPress = (day: DateData) => {
    const selectedDate = new Date(day.dateString);
    setCurrentDate(selectedDate);

    // Filter events for the selected day
    const dayClasses = classes.filter(c => c.scheduled_date === day.dateString);
    const dayTasks = tasks.filter(t => t.due_date && t.due_date.split('T')[0] === day.dateString);

    // If there are events on this day, you could show them in a modal or navigate to a detail view
    if (dayClasses.length > 0 || dayTasks.length > 0) {
      if (__DEV__) {
        console.log(
          `Selected day ${day.dateString} has ${dayClasses.length} classes and ${dayTasks.length} tasks`,
        );
      }
    }
  };

  const navigatePrevious = () => {
    const newDate = new Date(currentDate);
    if (view === 'week') {
      newDate.setDate(currentDate.getDate() - 7);
    } else if (view === 'month') {
      newDate.setMonth(currentDate.getMonth() - 1);
    } else {
      newDate.setMonth(currentDate.getMonth() - 1);
    }
    setCurrentDate(newDate);
  };

  const navigateNext = () => {
    const newDate = new Date(currentDate);
    if (view === 'week') {
      newDate.setDate(currentDate.getDate() + 7);
    } else if (view === 'month') {
      newDate.setMonth(currentDate.getMonth() + 1);
    } else {
      newDate.setMonth(currentDate.getMonth() + 1);
    }
    setCurrentDate(newDate);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  return (
    <MainLayout _title="Calendar">
      <VStack className="flex-1 p-4" space="md">
        {/* Header */}
        <HStack className="justify-between items-center">
          <Heading className="text-2xl font-bold">
            <ButtonText>Calendar</ButtonText>
          </Heading>
          {canSchedule && (
            <Button size="sm" onPress={handleNewClass}>
              <ButtonText>Book Class</ButtonText>
              <ButtonIcon as={Plus} className="ml-2" />
            </Button>
          )}
        </HStack>

        {/* View Controls */}
        <HStack className="justify-between items-center">
          <HStack space="xs">
            <Button
              variant={view === 'list' ? 'solid' : 'outline'}
              size="sm"
              onPress={() => setView('list')}
            >
              <ButtonText>List</ButtonText>
            </Button>
            <Button
              variant={view === 'week' ? 'solid' : 'outline'}
              size="sm"
              onPress={() => setView('week')}
            >
              <ButtonText>Week</ButtonText>
            </Button>
            <Button
              variant={view === 'month' ? 'solid' : 'outline'}
              size="sm"
              onPress={() => setView('month')}
            >
              <ButtonText>Month</ButtonText>
            </Button>
          </HStack>
          <HStack space="xs">
            <Button variant="outline" size="sm" onPress={navigatePrevious}>
              <ButtonText>←</ButtonText>
            </Button>
            <Button variant="outline" size="sm" onPress={goToToday}>
              <ButtonText>Today</ButtonText>
            </Button>
            <Button variant="outline" size="sm" onPress={navigateNext}>
              <ButtonText>→</ButtonText>
            </Button>
          </HStack>
        </HStack>

        {/* Content */}
        {loading ? (
          <Center className="flex-1">
            <Spinner size="large" />
            <Text className="mt-4 text-gray-600">Loading classes...</Text>
          </Center>
        ) : (
          <>
            {view === 'list' ? (
              <ListView classes={classes} tasks={tasks} onClassPress={handleClassPress} />
            ) : view === 'week' ? (
              <WeekView
                currentDate={currentDate}
                classes={classes}
                tasks={tasks}
                onClassPress={handleClassPress}
              />
            ) : (
              <MonthView
                currentDate={currentDate}
                classes={classes}
                tasks={tasks}
                onDayPress={handleDayPress}
                isDarkMode={false}
              />
            )}
          </>
        )}
      </VStack>
    </MainLayout>
  );
};

export default CalendarScreen;
