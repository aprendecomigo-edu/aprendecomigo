import { CalendarDays, Clock } from 'lucide-react-native';
import React from 'react';

import { Task } from '@/api/tasksApi';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface TaskCardProps {
  task: Task;
  showDate?: boolean;
}

export const TaskCard: React.FC<TaskCardProps> = ({ task, showDate = false }) => {
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