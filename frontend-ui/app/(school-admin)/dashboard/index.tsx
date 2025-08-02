import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import { router } from 'expo-router';
import { AlertTriangleIcon, RefreshCwIcon, WifiOffIcon, SchoolIcon, ChevronDownIcon } from 'lucide-react-native';
import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { useAuth } from '@/api/authContext';
import { getUserAdminSchools, SchoolMembership } from '@/api/userApi';
// Temporarily comment out problematic imports to debug
// import { ActivityFeed, MetricsCard, QuickActionsPanel } from '@/components/dashboard';

// Temporary placeholder components for debugging
const MetricsCard = ({ metrics, isLoading }: any) => (
  <Box className="p-4 bg-white rounded-lg border">
    <Text>MetricsCard Placeholder - {isLoading ? 'Loading...' : 'Loaded'}</Text>
  </Box>
);

const QuickActionsPanel = ({ school, onAction }: any) => (
  <Box className="p-4 bg-white rounded-lg border">
    <Text>QuickActionsPanel Placeholder</Text>
  </Box>
);

const ActivityFeed = ({ activities, isLoading, onLoadMore }: any) => (
  <Box className="p-4 bg-white rounded-lg border">
    <Text>ActivityFeed Placeholder - {isLoading ? 'Loading...' : 'Loaded'}</Text>
  </Box>
);
// Temporarily comment out problematic SchoolInfoCard import
// import SchoolInfoCard from '@/components/dashboard/SchoolInfoCard';

// Temporary placeholder for SchoolInfoCard
const SchoolInfoCard = ({ school, isLoading, onSave }: any) => (
  <Box className="p-4 bg-white rounded-lg border">
    <Text>SchoolInfoCard Placeholder - {isLoading ? 'Loading...' : 'Loaded'}</Text>
    {school && <Text className="text-sm text-gray-600">School: {school.name}</Text>}
  </Box>
);
import MainLayout from '@/components/layouts/main-layout';
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
import useSchoolDashboard, { DashboardError } from '@/hooks/useSchoolDashboard';

