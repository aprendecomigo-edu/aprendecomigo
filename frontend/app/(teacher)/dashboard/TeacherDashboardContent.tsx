import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import { router } from 'expo-router';
import {
  AlertTriangleIcon,
  RefreshCwIcon,
  GraduationCapIcon,
  CalendarIcon,
  UsersIcon,
  TrendingUpIcon,
  BookOpenIcon,
  ClockIcon,
  AwardIcon,
  MessageSquareIcon,
  SearchIcon,
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

export default function TeacherDashboardContent() {
  const { userProfile } = useUserProfile();
  const { data, isLoading, error, refresh, lastUpdated } = useTeacherDashboard();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedView, setSelectedView] = useState<'overview' | 'students' | 'sessions'>(
    'overview',
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
        student.name.toLowerCase().includes(query) || student.email.toLowerCase().includes(query),
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
          paddingBottom: isWeb() ? 0 : 100,
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

          {/* Welcome Message for New Teachers */}
          <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200">
            <CardBody className="p-6">
              <VStack space="md" className="items-center text-center">
                <Icon as={GraduationCapIcon} size="xl" className="text-blue-600" />
                <Heading size="lg" className="text-gray-900">
                  Bem-vindo, Professor!
                </Heading>
                <Text className="text-gray-600 max-w-md text-center">
                  Aqui você pode acompanhar suas aulas, gerenciar estudantes e acessar todas as
                  ferramentas necessárias para ensinar.
                </Text>
                <HStack space="sm" className="flex-wrap justify-center">
                  <Button onPress={handleViewProfile} size="sm">
                    <ButtonText>Ver Perfil</ButtonText>
                  </Button>
                  <Button onPress={handleScheduleSession} size="sm" variant="outline">
                    <ButtonText>Agendar Aula</ButtonText>
                  </Button>
                </HStack>
              </VStack>
            </CardBody>
          </Card>

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

          {/* Placeholder for future content */}
          <Card>
            <CardBody className="p-8">
              <VStack space="md" className="items-center text-center">
                <Icon as={BookOpenIcon} size="xl" className="text-gray-400" />
                <Text className="text-lg font-semibold text-gray-700">
                  Mais funcionalidades em breve
                </Text>
                <Text className="text-gray-600">
                  Estamos trabalhando para trazer mais recursos para melhorar sua experiência de
                  ensino.
                </Text>
              </VStack>
            </CardBody>
          </Card>
        </VStack>
      </ScrollView>
    </MainLayout>
  );
}
