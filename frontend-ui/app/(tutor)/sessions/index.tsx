import { router } from 'expo-router';
import { 
  CalendarIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  PlayIcon,
  PauseIcon,
  MoreVerticalIcon,
  UserIcon,
  FilterIcon,
  PlusIcon,
  DollarSignIcon
} from 'lucide-react-native';
import React, { useState, useMemo } from 'react';
import { Alert } from 'react-native';

import MainLayout from '@/components/layouts/main-layout';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Menu, MenuItem, MenuItemLabel } from '@/components/ui/menu';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface Session {
  id: number;
  studentName: string;
  subject: string;
  date: string;
  time: string;
  duration: number;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled' | 'missed';
  price: number;
  notes?: string;
  rating?: number;
  studentId: number;
}

const TutorSessionsPage = () => {
  const [filterStatus, setFilterStatus] = useState<'all' | 'scheduled' | 'completed' | 'cancelled'>('all');
  const [viewMode, setViewMode] = useState<'list' | 'calendar'>('list');

  // Mock session data - in real app, fetch from API
  const mockSessions: Session[] = useMemo(() => [
    {
      id: 1,
      studentName: 'Ana Silva',
      subject: 'Matemática',
      date: '2025-08-01',
      time: '14:00',
      duration: 60,
      status: 'scheduled',
      price: 25,
      studentId: 1,
    },
    {
      id: 2,
      studentName: 'João Santos',
      subject: 'Física',
      date: '2025-08-01',
      time: '16:00',
      duration: 90,
      status: 'scheduled',
      price: 35,
      studentId: 2,
    },
    {
      id: 3,
      studentName: 'Maria Costa',
      subject: 'Matemática',
      date: '2025-07-31',
      time: '15:00',
      duration: 60,
      status: 'completed',
      price: 25,
      rating: 5,
      notes: 'Excelente sessão. Estudante mostrou grande progresso.',
      studentId: 3,
    },
    {
      id: 4,
      studentName: 'Pedro Oliveira',
      subject: 'Química',
      date: '2025-07-30',
      time: '10:00',
      duration: 60,
      status: 'completed',
      price: 30,
      rating: 4,
      notes: 'Boa compreensão dos conceitos básicos.',
      studentId: 4,
    },
    {
      id: 5,
      studentName: 'Sofia Ferreira',
      subject: 'Matemática',
      date: '2025-07-29',
      time: '17:00',
      duration: 60,
      status: 'missed',
      price: 25,
      studentId: 5,
    },
    {
      id: 6,
      studentName: 'Rui Pereira',
      subject: 'Física',
      date: '2025-07-28',
      time: '11:00',
      duration: 60,
      status: 'cancelled',
      price: 25,
      notes: 'Cancelado pelo estudante com 2h de antecedência.',
      studentId: 6,
    },
  ], []);

  // Filter sessions based on status
  const filteredSessions = useMemo(() => {
    if (filterStatus === 'all') return mockSessions;
    return mockSessions.filter(session => session.status === filterStatus);
  }, [mockSessions, filterStatus]);

  // Group sessions by date for better organization
  const sessionsByDate = useMemo(() => {
    const grouped: { [date: string]: Session[] } = {};
    filteredSessions
      .sort((a, b) => new Date(b.date + ' ' + b.time).getTime() - new Date(a.date + ' ' + a.time).getTime())
      .forEach(session => {
        const date = session.date;
        if (!grouped[date]) {
          grouped[date] = [];
        }
        grouped[date].push(session);
      });
    return grouped;
  }, [filteredSessions]);

  // Calculate stats
  const stats = useMemo(() => {
    const total = mockSessions.length;
    const completed = mockSessions.filter(s => s.status === 'completed').length;
    const scheduled = mockSessions.filter(s => s.status === 'scheduled').length;
    const revenue = mockSessions
      .filter(s => s.status === 'completed')
      .reduce((acc, s) => acc + s.price, 0);
    const averageRating = mockSessions
      .filter(s => s.rating)
      .reduce((acc, s) => acc + (s.rating || 0), 0) / mockSessions.filter(s => s.rating).length || 0;

    return { total, completed, scheduled, revenue, averageRating };
  }, [mockSessions]);

  const handleSessionAction = (session: Session, action: 'start' | 'complete' | 'cancel' | 'reschedule' | 'notes') => {
    switch (action) {
      case 'start':
        Alert.alert(
          'Iniciar Sessão',
          `Iniciar sessão com ${session.studentName}?`,
          [
            { text: 'Cancelar', style: 'cancel' },
            { text: 'Iniciar', onPress: () => console.log('Start session:', session.id) }
          ]
        );
        break;
      case 'complete':
        Alert.alert(
          'Concluir Sessão',
          `Marcar sessão com ${session.studentName} como concluída?`,
          [
            { text: 'Cancelar', style: 'cancel' },
            { text: 'Concluir', onPress: () => console.log('Complete session:', session.id) }
          ]
        );
        break;
      case 'cancel':
        Alert.alert(
          'Cancelar Sessão',
          `Cancelar sessão com ${session.studentName}?`,
          [
            { text: 'Não', style: 'cancel' },
            { text: 'Sim, Cancelar', style: 'destructive', onPress: () => console.log('Cancel session:', session.id) }
          ]
        );
        break;
      case 'reschedule':
        router.push(`/calendar/book?reschedule=${session.id}`);
        break;
      case 'notes':
        Alert.alert(
          'Notas da Sessão',
          session.notes || 'Nenhuma nota disponível para esta sessão.',
          [{ text: 'OK' }]
        );
        break;
    }
  };

  const getStatusIcon = (status: Session['status']) => {
    switch (status) {
      case 'scheduled':
        return ClockIcon;
      case 'in_progress':
        return PlayIcon;
      case 'completed':
        return CheckCircleIcon;
      case 'cancelled':
      case 'missed':
        return XCircleIcon;
      default:
        return ClockIcon;
    }
  };

  const getStatusColor = (status: Session['status']) => {
    switch (status) {
      case 'scheduled':
        return 'text-blue-600';
      case 'in_progress':
        return 'text-green-600';
      case 'completed':
        return 'text-green-600';
      case 'cancelled':
        return 'text-red-600';
      case 'missed':
        return 'text-orange-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusLabel = (status: Session['status']) => {
    switch (status) {
      case 'scheduled':
        return 'Agendada';
      case 'in_progress':
        return 'Em Andamento';
      case 'completed':
        return 'Concluída';
      case 'cancelled':
        return 'Cancelada';
      case 'missed':
        return 'Faltou';
      default:
        return status;
    }
  };

  return (
    <MainLayout _title="Gestão de Sessões">
      <ScrollView 
        className="flex-1 bg-gray-50"
        contentContainerStyle={{ paddingBottom: 100 }}
      >
        <VStack className="p-6" space="lg">
          {/* Header */}
          <VStack space="sm">
            <HStack className="justify-between items-center">
              <VStack>
                <Heading size="xl" className="text-gray-900">
                  Gestão de Sessões
                </Heading>
                <Text className="text-gray-600">
                  {stats.total} sessões • {stats.scheduled} agendadas
                </Text>
              </VStack>
              <Button 
                variant="solid" 
                onPress={() => router.push('/calendar/book')}
              >
                <Icon as={PlusIcon} size="sm" className="text-white mr-1" />
                <ButtonText>Nova Sessão</ButtonText>
              </Button>
            </HStack>
          </VStack>

          {/* Stats Overview */}
          <HStack space="sm">
            <Card variant="elevated" className="bg-white shadow-sm flex-1">
              <CardBody>
                <VStack space="xs" className="items-center">
                  <Icon as={CalendarIcon} size="sm" className="text-blue-600" />
                  <Text className="text-lg font-bold text-gray-900">
                    {stats.scheduled}
                  </Text>
                  <Text className="text-xs text-gray-600">Agendadas</Text>
                </VStack>
              </CardBody>
            </Card>

            <Card variant="elevated" className="bg-white shadow-sm flex-1">
              <CardBody>
                <VStack space="xs" className="items-center">
                  <Icon as={CheckCircleIcon} size="sm" className="text-green-600" />
                  <Text className="text-lg font-bold text-gray-900">
                    {stats.completed}
                  </Text>
                  <Text className="text-xs text-gray-600">Concluídas</Text>
                </VStack>
              </CardBody>
            </Card>

            <Card variant="elevated" className="bg-white shadow-sm flex-1">
              <CardBody>
                <VStack space="xs" className="items-center">
                  <Icon as={DollarSignIcon} size="sm" className="text-green-600" />
                  <Text className="text-lg font-bold text-gray-900">
                    €{stats.revenue}
                  </Text>
                  <Text className="text-xs text-gray-600">Receita</Text>
                </VStack>
              </CardBody>
            </Card>
          </HStack>

          {/* Filters */}
          <HStack space="sm" className="items-center">
            <Menu
              trigger={({ ...triggerProps }) => (
                <Pressable {...triggerProps} className="flex-row items-center space-x-2 p-3 bg-white border border-gray-300 rounded-lg">
                  <Icon as={FilterIcon} size="sm" className="text-gray-600" />
                  <Text className="text-sm text-gray-600">
                    {filterStatus === 'all' ? 'Todas' : 
                     filterStatus === 'scheduled' ? 'Agendadas' :
                     filterStatus === 'completed' ? 'Concluídas' : 'Canceladas'}
                  </Text>
                </Pressable>
              )}
            >
              <MenuItem onPress={() => setFilterStatus('all')}>
                <MenuItemLabel>Todas as Sessões</MenuItemLabel>
              </MenuItem>
              <MenuItem onPress={() => setFilterStatus('scheduled')}>
                <MenuItemLabel>Agendadas</MenuItemLabel>
              </MenuItem>
              <MenuItem onPress={() => setFilterStatus('completed')}>
                <MenuItemLabel>Concluídas</MenuItemLabel>
              </MenuItem>
              <MenuItem onPress={() => setFilterStatus('cancelled')}>
                <MenuItemLabel>Canceladas</MenuItemLabel>
              </MenuItem>
            </Menu>
            
            {filterStatus !== 'all' && (
              <Pressable onPress={() => setFilterStatus('all')}>
                <Text className="text-sm text-blue-600">Limpar Filtro</Text>
              </Pressable>
            )}
          </HStack>

          {/* Sessions List */}
          {filteredSessions.length === 0 ? (
            <Card variant="elevated" className="bg-white shadow-sm">
              <CardBody>
                <VStack space="md" className="items-center py-8">
                  <Icon as={CalendarIcon} size="xl" className="text-gray-300" />
                  <Text className="text-lg font-medium text-gray-600">
                    Nenhuma sessão encontrada
                  </Text>
                  <Text className="text-sm text-gray-500 text-center max-w-sm">
                    {filterStatus === 'all' 
                      ? 'Ainda não tem sessões agendadas. Comece criando uma nova sessão.'
                      : `Nenhuma sessão ${getStatusLabel(filterStatus as Session['status']).toLowerCase()} encontrada.`
                    }
                  </Text>
                  <Button 
                    onPress={() => router.push('/calendar/book')}
                    variant="solid"
                  >
                    <ButtonText>Agendar Sessão</ButtonText>
                  </Button>
                </VStack>
              </CardBody>
            </Card>
          ) : (
            <VStack space="md">
              {Object.entries(sessionsByDate).map(([date, sessions]) => (
                <VStack key={date} space="sm">
                  <Text className="text-sm font-semibold text-gray-700">
                    {new Date(date).toLocaleDateString('pt-PT', {
                      weekday: 'long',
                      day: '2-digit',
                      month: 'long',
                      year: 'numeric'
                    })}
                  </Text>
                  
                  <VStack space="sm">
                    {sessions.map((session) => (
                      <Card key={session.id} variant="elevated" className="bg-white shadow-sm">
                        <CardBody>
                          <VStack space="sm">
                            <HStack className="justify-between items-start">
                              <HStack space="sm" className="items-center flex-1">
                                <Icon 
                                  as={getStatusIcon(session.status)} 
                                  size="sm" 
                                  className={getStatusColor(session.status)} 
                                />
                                <VStack className="flex-1">
                                  <Text className="text-lg font-semibold text-gray-900">
                                    {session.studentName}
                                  </Text>
                                  <Text className="text-sm text-gray-600">
                                    {session.subject} • {session.time} • {session.duration}min
                                  </Text>
                                  <HStack space="xs" className="items-center mt-1">
                                    <Badge 
                                      variant="outline"
                                      className={
                                        session.status === 'completed' ? 'bg-green-50' :
                                        session.status === 'scheduled' ? 'bg-blue-50' :
                                        session.status === 'cancelled' || session.status === 'missed' ? 'bg-red-50' :
                                        'bg-gray-50'
                                      }
                                    >
                                      <BadgeText className={getStatusColor(session.status)}>
                                        {getStatusLabel(session.status)}
                                      </BadgeText>
                                    </Badge>
                                    <Text className="text-sm font-semibold text-green-600">
                                      €{session.price}
                                    </Text>
                                  </HStack>
                                </VStack>
                              </HStack>
                              
                              <Menu
                                trigger={({ ...triggerProps }) => (
                                  <Pressable {...triggerProps} className="p-2">
                                    <Icon as={MoreVerticalIcon} size="sm" className="text-gray-400" />
                                  </Pressable>
                                )}
                              >
                                {session.status === 'scheduled' && (
                                  <>
                                    <MenuItem onPress={() => handleSessionAction(session, 'start')}>
                                      <Icon as={PlayIcon} size="sm" className="text-green-600 mr-2" />
                                      <MenuItemLabel>Iniciar Sessão</MenuItemLabel>
                                    </MenuItem>
                                    <MenuItem onPress={() => handleSessionAction(session, 'reschedule')}>
                                      <Icon as={CalendarIcon} size="sm" className="text-blue-600 mr-2" />
                                      <MenuItemLabel>Reagendar</MenuItemLabel>
                                    </MenuItem>
                                    <MenuItem onPress={() => handleSessionAction(session, 'cancel')}>
                                      <Icon as={XCircleIcon} size="sm" className="text-red-600 mr-2" />
                                      <MenuItemLabel>Cancelar</MenuItemLabel>
                                    </MenuItem>
                                  </>
                                )}
                                {session.status === 'in_progress' && (
                                  <MenuItem onPress={() => handleSessionAction(session, 'complete')}>
                                    <Icon as={CheckCircleIcon} size="sm" className="text-green-600 mr-2" />
                                    <MenuItemLabel>Concluir</MenuItemLabel>
                                  </MenuItem>
                                )}
                                <MenuItem onPress={() => router.push(`/(tutor)/students/${session.studentId}`)}>
                                  <Icon as={UserIcon} size="sm" className="text-blue-600 mr-2" />
                                  <MenuItemLabel>Ver Estudante</MenuItemLabel>
                                </MenuItem>
                                {session.notes && (
                                  <MenuItem onPress={() => handleSessionAction(session, 'notes')}>
                                    <MenuItemLabel>Ver Notas</MenuItemLabel>
                                  </MenuItem>
                                )}
                              </Menu>
                            </HStack>

                            {/* Rating and Notes Preview */}
                            {(session.rating || session.notes) && (
                              <VStack space="xs" className="bg-gray-50 rounded-lg p-3">
                                {session.rating && (
                                  <HStack space="xs" className="items-center">
                                    <Text className="text-xs text-gray-600">Avaliação:</Text>
                                    <HStack space="xs" className="items-center">
                                      {[...Array(session.rating)].map((_, i) => (
                                        <Icon key={i} as={CheckCircleIcon} size="xs" className="text-yellow-500" />
                                      ))}
                                      <Text className="text-xs text-gray-600">({session.rating}/5)</Text>
                                    </HStack>
                                  </HStack>
                                )}
                                {session.notes && (
                                  <Text className="text-xs text-gray-600">
                                    {session.notes.length > 80 
                                      ? `${session.notes.substring(0, 80)}...` 
                                      : session.notes
                                    }
                                  </Text>
                                )}
                              </VStack>
                            )}

                            {/* Quick Actions */}
                            <HStack space="xs">
                              {session.status === 'scheduled' && (
                                <>
                                  <Button 
                                    size="sm" 
                                    variant="solid" 
                                    className="flex-1 bg-green-600"
                                    onPress={() => handleSessionAction(session, 'start')}
                                  >
                                    <Icon as={PlayIcon} size="xs" className="text-white mr-1" />
                                    <ButtonText>Iniciar</ButtonText>
                                  </Button>
                                  <Button 
                                    size="sm" 
                                    variant="outline" 
                                    className="flex-1"
                                    onPress={() => handleSessionAction(session, 'reschedule')}
                                  >
                                    <Icon as={CalendarIcon} size="xs" className="text-blue-600 mr-1" />
                                    <ButtonText className="text-blue-600">Reagendar</ButtonText>
                                  </Button>
                                </>
                              )}
                              {session.status === 'completed' && (
                                <Button 
                                  size="sm" 
                                  variant="outline" 
                                  className="flex-1"
                                  onPress={() => router.push(`/(tutor)/students/${session.studentId}`)}
                                >
                                  <Icon as={UserIcon} size="xs" className="text-blue-600 mr-1" />
                                  <ButtonText className="text-blue-600">Ver Estudante</ButtonText>
                                </Button>
                              )}
                            </HStack>
                          </VStack>
                        </CardBody>
                      </Card>
                    ))}
                  </VStack>
                </VStack>
              ))}
            </VStack>
          )}
        </VStack>
      </ScrollView>
    </MainLayout>
  );
};

export default TutorSessionsPage;