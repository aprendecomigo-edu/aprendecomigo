import { router } from 'expo-router';
import { Plus, CalendarDays, Clock, User, MapPin } from 'lucide-react-native';
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Alert } from 'react-native';
import { DateData } from 'react-native-calendars';
import { useColorScheme } from '@/components/useColorScheme';
import { safeFormatDate, safeFormatTime, validateDate } from '@/components/calendar/dateUtils';

import apiClient from '@/api/apiClient';
import { useAuth, useUserProfile } from '@/api/auth';
import schedulerApi, { ClassSchedule } from '@/api/schedulerApi';
import { tasksApi, Task } from '@/api/tasksApi';
import MonthView from '@/components/calendar/MonthView';
import WeekView from '@/components/calendar/WeekView';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import MainLayout from '@/components/layouts/MainLayout';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Divider } from '@/components/ui/divider';
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
    return safeFormatDate(dateString);
  };

  return (
    <Box className="bg-white rounded-xl border border-l-4 border-l-orange-500 border-gray-200 p-5 shadow-sm hover:shadow-md transition-shadow">
      <VStack space="md">
        {/* Header */}
        <HStack className="justify-between items-start">
          <VStack className="flex-1 mr-3">
            <Text className="font-bold text-lg text-gray-900 leading-tight">{task.title}</Text>
            <Text className="text-orange-600 font-medium text-sm mt-1">{task.task_type}</Text>
          </VStack>
          <VStack space="xs" className="items-end">
            <Badge className={getPriorityColor(task.priority)}>
              <BadgeText className="font-semibold text-xs">{task.priority.toUpperCase()}</BadgeText>
            </Badge>
            {task.is_urgent && (
              <Badge className="bg-red-100 text-red-800">
                <BadgeText className="font-semibold text-xs">URGENT</BadgeText>
              </Badge>
            )}
          </VStack>
        </HStack>

        {/* Date and Time */}
        <HStack space="lg" className="flex-wrap">
          {showDate && task.due_date && (
            <HStack space="xs" className="items-center bg-gray-50 px-3 py-2 rounded-lg">
              <Icon as={CalendarDays} size="sm" className="text-gray-600" />
              <Text className="text-sm text-gray-700 font-medium">{formatDueDate(task.due_date)}</Text>
            </HStack>
          )}
          {task.due_date && (
            <HStack space="xs" className="items-center bg-orange-50 px-3 py-2 rounded-lg">
              <Icon as={Clock} size="sm" className="text-orange-600" />
              <Text className="text-sm text-orange-700 font-medium">
                Due: {safeFormatTime(task.due_date)}
              </Text>
            </HStack>
          )}
        </HStack>

        {/* Description */}
        {task.description && (
          <Box className="bg-gray-50 p-3 rounded-lg">
            <Text className="text-sm text-gray-700 leading-relaxed">{task.description}</Text>
          </Box>
        )}
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
    <Pressable onPress={onPress} className="active:scale-[0.98] transition-transform">
      <Box className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm hover:shadow-md transition-shadow">
        <VStack space="md">
          {/* Header */}
          <HStack className="justify-between items-start">
            <VStack className="flex-1 mr-3">
              <Text className="font-bold text-lg text-gray-900 leading-tight">{classSchedule.title}</Text>
              <Text className="text-blue-600 font-medium text-sm mt-1">
                {isTeacher
                  ? `Student: ${classSchedule.student_name}`
                  : `Teacher: ${classSchedule.teacher_name}`}
              </Text>
            </VStack>
            <Badge className={getStatusColor(classSchedule.status)}>
              <BadgeText className="font-semibold text-xs">{classSchedule.status_display}</BadgeText>
            </Badge>
          </HStack>

          {/* Date and Time */}
          <VStack space="sm">
            <HStack space="sm" className="flex-wrap">
              {showDate && (
                <HStack space="xs" className="items-center bg-gray-50 px-3 py-2 rounded-lg">
                  <Icon as={CalendarDays} size="sm" className="text-gray-600" />
                  <Text className="text-sm text-gray-700 font-medium">{safeFormatDate(classSchedule.scheduled_date)}</Text>
                </HStack>
              )}
              <HStack space="xs" className="items-center bg-blue-50 px-3 py-2 rounded-lg">
                <Icon as={Clock} size="sm" className="text-blue-600" />
                <Text className="text-sm text-blue-700 font-medium">
                  {classSchedule.start_time} - {classSchedule.end_time}
                </Text>
              </HStack>
            </HStack>
            
            <HStack space="xs" className="items-center bg-gray-50 px-3 py-2 rounded-lg">
              <Icon as={MapPin} size="sm" className="text-gray-600" />
              <Text className="text-sm text-gray-700 font-medium">{classSchedule.school_name}</Text>
            </HStack>
          </VStack>

          {/* Description */}
          {classSchedule.description && (
            <Box className="bg-gray-50 p-3 rounded-lg">
              <Text className="text-sm text-gray-700 leading-relaxed">{classSchedule.description}</Text>
            </Box>
          )}

          {/* Additional students for group classes */}
          {classSchedule.additional_students_names.length > 0 && (
            <HStack space="xs" className="items-center bg-green-50 px-3 py-2 rounded-lg">
              <Icon as={User} size="sm" className="text-green-600" />
              <Text className="text-sm text-green-700 font-medium">
                Group: {classSchedule.additional_students_names.join(', ')}
              </Text>
            </HStack>
          )}
        </VStack>
      </Box>
    </Pressable>
  );
};


