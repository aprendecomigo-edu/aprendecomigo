import { isWeb } from '@/utils/platform';

import { router } from 'expo-router';
import {
  AlertTriangleIcon,
  RefreshCwIcon,
  SchoolIcon,
  ChevronDownIcon,
  MailIcon,
  UsersIcon,
  SettingsIcon,
} from 'lucide-react-native';
import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { useAuth, useSchool } from '@/api/auth';
import { getSchoolInfo, SchoolInfo } from '@/api/userApi';
import { ToDoTaskList } from '@/components/dashboard/ToDoTaskList';
import { UpcomingEventsTable } from '@/components/dashboard/UpcomingEventsTable';

const QuickActionsPanel = ({
  onInviteTeacher,
  onAddStudent,
  onManageInvitations,
  onSettings,
  onCommunication,
}: any) => (
  <Box className="glass-container p-4 rounded-xl">
    <VStack space="sm">
      <Heading size="sm" className="font-primary text-gray-900">
        <Text className="bg-gradient-accent">Quick Actions</Text>
      </Heading>

      <HStack space="md" className="justify-center flex-wrap">
        {/* Communication System */}
        <Pressable
          onPress={onCommunication}
          className="items-center p-3 rounded-lg active:scale-95 transition-transform min-w-[60px]"
        >
          <Box className="p-3 bg-primary-600 rounded-full mb-1">
            <Icon as={MailIcon} size="sm" className="text-white" />
          </Box>
          <Text className="text-xs font-body text-gray-700 text-center">Email</Text>
        </Pressable>

        {/* Invite Teacher */}
        <Pressable
          onPress={onInviteTeacher}
          className="items-center p-3 rounded-lg active:scale-95 transition-transform min-w-[60px]"
        >
          <Box className="p-3 bg-accent-600 rounded-full mb-1">
            <Icon as={UsersIcon} size="sm" className="text-white" />
          </Box>
          <Text className="text-xs font-body text-gray-700 text-center">Convidar</Text>
        </Pressable>

        {/* Add Student */}
        <Pressable
          onPress={onAddStudent}
          className="items-center p-3 rounded-lg active:scale-95 transition-transform min-w-[60px]"
        >
          <Box className="p-3 bg-success-600 rounded-full mb-1">
            <Icon as={SchoolIcon} size="sm" className="text-white" />
          </Box>
          <Text className="text-xs font-body text-gray-700 text-center">Estudante</Text>
        </Pressable>

        {/* Manage Invitations */}
        <Pressable
          onPress={onManageInvitations}
          className="items-center p-3 rounded-lg active:scale-95 transition-transform min-w-[60px]"
        >
          <Box className="p-3 bg-orange-600 rounded-full mb-1">
            <Icon as={AlertTriangleIcon} size="sm" className="text-white" />
          </Box>
          <Text className="text-xs font-body text-gray-700 text-center">Convites</Text>
        </Pressable>

        {/* Settings */}
        <Pressable
          onPress={onSettings}
          className="items-center p-3 rounded-lg active:scale-95 transition-transform min-w-[60px]"
        >
          <Box className="p-3 bg-gray-600 rounded-full mb-1">
            <Icon as={SettingsIcon} size="sm" className="text-white" />
          </Box>
          <Text className="text-xs font-body text-gray-700 text-center">Config</Text>
        </Pressable>
      </HStack>
    </VStack>
  </Box>
);

import MainLayout from '@/components/layouts/MainLayout';
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

