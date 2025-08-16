import { CalendarDays, Clock, MapPin, User } from 'lucide-react-native';
import React from 'react';

import { useUserProfile } from '@/api/auth';
import { ClassSchedule } from '@/api/schedulerApi';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface ClassCardProps {
  classSchedule: ClassSchedule;
  onPress: () => void;
  showDate?: boolean;
}

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

export const ClassCard: React.FC<ClassCardProps> = ({
  classSchedule,
  onPress,
  showDate = false,
}) => {
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
