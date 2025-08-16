import {
  ActivityIcon,
  CalendarIcon,
  CheckCircleIcon,
  MailIcon,
  UserIcon,
  UserPlusIcon,
  XCircleIcon,
} from 'lucide-react-native';
import React, { useCallback } from 'react';
import { FlatList, RefreshControl } from 'react-native';

import { SchoolActivity } from '@/api/userApi';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Skeleton } from '@/components/ui/skeleton';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface ActivityFeedProps {
  activities: SchoolActivity[];
  isLoading: boolean;
  isLoadingMore: boolean;
  hasNextPage: boolean;
  onLoadMore: () => void;
  onRefresh: () => void;
  totalCount: number;
}

const getActivityIcon = (activityType: SchoolActivity['activity_type']) => {
  switch (activityType) {
    case 'invitation_sent':
      return MailIcon;
    case 'invitation_accepted':
      return CheckCircleIcon;
    case 'invitation_declined':
      return XCircleIcon;
    case 'student_joined':
    case 'teacher_joined':
      return UserPlusIcon;
    case 'class_created':
      return CalendarIcon;
    case 'class_completed':
      return CheckCircleIcon;
    case 'class_cancelled':
      return XCircleIcon;
    default:
      return ActivityIcon;
  }
};

const getActivityColor = (activityType: SchoolActivity['activity_type']) => {
  switch (activityType) {
    case 'invitation_sent':
      return 'blue';
    case 'invitation_accepted':
    case 'student_joined':
    case 'teacher_joined':
    case 'class_completed':
      return 'green';
    case 'invitation_declined':
    case 'class_cancelled':
      return 'red';
    case 'class_created':
      return 'purple';
    default:
      return 'gray';
  }
};

const formatRelativeTime = (timestamp: string): string => {
  const now = new Date();
  const activityTime = new Date(timestamp);
  const diffInMs = now.getTime() - activityTime.getTime();
  const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
  const diffInHours = Math.floor(diffInMinutes / 60);
  const diffInDays = Math.floor(diffInHours / 24);

  if (diffInMinutes < 1) {
    return 'Agora mesmo';
  } else if (diffInMinutes < 60) {
    return `${diffInMinutes}min atrás`;
  } else if (diffInHours < 24) {
    return `${diffInHours}h atrás`;
  } else if (diffInDays === 1) {
    return 'Ontem';
  } else if (diffInDays < 7) {
    return `${diffInDays} dias atrás`;
  } else {
    return activityTime.toLocaleDateString('pt-PT', {
      day: '2-digit',
      month: 'short',
    });
  }
};

const ActivityItem = React.memo<{ activity: SchoolActivity; isLast: boolean }>(
  ({ activity, isLast }) => {
    const IconComponent = getActivityIcon(activity.activity_type);
    const color = getActivityColor(activity.activity_type);

    return (
      <VStack
        className={`${!isLast ? 'border-b border-gray-100' : ''} pb-4 ${!isLast ? 'mb-4' : ''}`}
      >
        <HStack space="sm" className="items-start">
          <VStack className={`bg-${color}-100 p-2 rounded-full mt-1`}>
            <Icon as={IconComponent} size="xs" className={`text-${color}-600`} />
          </VStack>

          <VStack space="xs" className="flex-1 min-w-0">
            <Text className="text-sm text-gray-900 leading-5">{activity.description}</Text>

            <HStack space="sm" className="items-center">
              <Text className="text-xs text-gray-500">
                {formatRelativeTime(activity.timestamp)}
              </Text>

              {activity.actor && (
                <>
                  <Text className="text-xs text-gray-300">•</Text>
                  <Text className="text-xs text-gray-500">por {activity.actor.name}</Text>
                </>
              )}
            </HStack>
          </VStack>
        </HStack>
      </VStack>
    );
  },
);

const ActivityItemSkeleton = React.memo<{ isLast: boolean }>(({ isLast }) => (
  <VStack className={`${!isLast ? 'border-b border-gray-100' : ''} pb-4 ${!isLast ? 'mb-4' : ''}`}>
    <HStack space="sm" className="items-start">
      <Skeleton className="w-8 h-8 rounded-full mt-1" />
      <VStack space="xs" className="flex-1">
        <Skeleton className="h-4 w-full rounded" />
        <Skeleton className="h-3 w-24 rounded" />
      </VStack>
    </HStack>
  </VStack>
));

const EmptyState = React.memo(() => (
  <VStack space="md" className="items-center py-12">
    <Icon as={ActivityIcon} size="xl" className="text-gray-300" />
    <Text className="text-lg font-medium text-gray-600">Nenhuma atividade recente</Text>
    <Text className="text-sm text-gray-500 text-center max-w-sm">
      As atividades da escola aparecerão aqui quando professores e estudantes começarem a interagir
    </Text>
  </VStack>
));

const LoadMoreButton = React.memo<{ onPress: () => void; isLoading: boolean }>(
  ({ onPress, isLoading }) => (
    <Pressable
      onPress={onPress}
      disabled={isLoading}
      className="mt-4 py-3 px-4 bg-blue-50 border border-blue-200 rounded-lg"
    >
      <Text className="text-center text-blue-600 font-medium">
        {isLoading ? 'Carregando...' : 'Carregar mais atividades'}
      </Text>
    </Pressable>
  ),
);

const ActivityFeed: React.FC<ActivityFeedProps> = ({
  activities,
  isLoading,
  isLoadingMore,
  hasNextPage,
  onLoadMore,
  onRefresh,
  totalCount,
}) => {
  const renderActivity = useCallback(
    ({ item, index }: { item: SchoolActivity; index: number }) => (
      <ActivityItem activity={item} isLast={index === activities.length - 1} />
    ),
    [activities.length],
  );

  // Optimized item layout for better performance
  const getItemLayout = useCallback(
    (data: any, index: number) => ({
      length: 72, // Approximate height: 64px + 8px margin
      offset: 72 * index,
      index,
    }),
    [],
  );

  const renderFooter = () => {
    if (isLoadingMore) {
      return (
        <VStack space="md" className="py-4">
          {[...Array(3)].map((_, i) => (
            <ActivityItemSkeleton key={i} isLast={i === 2} />
          ))}
        </VStack>
      );
    }

    if (hasNextPage && activities.length > 0) {
      return <LoadMoreButton onPress={onLoadMore} isLoading={false} />;
    }

    return null;
  };

  return (
    <Card variant="elevated" className="bg-white shadow-sm">
      <CardHeader>
        <HStack className="justify-between items-center">
          <Heading size="md" className="text-gray-900">
            Atividade Recente
          </Heading>
          {totalCount > 0 && (
            <Text className="text-sm text-gray-500">
              {activities.length} de {totalCount}
            </Text>
          )}
        </HStack>
      </CardHeader>
      <CardBody>
        {isLoading ? (
          <VStack space="md">
            {[...Array(5)].map((_, i) => (
              <ActivityItemSkeleton key={i} isLast={i === 4} />
            ))}
          </VStack>
        ) : activities.length === 0 ? (
          <EmptyState />
        ) : (
          <FlatList
            data={activities}
            renderItem={renderActivity}
            keyExtractor={item => item.id}
            getItemLayout={getItemLayout}
            showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={isLoading} onRefresh={onRefresh} />}
            ListFooterComponent={renderFooter}
            onEndReached={hasNextPage ? onLoadMore : undefined}
            onEndReachedThreshold={0.5}
            style={{ maxHeight: 400 }}
          />
        )}
      </CardBody>
    </Card>
  );
};

export { ActivityFeed };
export default ActivityFeed;