const SchoolAdminDashboard = () => {
  const { userProfile } = useAuth();
  const { userSchools, currentSchool } = useSchool();

  // Filter admin schools from user schools
  const adminSchools = useMemo(() => {
    return userSchools.filter(
      school => school.role === 'school_owner' || school.role === 'school_admin',
    );
  }, [userSchools]);

  // State for school info only (no or activities)
  const [schoolInfo, setSchoolInfo] = useState<SchoolInfo | null>(null);
  const [schoolInfoLoading, setSchoolInfoLoading] = useState(false);
  const [schoolInfoError, setSchoolInfoError] = useState<string | null>(null);

  // Check if user has admin access to any schools
  const hasAdminAccess = adminSchools.length > 0;
  const schoolsLoading = false; // No loading needed since schools come from auth context
  const schoolsError =
    !hasAdminAccess && userSchools.length > 0
      ? 'Você não tem permissões de administrador em nenhuma escola.'
      : null;

  // Get current selected school info
  const selectedSchool = useMemo(() => {
    if (!currentSchool) return null;
    return adminSchools.find(school => school.id === currentSchool.id);
  }, [adminSchools, currentSchool]);

  // Get selected school ID
  const selectedSchoolId = currentSchool?.id;

  // Fetch school info when school changes
  useEffect(() => {
    const fetchSchoolInfo = async () => {
      if (!selectedSchoolId || selectedSchoolId <= 0) {
        setSchoolInfo(null);
        return;
      }

      try {
        setSchoolInfoLoading(true);
        setSchoolInfoError(null);
        const data = await getSchoolInfo(selectedSchoolId);
        setSchoolInfo(data);
      } catch (error) {
        if (__DEV__) {
          console.error('Error fetching school info:', error); // TODO: Review for sensitive data
        }
        setSchoolInfoError('Falha ao carregar informações da escola');
      } finally {
        setSchoolInfoLoading(false);
      }
    };

    fetchSchoolInfo();
  }, [selectedSchoolId]);

  // Quick action handlers
  const handleInviteTeacher = useCallback(() => {
    router.push('/users?action=invite-teacher');
  }, []);

  const handleAddStudent = useCallback(() => {
    router.push('/users?action=add-student');
  }, []);

  const handleScheduleClass = useCallback(() => {
    router.push('/calendar/book');
  }, []);

  const handleViewMessages = useCallback(() => {
    router.push('/chat');
  }, []);

  const handleManageUsers = useCallback(() => {
    router.push('/users');
  }, []);

  const handleManageInvitations = useCallback(() => {
    router.push('/(school-admin)/invitations');
  }, []);

  const handleSettings = useCallback(() => {
    router.push('/(school-admin)/settings');
  }, []);

  const handleCommunication = useCallback(() => {
    router.push('/(school-admin)/communication');
  }, []);

  const _handleUpdateSchool = useCallback(
    async (_data: any) => {
      if (!selectedSchoolId) return;

      try {
        setSchoolInfoLoading(true);
        setSchoolInfoError(null);
        // Note: updateSchoolInfo is imported from userApi
        // const updatedSchool = await updateSchoolInfo(selectedSchoolId, data);
        // setSchoolInfo(updatedSchool);

        // For now, just refetch the school info
        const updatedData = await getSchoolInfo(selectedSchoolId);
        setSchoolInfo(updatedData);
      } catch (error) {
        if (__DEV__) {
          console.error('Error updating school:', error); // TODO: Review for sensitive data
        }
        setSchoolInfoError('Falha ao atualizar escola');
        throw error;
      } finally {
        setSchoolInfoLoading(false);
      }
    },
    [selectedSchoolId],
  );

  // Welcome message
  const welcomeMessage = useMemo(() => {
    const name = userProfile?.name?.split(' ')[0] || 'Administrador';
    const currentHour = new Date().getHours();

    if (currentHour < 12) {
      return `Bom dia, ${name}!`;
    } else if (currentHour < 18) {
      return `Boa tarde, ${name}!`;
    } else {
      return `Boa noite, ${name}!`;
    }
  }, [userProfile]);

  // Loading state for schools
  if (schoolsLoading) {
    return (
      <Center className="flex-1 p-6">
        <VStack space="md" className="items-center">
          <Icon as={SchoolIcon} size="xl" className="text-blue-500" />
          <Text className="font-body text-gray-600">Carregando suas escolas...</Text>
        </VStack>
      </Center>
    );
  }

  // No admin schools available
  if (!schoolsLoading && adminSchools.length === 0) {
    return (
      <Center className="flex-1 p-6">
        <VStack space="lg" className="items-center max-w-md">
          <Icon as={SchoolIcon} size="xl" className="text-gray-400" />
          <VStack space="sm" className="items-center">
            <Heading size="lg" className="font-primary text-center text-gray-900">
              <Text className="bg-gradient-accent">Nenhuma escola encontrada</Text>
            </Heading>
            <Text className="font-body text-center text-gray-600">
              {schoolsError || 'Você não possui permissões de administrador em nenhuma escola.'}
            </Text>
          </VStack>
          <Button onPress={() => router.push('/')} variant="outline">
            <ButtonText>Voltar ao início</ButtonText>
          </Button>
        </VStack>
      </Center>
    );
  }

  // No school selected yet
  if (!selectedSchoolId) {
    return (
      <Center className="flex-1 p-6">
        <VStack space="md" className="items-center">
          <Icon as={SchoolIcon} size="xl" className="text-blue-500" />
          <Text className="font-body text-gray-600">Selecionando escola...</Text>
        </VStack>
      </Center>
    );
  }

  // Dashboard error state (for critical school info errors)
  if (schoolInfoError && !schoolInfoLoading && selectedSchoolId) {
    return (
      <Center className="flex-1 p-6">
        <VStack space="lg" className="items-center max-w-md">
          <Icon as={AlertTriangleIcon} size="xl" className="text-red-500" />
          <VStack space="sm" className="items-center">
            <Heading size="lg" className="font-primary text-center text-gray-900">
              <Text className="bg-gradient-accent">Erro ao carregar dashboard</Text>
            </Heading>
            <Text className="font-body text-center text-gray-600">{schoolInfoError}</Text>
          </VStack>
          <Button
            onPress={() => {
              setSchoolInfoError(null);
              // Retry fetching school info
              if (selectedSchoolId) {
                setSchoolInfoLoading(true);
                getSchoolInfo(selectedSchoolId)
                  .then(setSchoolInfo)
                  .catch(() => setSchoolInfoError('Falha ao carregar informações da escola'))
                  .finally(() => setSchoolInfoLoading(false));
              }
            }}
            variant="solid"
          >
            <ButtonText>Tentar novamente</ButtonText>
          </Button>
          <Button onPress={() => router.push('/')} variant="outline">
            <ButtonText>Voltar ao início</ButtonText>
          </Button>
        </VStack>
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
      className="flex-1 bg-gradient-page"
    >
      <VStack className="p-6" space="lg">
        {/* Header Section */}
        <VStack space="sm">
          <HStack className="justify-between items-start">
            <VStack space="xs" className="flex-1">
              <Heading size="xl" className="font-primary text-gray-900">
                <Text className="bg-gradient-accent">{welcomeMessage}</Text>
              </Heading>

              {/* School Selector */}
              {adminSchools.length > 1 && (
                <Pressable
                  onPress={() => {
                    // In a real app, you might want to show a modal or dropdown
                    // For now, cycle through schools
                    const currentIndex = adminSchools.findIndex(s => s.id === selectedSchoolId);
                    const _nextIndex = (currentIndex + 1) % adminSchools.length;
                    // In a real implementation, you would update currentSchool in the auth context
                    // For now, this is just a placeholder - school switching needs proper implementation
                  }}
                  className="flex-row items-center space-x-2"
                >
                  <Text className="font-body text-gray-600 font-medium">
                    {selectedSchool?.name || 'Carregando...'}
                  </Text>
                  <Icon as={ChevronDownIcon} size="sm" className="text-gray-400" />
                </Pressable>
              )}

              {adminSchools.length === 1 && (
                <Text className="font-body text-gray-600">
                  {selectedSchool?.name || schoolInfo?.name || 'Carregando...'}
                </Text>
              )}
            </VStack>

            <HStack space="xs" className="items-center">
              {/* Refresh Button */}
              <Pressable
                onPress={() => {
                  if (selectedSchoolId) {
                    setSchoolInfoLoading(true);
                    getSchoolInfo(selectedSchoolId)
                      .then(setSchoolInfo)
                      .catch(() => setSchoolInfoError('Falha ao carregar informações da escola'))
                      .finally(() => setSchoolInfoLoading(false));
                  }
                }}
                disabled={schoolInfoLoading}
                className="glass-light p-2 rounded-md active:scale-98"
              >
                <Icon
                  as={RefreshCwIcon}
                  size="sm"
                  className={`text-gray-600 ${schoolInfoLoading ? 'animate-spin' : ''}`}
                />
              </Pressable>
            </HStack>
          </HStack>

          {/* Date */}
          <Text className="text-sm font-body text-gray-500">
            {new Date().toLocaleDateString('pt-PT', {
              weekday: 'long',
              day: '2-digit',
              month: 'long',
              year: 'numeric',
            })}
          </Text>
        </VStack>

        {/* Error Alert */}
        {schoolInfoError && (
          <Box className="bg-red-50 border border-red-200 rounded-lg p-4">
            <HStack space="sm" className="items-start">
              <Icon as={AlertTriangleIcon} size="sm" className="text-red-600 mt-0.5" />
              <VStack className="flex-1">
                <Text className="font-medium text-red-900">Erro no carregamento</Text>
                <Text className="text-sm text-red-700">{schoolInfoError}</Text>
              </VStack>
              <VStack space="xs">
                <Pressable onPress={() => setSchoolInfoError(null)}>
                  <Text className="text-sm font-medium text-red-600">Dispensar</Text>
                </Pressable>
              </VStack>
            </HStack>
          </Box>
        )}

        {/* Main Dashboard Content */}
        <VStack space="lg">
          {/* Quick Actions Row - Slim horizontal layout */}
          <QuickActionsPanel
            onInviteTeacher={handleInviteTeacher}
            onAddStudent={handleAddStudent}
            onScheduleClass={handleScheduleClass}
            onViewMessages={handleViewMessages}
            onManageUsers={handleManageUsers}
            onManageInvitations={handleManageInvitations}
            onSettings={handleSettings}
            onCommunication={handleCommunication}
          />

          {/* Upcoming Events Table Row - Full width */}
          <UpcomingEventsTable />

          {/* To-Do Task List Row - Full width */}
          <ToDoTaskList />
        </VStack>

        {/* Welcome State for New Schools - Always visible as a helpful guide */}
        {!schoolInfoLoading && (
          <Box className="hero-card p-8 text-center">
            <VStack space="md" className="items-center">
              <Text className="text-xl font-bold font-primary text-gray-900">
                <Text className="bg-gradient-primary">Bem-vindo à sua escola! 🎉</Text>
              </Text>
              <Text className="font-body text-gray-600 max-w-md">
                Comece convidando professores e adicionando estudantes para ativar totalmente sua
                conta. Este é o primeiro passo para reduzir a taxa de abandono e criar um ambiente
                de aprendizagem ativo.
              </Text>
              <HStack space="md" className="flex-wrap justify-center">
                <Pressable
                  onPress={handleInviteTeacher}
                  className="bg-gradient-primary px-6 py-3 rounded-xl active:scale-98 transition-transform"
                >
                  <Text className="text-white font-bold font-primary">Convidar Professor</Text>
                </Pressable>
                <Pressable
                  onPress={handleAddStudent}
                  className="glass-nav px-6 py-3 rounded-xl active:scale-98 transition-transform"
                >
                  <Text className="text-gray-800 font-bold font-primary">Adicionar Estudante</Text>
                </Pressable>
              </HStack>
            </VStack>
          </Box>
        )}
      </VStack>
    </ScrollView>
  );
};

// Export wrapped with MainLayout
export const SchoolAdminDashboardPage = () => {
  return (
    <MainLayout _title="Dashboard da Escola">
      <SchoolAdminDashboard />
    </MainLayout>
  );
};

export default SchoolAdminDashboardPage;
