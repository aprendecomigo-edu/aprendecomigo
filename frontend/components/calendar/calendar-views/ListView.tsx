import { CalendarDays } from 'lucide-react-native';
import React from 'react';

import { ClassSchedule } from '@/api/schedulerApi';
import { Task } from '@/api/tasksApi';
import { Center } from '@/components/ui/center';
import { Icon } from '@/components/ui/icon';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

import { ClassCard } from '../cards/ClassCard';
import { TaskCard } from '../cards/TaskCard';

interface ListViewProps {
  classes: ClassSchedule[];
  tasks: Task[];
  onClassPress: (classSchedule: ClassSchedule) => void;
}

export const ListView: React.FC<ListViewProps> = ({ classes, tasks, onClassPress }) => {
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