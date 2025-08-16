import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import React, { useState, useEffect } from 'react';

import { useAuth, useUserProfile } from '@/api/auth';
import { tasksApi, Task } from '@/api/tasksApi';
import { getDashboardInfo, DashboardInfo } from '@/api/userApi';
import MainLayout from '@/components/layouts/MainLayout';
import TasksTable from '@/components/tasks/TasksTable';
import { useTutorial, TutorialHighlight, TutorialTrigger } from '@/components/tutorial';
import { dashboardTutorial } from '@/components/tutorial/configs/dashboardTutorial';
import { Avatar, AvatarFallbackText } from '@/components/ui/avatar';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { AlertTriangle, CalendarIcon } from '@/components/ui/icons';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Interfaces for the dashboard

interface ActivityFilter {
  label: string;
  value: string;
  active: boolean;
}

// Enhanced Activity Table Component
const ActivityTable = () => {
  return (
    <VStack space="sm" className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Table Header */}
      <HStack className="bg-gray-50 px-4 py-3 border-b border-gray-200">
        <Text className="font-semibold text-gray-700 flex-1 text-center">Horas</Text>
        <Text className="font-semibold text-gray-700 flex-1 text-center">Aluno</Text>
        <Text className="font-semibold text-gray-700 flex-1 text-center">Professora</Text>
        <Text className="font-semibold text-gray-700 flex-1 text-center">Local</Text>
        <Text className="font-semibold text-gray-700 flex-1 text-center">Endereço</Text>
      </HStack>

      {/* Empty State */}
      <Center className="py-12">
        <Icon as={CalendarIcon} size="xl" className="text-gray-300 mb-3" />
        <Text className="text-lg font-medium text-gray-600 mb-1">
          Não existem atividades agendadas
        </Text>
        <Text className="text-gray-500 text-center max-w-sm">
          As atividades aparecerão aqui quando você tiver professores e alunos ativos
        </Text>
      </Center>
    </VStack>
  );
};

