import {
  CalendarIcon,
  ClockIcon,
  UsersIcon,
  CheckCircleIcon,
  AlertCircleIcon,
  PlayIcon,
  PauseIcon,
} from 'lucide-react-native';
import React from 'react';
import { Pressable } from 'react-native';

import type { SessionInfo, SessionsData } from '@/api/teacherApi';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface TodaysOverviewProps {
  sessions: SessionsData;
  onScheduleSession: () => void;
  onViewSession: (sessionId: number) => void;
  onStartSession?: (sessionId: number) => void;
  isLoading?: boolean;
}

const SessionCard: React.FC<{
  session: SessionInfo;
  onPress: () => void;
  onStart?: () => void;
  showActions?: boolean;
}> = ({ session, onPress, onStart, showActions = true }) => {
  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'scheduled':
        return { color: 'bg-blue-100 text-blue-800', label: 'Agendada', icon: CalendarIcon };
      case 'in_progress':
        return { color: 'bg-green-100 text-green-800', label: 'Em Curso', icon: PlayIcon };
      case 'completed':
        return { color: 'bg-gray-100 text-gray-800', label: 'Concluída', icon: CheckCircleIcon };
      case 'cancelled':
        return { color: 'bg-red-100 text-red-800', label: 'Cancelada', icon: AlertCircleIcon };
      default:
        return { color: 'bg-gray-100 text-gray-800', label: status, icon: ClockIcon };
    }
  };

  const statusInfo = getStatusInfo(session.status);
  const currentTime = new Date();
  const sessionStart = new Date(`${session.date}T${session.start_time}`);
  const sessionEnd = new Date(`${session.date}T${session.end_time}`);
  const isNow = currentTime >= sessionStart && currentTime <= sessionEnd;
  const isUpcoming = sessionStart > currentTime;

  return (
    <Pressable
      onPress={onPress}
      className="bg-white rounded-lg border border-gray-200 p-4 mb-3 shadow-sm hover:shadow-md transition-shadow"
      accessibilityLabel={`Sessão ${session.session_type} às ${session.start_time}`}
      accessibilityRole="button"
    >
      <VStack space="sm">
        {/* Header */}
        <HStack className="justify-between items-start">
          <VStack className="flex-1">
            <Text className="text-base font-semibold text-gray-900">
              {session.session_type} - {session.grade_level}
            </Text>
            <Text className="text-sm text-gray-600">
              {session.start_time} - {session.end_time} ({session.duration_hours}h)
            </Text>
          </VStack>
          <Badge className={statusInfo.color.split(' ')[0]}>
            <BadgeText className={statusInfo.color.split(' ')[1]}>{statusInfo.label}</BadgeText>
          </Badge>
        </HStack>

        {/* Students */}
        <HStack space="sm" className="items-center">
          <Icon as={UsersIcon} size="xs" className="text-gray-500" />
          <Text className="text-sm text-gray-600">
            {session.student_names?.length > 0
              ? session.student_names.join(', ')
              : `${session.student_count} estudante(s)`}
          </Text>
        </HStack>

        {/* Notes */}
        {session.notes && (
          <Text className="text-sm text-gray-600 italic" numberOfLines={2}>
            {session.notes}
          </Text>
        )}

        {/* Actions */}
        {showActions && (
          <HStack space="sm" className="items-center pt-2">
            {isNow && session.status === 'scheduled' && onStart && (
              <Button size="sm" className="bg-green-600" onPress={onStart}>
                <Icon as={PlayIcon} size="xs" className="text-white mr-1" />
                <ButtonText>Iniciar</ButtonText>
              </Button>
            )}
            {isUpcoming && (
              <Box className="flex-1">
                <Text className="text-xs text-blue-600 font-medium">
                  Começa em{' '}
                  {Math.ceil((sessionStart.getTime() - currentTime.getTime()) / (1000 * 60))} min
                </Text>
              </Box>
            )}
          </HStack>
        )}
      </VStack>
    </Pressable>
  );
};

