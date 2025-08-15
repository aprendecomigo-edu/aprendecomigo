import {
  CalendarIcon,
  ClockIcon,
  FilterIcon,
  UserIcon,
  BookOpenIcon,
  AlertCircleIcon,
  CheckCircleIcon,
} from 'lucide-react-native';
import React, { useMemo, useState, useCallback } from 'react';

import { ClassSchedule } from '@/api/schedulerApi';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useSchedules } from '@/hooks/useSchedules';

// UI Event interface (mapped from API ClassSchedule)
interface UIEvent {
  id: string;
  date: string;
  time: string;
  subject: string;
  teacher: string;
  student: string;
  status: 'scheduled' | 'confirmed' | 'pending' | 'cancelled' | 'completed';
  duration?: string;
}

// Helper function to map API ClassSchedule to UI Event
const mapClassScheduleToUIEvent = (schedule: ClassSchedule): UIEvent => {
  // Calculate duration from start/end times or use duration_minutes
  const duration = schedule.duration_minutes
    ? `${Math.floor(schedule.duration_minutes / 60)}h${
        schedule.duration_minutes % 60 > 0 ? (schedule.duration_minutes % 60) + 'm' : ''
      }`
    : undefined;

  return {
    id: schedule.id.toString(),
    date: schedule.scheduled_date,
    time: schedule.start_time,
    subject: schedule.title,
    teacher: schedule.teacher_name,
    student: schedule.student_name,
    status: schedule.status === 'no_show' ? 'cancelled' : schedule.status,
    duration,
  };
};

type FilterType = 'today' | 'week' | 'month';

interface FilterOption {
  value: FilterType;
  label: string;
}

const FILTER_OPTIONS: FilterOption[] = [
  { value: 'today', label: 'Hoje' },
  { value: 'week', label: 'Esta Semana' },
  { value: 'month', label: 'Este Mês' },
];

const STATUS_CONFIG: Record<UIEvent['status'], { color: string; label: string; icon: any }> = {
  scheduled: {
    color: 'blue',
    label: 'Agendada',
    icon: CalendarIcon,
  },
  confirmed: {
    color: 'green',
    label: 'Confirmada',
    icon: CheckCircleIcon,
  },
  pending: {
    color: 'yellow',
    label: 'Pendente',
    icon: AlertCircleIcon,
  },
  cancelled: {
    color: 'red',
    label: 'Cancelada',
    icon: AlertCircleIcon,
  },
  completed: {
    color: 'blue',
    label: 'Concluída',
    icon: CheckCircleIcon,
  },
};

interface UpcomingEventsTableProps {
  onRefresh?: () => void;
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(today.getDate() + 1);

  if (date.toDateString() === today.toDateString()) {
    return 'Hoje';
  } else if (date.toDateString() === tomorrow.toDateString()) {
    return 'Amanhã';
  } else {
    return date.toLocaleDateString('pt-PT', {
      day: '2-digit',
      month: 'short',
    });
  }
};

const filterEventsByPeriod = (events: UIEvent[], filter: FilterType): UIEvent[] => {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  return events.filter(event => {
    const eventDate = new Date(event.date);

    switch (filter) {
      case 'today':
        return eventDate.toDateString() === today.toDateString();
      case 'week':
        const weekFromNow = new Date(today);
        weekFromNow.setDate(today.getDate() + 7);
        return eventDate >= today && eventDate <= weekFromNow;
      case 'month':
        const monthFromNow = new Date(today);
        monthFromNow.setMonth(today.getMonth() + 1);
        return eventDate >= today && eventDate <= monthFromNow;
      default:
        return true;
    }
  });
};

const StatusBadge: React.FC<{ status: UIEvent['status'] }> = ({ status }) => {
  const config = STATUS_CONFIG[status];

  return (
    <HStack
      space="xs"
      className={`glass-light px-3 py-1 rounded-full items-center border-${config.color}-200`}
    >
      <Icon as={config.icon} size="xs" className={`text-${config.color}-600`} />
      <Text className={`text-xs font-medium text-${config.color}-700`}>{config.label}</Text>
    </HStack>
  );
};

const EventRow: React.FC<{ event: UIEvent; isLast: boolean }> = ({ event, isLast }) => (
  <VStack className={`p-4 w-full ${!isLast ? 'border-b border-gray-100' : ''}`}>
    <HStack space="sm" className="items-start w-full">
      {/* Date/Time Column */}
      <VStack space="xs" className="min-w-0 flex-shrink-0" style={{ width: 80 }}>
        <Text className="text-sm font-semibold font-primary text-gray-900">
          {formatDate(event.date)}
        </Text>
        <HStack space="xs" className="items-center">
          <Icon as={ClockIcon} size="xs" className="text-gray-500" />
          <Text className="text-xs font-body text-gray-600">{event.time}</Text>
        </HStack>
        {event.duration && (
          <Text className="text-xs font-body text-gray-500">{event.duration}</Text>
        )}
      </VStack>

      {/* Content Column */}
      <VStack space="xs" className="flex-1 min-w-0">
        {/* Subject */}
        <HStack space="xs" className="items-center">
          <Icon as={BookOpenIcon} size="xs" className="text-primary-600" />
          <Text className="text-sm font-semibold font-primary text-gray-900">{event.subject}</Text>
        </HStack>

        {/* Teacher & Student */}
        <VStack space="xs">
          <HStack space="xs" className="items-center">
            <Icon as={UserIcon} size="xs" className="text-gray-500" />
            <Text className="text-xs font-body text-gray-600">{event.teacher}</Text>
          </HStack>
          <Text className="text-xs font-body text-gray-600 ml-4">com {event.student}</Text>
        </VStack>

        {/* Status */}
        <Box className="mt-2">
          <StatusBadge status={event.status} />
        </Box>
      </VStack>
    </HStack>
  </VStack>
);

