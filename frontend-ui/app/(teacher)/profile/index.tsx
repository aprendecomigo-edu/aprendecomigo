import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import { router } from 'expo-router';
import { 
  UserIcon, 
  EditIcon, 
  SettingsIcon, 
  AwardIcon,
  SchoolIcon,
  DollarSignIcon,
  RefreshCwIcon,
  AlertTriangleIcon,
  StarIcon,
  MapPinIcon,
  MailIcon,
  PhoneIcon,
  CalendarIcon
} from 'lucide-react-native';
import React, { useCallback } from 'react';
import { Pressable, RefreshControl } from 'react-native';

import { useAuth } from '@/api/authContext';
import MainLayout from '@/components/layouts/main-layout';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { Badge, BadgeText } from '@/components/ui/badge';

import { useTeacherDashboard } from '@/hooks/useTeacherDashboard';

const TeacherProfilePage = () => {
  const { userProfile } = useAuth();
  const { data, isLoading, error, refresh } = useTeacherDashboard();

  const handleEditProfile = useCallback(() => {
    router.push('/onboarding/teacher-profile');
  }, []);

  const handleSettings = useCallback(() => {
    router.push('/settings');
  }, []);

  // Loading state
  if (isLoading && !data) {
    return (
      <MainLayout _title="Perfil">
        <Center className="flex-1 p-6">
          <VStack space="md" className="items-center">
            <Icon as={UserIcon} size="xl" className="text-blue-500" />
            <Text className="text-gray-600">Carregando perfil...</Text>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  // Error state
  if (error && !data) {
    return (
      <MainLayout _title="Perfil">
        <Center className="flex-1 p-6">
          <VStack space="lg" className="items-center max-w-md">
            <Icon as={AlertTriangleIcon} size="xl" className="text-red-500" />
            <VStack space="sm" className="items-center">
              <Heading size="lg" className="text-center text-gray-900">
                Erro ao Carregar Perfil
              </Heading>
              <Text className="text-center text-gray-600">
                {error}
              </Text>
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

  const teacherInfo = data?.teacher_info || userProfile;

  return (
    <MainLayout _title="Perfil">
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={isLoading} onRefresh={refresh} />
        }
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
                Perfil
              </Heading>
              <Text className="text-gray-600">
                Gerencie as suas informações pessoais
              </Text>
            </VStack>
            
            <HStack space="xs">
              <Pressable
                onPress={refresh}
                disabled={isLoading}
                className="p-2 rounded-md bg-gray-100 hover:bg-gray-200"
                accessibilityLabel="Atualizar perfil"
                accessibilityRole="button"
              >
                <Icon 
                  as={RefreshCwIcon} 
                  size="sm" 
                  className={`text-gray-600 ${isLoading ? 'animate-spin' : ''}`} 
                />
              </Pressable>
              
              <Pressable
                onPress={handleSettings}
                className="p-2 rounded-md bg-gray-100 hover:bg-gray-200"
                accessibilityLabel="Configurações"
                accessibilityRole="button"
              >
                <Icon as={SettingsIcon} size="sm" className="text-gray-600" />
              </Pressable>
            </HStack>
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
                  <Text className="text-sm text-yellow-700">
                    {error}
                  </Text>
                </VStack>
                <Pressable onPress={refresh}>
                  <Text className="text-sm font-medium text-yellow-600">Atualizar</Text>
                </Pressable>
              </HStack>
            </Box>
          )}

          {/* Profile Header Card */}
          <Card variant="elevated" className="bg-white shadow-sm">
            <CardBody>
              <VStack space="md">
                <HStack space="md" className="items-center">
                  {/* Avatar */}
                  <VStack className="w-20 h-20 bg-blue-100 rounded-full items-center justify-center">
                    <Text className="text-2xl font-bold text-blue-600">
                      {(teacherInfo?.name || 'P').charAt(0).toUpperCase()}
                    </Text>
                  </VStack>
                  
                  {/* Basic Info */}
                  <VStack className="flex-1">
                    <Text className="text-xl font-bold text-gray-900">
                      {teacherInfo?.name || 'Nome não disponível'}
                    </Text>
                    <Text className="text-sm text-gray-600">
                      {teacherInfo?.email || userProfile?.email}
                    </Text>
                    {teacherInfo?.specialty && (
                      <Badge className="bg-blue-100 self-start">
                        <BadgeText className="text-blue-800">
                          {teacherInfo.specialty}
                        </BadgeText>
                      </Badge>
                    )}
                  </VStack>
                  
                  <Button 
                    onPress={handleEditProfile}
                    variant="outline"
                    size="sm"
                  >
                    <Icon as={EditIcon} size="sm" className="text-blue-600 mr-2" />
                    <ButtonText className="text-blue-600">Editar</ButtonText>
                  </Button>
                </HStack>
                
                {/* Profile Completion */}
                {teacherInfo?.profile_completion_score !== undefined && (
                  <Box className="bg-gray-50 rounded-lg p-3">
                    <HStack className="justify-between items-center mb-2">
                      <Text className="text-sm font-medium text-gray-700">
                        Completude do Perfil
                      </Text>
                      <Text className="text-sm font-semibold text-gray-900">
                        {Math.round(teacherInfo.profile_completion_score)}%
                      </Text>
                    </HStack>
                    <Box className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <Box 
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${Math.min(teacherInfo.profile_completion_score, 100)}%` }}
                      />
                    </Box>
                  </Box>
                )}
              </VStack>
            </CardBody>
          </Card>

          {/* Schools */}
          {teacherInfo?.schools && teacherInfo.schools.length > 0 && (
            <Card variant="elevated" className="bg-white shadow-sm">
              <CardHeader>
                <HStack className="items-center">
                  <Icon as={SchoolIcon} size="sm" className="text-gray-600 mr-2" />
                  <Heading size="md" className="text-gray-900">
                    Escolas
                  </Heading>
                </HStack>
              </CardHeader>
              <CardBody>
                <VStack space="sm">
                  {teacherInfo.schools.map((school) => (
                    <HStack key={school.id} space="sm" className="items-center py-2 border-b border-gray-100 last:border-b-0">
                      <VStack className="w-8 h-8 bg-green-100 rounded-full items-center justify-center">
                        <Icon as={SchoolIcon} size="xs" className="text-green-600" />
                      </VStack>
                      <VStack className="flex-1">
                        <Text className="text-sm font-medium text-gray-900">
                          {school.name}
                        </Text>
                        <Text className="text-xs text-gray-500">
                          Membro desde {new Date(school.joined_at).toLocaleDateString('pt-PT')}
                        </Text>
                      </VStack>
                    </HStack>
                  ))}
                </VStack>
              </CardBody>
            </Card>
          )}

          {/* Courses Taught */}
          {teacherInfo?.courses_taught && teacherInfo.courses_taught.length > 0 && (
            <Card variant="elevated" className="bg-white shadow-sm">
              <CardHeader>
                <HStack className="items-center">
                  <Icon as={AwardIcon} size="sm" className="text-gray-600 mr-2" />
                  <Heading size="md" className="text-gray-900">
                    Disciplinas Lecionadas
                  </Heading>
                </HStack>
              </CardHeader>
              <CardBody>
                <VStack space="sm">
                  {teacherInfo.courses_taught.map((course) => (
                    <HStack key={course.id} space="sm" className="items-center py-2 border-b border-gray-100 last:border-b-0">
                      <VStack className="w-8 h-8 bg-purple-100 rounded-full items-center justify-center">
                        <Text className="text-xs font-bold text-purple-600">
                          {course.code}
                        </Text>
                      </VStack>
                      <VStack className="flex-1">
                        <Text className="text-sm font-medium text-gray-900">
                          {course.name}
                        </Text>
                        <Text className="text-xs text-gray-500">
                          Código: {course.code}
                        </Text>
                      </VStack>
                      <VStack className="items-end">
                        <Text className="text-sm font-semibold text-green-600">
                          €{course.hourly_rate.toFixed(2)}/h
                        </Text>
                      </VStack>
                    </HStack>
                  ))}
                </VStack>
              </CardBody>
            </Card>
          )}

          {/* Quick Actions */}
          <Card variant="elevated" className="bg-white shadow-sm">
            <CardHeader>
              <Heading size="md" className="text-gray-900">
                Ações Rápidas
              </Heading>
            </CardHeader>
            <CardBody>
              <VStack space="sm">
                <Button 
                  variant="outline" 
                  onPress={handleEditProfile}
                  className="justify-start"
                >
                  <Icon as={EditIcon} size="sm" className="text-blue-600 mr-3" />
                  <ButtonText className="text-blue-600">Editar Perfil Completo</ButtonText>
                </Button>
                
                <Button 
                  variant="outline" 
                  onPress={() => router.push('/(teacher)/analytics')}
                  className="justify-start"
                >
                  <Icon as={StarIcon} size="sm" className="text-green-600 mr-3" />
                  <ButtonText className="text-green-600">Ver Desempenho</ButtonText>
                </Button>
                
                <Button 
                  variant="outline" 
                  onPress={handleSettings}
                  className="justify-start"
                >
                  <Icon as={SettingsIcon} size="sm" className="text-gray-600 mr-3" />
                  <ButtonText className="text-gray-600">Configurações</ButtonText>
                </Button>
              </VStack>
            </CardBody>
          </Card>

          {/* Stats Summary */}
          {data?.quick_stats && (
            <Card variant="elevated" className="bg-gradient-to-r from-blue-500 to-purple-600 shadow-sm">
              <CardBody>
                <VStack space="md">
                  <Text className="text-white font-semibold text-lg">
                    Resumo de Atividade
                  </Text>
                  <HStack space="lg" className="flex-wrap">
                    <VStack className="items-center">
                      <Text className="text-2xl font-bold text-white">
                        {data.quick_stats.total_students}
                      </Text>
                      <Text className="text-blue-100 text-sm">Estudantes</Text>
                    </VStack>
                    <VStack className="items-center">
                      <Text className="text-2xl font-bold text-white">
                        {data.quick_stats.sessions_this_week}
                      </Text>
                      <Text className="text-blue-100 text-sm">Sessões/Semana</Text>
                    </VStack>
                    <VStack className="items-center">
                      <Text className="text-2xl font-bold text-white">
                        {Math.round(data.quick_stats.completion_rate)}%
                      </Text>
                      <Text className="text-blue-100 text-sm">Taxa Conclusão</Text>
                    </VStack>
                    {data.quick_stats.average_rating && (
                      <VStack className="items-center">
                        <Text className="text-2xl font-bold text-white">
                          {data.quick_stats.average_rating.toFixed(1)}
                        </Text>
                        <Text className="text-blue-100 text-sm">Avaliação</Text>
                      </VStack>
                    )}
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
          )}
        </VStack>
      </ScrollView>
    </MainLayout>
  );
};

export default TeacherProfilePage;