import React from 'react';

import { ClassCard } from '../cards/ClassCard';
import { TaskCard } from '../cards/TaskCard';

import { ClassSchedule } from '@/api/schedulerApi';
import { Task } from '@/api/tasksApi';
import { Box } from '@/components/ui/box';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface WeekViewProps {
  currentDate: Date;
  classes: ClassSchedule[];
  tasks: Task[];
  onClassPress: (classSchedule: ClassSchedule) => void;
}

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

export const WeekView: React.FC<WeekViewProps> = ({
  currentDate,
  classes,
  tasks,
  onClassPress,
}) => {
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
