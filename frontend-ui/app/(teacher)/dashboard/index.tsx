import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import { router } from 'expo-router';
import {
  AlertTriangleIcon,
  RefreshCwIcon,
  WifiOffIcon,
  GraduationCapIcon,
  CalendarIcon,
  UsersIcon,
  TrendingUpIcon,
  DollarSignIcon,
  BookOpenIcon,
  ClockIcon,
  AwardIcon,
  MessageSquareIcon,
  SearchIcon,
  FilterIcon,
  PlusIcon,
  BarChart3Icon,
} from 'lucide-react-native';
import React, { useCallback, useMemo, useState } from 'react';
import { Pressable, RefreshControl } from 'react-native';

import { useUserProfile } from '@/api/auth';
import MainLayout from '@/components/layouts/MainLayout';
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
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useTeacherDashboard } from '@/hooks/useTeacherDashboard';

const TeacherDashboard = () => {
  const { userProfile } = useUserProfile();
  const { data, isLoading, error, refresh, lastUpdated } = useTeacherDashboard();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedView, setSelectedView] = useState<'overview' | 'students' | 'sessions'>(
    'overview'
  );

  // Quick action handlers
  const handleScheduleSession = useCallback(() => {
    router.push('/calendar/book');
  }, []);

  const handleViewAllStudents = useCallback(() => {
    router.push('/(teacher)/students');
  }, []);

  const handleViewAnalytics = useCallback(() => {
    router.push('/(teacher)/analytics');
  }, []);

  const handleViewSessions = useCallback(() => {
    router.push('/(teacher)/sessions');
  }, []);

  const handleViewProfile = useCallback(() => {
    router.push('/(teacher)/profile');
  }, []);

  // Welcome message
  const welcomeMessage = useMemo(() => {
    const name = userProfile?.name?.split(' ')[0] || 'Professor';
    const currentHour = new Date().getHours();

    if (currentHour < 12) {
      return `Bom dia, ${name}!`;
    } else if (currentHour < 18) {
      return `Boa tarde, ${name}!`;
    } else {
      return `Boa noite, ${name}!`;
    }
  }, [userProfile]);

  // Filter students based on search
  const filteredStudents = useMemo(() => {
    if (!data?.students || !searchQuery.trim()) {
      return data?.students || [];
    }

    const query = searchQuery.toLowerCase().trim();
    return data.students.filter(
      student =>
        student.name.toLowerCase().includes(query) || student.email.toLowerCase().includes(query)
    );
  }, [data?.students, searchQuery]);

  // Loading state
  if (isLoading && !data) {
    return (
      <MainLayout _title="Dashboard do Professor">
        <Center className="flex-1 p-6">
          <VStack space="md" className="items-center">
            <Icon as={GraduationCapIcon} size="xl" className="text-blue-500" />
            <Text className="text-gray-600">Carregando dashboard...</Text>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  // Error state
  if (error && !data) {
    return (
      <MainLayout _title="Dashboard do Professor">
        <Center className="flex-1 p-6">
          <VStack space="lg" className="items-center max-w-md">
            <Icon as={AlertTriangleIcon} size="xl" className="text-red-500" />
            <VStack space="sm" className="items-center">
              <Heading size="lg" className="text-center text-gray-900">
                Erro ao Carregar Dashboard
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
    <MainLayout _title="Dashboard do Professor">
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
          {/* Header Section */}
          <VStack space="sm">
            <HStack className="justify-between items-start">
              <VStack space="xs" className="flex-1">
                <Heading size="xl" className="text-gray-900">
                  {welcomeMessage}
                </Heading>

                <Text className="text-gray-600">
                  {data?.teacher_info?.schools?.[0]?.name || 'Professor'}
                </Text>
              </VStack>

              <HStack space="xs" className="items-center">
                <Pressable
                  onPress={refresh}
                  disabled={isLoading}
                  className="p-2 rounded-md bg-gray-100 hover:bg-gray-200"
                  accessibilityLabel="Atualizar dashboard"
                  accessibilityRole="button"
                >
                  <Icon
                    as={RefreshCwIcon}
                    size="sm"
                    className={`text-gray-600 ${isLoading ? 'animate-spin' : ''}`}
                  />
                </Pressable>
              </HStack>
            </HStack>

            <Text className="text-sm text-gray-500">
              {new Date().toLocaleDateString('pt-PT', {
                weekday: 'long',
                day: '2-digit',
                month: 'long',
                year: 'numeric',
              })}
            </Text>
          </VStack>

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

          {/* Quick Stats Overview */}
          {data?.quick_stats && (
            <Box className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-6 shadow-lg">
              <VStack space="md">
                <Text className="text-white font-semibold text-lg">Resumo Rápido</Text>
                <HStack space="lg" className="flex-wrap">
                  <VStack className="items-center">
                    <Text className="text-2xl font-bold text-white">
                      {data.quick_stats.total_students}
                    </Text>
                    <Text className="text-blue-100 text-sm">Estudantes</Text>
                  </VStack>
                  <VStack className="items-center">
                    <Text className="text-2xl font-bold text-white">
                      {data.quick_stats.sessions_today}
                    </Text>
                    <Text className="text-blue-100 text-sm">Hoje</Text>
                  </VStack>
                  <VStack className="items-center">
                    <Text className="text-2xl font-bold text-white">
                      {data.quick_stats.sessions_this_week}
                    </Text>
                    <Text className="text-blue-100 text-sm">Esta Semana</Text>
                  </VStack>
                  <VStack className="items-center">
                    <Text className="text-2xl font-bold text-white">
                      {Math.round(data.quick_stats.completion_rate)}%
                    </Text>
                    <Text className="text-blue-100 text-sm">Progresso</Text>
                  </VStack>
                </HStack>
              </VStack>
            </Box>
          )}

          {/* Quick Actions Panel */}
          <Card variant="elevated" className="bg-white shadow-sm">
            <CardHeader>
              <Heading size="md" className="text-gray-900">
                Ações Rápidas
              </Heading>
            </CardHeader>
            <CardBody>
              <VStack space="sm">
                <HStack space="sm">
                  <Button
                    className="flex-1 bg-blue-600"
                    onPress={handleScheduleSession}
                    accessibilityLabel="Agendar nova sessão"
                  >
                    <Icon as={CalendarIcon} size="sm" className="text-white mr-2" />
                    <ButtonText>Agendar Sessão</ButtonText>
                  </Button>
                  <Button
                    className="flex-1 bg-green-600"
                    onPress={handleViewAllStudents}
                    accessibilityLabel="Ver todos os estudantes"
                  >
                    <Icon as={UsersIcon} size="sm" className="text-white mr-2" />
                    <ButtonText>Estudantes</ButtonText>
                  </Button>
                </HStack>
                <HStack space="sm">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onPress={handleViewAnalytics}
                    accessibilityLabel="Ver analytics detalhados"
                  >
                    <Icon as={TrendingUpIcon} size="sm" className="text-blue-600 mr-2" />
                    <ButtonText className="text-blue-600">Analytics</ButtonText>
                  </Button>
                  <Button
                    variant="outline"
                    className="flex-1"
                    onPress={handleViewSessions}
                    accessibilityLabel="Gerenciar sessões"
                  >
                    <Icon as={ClockIcon} size="sm" className="text-green-600 mr-2" />
                    <ButtonText className="text-green-600">Sessões</ButtonText>
                  </Button>
                </HStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Today's Sessions */}
          {data?.sessions?.today && data.sessions.today.length > 0 && (
            <Card variant="elevated" className="bg-white shadow-sm">
              <CardHeader>
                <HStack className="justify-between items-center">
                  <Heading size="md" className="text-gray-900">
                    Sessões de Hoje
                  </Heading>
                  <Badge className="bg-blue-100">
                    <BadgeText className="text-blue-800">{data.sessions.today.length}</BadgeText>
                  </Badge>
                </HStack>
              </CardHeader>
              <CardBody>
                <VStack space="sm">
                  {data.sessions.today.slice(0, 3).map(session => (
                    <HStack
                      key={session.id}
                      space="sm"
                      className="items-center py-2 border-b border-gray-100 last:border-b-0"
                    >
                      <VStack className="w-12 h-12 bg-blue-100 rounded-lg items-center justify-center">
                        <Text className="text-xs font-bold text-blue-600">
                          {session.start_time.substring(0, 5)}
                        </Text>
                      </VStack>
                      <VStack className="flex-1">
                        <Text className="text-sm font-medium text-gray-900">
                          {session.session_type} - {session.grade_level}
                        </Text>
                        <Text className="text-xs text-gray-500">
                          {session.student_names?.join(', ') ||
                            `${session.student_count} estudante(s)`}
                        </Text>
                      </VStack>
                      <VStack className="items-end">
                        <Badge
                          className={`${
                            session.status === 'scheduled'
                              ? 'bg-yellow-100'
                              : session.status === 'completed'
                              ? 'bg-green-100'
                              : 'bg-gray-100'
                          }`}
                        >
                          <BadgeText
                            className={`${
                              session.status === 'scheduled'
                                ? 'text-yellow-800'
                                : session.status === 'completed'
                                ? 'text-green-800'
                                : 'text-gray-800'
                            }`}
                          >
                            {session.status === 'scheduled'
                              ? 'Agendada'
                              : session.status === 'completed'
                              ? 'Concluída'
                              : session.status}
                          </BadgeText>
                        </Badge>
                      </VStack>
                    </HStack>
                  ))}
                  {data.sessions.today.length > 3 && (
                    <Pressable onPress={handleViewSessions} className="pt-2">
                      <Text className="text-sm font-medium text-blue-600 text-center">
                        Ver todas as sessões de hoje ({data.sessions.today.length})
                      </Text>
                    </Pressable>
                  )}
                </VStack>
              </CardBody>
            </Card>
          )}

          {/* Student Roster Preview */}
          <Card variant="elevated" className="bg-white shadow-sm">
            <CardHeader>
              <HStack className="justify-between items-center">
                <Heading size="md" className="text-gray-900">
                  Estudantes
                </Heading>
                <Badge className="bg-green-100">
                  <BadgeText className="text-green-800">{data?.students?.length || 0}</BadgeText>
                </Badge>
              </HStack>
            </CardHeader>
            <CardBody>
              <VStack space="md">
                {/* Search Input */}
                <HStack space="sm" className="items-center">
                  <Box className="flex-1 relative">
                    <Input className="pl-10">
                      <InputField
                        placeholder="Pesquisar estudante..."
                        value={searchQuery}
                        onChangeText={setSearchQuery}
                        accessibilityLabel="Pesquisar estudantes"
                      />
                    </Input>
                    <Box className="absolute left-3 top-1/2 transform -translate-y-1/2">
                      <Icon as={SearchIcon} size="sm" className="text-gray-400" />
                    </Box>
                  </Box>
                </HStack>

                {/* Students List */}
                <VStack space="sm">
                  {filteredStudents.slice(0, 5).map(student => (
                    <Pressable
                      key={student.id}
                      onPress={() => router.push(`/(teacher)/students/${student.id}`)}
                      className="py-2 border-b border-gray-100 last:border-b-0"
                      accessibilityLabel={`Ver detalhes de ${student.name}`}
                      accessibilityRole="button"
                    >
                      <HStack space="sm" className="items-center">
                        <VStack className="w-10 h-10 bg-blue-100 rounded-full items-center justify-center">
                          <Text className="text-sm font-bold text-blue-600">
                            {student.name.charAt(0).toUpperCase()}
                          </Text>
                        </VStack>
                        <VStack className="flex-1">
                          <Text className="text-sm font-medium text-gray-900">{student.name}</Text>
                          <Text className="text-xs text-gray-500">
                            {student.last_session_date
                              ? `Última aula: ${new Date(
                                  student.last_session_date
                                ).toLocaleDateString('pt-PT')}`
                              : 'Primeira aula pendente'}
                          </Text>
                        </VStack>
                        <VStack className="items-end">
                          <Text className="text-xs font-semibold text-green-600">
                            {Math.round(student.completion_percentage)}%
                          </Text>
                          <Box
                            className="w-16 h-1 bg-gray-200 rounded-full overflow-hidden"
                            accessibilityLabel={`Progresso: ${Math.round(
                              student.completion_percentage
                            )}%`}
                          >
                            <Box
                              className="h-full bg-green-500 rounded-full"
                              style={{ width: `${Math.min(student.completion_percentage, 100)}%` }}
                            />
                          </Box>
                        </VStack>
                      </HStack>
                    </Pressable>
                  ))}

                  {data?.students && data.students.length > 5 && (
                    <Pressable onPress={handleViewAllStudents} className="pt-2">
                      <Text className="text-sm font-medium text-blue-600 text-center">
                        Ver todos os estudantes ({data.students.length})
                      </Text>
                    </Pressable>
                  )}

                  {filteredStudents.length === 0 && searchQuery && (
                    <Center className="py-8">
                      <VStack space="sm" className="items-center">
                        <Icon as={SearchIcon} size="lg" className="text-gray-400" />
                        <Text className="text-gray-500">
                          Nenhum estudante encontrado para "{searchQuery}"
                        </Text>
                      </VStack>
                    </Center>
                  )}
                </VStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Progress Metrics */}
          {data?.progress_metrics && (
            <Card variant="elevated" className="bg-white shadow-sm">
              <CardHeader>
                <Heading size="md" className="text-gray-900">
                  Métricas de Progresso
                </Heading>
              </CardHeader>
              <CardBody>
                <VStack space="md">
                  <HStack space="lg" className="flex-wrap">
                    <VStack className="items-center">
                      <Text className="text-lg font-bold text-gray-900">
                        {Math.round(data.progress_metrics.average_student_progress)}%
                      </Text>
                      <Text className="text-xs text-gray-500 text-center">Progresso Médio</Text>
                    </VStack>
                    <VStack className="items-center">
                      <Text className="text-lg font-bold text-gray-900">
                        {data.progress_metrics.total_assessments_given}
                      </Text>
                      <Text className="text-xs text-gray-500 text-center">Avaliações Feitas</Text>
                    </VStack>
                    <VStack className="items-center">
                      <Text className="text-lg font-bold text-gray-900">
                        {data.progress_metrics.students_improved_this_month}
                      </Text>
                      <Text className="text-xs text-gray-500 text-center">Melhoraram Este Mês</Text>
                    </VStack>
                  </HStack>

                  <Button
                    variant="outline"
                    onPress={handleViewAnalytics}
                    accessibilityLabel="Ver analytics detalhados"
                  >
                    <Icon as={BarChart3Icon} size="sm" className="text-blue-600 mr-2" />
                    <ButtonText className="text-blue-600">Ver Analytics Detalhados</ButtonText>
                  </Button>
                </VStack>
              </CardBody>
            </Card>
          )}

          {/* Recent Activities */}
          {data?.recent_activities && data.recent_activities.length > 0 && (
            <Card variant="elevated" className="bg-white shadow-sm">
              <CardHeader>
                <Heading size="md" className="text-gray-900">
                  Atividade Recente
                </Heading>
              </CardHeader>
              <CardBody>
                <VStack space="sm">
                  {data.recent_activities.slice(0, 5).map(activity => (
                    <HStack
                      key={activity.id}
                      space="sm"
                      className="items-start py-2 border-b border-gray-100 last:border-b-0"
                    >
                      <VStack className="w-8 h-8 bg-gray-100 rounded-full items-center justify-center">
                        <Icon
                          as={
                            activity.activity_type.includes('session')
                              ? ClockIcon
                              : activity.activity_type.includes('student')
                              ? UsersIcon
                              : activity.activity_type.includes('assessment')
                              ? AwardIcon
                              : MessageSquareIcon
                          }
                          size="xs"
                          className="text-gray-600"
                        />
                      </VStack>
                      <VStack className="flex-1">
                        <Text className="text-sm text-gray-900">{activity.description}</Text>
                        <Text className="text-xs text-gray-500">
                          {new Date(activity.timestamp).toLocaleDateString('pt-PT', {
                            day: '2-digit',
                            month: 'short',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </Text>
                      </VStack>
                    </HStack>
                  ))}
                </VStack>
              </CardBody>
            </Card>
          )}

          {/* Empty State for New Teachers */}
          {data &&
            data.quick_stats.total_students === 0 &&
            (!data.sessions.today || data.sessions.today.length === 0) && (
              <Box className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-dashed border-green-200 rounded-xl p-8 text-center">
                <VStack space="md" className="items-center">
                  <Icon as={GraduationCapIcon} size="xl" className="text-green-500" />
                  <Text className="text-xl font-bold text-gray-900">
                    Bem-vindo como Professor! 👨‍🏫
                  </Text>
                  <Text className="text-gray-600 max-w-md">
                    Está pronto para começar a ensinar? Configure o seu perfil e explore as
                    funcionalidades disponíveis.
                  </Text>
                  <HStack space="md" className="flex-wrap justify-center">
                    <Button onPress={handleViewProfile} variant="solid">
                      <ButtonText>Configurar Perfil</ButtonText>
                    </Button>
                    <Button onPress={handleScheduleSession} variant="outline">
                      <ButtonText>Agendar Primeira Aula</ButtonText>
                    </Button>
                  </HStack>
                </VStack>
              </Box>
            )}
        </VStack>
      </ScrollView>
    </MainLayout>
  );
};

// Add keyboard shortcuts for web
if (isWeb) {
  // TODO: Implement keyboard shortcuts
  // - Ctrl+1: Overview
  // - Ctrl+2: Students 
  // - Ctrl+3: Analytics
  // - Ctrl+4: Quick Actions
  // - Ctrl+R: Refresh
}

export default TeacherDashboard;