// List view component with improved UX
const ListView: React.FC<{
  classes: ClassSchedule[];
  tasks: Task[];
  onClassPress: (classSchedule: ClassSchedule) => void;
}> = ({ classes, tasks, onClassPress }) => {
  // Add null check and default to empty array
  const safeClasses = classes || [];
  const safeTasks = tasks || [];

  // Combine and sort events by date
  const allEvents = useMemo(() => {
    const events: Array<{
      type: 'class' | 'task';
      date: string;
      sortDate: Date;
      data: ClassSchedule | Task;
    }> = [];

    // Add classes
    safeClasses.forEach(classSchedule => {
      const validation = validateDate(classSchedule.scheduled_date);
      if (validation.isValid && validation.date) {
        events.push({
          type: 'class',
          date: classSchedule.scheduled_date,
          sortDate: validation.date,
          data: classSchedule,
        });
      }
    });

    // Add tasks
    safeTasks.forEach(task => {
      if (!task.due_date) return;
      const validation = validateDate(task.due_date);
      if (validation.isValid && validation.date) {
        events.push({
          type: 'task',
          date: task.due_date,
          sortDate: validation.date,
          data: task,
        });
      }
    });

    // Sort by date
    return events.sort((a, b) => a.sortDate.getTime() - b.sortDate.getTime());
  }, [safeClasses, safeTasks]);

  // Group events by date
  const eventsByDate = useMemo(() => {
    const grouped: { [key: string]: Array<typeof allEvents[0]> } = {};
    
    allEvents.forEach(event => {
      const dateKey = event.sortDate.toISOString().split('T')[0];
      if (!grouped[dateKey]) {
        grouped[dateKey] = [];
      }
      grouped[dateKey].push(event);
    });

    return Object.keys(grouped)
      .sort()
      .map(dateKey => ({
        date: new Date(dateKey),
        dateKey,
        events: grouped[dateKey],
      }));
  }, [allEvents]);

  if (eventsByDate.length === 0) {
    return (
      <Center className="flex-1 py-16">
        <Box className="bg-gray-50 rounded-full p-6 mb-6">
          <Icon as={CalendarDays} size="2xl" className="text-gray-400" />
        </Box>
        <Text className="text-xl font-semibold text-gray-700 mb-3">
          No upcoming events
        </Text>
        <Text className="text-gray-500 text-center max-w-sm leading-6">
          Your scheduled classes and tasks will appear here. Start by booking a class or creating a task.
        </Text>
      </Center>
    );
  }

  return (
    <ScrollView showsVerticalScrollIndicator={false} className="flex-1">
      <VStack space="lg" className="pb-6">
        {eventsByDate.map(({ date, dateKey, events }) => {
          const isToday = date.toDateString() === new Date().toDateString();
          const isThisWeek = date.getTime() - Date.now() < 7 * 24 * 60 * 60 * 1000 && date.getTime() > Date.now() - 24 * 60 * 60 * 1000;
          
          return (
            <VStack key={dateKey} space="md">
              {/* Date Header */}
              <Box className={`px-4 py-3 rounded-xl ${isToday ? 'bg-blue-50 border border-blue-200' : isThisWeek ? 'bg-orange-50 border border-orange-200' : 'bg-gray-50 border border-gray-200'}`}>
                <HStack className="justify-between items-center">
                  <VStack space="xs">
                    <Text className={`text-lg font-bold ${isToday ? 'text-blue-900' : isThisWeek ? 'text-orange-900' : 'text-gray-900'}`}>
                      {date.toLocaleDateString('pt-PT', {
                        weekday: 'long',
                        day: 'numeric',
                        month: 'long',
                      })}
                    </Text>
                    {isToday && (
                      <Text className="text-sm font-medium text-blue-700">
                        Today
                      </Text>
                    )}
                  </VStack>
                  <Badge className={`${isToday ? 'bg-blue-100 text-blue-800' : isThisWeek ? 'bg-orange-100 text-orange-800' : 'bg-gray-100 text-gray-800'}`}>
                    <BadgeText className="font-medium">
                      {events.length} {events.length === 1 ? 'event' : 'events'}
                    </BadgeText>
                  </Badge>
                </HStack>
              </Box>

              {/* Events for this date */}
              <VStack space="sm" className="px-2">
                {events.map((event, index) => (
                  <Box key={`${event.type}-${event.data.id}-${index}`} className="transform transition-all">
                    {event.type === 'class' ? (
                      <ClassCard
                        classSchedule={event.data as ClassSchedule}
                        onPress={() => onClassPress(event.data as ClassSchedule)}
                        showDate={false}
                      />
                    ) : (
                      <TaskCard
                        task={event.data as Task}
                        showDate={false}
                      />
                    )}
                  </Box>
                ))}
              </VStack>
            </VStack>
          );
        })}
      </VStack>
    </ScrollView>
  );
};