const EmptyState: React.FC<{ filter: FilterType }> = ({ filter }) => {
  const getEmptyMessage = () => {
    switch (filter) {
      case 'today':
        return 'Nenhuma aula agendada para hoje';
      case 'week':
        return 'Nenhuma aula agendada para esta semana';
      case 'month':
        return 'Nenhuma aula agendada para este mês';
      default:
        return 'Nenhuma aula agendada';
    }
  };

  return (
    <VStack space="md" className="items-center py-12">
      <Icon as={CalendarIcon} size="xl" className="text-gray-300" />
      <Text className="text-lg font-medium font-primary text-gray-600">{getEmptyMessage()}</Text>
      <Text className="text-sm font-body text-gray-500 text-center max-w-sm">
        As aulas aparecerão aqui quando professores e estudantes agendarem sessões de tutoria
      </Text>
    </VStack>
  );
};

const FilterButtons: React.FC<{
  activeFilter: FilterType;
  onFilterChange: (filter: FilterType) => void;
}> = ({ activeFilter, onFilterChange }) => (
  <HStack space="xs" className="flex-wrap">
    {FILTER_OPTIONS.map(option => (
      <Pressable
        key={option.value}
        onPress={() => onFilterChange(option.value)}
        className={`px-3 py-1.5 rounded-lg active:scale-98 transition-transform ${
          activeFilter === option.value ? 'bg-gradient-primary' : 'glass-light'
        }`}
      >
        <Text
          className={`text-sm font-medium font-primary ${
            activeFilter === option.value ? 'text-white' : 'text-gray-700'
          }`}
        >
          {option.label}
        </Text>
      </Pressable>
    ))}
  </HStack>
);

const UpcomingEventsTable = React.memo<UpcomingEventsTableProps>(({ onRefresh }) => {
  const [activeFilter, setActiveFilter] = useState<FilterType>('week');

  // Use the API hook
  const { schedules, loading, error, refreshSchedules } = useSchedules();

  // Convert API schedules to UI events
  const events = useMemo(() => {
    return schedules.map(mapClassScheduleToUIEvent);
  }, [schedules]);

  const filteredEvents = useMemo(() => {
    return filterEventsByPeriod(events, activeFilter).sort((a, b) => {
      const dateA = new Date(`${a.date} ${a.time}`);
      const dateB = new Date(`${b.date} ${b.time}`);
      return dateA.getTime() - dateB.getTime();
    });
  }, [events, activeFilter]);

  // Handle refresh - use API refresh or custom callback
  const handleRefresh = useCallback(async () => {
    if (onRefresh) {
      onRefresh();
    } else {
      await refreshSchedules();
    }
  }, [onRefresh, refreshSchedules]);

  return (
    <Box className="glass-container p-6 rounded-xl w-full">
      <VStack space="md" className="w-full">
        {/* Header */}
        <HStack className="justify-between items-start w-full">
          <VStack space="xs">
            <Heading size="md" className="font-primary text-gray-900">
              <Text className="bg-gradient-accent">Próximas Aulas</Text>
            </Heading>
            <Text className="text-sm font-body text-gray-600">
              {filteredEvents.length} aulas agendadas
            </Text>
          </VStack>

          <HStack space="xs" className="items-center">
            <Icon as={FilterIcon} size="sm" className="text-gray-500" />
          </HStack>
        </HStack>

        {/* Filters */}
        <FilterButtons activeFilter={activeFilter} onFilterChange={setActiveFilter} />

        {/* Events List */}
        <Box className="bg-white rounded-xl border border-gray-100 w-full">
          {loading ? (
            <VStack space="md" className="p-8">
              <Text className="text-center font-body text-gray-500">Carregando aulas...</Text>
            </VStack>
          ) : error ? (
            <VStack space="md" className="items-center py-8">
              <Text className="text-center font-body text-red-600">Erro: {error}</Text>
              <Button variant="outline" size="sm" onPress={handleRefresh}>
                <ButtonText>Tentar Novamente</ButtonText>
              </Button>
            </VStack>
          ) : filteredEvents.length === 0 ? (
            <EmptyState filter={activeFilter} />
          ) : (
            <ScrollView
              showsVerticalScrollIndicator={false}
              style={{ maxHeight: 400 }}
              className="w-full"
            >
              <VStack className="w-full">
                {filteredEvents.map((event, index) => (
                  <EventRow
                    key={event.id}
                    event={event}
                    isLast={index === filteredEvents.length - 1}
                  />
                ))}
              </VStack>
            </ScrollView>
          )}
        </Box>

        {/* Actions */}
        {filteredEvents.length > 0 && (
          <HStack space="md" className="justify-center">
            <Button
              variant="outline"
              size="sm"
              onPress={() => {
                // Navigate to full calendar view
                if (__DEV__) {
                  console.log('Navigate to calendar');
                }
              }}
            >
              <ButtonText>Ver Calendário</ButtonText>
            </Button>

            <Button variant="solid" size="sm" onPress={handleRefresh}>
              <ButtonText>Atualizar</ButtonText>
            </Button>
          </HStack>
        )}
      </VStack>
    </Box>
  );
}, (prevProps, nextProps) => {
  // Custom comparison function for UpcomingEventsTable
  // Since onRefresh is likely a stable function, we don't need deep comparison
  return true; // Let React handle the comparison for the callback
});

export { UpcomingEventsTable };
export default UpcomingEventsTable;