const TodaysOverview: React.FC<TodaysOverviewProps> = ({
  sessions,
  onScheduleSession,
  onViewSession,
  onStartSession,
  isLoading = false,
}) => {
  const todaySessions = sessions.today || [];
  const upcomingSessions = sessions.upcoming?.slice(0, 3) || [];

  const todayStats = {
    total: todaySessions.length,
    completed: todaySessions.filter(s => s.status === 'completed').length,
    inProgress: todaySessions.filter(s => s.status === 'in_progress').length,
    upcoming: todaySessions.filter(s => s.status === 'scheduled').length,
  };

  return (
    <VStack space="md">
      {/* Stats Overview */}
      <Card variant="elevated" className="bg-white shadow-sm">
        <CardHeader>
          <HStack className="justify-between items-center">
            <Heading size="md" className="text-gray-900">
              Hoje
            </Heading>
            <Text className="text-sm text-gray-500">
              {new Date().toLocaleDateString('pt-PT', {
                weekday: 'long',
                day: '2-digit',
                month: 'long',
              })}
            </Text>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack space="md">
            {/* Quick Stats */}
            <HStack space="lg" className="justify-around">
              <VStack className="items-center">
                <Text className="text-2xl font-bold text-blue-600">{todayStats.total}</Text>
                <Text className="text-xs text-gray-500">Total</Text>
              </VStack>
              <VStack className="items-center">
                <Text className="text-2xl font-bold text-green-600">{todayStats.completed}</Text>
                <Text className="text-xs text-gray-500">Concluídas</Text>
              </VStack>
              <VStack className="items-center">
                <Text className="text-2xl font-bold text-orange-600">{todayStats.inProgress}</Text>
                <Text className="text-xs text-gray-500">Em Curso</Text>
              </VStack>
              <VStack className="items-center">
                <Text className="text-2xl font-bold text-blue-600">{todayStats.upcoming}</Text>
                <Text className="text-xs text-gray-500">Pendentes</Text>
              </VStack>
            </HStack>

            {/* Quick Action */}
            <Button
              onPress={onScheduleSession}
              className="bg-blue-600"
              accessibilityLabel="Agendar nova sessão"
            >
              <Icon as={CalendarIcon} size="sm" className="text-white mr-2" />
              <ButtonText>Agendar Nova Sessão</ButtonText>
            </Button>
          </VStack>
        </CardBody>
      </Card>

      {/* Today's Sessions */}
      {todaySessions.length > 0 && (
        <Card variant="elevated" className="bg-white shadow-sm">
          <CardHeader>
            <HStack className="justify-between items-center">
              <Heading size="md" className="text-gray-900">
                Sessões de Hoje
              </Heading>
              <Badge className="bg-blue-100">
                <BadgeText className="text-blue-800">{todaySessions.length}</BadgeText>
              </Badge>
            </HStack>
          </CardHeader>
          <CardBody>
            <VStack space="sm">
              {todaySessions.map(session => (
                <SessionCard
                  key={session.id}
                  session={session}
                  onPress={() => onViewSession(session.id)}
                  onStart={onStartSession ? () => onStartSession(session.id) : undefined}
                />
              ))}
            </VStack>
          </CardBody>
        </Card>
      )}

      {/* Upcoming Sessions */}
      {upcomingSessions.length > 0 && (
        <Card variant="elevated" className="bg-white shadow-sm">
          <CardHeader>
            <HStack className="justify-between items-center">
              <Heading size="md" className="text-gray-900">
                Próximas Sessões
              </Heading>
              <Badge className="bg-green-100">
                <BadgeText className="text-green-800">{upcomingSessions.length}</BadgeText>
              </Badge>
            </HStack>
          </CardHeader>
          <CardBody>
            <VStack space="sm">
              {upcomingSessions.map(session => (
                <SessionCard
                  key={session.id}
                  session={session}
                  onPress={() => onViewSession(session.id)}
                  showActions={false}
                />
              ))}
            </VStack>
          </CardBody>
        </Card>
      )}

      {/* Empty State */}
      {todaySessions.length === 0 && upcomingSessions.length === 0 && !isLoading && (
        <Card variant="elevated" className="bg-white shadow-sm">
          <CardBody>
            <VStack space="md" className="items-center py-8">
              <Icon as={CalendarIcon} size="xl" className="text-gray-400" />
              <VStack space="sm" className="items-center">
                <Text className="text-lg font-semibold text-gray-900">Sem Sessões Hoje</Text>
                <Text className="text-gray-600 text-center">
                  Que tal agendar uma sessão para hoje ou para os próximos dias?
                </Text>
              </VStack>
              <Button onPress={onScheduleSession} variant="solid">
                <Icon as={CalendarIcon} size="sm" className="text-white mr-2" />
                <ButtonText>Agendar Sessão</ButtonText>
              </Button>
            </VStack>
          </CardBody>
        </Card>
      )}
    </VStack>
  );
};

export default TodaysOverview;