// Main calendar component
const CalendarScreen: React.FC = () => {
  const { userProfile } = useUserProfile();
  const colorScheme = useColorScheme();
  const isDarkMode = colorScheme === 'dark';
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
        console.error('Error loading classes:', error);
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
        `/tasks/calendar/${params.toString() ? '?' + params.toString() : ''}`
      );
      const calendarTasks = response.data;

      setTasks(calendarTasks || []);
    } catch (error) {
      if (__DEV__) {
        console.error('Error loading tasks:', error);
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
          console.error('Error in initializeData:', error);
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
    try {
      const selectedDate = new Date(day.dateString);
      
      // Validate the selected date
      if (isNaN(selectedDate.getTime())) {
        if (__DEV__) {
          console.warn('Invalid date selected:', day.dateString);
        }
        return;
      }
      
      setCurrentDate(selectedDate);
      
      // Filter events for the selected day with validation
      const dayClasses = classes.filter(c => {
        const validation = validateDate(c.scheduled_date);
        return validation.isValid && validation.date?.toISOString().split('T')[0] === day.dateString;
      });
      const dayTasks = tasks.filter(t => {
        if (!t.due_date) return false;
        const validation = validateDate(t.due_date);
        return validation.isValid && validation.date?.toISOString().split('T')[0] === day.dateString;
      });
      
      // If there are events on this day, you could show them in a modal or navigate to a detail view
      if (dayClasses.length > 0 || dayTasks.length > 0) {
        // Future enhancement: Show day detail modal
      }
    } catch (error) {
      if (__DEV__) {
        console.error('Error handling day press:', error);
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
              <ErrorBoundary
                onError={(error, errorInfo) => {
                  if (__DEV__) {
                    console.error('List view error:', error, errorInfo);
                  }
                }}
              >
                <ListView classes={classes} tasks={tasks} onClassPress={handleClassPress} />
              </ErrorBoundary>
            ) : view === 'week' ? (
              <ErrorBoundary
                onError={(error, errorInfo) => {
                  if (__DEV__) {
                    console.error('Week view error:', error, errorInfo);
                  }
                }}
              >
                <WeekView
                  currentDate={currentDate}
                  classes={classes}
                  tasks={tasks}
                  onClassPress={handleClassPress}
                />
              </ErrorBoundary>
            ) : (
              <ErrorBoundary
                onError={(error, errorInfo) => {
                  if (__DEV__) {
                    console.error('Month view error:', error, errorInfo);
                  }
                }}
              >
                <MonthView
                  currentDate={currentDate}
                  classes={classes}
                  tasks={tasks}
                  onDayPress={handleDayPress}
                  isDarkMode={isDarkMode}
                />
              </ErrorBoundary>
            )}
          </>
        )}
      </VStack>
    </MainLayout>
  );
};

export default CalendarScreen;