const SchoolAdminDashboard = () => {
  const { userProfile } = useAuth();
  
  // State for school management
  const [adminSchools, setAdminSchools] = useState<SchoolMembership[]>([]);
  const [selectedSchoolId, setSelectedSchoolId] = useState<number | null>(null);
  const [schoolsLoading, setSchoolsLoading] = useState(true);
  const [schoolsError, setSchoolsError] = useState<string | null>(null);
  
  // Load user's admin schools on mount
  useEffect(() => {
    const loadAdminSchools = async () => {
      try {
        setSchoolsLoading(true);
        setSchoolsError(null);
        const schools = await getUserAdminSchools();
        setAdminSchools(schools);
        
        // Auto-select the first school if only one, or the last selected one
        if (schools.length === 1) {
          setSelectedSchoolId(schools[0].school.id);
        } else if (schools.length > 1) {
          // For now, default to the first school - in a real app, you might want to
          // save the user's last selected school in localStorage
          setSelectedSchoolId(schools[0].school.id);
        }
      } catch (error) {
        console.error('Error loading admin schools:', error);
        setSchoolsError('Falha ao carregar escolas. Você pode não ter permissões de administrador.');
      } finally {
        setSchoolsLoading(false);
      }
    };
    
    if (userProfile) {
      loadAdminSchools();
    }
  }, [userProfile]);
  
  // Get selected school info
  const selectedSchool = useMemo(() => {
    return adminSchools.find(school => school.school.id === selectedSchoolId);
  }, [adminSchools, selectedSchoolId]);

  const {
    metrics,
    schoolInfo,
    activities,
    isLoading,
    isLoadingMore,
    hasNextPage,
    totalActivities,
    error,
    wsError,
    isConnected,
    refreshAll,
    refreshAllWithRetry,
    loadMoreActivities,
    updateSchool,
    clearError,
  } = useSchoolDashboard({
    schoolId: selectedSchoolId || 0,
    enableRealtime: true,
    refreshInterval: 30000,
  });

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

  const handleUpdateSchool = useCallback(async (data: any) => {
    try {
      await updateSchool(data);
    } catch (err) {
      // Error handling is done in the hook
      throw err;
    }
  }, [updateSchool]);

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
          <Text className="text-gray-600">Carregando suas escolas...</Text>
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
            <Heading size="lg" className="text-center text-gray-900">
              Nenhuma escola encontrada
            </Heading>
            <Text className="text-center text-gray-600">
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
          <Text className="text-gray-600">Selecionando escola...</Text>
        </VStack>
      </Center>
    );
  }
  
  // Dashboard error state
  if (error && !isLoading) {
    const dashboardError = error as DashboardError;
    return (
      <Center className="flex-1 p-6">
        <VStack space="lg" className="items-center max-w-md">
          <Icon as={AlertTriangleIcon} size="xl" className="text-red-500" />
          <VStack space="sm" className="items-center">
            <Heading size="lg" className="text-center text-gray-900">
              {dashboardError.type === 'permission' ? 'Acesso negado' : 'Erro ao carregar dashboard'}
            </Heading>
            <Text className="text-center text-gray-600">
              {dashboardError.message}
            </Text>
            {dashboardError.details && (
              <Text className="text-center text-gray-500 text-sm">
                {dashboardError.details}
              </Text>
            )}
          </VStack>
          {dashboardError.canRetry && (
            <Button onPress={refreshAllWithRetry} variant="solid">
              <ButtonText>Tentar novamente</ButtonText>
            </Button>
          )}
          {!dashboardError.canRetry && (
            <Button onPress={() => router.push('/')} variant="outline">
              <ButtonText>Voltar ao início</ButtonText>
            </Button>
          )}
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
              
              {/* School Selector */}
              {adminSchools.length > 1 && (
                <Pressable 
                  onPress={() => {
                    // In a real app, you might want to show a modal or dropdown
                    // For now, cycle through schools
                    const currentIndex = adminSchools.findIndex(s => s.school.id === selectedSchoolId);
                    const nextIndex = (currentIndex + 1) % adminSchools.length;
                    setSelectedSchoolId(adminSchools[nextIndex].school.id);
                  }}
                  className="flex-row items-center space-x-2"
                >
                  <Text className="text-gray-600 font-medium">
                    {selectedSchool?.school.name || 'Carregando...'}
                  </Text>
                  <Icon as={ChevronDownIcon} size="sm" className="text-gray-400" />
                </Pressable>
              )}
              
              {adminSchools.length === 1 && (
                <Text className="text-gray-600">
                  {selectedSchool?.school.name || schoolInfo?.name || 'Carregando...'}
                </Text>
              )}
            </VStack>
            
            <HStack space="xs" className="items-center">
              {/* WebSocket Connection Status */}
              {!isConnected && (
                <Icon as={WifiOffIcon} size="sm" className="text-orange-500" />
              )}
              
              {/* Refresh Button */}
              <Pressable
                onPress={refreshAll}
                disabled={isLoading}
                className="p-2 rounded-md bg-gray-100 hover:bg-gray-200"
              >
                <Icon 
                  as={RefreshCwIcon} 
                  size="sm" 
                  className={`text-gray-600 ${isLoading ? 'animate-spin' : ''}`} 
                />
              </Pressable>
            </HStack>
          </HStack>

          {/* Date */}
          <Text className="text-sm text-gray-500">
            {new Date().toLocaleDateString('pt-PT', {
              weekday: 'long',
              day: '2-digit',
              month: 'long',
              year: 'numeric',
            })}
          </Text>
        </VStack>

        {/* Connection Warning */}
        {wsError && (
          <Box className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <HStack space="sm" className="items-start">
              <Icon as={WifiOffIcon} size="sm" className="text-orange-600 mt-0.5" />
              <VStack className="flex-1">
                <Text className="font-medium text-orange-900">
                  Atualizações em tempo real indisponíveis
                </Text>
                <Text className="text-sm text-orange-700">
                  Os dados serão atualizados automaticamente a cada 30 segundos
                </Text>
              </VStack>
            </HStack>
          </Box>
        )}

        {/* Error Alert */}
        {error && (
          <Box className="bg-red-50 border border-red-200 rounded-lg p-4">
            <HStack space="sm" className="items-start">
              <Icon as={AlertTriangleIcon} size="sm" className="text-red-600 mt-0.5" />
              <VStack className="flex-1">
                <Text className="font-medium text-red-900">
                  {(error as DashboardError).type === 'permission' ? 'Acesso negado' : 'Erro no carregamento'}
                </Text>
                <Text className="text-sm text-red-700">
                  {(error as DashboardError).message}
                </Text>
                {(error as DashboardError).details && (
                  <Text className="text-xs text-red-600 mt-1">
                    {(error as DashboardError).details}
                  </Text>
                )}
              </VStack>
              <VStack space="xs">
                {(error as DashboardError).canRetry && (
                  <Pressable onPress={refreshAllWithRetry}>
                    <Text className="text-sm font-medium text-red-600">Tentar novamente</Text>
                  </Pressable>
                )}
                <Pressable onPress={clearError}>
                  <Text className="text-sm font-medium text-red-600">Dispensar</Text>
                </Pressable>
              </VStack>
            </HStack>
          </Box>
        )}

        {/* Quick Stats Overview */}
        {metrics && !isLoading && (
          <Box className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-6 shadow-lg">
            <VStack space="md">
              <Text className="text-white font-semibold text-lg">
                Resumo Rápido
              </Text>
              <HStack space="lg" className="flex-wrap">
                <VStack className="items-center">
                  <Text className="text-2xl font-bold text-white">
                    {metrics.student_count.total}
                  </Text>
                  <Text className="text-blue-100 text-sm">Estudantes</Text>
                </VStack>
                <VStack className="items-center">
                  <Text className="text-2xl font-bold text-white">
                    {metrics.teacher_count.total}
                  </Text>
                  <Text className="text-blue-100 text-sm">Professores</Text>
                </VStack>
                <VStack className="items-center">
                  <Text className="text-2xl font-bold text-white">
                    {metrics.class_metrics.active_classes}
                  </Text>
                  <Text className="text-blue-100 text-sm">Aulas Ativas</Text>
                </VStack>
                <VStack className="items-center">
                  <Text className="text-2xl font-bold text-white">
                    {Math.round(metrics.engagement_metrics.acceptance_rate * 100)}%
                  </Text>
                  <Text className="text-blue-100 text-sm">Taxa Aceitação</Text>
                </VStack>
              </HStack>
            </VStack>
          </Box>
        )}

        {/* Main Dashboard Content */}
        <VStack space="lg" className={isWeb ? 'lg:grid lg:grid-cols-2 lg:gap-6' : ''}>
          {/* Left Column */}
          <VStack space="lg">
            {/* Metrics Card */}
            <MetricsCard metrics={metrics} isLoading={isLoading} />

            {/* Quick Actions Panel */}
            <QuickActionsPanel
              onInviteTeacher={handleInviteTeacher}
              onAddStudent={handleAddStudent}
              onScheduleClass={handleScheduleClass}
              onViewMessages={handleViewMessages}
              onManageUsers={handleManageUsers}
              onManageInvitations={handleManageInvitations}
              onSettings={handleSettings}
            />
          </VStack>

          {/* Right Column */}
          <VStack space="lg">
            {/* School Info Card */}
            <SchoolInfoCard
              schoolInfo={schoolInfo}
              isLoading={isLoading}
              onUpdate={handleUpdateSchool}
            />

            {/* Activity Feed */}
            <ActivityFeed
              activities={activities}
              isLoading={isLoading}
              isLoadingMore={isLoadingMore}
              hasNextPage={hasNextPage}
              totalCount={totalActivities}
              onLoadMore={loadMoreActivities}
              onRefresh={refreshAll}
            />
          </VStack>
        </VStack>

        {/* Empty State for New Schools */}
        {!isLoading && 
         metrics &&
         metrics.student_count.total === 0 && 
         metrics.teacher_count.total === 0 && (
          <Box className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-dashed border-green-200 rounded-xl p-8 text-center">
            <VStack space="md" className="items-center">
              <Text className="text-xl font-bold text-gray-900">
                Bem-vindo à sua escola! 🎉
              </Text>
              <Text className="text-gray-600 max-w-md">
                Comece convidando professores e adicionando estudantes para ativar totalmente sua conta.
                Este é o primeiro passo para reduzir a taxa de abandono e criar um ambiente de aprendizagem ativo.
              </Text>
              <HStack space="md" className="flex-wrap justify-center">
                <Button onPress={handleInviteTeacher} variant="solid">
                  <ButtonText>Convidar Professor</ButtonText>
                </Button>
                <Button onPress={handleAddStudent} variant="outline">
                  <ButtonText>Adicionar Estudante</ButtonText>
                </Button>
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