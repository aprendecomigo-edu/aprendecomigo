import { router } from 'expo-router';
import { Plus, CalendarDays, Clock, User, MapPin } from 'lucide-react-native';
import React, { useState, useEffect, useCallback } from 'react';
import { Alert } from 'react-native';

import { useAuth } from '@/api/authContext';
import schedulerApi, { ClassSchedule } from '@/api/schedulerApi';
import MainLayout from '@/components/layouts/main-layout';
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
type CalendarView = 'week' | 'month' | 'list';

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

// Class card component
const ClassCard: React.FC<{
  classSchedule: ClassSchedule;
  onPress: () => void;
  showDate?: boolean;
}> = ({ classSchedule, onPress, showDate = false }) => {
  const { userProfile } = useAuth();
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
  onClassPress: (classSchedule: ClassSchedule) => void;
}> = ({ currentDate, classes, onClassPress }) => {
  const weekDates = getWeekDates(currentDate);

  return (
    <VStack space="md">
      {/* Week header */}
      <HStack className="justify-between items-center px-2">
        {weekDates.map((date, index) => (
          <VStack key={index} className="items-center flex-1">
            <Text className="text-xs text-gray-500 uppercase">
              {date.toLocaleDateString('pt-PT', { weekday: 'short' })}
            </Text>
            <Text className="text-lg font-medium">{date.getDate()}</Text>
          </VStack>
        ))}
      </HStack>

      <Divider />

      {/* Week content */}
      <ScrollView>
        <VStack space="md">
          {weekDates.map((date, index) => {
            const dateStr = date.toISOString().split('T')[0];
            const dayClasses = classes.filter(c => c.scheduled_date === dateStr);

            return (
              <VStack key={index} space="sm">
                <Text className="font-medium text-gray-700">
                  {date.toLocaleDateString('pt-PT', {
                    weekday: 'long',
                    day: 'numeric',
                    month: 'long',
                  })}
                </Text>
                {dayClasses.length > 0 ? (
                  dayClasses.map(classSchedule => (
                    <ClassCard
                      key={classSchedule.id}
                      classSchedule={classSchedule}
                      onPress={() => onClassPress(classSchedule)}
                    />
                  ))
                ) : (
                  <Box className="bg-gray-50 rounded-lg p-4">
                    <Text className="text-gray-500 text-center">No classes scheduled</Text>
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
  onClassPress: (classSchedule: ClassSchedule) => void;
}> = ({ classes, onClassPress }) => {
  if (classes.length === 0) {
    return (
      <Center className="flex-1 py-12">
        <Icon as={CalendarDays} size="xl" className="text-gray-300 mb-4" />
        <Text className="text-lg font-medium text-gray-600 mb-2">No classes scheduled</Text>
        <Text className="text-gray-500 text-center max-w-sm">
          Your upcoming classes will appear here
        </Text>
      </Center>
    );
  }

  return (
    <ScrollView>
      <VStack space="md">
        {classes.map(classSchedule => (
          <ClassCard
            key={classSchedule.id}
            classSchedule={classSchedule}
            onPress={() => onClassPress(classSchedule)}
            showDate={true}
          />
        ))}
      </VStack>
    </ScrollView>
  );
};

// Main calendar component
const CalendarScreen: React.FC = () => {
  const { userProfile } = useAuth();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<CalendarView>('list');
  const [classes, setClasses] = useState<ClassSchedule[]>([]);
  const [loading, setLoading] = useState(true);

  const canSchedule = userProfile?.user_type !== 'teacher';

  const loadClasses = useCallback(async () => {
    try {
      setLoading(true);
      const response = await schedulerApi.getClassSchedules();
      setClasses(response.results);
    } catch (error) {
      console.error('Error loading classes:', error);
      Alert.alert('Error', 'Failed to load classes');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadClasses();
  }, [loadClasses]);

  const handleClassPress = (classSchedule: ClassSchedule) => {
    router.push(`/calendar/${classSchedule.id}`);
  };

  const handleNewClass = () => {
    router.push('/calendar/book');
  };

  const navigatePrevious = () => {
    const newDate = new Date(currentDate);
    if (view === 'week') {
      newDate.setDate(currentDate.getDate() - 7);
    } else {
      newDate.setMonth(currentDate.getMonth() - 1);
    }
    setCurrentDate(newDate);
  };

  const navigateNext = () => {
    const newDate = new Date(currentDate);
    if (view === 'week') {
      newDate.setDate(currentDate.getDate() + 7);
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
              <ListView classes={classes} onClassPress={handleClassPress} />
            ) : (
              <WeekView
                currentDate={currentDate}
                classes={classes}
                onClassPress={handleClassPress}
              />
            )}
          </>
        )}
      </VStack>
    </MainLayout>
  );
};

export default CalendarScreen;
