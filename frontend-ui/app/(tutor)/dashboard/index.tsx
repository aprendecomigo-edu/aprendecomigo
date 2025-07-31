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
  DollarSignIcon
} from 'lucide-react-native';
import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { useAuth } from '@/api/authContext';
import { getUserAdminSchools, SchoolMembership } from '@/api/userApi';
import MainLayout from '@/components/layouts/main-layout';
import StudentAcquisitionHub from '@/components/tutor-dashboard/StudentAcquisitionHub';
import TutorMetricsCard from '@/components/tutor-dashboard/TutorMetricsCard';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import useTutorAnalytics from '@/hooks/useTutorAnalytics';
import useTutorStudents from '@/hooks/useTutorStudents';

const TutorDashboard = () => {
  const { userProfile } = useAuth();
  
  // State for school management (tutors have their own schools)
  const [tutorSchools, setTutorSchools] = useState<SchoolMembership[]>([]);
  const [selectedSchoolId, setSelectedSchoolId] = useState<number | null>(null);
  const [schoolsLoading, setSchoolsLoading] = useState(true);
  const [schoolsError, setSchoolsError] = useState<string | null>(null);
  
  // Load tutor's schools on mount
  useEffect(() => {
    const loadTutorSchools = async () => {
      try {
        setSchoolsLoading(true);
        setSchoolsError(null);
        const schools = await getUserAdminSchools();
        
        // Filter for tutor schools (individual tutoring practices)
        const tutorSchools = schools.filter(school => 
          school.school.name?.toLowerCase().includes(userProfile?.name?.toLowerCase() || '') ||
          school.role === 'teacher' // Individual tutors are typically both admin and teacher
        );
        
        setTutorSchools(tutorSchools);
        
        // Auto-select the first tutor school
        if (tutorSchools.length > 0) {
          setSelectedSchoolId(tutorSchools[0].school.id);
        }
      } catch (error) {
        console.error('Error loading tutor schools:', error);
        setSchoolsError('Falha ao carregar informações do negócio de tutoria.');
      } finally {
        setSchoolsLoading(false);
      }
    };
    
    if (userProfile) {
      loadTutorSchools();
    }
  }, [userProfile]);

  // Get selected school info
  const selectedSchool = useMemo(() => {
    return tutorSchools.find(school => school.school.id === selectedSchoolId);
  }, [tutorSchools, selectedSchoolId]);

  // Hooks for data fetching
  const { 
    analytics, 
    isLoading: analyticsLoading, 
    error: analyticsError, 
    refresh: refreshAnalytics 
  } = useTutorAnalytics(selectedSchoolId || undefined);

  const { 
    students, 
    totalStudents, 
    activeStudents,
    isLoading: studentsLoading, 
    error: studentsError, 
    refresh: refreshStudents 
  } = useTutorStudents(selectedSchoolId || undefined);

  // Quick action handlers
  const handleScheduleSession = useCallback(() => {
    router.push('/calendar/book');
  }, []);

  const handleViewStudents = useCallback(() => {
    router.push('/(tutor)/students');
  }, []);

  const handleViewAnalytics = useCallback(() => {
    router.push('/(tutor)/analytics');
  }, []);

  const handleManageSessions = useCallback(() => {
    router.push('/(tutor)/sessions');
  }, []);

  const handleSettings = useCallback(() => {
    router.push('/settings');
  }, []);

  const refreshAll = useCallback(async () => {
    await Promise.all([
      refreshAnalytics(),
      refreshStudents(),
    ]);
  }, [refreshAnalytics, refreshStudents]);

  // Welcome message
  const welcomeMessage = useMemo(() => {
    const name = userProfile?.name?.split(' ')[0] || 'Tutor';
    const currentHour = new Date().getHours();
    
    if (currentHour < 12) {
      return `Bom dia, ${name}!`;
    } else if (currentHour < 18) {
      return `Boa tarde, ${name}!`;
    } else {
      return `Boa noite, ${name}!`;
    }
  }, [userProfile]);

  // Loading state
  if (schoolsLoading) {
    return (
      <Center className="flex-1 p-6">
        <VStack space="md" className="items-center">
          <Icon as={GraduationCapIcon} size="xl" className="text-blue-500" />
          <Text className="text-gray-600">Carregando seu negócio de tutoria...</Text>
        </VStack>
      </Center>
    );
  }
  
  // No tutor schools available
  if (!schoolsLoading && tutorSchools.length === 0) {
    return (
      <Center className="flex-1 p-6">
        <VStack space="lg" className="items-center max-w-md">
          <Icon as={GraduationCapIcon} size="xl" className="text-gray-400" />
          <VStack space="sm" className="items-center">
            <Heading size="lg" className="text-center text-gray-900">
              Negócio de Tutoria Não Encontrado
            </Heading>
            <Text className="text-center text-gray-600">
              {schoolsError || 'Não foi possível encontrar seu negócio de tutoria. Complete o processo de configuração.'}
            </Text>
          </VStack>
          <Button onPress={() => router.push('/onboarding/tutor-onboarding')} variant="solid">
            <ButtonText>Configurar Tutoria</ButtonText>
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
          <Icon as={GraduationCapIcon} size="xl" className="text-blue-500" />
          <Text className="text-gray-600">Carregando dashboard...</Text>
        </VStack>
      </Center>
    );
  }

  const isLoading = analyticsLoading || studentsLoading;
  const hasError = analyticsError || studentsError;

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
              
              <Text className="text-gray-600">
                {selectedSchool?.school.name || 'Meu Negócio de Tutoria'}
              </Text>
            </VStack>
            
            <HStack space="xs" className="items-center">
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

        {/* Error Alert */}
        {hasError && (
          <Box className="bg-red-50 border border-red-200 rounded-lg p-4">
            <HStack space="sm" className="items-start">
              <Icon as={AlertTriangleIcon} size="sm" className="text-red-600 mt-0.5" />
              <VStack className="flex-1">
                <Text className="font-medium text-red-900">
                  Erro no carregamento
                </Text>
                <Text className="text-sm text-red-700">
                  {analyticsError || studentsError || 'Erro desconhecido'}
                </Text>
              </VStack>
              <Pressable onPress={refreshAll}>
                <Text className="text-sm font-medium text-red-600">Tentar novamente</Text>
              </Pressable>
            </HStack>
          </Box>
        )}

        {/* Quick Stats Overview */}
        {analytics && !isLoading && (
          <Box className="bg-gradient-to-r from-purple-500 to-blue-600 rounded-xl p-6 shadow-lg">
            <VStack space="md">
              <Text className="text-white font-semibold text-lg">
                Resumo do Mês
              </Text>
              <HStack space="lg" className="flex-wrap">
                <VStack className="items-center">
                  <Text className="text-2xl font-bold text-white">
                    {totalStudents}
                  </Text>
                  <Text className="text-purple-100 text-sm">Estudantes</Text>
                </VStack>
                <VStack className="items-center">
                  <Text className="text-2xl font-bold text-white">
                    {activeStudents}
                  </Text>
                  <Text className="text-purple-100 text-sm">Ativos</Text>
                </VStack>
                <VStack className="items-center">
                  <Text className="text-2xl font-bold text-white">
                    €{analytics.total_earnings.toFixed(0)}
                  </Text>
                  <Text className="text-purple-100 text-sm">Receita</Text>
                </VStack>
                <VStack className="items-center">
                  <Text className="text-2xl font-bold text-white">
                    {analytics.average_rating.toFixed(1)}
                  </Text>
                  <Text className="text-purple-100 text-sm">Avaliação</Text>
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
                >
                  <Icon as={CalendarIcon} size="sm" className="text-white mr-2" />
                  <ButtonText>Agendar Aula</ButtonText>
                </Button>
                <Button 
                  className="flex-1 bg-green-600" 
                  onPress={handleViewStudents}
                >
                  <Icon as={UsersIcon} size="sm" className="text-white mr-2" />
                  <ButtonText>Ver Estudantes</ButtonText>
                </Button>
              </HStack>
              <HStack space="sm">
                <Button 
                  variant="outline" 
                  className="flex-1" 
                  onPress={handleViewAnalytics}
                >
                  <Icon as={TrendingUpIcon} size="sm" className="text-blue-600 mr-2" />
                  <ButtonText className="text-blue-600">Analytics</ButtonText>
                </Button>
                <Button 
                  variant="outline" 
                  className="flex-1" 
                  onPress={handleManageSessions}
                >
                  <Icon as={DollarSignIcon} size="sm" className="text-green-600 mr-2" />
                  <ButtonText className="text-green-600">Sessões</ButtonText>
                </Button>
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        {/* Main Dashboard Content */}
        <VStack space="lg" className={isWeb ? 'lg:grid lg:grid-cols-2 lg:gap-6' : ''}>
          {/* Left Column */}
          <VStack space="lg">
            {/* Business Metrics Card */}
            <TutorMetricsCard analytics={analytics} isLoading={analyticsLoading} />
          </VStack>

          {/* Right Column */}
          <VStack space="lg">
            {/* Student Acquisition Hub */}
            <StudentAcquisitionHub 
              schoolId={selectedSchoolId}
              tutorName={userProfile?.name || 'Tutor'}
            />
          </VStack>
        </VStack>

        {/* Getting Started Guide for New Tutors */}
        {!isLoading && 
         analytics &&
         totalStudents === 0 && (
          <Box className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-dashed border-green-200 rounded-xl p-8 text-center">
            <VStack space="md" className="items-center">
              <Text className="text-xl font-bold text-gray-900">
                Bem-vindo ao teu negócio de tutoria! 🎓
              </Text>
              <Text className="text-gray-600 max-w-md">
                Comece convidando estudantes e configurando a disponibilidade para começar a lecionar.
                O teu sucesso começa com o primeiro estudante!
              </Text>
              <HStack space="md" className="flex-wrap justify-center">
                <Button onPress={() => router.push('/(tutor)/acquisition')} variant="solid">
                  <ButtonText>Convidar Estudantes</ButtonText>
                </Button>
                <Button onPress={handleSettings} variant="outline">
                  <ButtonText>Configurar Perfil</ButtonText>
                </Button>
              </HStack>
            </VStack>
          </Box>
        )}

        {/* Recent Activity Placeholder */}
        {totalStudents > 0 && (
          <Card variant="elevated" className="bg-white shadow-sm">
            <CardHeader>
              <Heading size="md" className="text-gray-900">
                Atividade Recente
              </Heading>
            </CardHeader>
            <CardBody>
              <VStack space="sm">
                {students.slice(0, 3).map((student, index) => (
                  <HStack key={student.id} space="sm" className="items-center py-2">
                    <VStack className="w-8 h-8 bg-blue-100 rounded-full items-center justify-center">
                      <Text className="text-xs font-bold text-blue-600">
                        {student.name.charAt(0).toUpperCase()}
                      </Text>
                    </VStack>
                    <VStack className="flex-1">
                      <Text className="text-sm font-medium text-gray-900">
                        {student.name}
                      </Text>
                      <Text className="text-xs text-gray-500">
                        {student.progress?.lastSessionDate 
                          ? `Última aula: ${new Date(student.progress.lastSessionDate).toLocaleDateString('pt-PT')}`
                          : 'Primeira aula pendente'
                        }
                      </Text>
                    </VStack>
                    <VStack className="items-end">
                      <Text className="text-xs font-semibold text-green-600">
                        {student.progress?.completionRate 
                          ? `${Math.round(student.progress.completionRate * 100)}%`
                          : '--'
                        }
                      </Text>
                    </VStack>
                  </HStack>
                ))}
                {students.length > 3 && (
                  <Pressable onPress={handleViewStudents} className="pt-2">
                    <Text className="text-sm font-medium text-blue-600 text-center">
                      Ver todos os estudantes ({totalStudents})
                    </Text>
                  </Pressable>
                )}
              </VStack>
            </CardBody>
          </Card>
        )}
      </VStack>
    </ScrollView>
  );
};

// Export wrapped with MainLayout
export const TutorDashboardPage = () => {
  return (
    <MainLayout _title="Dashboard do Tutor">
      <TutorDashboard />
    </MainLayout>
  );
};

export default TutorDashboardPage;