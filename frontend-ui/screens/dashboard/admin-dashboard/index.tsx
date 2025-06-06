import React, { useState, useEffect } from 'react';

import { useAuth } from '@/api/authContext';
import { getDashboardInfo, DashboardInfo } from '@/api/userApi';
import MainLayout from '@/components/layouts/main-layout';
import { Avatar, AvatarFallbackText } from '@/components/ui/avatar';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import {
  AlertTriangleIcon,
  UserPlusIcon,
  GraduationCapIcon,
  CalendarIcon,
  CheckCircle,
} from 'lucide-react-native';

// Interfaces for the onboarding dashboard
interface OnboardingTask {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  priority: 'high' | 'medium' | 'low';
  type: string;
  icon: any;
  action?: () => void;
}

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

// Enhanced Tasks Table Component
const TasksTable = ({ tasks }: { tasks: OnboardingTask[] }) => {
  return (
    <VStack space="xs">
      {tasks.map(task => (
        <Box
          key={task.id}
          className={`rounded-lg p-4 border-l-4 ${
            task.completed
              ? 'bg-green-50 border-l-green-500 border-green-200'
              : task.priority === 'high'
                ? 'bg-orange-50 border-l-orange-500 border-orange-200'
                : 'bg-gray-50 border-l-gray-300 border-gray-200'
          }`}
          style={{
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 1 },
            shadowOpacity: 0.05,
            shadowRadius: 2,
            elevation: 1,
          }}
        >
          <HStack space="md" className="items-center">
            {/* Icon */}
            <Box
              className={`p-3 rounded-lg ${
                task.completed
                  ? 'bg-green-100'
                  : task.priority === 'high'
                    ? 'bg-orange-100'
                    : 'bg-gray-100'
              }`}
            >
              <Icon
                as={task.icon}
                size="sm"
                className={
                  task.completed
                    ? 'text-green-600'
                    : task.priority === 'high'
                      ? 'text-orange-600'
                      : 'text-gray-600'
                }
              />
            </Box>

            {/* Content */}
            <VStack className="flex-1" space="xs">
              <HStack space="sm" className="items-center">
                <Text className="font-semibold text-gray-900">{task.title}</Text>
                <Badge
                  variant="solid"
                  className={`${
                    task.completed
                      ? 'bg-green-100'
                      : task.priority === 'high'
                        ? 'bg-orange-100'
                        : 'bg-gray-100'
                  } px-2 py-1`}
                >
                  <BadgeText
                    className={`text-xs font-medium ${
                      task.completed
                        ? 'text-green-700'
                        : task.priority === 'high'
                          ? 'text-orange-700'
                          : 'text-gray-700'
                    }`}
                  >
                    {task.type}
                  </BadgeText>
                </Badge>
              </HStack>
              <Text className="text-sm text-gray-600 leading-5">{task.description}</Text>
            </VStack>

            {/* Action Button */}
            <VStack className="items-end" space="xs">
              <Text className="text-xs text-gray-500 font-medium">Ação</Text>
              {!task.completed ? (
                <Button
                  size="sm"
                  variant="solid"
                  className="bg-blue-600 px-4"
                  onPress={task.action}
                >
                  <ButtonText className="text-white font-medium">Resolver</ButtonText>
                </Button>
              ) : (
                <Box className="bg-green-600 rounded-full p-2">
                  <Icon as={CheckCircle} size="xs" className="text-white" />
                </Box>
              )}
            </VStack>
          </HStack>
        </Box>
      ))}
    </VStack>
  );
};

// Main Admin Dashboard Component
const AdminDashboard = () => {
  const { userProfile } = useAuth();
  const [dashboardData, setDashboardData] = useState<DashboardInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedView, setSelectedView] = useState<'list' | 'calendar'>('list');
  const [activityFilters, setActivityFilters] = useState<ActivityFilter[]>([
    { label: 'Pessoa', value: 'person', active: false },
    { label: 'Evento', value: 'event', active: false },
    { label: 'Lista', value: 'list', active: true },
  ]);

  // Get user name - school name is now handled by MainLayout
  const userName = userProfile?.name || 'Administrador';
  const userInitials = userName
    .split(' ')
    .map(n => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  // Load dashboard data
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setIsLoading(true);
        const data = await getDashboardInfo();
        setDashboardData(data);
      } catch (error) {
        console.error('Error loading dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  // Determine onboarding status
  const hasTeachers = (dashboardData?.stats?.teacher_count ?? 0) > 0;
  const hasStudents = (dashboardData?.stats?.student_count ?? 0) > 0;

  // Define onboarding tasks
  const onboardingTasks: OnboardingTask[] = [
    {
      id: 'add-teacher',
      title: 'Adicionar novo professor',
      description: 'Para usar esta conta, precisa de adicionar pelo menos um perfil de professor',
      completed: hasTeachers,
      priority: 'high',
      type: 'Recursos humanos',
      icon: UserPlusIcon,
      action: () => {
        console.log('Navigate to add teacher');
      },
    },
    {
      id: 'add-student',
      title: 'Adicionar novo aluno',
      description: 'Para usar esta conta, precisa de adicionar pelo menos um perfil de aluno',
      completed: hasStudents,
      priority: 'high',
      type: 'Recursos humanos',
      icon: GraduationCapIcon,
      action: () => {
        console.log('Navigate to add student');
      },
    },
  ];

  const incompleteTasks = onboardingTasks.filter(task => !task.completed);
  const hasIncompleteOnboarding = incompleteTasks.length > 0;

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
      }))
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
        <VStack space="sm">
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
          <Text className="text-gray-500 mt-1">{formatDate()}</Text>
        </VStack>

        {/* Warning Banner */}
        {hasIncompleteOnboarding && (
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
              <Icon as={AlertTriangleIcon} size="sm" className="text-amber-600 mt-1" />
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
        )}

        {/* Activities Section */}
        <VStack space="md">
          <Heading className="text-xl font-bold text-gray-900">Próximas atividades</Heading>

          {/* Filters and View Toggle */}
          <HStack space="sm" className="flex-wrap items-center justify-between">
            <HStack space="xs">
              {activityFilters.map(filter => (
                <Pressable
                  key={filter.value}
                  onPress={() => toggleFilter(filter.value)}
                >
                  <Badge
                    variant={filter.active ? 'solid' : 'outline'}
                    className={`px-3 py-2 ${
                      filter.active
                        ? 'bg-blue-600 border-blue-600'
                        : 'border-gray-300 bg-white'
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

          {/* Activities Table */}
          <ActivityTable />
        </VStack>

        {/* Tasks Section */}
        <VStack space="md">
          <Heading className="text-xl font-bold text-gray-900">Tarefas pendentes</Heading>
          <TasksTable tasks={onboardingTasks} />
        </VStack>
      </VStack>
    </ScrollView>
  );
};

// Export wrapped with MainLayout
export const AdminDashboardPage = () => {
  return (
    <MainLayout title="Dashboard">
      <AdminDashboard />
    </MainLayout>
  );
};

export default AdminDashboardPage;
