import { router, useLocalSearchParams } from 'expo-router';
import {
  ArrowLeftIcon,
  CalendarIcon,
  MessageSquareIcon,
  TrendingUpIcon,
  ClockIcon,
  AwardIcon,
  BookOpenIcon,
  TargetIcon,
  AlertTriangleIcon,
  RefreshCwIcon,
  BarChart3Icon,
  UserIcon,
  MailIcon,
} from 'lucide-react-native';
import React, { useCallback, useMemo } from 'react';
import { Pressable, RefreshControl } from 'react-native';

import MainLayout from '@/components/layouts/MainLayout';
import { Badge, BadgeText } from '@/components/ui/badge';
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
import { useStudentDetail } from '@/hooks/useTeacherDashboard';
import { isWeb } from '@/utils/platform';

const StudentDetailPage = () => {
  const { id } = useLocalSearchParams<{ id: string }>();
  const studentId = parseInt(id as string, 10);

  const { student, isLoading, error, refresh } = useStudentDetail(studentId);

  const handleGoBack = useCallback(() => {
    router.back();
  }, []);

  const handleScheduleSession = useCallback(() => {
    router.push(`/calendar/book?student_id=${studentId}`);
  }, [studentId]);

  const handleSendMessage = useCallback(() => {
    router.push(`/chat?student_id=${studentId}`);
  }, [studentId]);

  // Calculate student status
  const studentStatus = useMemo(() => {
    if (!student)
      return { label: 'Desconhecido', color: 'bg-gray-100', textColor: 'text-gray-800' };

    if (!student.last_session_date) {
      return { label: 'Novo', color: 'bg-blue-100', textColor: 'text-blue-800' };
    }

    const lastSessionDate = new Date(student.last_session_date);
    const daysSinceLastSession = Math.floor(
      (Date.now() - lastSessionDate.getTime()) / (1000 * 60 * 60 * 24),
    );

    if (daysSinceLastSession <= 7) {
      return { label: 'Ativo', color: 'bg-green-100', textColor: 'text-green-800' };
    } else if (daysSinceLastSession <= 14) {
      return { label: 'Moderado', color: 'bg-yellow-100', textColor: 'text-yellow-800' };
    } else {
      return { label: 'Inativo', color: 'bg-red-100', textColor: 'text-red-800' };
    }
  }, [student]);

  // Progress color based on percentage
  const getProgressColor = useCallback((percentage: number) => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 60) return 'bg-yellow-500';
    if (percentage >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  }, []);

  // Loading state
  if (isLoading) {
    return (
      <MainLayout _title="Detalhes do Estudante">
        <Center className="flex-1 p-6">
          <VStack space="md" className="items-center">
            <Icon as={UserIcon} size="xl" className="text-blue-500" />
            <Text className="text-gray-600">Carregando detalhes do estudante...</Text>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  // Error state
  if (error || !student) {
    return (
      <MainLayout _title="Detalhes do Estudante">
        <Center className="flex-1 p-6">
          <VStack space="lg" className="items-center max-w-md">
            <Icon as={AlertTriangleIcon} size="xl" className="text-red-500" />
            <VStack space="sm" className="items-center">
              <Heading size="lg" className="text-center text-gray-900">
                {error || 'Estudante não encontrado'}
              </Heading>
              <Text className="text-center text-gray-600">
                Não foi possível carregar os detalhes do estudante.
              </Text>
            </VStack>
            <HStack space="sm">
              <Button onPress={refresh} variant="solid">
                <Icon as={RefreshCwIcon} size="sm" className="text-white mr-2" />
                <ButtonText>Tentar Novamente</ButtonText>
              </Button>
              <Button onPress={handleGoBack} variant="outline">
                <ButtonText>Voltar</ButtonText>
              </Button>
            </HStack>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  return (
    <MainLayout _title={student.name}>
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
            <Pressable
              onPress={handleGoBack}
              className="p-2 rounded-md bg-gray-100 hover:bg-gray-200"
              accessibilityLabel="Voltar"
              accessibilityRole="button"
            >
              <Icon as={ArrowLeftIcon} size="sm" className="text-gray-600" />
            </Pressable>

            <Pressable
              onPress={refresh}
              disabled={isLoading}
              className="p-2 rounded-md bg-gray-100 hover:bg-gray-200"
              accessibilityLabel="Atualizar dados"
              accessibilityRole="button"
            >
              <Icon
                as={RefreshCwIcon}
                size="sm"
                className={`text-gray-600 ${isLoading ? 'animate-spin' : ''}`}
              />
            </Pressable>
          </HStack>

          {/* Student Profile Card */}
          <Card variant="elevated" className="bg-white shadow-sm">
            <CardBody>
              <VStack space="md">
                <HStack space="md" className="items-center">
                  {/* Avatar */}
                  <VStack className="w-16 h-16 bg-blue-100 rounded-full items-center justify-center">
                    <Text className="text-xl font-bold text-blue-600">
                      {student.name.charAt(0).toUpperCase()}
                    </Text>
                  </VStack>

                  {/* Basic Info */}
                  <VStack className="flex-1" space="xs">
                    <HStack className="justify-between items-start">
                      <VStack>
                        <Heading size="lg" className="text-gray-900">
                          {student.name}
                        </Heading>
                        <HStack space="sm" className="items-center">
                          <Icon as={MailIcon} size="xs" className="text-gray-500" />
                          <Text className="text-sm text-gray-600">{student.email}</Text>
                        </HStack>
                      </VStack>

                      <Badge className={studentStatus.color}>
                        <BadgeText className={studentStatus.textColor}>
                          {studentStatus.label}
                        </BadgeText>
                      </Badge>
                    </HStack>

                    {/* Level and Progress */}
                    <VStack space="xs">
                      <HStack className="justify-between items-center">
                        <Text className="text-sm text-gray-500">
                          Nível: {student.current_level || 'Não definido'}
                        </Text>
                        <Text className="text-sm font-semibold text-gray-700">
                          {Math.round(student.completion_percentage)}% completo
                        </Text>
                      </HStack>
                      <Box className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                        <Box
                          className={`h-full rounded-full ${getProgressColor(
                            student.completion_percentage,
                          )}`}
                          style={{ width: `${Math.min(student.completion_percentage, 100)}%` }}
                        />
                      </Box>
                    </VStack>
                  </VStack>
                </HStack>

                {/* Quick Actions */}
                <HStack space="sm">
                  <Button
                    className="flex-1 bg-blue-600"
                    onPress={handleScheduleSession}
                    accessibilityLabel="Agendar sessão com este estudante"
                  >
                    <Icon as={CalendarIcon} size="sm" className="text-white mr-2" />
                    <ButtonText>Agendar Sessão</ButtonText>
                  </Button>
                  <Button
                    variant="outline"
                    className="flex-1"
                    onPress={handleSendMessage}
                    accessibilityLabel="Enviar mensagem para este estudante"
                  >
                    <Icon as={MessageSquareIcon} size="sm" className="text-blue-600 mr-2" />
                    <ButtonText className="text-blue-600">Mensagem</ButtonText>
                  </Button>
                </HStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Progress Overview */}
          <Card variant="elevated" className="bg-white shadow-sm">
            <CardHeader>
              <HStack className="justify-between items-center">
                <Heading size="md" className="text-gray-900">
                  Visão Geral do Progresso
                </Heading>
                <Icon as={TrendingUpIcon} size="sm" className="text-blue-600" />
              </HStack>
            </CardHeader>
            <CardBody>
              <VStack space="md">
                <HStack space="lg" className="justify-around">
                  <VStack className="items-center">
                    <Text className="text-2xl font-bold text-gray-900">
                      {Math.round(student.completion_percentage)}%
                    </Text>
                    <Text className="text-xs text-gray-500 text-center">Progresso Geral</Text>
                  </VStack>
                  <VStack className="items-center">
                    <Text className="text-2xl font-bold text-gray-900">
                      {student.skills_mastered?.length || 0}
                    </Text>
                    <Text className="text-xs text-gray-500 text-center">
                      Competências Dominadas
                    </Text>
                  </VStack>
                  <VStack className="items-center">
                    <Text className="text-2xl font-bold text-gray-900">
                      {student.recent_assessments?.length || 0}
                    </Text>
                    <Text className="text-xs text-gray-500 text-center">Avaliações Recentes</Text>
                  </VStack>
                </HStack>

                {/* Last Session Info */}
                <Box className="bg-gray-50 rounded-lg p-4">
                  <HStack space="sm" className="items-center">
                    <Icon as={ClockIcon} size="sm" className="text-gray-600" />
                    <VStack className="flex-1">
                      <Text className="text-sm font-medium text-gray-900">Última Sessão</Text>
                      <Text className="text-xs text-gray-600">
                        {student.last_session_date
                          ? new Date(student.last_session_date).toLocaleDateString('pt-PT', {
                              weekday: 'long',
                              day: '2-digit',
                              month: 'long',
                              year: 'numeric',
                            })
                          : 'Nenhuma sessão ainda'}
                      </Text>
                    </VStack>
                  </HStack>
                </Box>
              </VStack>
            </CardBody>
          </Card>

          {/* Skills Mastered */}
          {student.skills_mastered && student.skills_mastered.length > 0 && (
            <Card variant="elevated" className="bg-white shadow-sm">
              <CardHeader>
                <HStack className="justify-between items-center">
                  <Heading size="md" className="text-gray-900">
                    Competências Dominadas
                  </Heading>
                  <Icon as={AwardIcon} size="sm" className="text-green-600" />
                </HStack>
              </CardHeader>
              <CardBody>
                <VStack space="sm">
                  {student.skills_mastered.map((skill, index) => (
                    <HStack
                      key={index}
                      space="sm"
                      className="items-center py-2 border-b border-gray-100 last:border-b-0"
                    >
                      <Icon as={TargetIcon} size="xs" className="text-green-600" />
                      <Text className="text-sm text-gray-900 flex-1">{skill}</Text>
                      <Badge className="bg-green-100">
                        <BadgeText className="text-green-800">Dominada</BadgeText>
                      </Badge>
                    </HStack>
                  ))}
                </VStack>
              </CardBody>
            </Card>
          )}

          {/* Recent Assessments */}
          {student.recent_assessments && student.recent_assessments.length > 0 && (
            <Card variant="elevated" className="bg-white shadow-sm">
              <CardHeader>
                <HStack className="justify-between items-center">
                  <Heading size="md" className="text-gray-900">
                    Avaliações Recentes
                  </Heading>
                  <Icon as={BarChart3Icon} size="sm" className="text-blue-600" />
                </HStack>
              </CardHeader>
              <CardBody>
                <VStack space="sm">
                  {student.recent_assessments.map(assessment => (
                    <HStack
                      key={assessment.id}
                      space="sm"
                      className="items-center py-3 border-b border-gray-100 last:border-b-0"
                    >
                      <VStack className="w-12 h-12 bg-blue-100 rounded-lg items-center justify-center">
                        <Text className="text-xs font-bold text-blue-600">
                          {Math.round(assessment.percentage)}%
                        </Text>
                      </VStack>
                      <VStack className="flex-1" space="xs">
                        <Text className="text-sm font-medium text-gray-900">
                          {assessment.title}
                        </Text>
                        <HStack space="md" className="items-center">
                          <Badge
                            className={
                              assessment.assessment_type === 'quiz'
                                ? 'bg-blue-100'
                                : assessment.assessment_type === 'test'
                                  ? 'bg-purple-100'
                                  : assessment.assessment_type === 'homework'
                                    ? 'bg-orange-100'
                                    : 'bg-gray-100'
                            }
                          >
                            <BadgeText
                              className={
                                assessment.assessment_type === 'quiz'
                                  ? 'text-blue-800'
                                  : assessment.assessment_type === 'test'
                                    ? 'text-purple-800'
                                    : assessment.assessment_type === 'homework'
                                      ? 'text-orange-800'
                                      : 'text-gray-800'
                              }
                            >
                              {assessment.assessment_type === 'quiz'
                                ? 'Quiz'
                                : assessment.assessment_type === 'test'
                                  ? 'Teste'
                                  : assessment.assessment_type === 'homework'
                                    ? 'TPC'
                                    : assessment.assessment_type}
                            </BadgeText>
                          </Badge>
                          <Text className="text-xs text-gray-500">
                            {new Date(assessment.assessment_date).toLocaleDateString('pt-PT', {
                              day: '2-digit',
                              month: 'short',
                            })}
                          </Text>
                        </HStack>
                      </VStack>
                      <VStack className="items-end">
                        <Box
                          className={`w-2 h-2 rounded-full ${
                            assessment.percentage >= 80
                              ? 'bg-green-500'
                              : assessment.percentage >= 60
                                ? 'bg-yellow-500'
                                : assessment.percentage >= 40
                                  ? 'bg-orange-500'
                                  : 'bg-red-500'
                          }`}
                        />
                      </VStack>
                    </HStack>
                  ))}
                </VStack>
              </CardBody>
            </Card>
          )}

          {/* Empty States */}
          {(!student.skills_mastered || student.skills_mastered.length === 0) &&
            (!student.recent_assessments || student.recent_assessments.length === 0) && (
              <Card variant="elevated" className="bg-white shadow-sm">
                <CardBody>
                  <Center className="py-8">
                    <VStack space="md" className="items-center">
                      <Icon as={BookOpenIcon} size="xl" className="text-gray-400" />
                      <VStack space="sm" className="items-center">
                        <Heading size="md" className="text-center text-gray-900">
                          Ainda não há dados de progresso
                        </Heading>
                        <Text className="text-center text-gray-600 max-w-md">
                          Este estudante ainda não tem competências dominadas ou avaliações
                          registadas. Agende uma sessão para começar a acompanhar o progresso.
                        </Text>
                      </VStack>
                      <Button onPress={handleScheduleSession} variant="solid">
                        <ButtonText>Agendar Primeira Sessão</ButtonText>
                      </Button>
                    </VStack>
                  </Center>
                </CardBody>
              </Card>
            )}
        </VStack>
      </ScrollView>
    </MainLayout>
  );
};

export default StudentDetailPage;
