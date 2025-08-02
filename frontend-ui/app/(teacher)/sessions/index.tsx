import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import { router } from 'expo-router';
import {
  CalendarIcon,
  ClockIcon,
  UsersIcon,
  RefreshCwIcon,
  AlertTriangleIcon,
  PlusIcon,
  FilterIcon,
  SearchIcon,
  ChevronRightIcon,
} from 'lucide-react-native';
import React, { useCallback, useState, useMemo } from 'react';
import { Pressable, RefreshControl } from 'react-native';

import MainLayout from '@/components/layouts/main-layout';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { ScrollView } from '@/components/ui/scroll-view';
import {
  Select,
  SelectTrigger,
  SelectInput,
  SelectIcon,
  SelectPortal,
  SelectBackdrop,
  SelectContent,
  SelectDragIndicatorWrapper,
  SelectDragIndicator,
  SelectItem,
} from '@/components/ui/select';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useTeacherDashboard } from '@/hooks/useTeacherDashboard';

const TeacherSessionsPage = () => {
  const { data, isLoading, error, refresh } = useTeacherDashboard();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterBy, setFilterBy] = useState<'all' | 'today' | 'upcoming' | 'completed'>('all');

  // Get all sessions from dashboard data
  const allSessions = useMemo(() => {
    if (!data?.sessions) return [];

    return [
      ...(data.sessions.today || []).map(s => ({ ...s, category: 'today' })),
      ...(data.sessions.upcoming || []).map(s => ({ ...s, category: 'upcoming' })),
      ...(data.sessions.recent_completed || []).map(s => ({ ...s, category: 'completed' })),
    ];
  }, [data?.sessions]);

  // Filter sessions
  const filteredSessions = useMemo(() => {
    let filtered = allSessions;

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      filtered = filtered.filter(
        session =>
          session.session_type.toLowerCase().includes(query) ||
          session.grade_level.toLowerCase().includes(query) ||
          (session.student_names &&
            session.student_names.some(name => name.toLowerCase().includes(query))) ||
          session.notes.toLowerCase().includes(query)
      );
    }

    // Apply category filter
    if (filterBy !== 'all') {
      filtered = filtered.filter(session => session.category === filterBy);
    }

    return filtered.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [allSessions, searchQuery, filterBy]);

  const handleScheduleSession = useCallback(() => {
    router.push('/calendar/book');
  }, []);

  const getStatusBadge = useCallback((session: any) => {
    switch (session.status) {
      case 'scheduled':
        return { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Agendada' };
      case 'completed':
        return { bg: 'bg-green-100', text: 'text-green-800', label: 'Concluída' };
      case 'cancelled':
        return { bg: 'bg-red-100', text: 'text-red-800', label: 'Cancelada' };
      default:
        return { bg: 'bg-gray-100', text: 'text-gray-800', label: session.status };
    }
  }, []);

  // Loading state
  if (isLoading && !data) {
    return (
      <MainLayout _title="Sessões">
        <Center className="flex-1 p-6">
          <VStack space="md" className="items-center">
            <Icon as={CalendarIcon} size="xl" className="text-blue-500" />
            <Text className="text-gray-600">Carregando sessões...</Text>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  // Error state
  if (error && !data) {
    return (
      <MainLayout _title="Sessões">
        <Center className="flex-1 p-6">
          <VStack space="lg" className="items-center max-w-md">
            <Icon as={AlertTriangleIcon} size="xl" className="text-red-500" />
            <VStack space="sm" className="items-center">
              <Heading size="lg" className="text-center text-gray-900">
                Erro ao Carregar Sessões
              </Heading>
              <Text className="text-center text-gray-600">{error}</Text>
            </VStack>
            <Button onPress={refresh} variant="solid">
              <Icon as={RefreshCwIcon} size="sm" className="text-white mr-2" />
              <ButtonText>Tentar Novamente</ButtonText>
            </Button>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  return (
    <MainLayout _title="Sessões">
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refresh} />}
        contentContainerStyle={{
          paddingBottom: isWeb ? 0 : 100,
          flexGrow: 1,
        }}
        className="flex-1 bg-gray-50"
      >
        <VStack className="p-6" space="lg">
          {/* Header */}
          <HStack className="justify-between items-center">
            <VStack>
              <Heading size="xl" className="text-gray-900">
                Sessões
              </Heading>
              <Text className="text-gray-600">Gerencie as suas sessões de ensino</Text>
            </VStack>

            <Button
              onPress={handleScheduleSession}
              className="bg-blue-600"
              accessibilityLabel="Agendar nova sessão"
            >
              <Icon as={PlusIcon} size="sm" className="text-white mr-2" />
              <ButtonText>Nova Sessão</ButtonText>
            </Button>
          </HStack>

          {/* Error Alert */}
          {error && data && (
            <Box className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <HStack space="sm" className="items-start">
                <Icon as={AlertTriangleIcon} size="sm" className="text-yellow-600 mt-0.5" />
                <VStack className="flex-1">
                  <Text className="font-medium text-yellow-900">
                    Dados parcialmente desatualizados
                  </Text>
                  <Text className="text-sm text-yellow-700">{error}</Text>
                </VStack>
                <Pressable onPress={refresh}>
                  <Text className="text-sm font-medium text-yellow-600">Atualizar</Text>
                </Pressable>
              </HStack>
            </Box>
          )}

          {/* Quick Stats */}
          {data?.quick_stats && (
            <HStack space="md" className="flex-wrap">
              <Card variant="elevated" className="flex-1 bg-white shadow-sm">
                <CardBody className="items-center">
                  <Icon as={CalendarIcon} size="lg" className="text-blue-600 mb-2" />
                  <Text className="text-2xl font-bold text-gray-900">
                    {data.quick_stats.sessions_today}
                  </Text>
                  <Text className="text-sm text-gray-600">Hoje</Text>
                </CardBody>
              </Card>

              <Card variant="elevated" className="flex-1 bg-white shadow-sm">
                <CardBody className="items-center">
                  <Icon as={ClockIcon} size="lg" className="text-green-600 mb-2" />
                  <Text className="text-2xl font-bold text-gray-900">
                    {data.quick_stats.sessions_this_week}
                  </Text>
                  <Text className="text-sm text-gray-600">Esta Semana</Text>
                </CardBody>
              </Card>
            </HStack>
          )}

          {/* Search and Filter */}
          <VStack space="sm">
            <HStack space="sm" className="items-center">
              <Box className="flex-1 relative">
                <Input className="pl-10">
                  <InputField
                    placeholder="Pesquisar sessões..."
                    value={searchQuery}
                    onChangeText={setSearchQuery}
                    accessibilityLabel="Pesquisar sessões"
                  />
                </Input>
                <Box className="absolute left-3 top-1/2 transform -translate-y-1/2">
                  <Icon as={SearchIcon} size="sm" className="text-gray-400" />
                </Box>
              </Box>

              <Select
                selectedValue={filterBy}
                onValueChange={value => setFilterBy(value as typeof filterBy)}
              >
                <SelectTrigger variant="outline" size="md">
                  <SelectInput placeholder="Filtrar" />
                  <SelectIcon as={FilterIcon} />
                </SelectTrigger>
                <SelectPortal>
                  <SelectBackdrop />
                  <SelectContent>
                    <SelectDragIndicatorWrapper>
                      <SelectDragIndicator />
                    </SelectDragIndicatorWrapper>
                    <SelectItem label="Todas" value="all" />
                    <SelectItem label="Hoje" value="today" />
                    <SelectItem label="Próximas" value="upcoming" />
                    <SelectItem label="Concluídas" value="completed" />
                  </SelectContent>
                </SelectPortal>
              </Select>
            </HStack>
          </VStack>

          {/* Sessions List */}
          <VStack space="sm">
            {filteredSessions.length > 0 ? (
              filteredSessions.map(session => {
                const status = getStatusBadge(session);

                return (
                  <Card key={session.id} variant="elevated" className="bg-white shadow-sm">
                    <CardBody>
                      <VStack space="md">
                        <HStack className="justify-between items-start">
                          <VStack className="flex-1">
                            <HStack space="sm" className="items-center">
                              <Text className="text-base font-semibold text-gray-900">
                                {session.session_type}
                              </Text>
                              <Badge className={status.bg}>
                                <BadgeText className={status.text}>{status.label}</BadgeText>
                              </Badge>
                            </HStack>

                            <Text className="text-sm text-gray-600">{session.grade_level}</Text>
                          </VStack>

                          <VStack className="items-end">
                            <Text className="text-sm font-medium text-gray-900">
                              {new Date(session.date).toLocaleDateString('pt-PT')}
                            </Text>
                            <Text className="text-sm text-gray-500">
                              {session.start_time} - {session.end_time}
                            </Text>
                          </VStack>
                        </HStack>

                        <HStack space="sm" className="items-center">
                          <Icon as={UsersIcon} size="sm" className="text-gray-400" />
                          <Text className="text-sm text-gray-600">
                            {session.student_names?.join(', ') ||
                              `${session.student_count} estudante(s)`}
                          </Text>
                        </HStack>

                        {session.notes && (
                          <Text className="text-sm text-gray-600 bg-gray-50 p-2 rounded">
                            {session.notes}
                          </Text>
                        )}

                        <HStack className="justify-between items-center">
                          <Text className="text-sm text-gray-500">
                            Duração: {session.duration_hours}h
                          </Text>

                          <Pressable
                            className="flex-row items-center"
                            onPress={() => {
                              // Navigate to session details
                              console.log('Navigate to session details:', session.id);
                            }}
                          >
                            <Text className="text-sm font-medium text-blue-600 mr-1">
                              Ver Detalhes
                            </Text>
                            <Icon as={ChevronRightIcon} size="sm" className="text-blue-600" />
                          </Pressable>
                        </HStack>
                      </VStack>
                    </CardBody>
                  </Card>
                );
              })
            ) : (
              <Center className="py-16">
                <VStack space="md" className="items-center max-w-md">
                  <Icon as={CalendarIcon} size="xl" className="text-gray-400" />
                  <VStack space="sm" className="items-center">
                    <Heading size="lg" className="text-center text-gray-900">
                      {searchQuery || filterBy !== 'all'
                        ? 'Nenhuma sessão encontrada'
                        : 'Nenhuma sessão agendada'}
                    </Heading>
                    <Text className="text-center text-gray-600">
                      {searchQuery || filterBy !== 'all'
                        ? 'Ajuste os filtros para ver mais resultados.'
                        : 'Agende a sua primeira sessão de ensino.'}
                    </Text>
                  </VStack>
                  {!searchQuery && filterBy === 'all' && (
                    <Button onPress={handleScheduleSession} variant="solid">
                      <Icon as={PlusIcon} size="sm" className="text-white mr-2" />
                      <ButtonText>Agendar Sessão</ButtonText>
                    </Button>
                  )}
                </VStack>
              </Center>
            )}
          </VStack>
        </VStack>
      </ScrollView>
    </MainLayout>
  );
};

export default TeacherSessionsPage;