// Main Admin Dashboard Component
const AdminDashboard = () => {
  const { userProfile } = useUserProfile();
  const { startTutorial, isTutorialCompleted, state } = useTutorial();
  const [dashboardData, setDashboardData] = useState<DashboardInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedView, setSelectedView] = useState<'list' | 'calendar'>('list');
  const [activityFilters, setActivityFilters] = useState<ActivityFilter[]>([
    { label: 'Pessoa', value: 'person', active: false },
    { label: 'Evento', value: 'event', active: false },
    { label: 'Lista', value: 'list', active: true },
  ]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);

  // Function to load tasks
  const loadTasks = async () => {
    try {
      setIsLoadingTasks(true);
      const allTasks = await tasksApi.getAllTasks();
      setTasks(allTasks);
    } catch (error) {
      console.error('Error loading tasks:', error);
    } finally {
      setIsLoadingTasks(false);
    }
  };

  // Get user name - school name is now handled by MainLayout
  const userName = userProfile?.name || 'Administrador';
  const userInitials = userName
    .split(' ')
    .map(n => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  // Check if user has incomplete onboarding (for warning banner)
  const hasIncompleteOnboarding = tasks.length > 0 || !isTutorialCompleted(dashboardTutorial.id);

  // Load dashboard data
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setIsLoading(true);

        // Load dashboard-specific data
        const data = await getDashboardInfo();
        setDashboardData(data);

        // Load tasks
        await loadTasks();
      } catch (error) {
        console.error('Error loading dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  // Auto-start tutorial for new users
  useEffect(() => {
    let timeoutId: NodeJS.Timeout | null = null;

    const autoStartTutorial = async () => {
      if (!isLoading && dashboardData && !dashboardData.user_info.first_login_completed) {
        // Small delay to ensure the dashboard is fully rendered
        timeoutId = setTimeout(() => {
          startTutorial(dashboardTutorial);
        }, 1000);
      }
    };

    autoStartTutorial();

    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [isLoading, dashboardData, startTutorial]);

  const formatDate = () => {
    const now = new Date();
    return now.toLocaleDateString('pt-BR', {
      weekday: 'long',
      day: '2-digit',
      month: 'long',
      year: 'numeric',
    });
  };

  const toggleFilter = (filterValue: string) => {
    setActivityFilters(prev =>
      prev.map(filter => ({
        ...filter,
        active: filter.value === filterValue,
      })),
    );
  };

  if (isLoading) {
    return (
      <Center className="flex-1">
        <Text className="text-gray-600">Carregando dashboard...</Text>
      </Center>
    );
  }

  return (
    <ScrollView
      showsVerticalScrollIndicator={false}
      contentContainerStyle={{
        paddingBottom: isWeb ? 0 : 100,
        flexGrow: 1,
      }}
      className="flex-1 bg-gray-50"
    >
      <VStack className="p-6" space="lg">
        {/* Welcome Header */}
        <TutorialHighlight
          id="profile-section"
          isActive={
            state.isActive && state.config?.steps[state.currentStep]?.id === 'profile-section'
          }
        >
          <VStack space="sm">
            <HStack className="items-center justify-between">
              <HStack className="items-center" space="md">
                <Avatar className="bg-blue-600 h-14 w-14 border-2 border-white shadow-lg">
                  <AvatarFallbackText className="text-white font-bold">
                    {userInitials}
                  </AvatarFallbackText>
                </Avatar>
                <VStack>
                  <Text className="font-bold text-2xl text-gray-900">
                    Olá, {userName.split(' ')[0]}!
                  </Text>
                </VStack>
              </HStack>
              <TutorialTrigger
                config={dashboardTutorial}
                variant="icon"
                size="sm"
                className="opacity-70"
              />
            </HStack>
            <Text className="text-gray-500 mt-1">{formatDate()}</Text>
          </VStack>
        </TutorialHighlight>

        {/* Warning Banner */}
        {hasIncompleteOnboarding && (
          <TutorialHighlight
            id="warning-banner"
            isActive={
              state.isActive && state.config?.steps[state.currentStep]?.id === 'warning-banner'
            }
          >
            <Box
              className="bg-amber-50 border border-amber-200 rounded-xl p-4"
              style={{
                shadowColor: '#F59E0B',
                shadowOffset: { width: 0, height: 2 },
                shadowOpacity: 0.1,
                shadowRadius: 4,
                elevation: 2,
              }}
            >
              <HStack space="sm" className="items-start">
                <Icon as={AlertTriangle} size="sm" className="text-amber-600 mt-1" />
                <VStack className="flex-1">
                  <Text className="font-semibold text-amber-900 mb-1">
                    Precisa de adicionar novo professor e aluno em 7 dias antes que a conta seja
                    desativada
                  </Text>
                  <Text className="text-amber-700 text-sm">
                    Complete as tarefas pendentes abaixo para ativar totalmente sua conta.
                  </Text>
                </VStack>
              </HStack>
            </Box>
          </TutorialHighlight>
        )}

        {/* Activities Section */}
        <TutorialHighlight
          id="activities-section"
          isActive={
            state.isActive && state.config?.steps[state.currentStep]?.id === 'activities-section'
          }
        >
          <VStack space="md">
            <Heading className="text-xl font-bold text-gray-900">Próximas atividades</Heading>

            {/* Filters and View Toggle */}
            <TutorialHighlight
              id="view-filters"
              isActive={
                state.isActive && state.config?.steps[state.currentStep]?.id === 'view-filters'
              }
            >
              <HStack space="sm" className="flex-wrap items-center justify-between">
                <HStack space="xs">
                  {activityFilters.map(filter => (
                    <Pressable key={filter.value} onPress={() => toggleFilter(filter.value)}>
                      <Badge
                        variant={filter.active ? 'solid' : 'outline'}
                        className={`px-3 py-2 ${
                          filter.active ? 'bg-blue-600 border-blue-600' : 'border-gray-300 bg-white'
                        }`}
                      >
                        <BadgeText
                          className={`font-medium ${
                            filter.active ? 'text-white' : 'text-gray-600'
                          }`}
                        >
                          {filter.label}
                        </BadgeText>
                      </Badge>
                    </Pressable>
                  ))}
                </HStack>

                {/* View Toggle */}
                <HStack space="xs" className="bg-gray-100 rounded-lg p-1">
                  <Pressable
                    onPress={() => setSelectedView('list')}
                    className={`px-4 py-2 rounded-md ${
                      selectedView === 'list' ? 'bg-blue-600' : 'bg-transparent'
                    }`}
                  >
                    <Text
                      className={`font-medium ${
                        selectedView === 'list' ? 'text-white' : 'text-gray-600'
                      }`}
                    >
                      Lista
                    </Text>
                  </Pressable>
                  <Pressable
                    onPress={() => setSelectedView('calendar')}
                    className={`px-4 py-2 rounded-md ${
                      selectedView === 'calendar' ? 'bg-blue-600' : 'bg-transparent'
                    }`}
                  >
                    <Text
                      className={`font-medium ${
                        selectedView === 'calendar' ? 'text-white' : 'text-gray-600'
                      }`}
                    >
                      Calendário
                    </Text>
                  </Pressable>
                </HStack>
              </HStack>
            </TutorialHighlight>

            {/* Activities Table */}
            <ActivityTable />
          </VStack>
        </TutorialHighlight>

        {/* Tasks Section */}
        <TutorialHighlight
          id="tasks-section"
          isActive={
            state.isActive && state.config?.steps[state.currentStep]?.id === 'tasks-section'
          }
        >
          <TasksTable tasks={tasks} onTasksChange={loadTasks} title="Tarefas Pendentes" />
        </TutorialHighlight>
      </VStack>
    </ScrollView>
  );
};

// Export wrapped with MainLayout
export const AdminDashboardPage = () => {
  return (
    <MainLayout _title="Dashboard">
      <AdminDashboard />
    </MainLayout>
  );
};

export default AdminDashboardPage;
