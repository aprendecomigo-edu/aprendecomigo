import { router, useLocalSearchParams } from 'expo-router';
import {
  ArrowLeftIcon,
  CalendarIcon,
  MessageCircleIcon,
  TrendingUpIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  MailIcon,
  PhoneIcon,
  UserIcon,
  BookOpenIcon,
  StarIcon,
} from 'lucide-react-native';
import React, { useState, useMemo } from 'react';
import { Alert } from 'react-native';

import MainLayout from '@/components/layouts/main-layout';
import { Badge, BadgeText } from '@/components/ui/badge';
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
import useTutorStudents from '@/hooks/useTutorStudents';

const StudentDetailPage = () => {
  const { id } = useLocalSearchParams<{ id: string }>();
  const studentId = parseInt(id || '0', 10);

  // For now, using a mock school ID - in real app, get from tutor context
  const mockSchoolId = 1;

  const { students, isLoading } = useTutorStudents(mockSchoolId);

  const student = useMemo(() => {
    return students.find(s => s.id === studentId);
  }, [students, studentId]);

  // Mock session data - in real app, fetch from API
  const mockSessions = useMemo(
    () => [
      {
        id: 1,
        date: '2025-07-28',
        time: '14:00',
        subject: 'Matemática',
        status: 'completed' as const,
        duration: 60,
        rating: 5,
        notes: 'Excelente progresso com equações quadráticas',
      },
      {
        id: 2,
        date: '2025-07-25',
        time: '16:00',
        subject: 'Matemática',
        status: 'completed' as const,
        duration: 60,
        rating: 4,
        notes: 'Trabalhou bem os problemas de geometria',
      },
      {
        id: 3,
        date: '2025-07-23',
        time: '14:00',
        subject: 'Matemática',
        status: 'missed' as const,
        duration: 60,
        notes: 'Estudante não compareceu',
      },
      {
        id: 4,
        date: '2025-08-01',
        time: '15:00',
        subject: 'Matemática',
        status: 'scheduled' as const,
        duration: 60,
      },
    ],
    []
  );

  const handleContactStudent = (method: 'email' | 'phone' | 'message') => {
    if (!student) return;

    switch (method) {
      case 'email':
        Alert.alert('Enviar Email', `Abrir cliente de email para ${student.user.email}?`, [
          { text: 'Cancelar', style: 'cancel' },
          { text: 'Abrir', onPress: () => console.log('Open email client') },
        ]);
        break;
      case 'phone':
        Alert.alert('Ligar', `Ligar para ${student.user.name}?`, [
          { text: 'Cancelar', style: 'cancel' },
          { text: 'Ligar', onPress: () => console.log('Make phone call') },
        ]);
        break;
      case 'message':
        router.push(`/chat?student=${student.id}`);
        break;
    }
  };

  const handleScheduleSession = () => {
    if (!student) return;
    router.push(`/calendar/book?student=${student.id}`);
  };

  if (isLoading) {
    return (
      <MainLayout _title="Detalhes do Estudante">
        <Center className="flex-1 p-6">
          <VStack space="md" className="items-center">
            <Icon as={UserIcon} size="xl" className="text-blue-500" />
            <Text className="text-gray-600">Carregando detalhes...</Text>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  if (!student) {
    return (
      <MainLayout _title="Estudante Não Encontrado">
        <Center className="flex-1 p-6">
          <VStack space="lg" className="items-center max-w-md">
            <Icon as={UserIcon} size="xl" className="text-gray-400" />
            <VStack space="sm" className="items-center">
              <Heading size="lg" className="text-center text-gray-900">
                Estudante Não Encontrado
              </Heading>
              <Text className="text-center text-gray-600">
                O estudante que procura não foi encontrado.
              </Text>
            </VStack>
            <Button onPress={() => router.back()} variant="solid">
              <ButtonText>Voltar</ButtonText>
            </Button>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  const isActive =
    student.progress?.lastSessionDate &&
    (Date.now() - new Date(student.progress.lastSessionDate).getTime()) / (1000 * 60 * 60 * 24) <=
      7;

  const completedSessions = mockSessions.filter(s => s.status === 'completed').length;
  const averageRating =
    mockSessions.filter(s => s.rating).reduce((acc, s) => acc + (s.rating || 0), 0) /
      mockSessions.filter(s => s.rating).length || 0;

  return (
    <MainLayout _title={student.user.name}>
      <ScrollView className="flex-1 bg-gray-50" contentContainerStyle={{ paddingBottom: 100 }}>
        <VStack className="p-6" space="lg">
          {/* Header */}
          <VStack space="sm">
            <HStack className="items-center" space="sm">
              <Pressable onPress={() => router.back()} className="p-2">
                <Icon as={ArrowLeftIcon} size="sm" className="text-gray-600" />
              </Pressable>
              <Heading size="xl" className="text-gray-900 flex-1">
                {student.user.name}
              </Heading>
            </HStack>
          </VStack>

          {/* Student Profile Card */}
          <Card variant="elevated" className="bg-white shadow-sm">
            <CardBody>
              <VStack space="md">
                <HStack space="sm" className="items-center">
                  <VStack className="w-16 h-16 bg-blue-100 rounded-full items-center justify-center">
                    <Text className="text-2xl font-bold text-blue-600">
                      {student.user.name.charAt(0).toUpperCase()}
                    </Text>
                  </VStack>
                  <VStack className="flex-1">
                    <Text className="text-xl font-semibold text-gray-900">{student.user.name}</Text>
                    <Text className="text-sm text-gray-600">{student.user.email}</Text>
                    <HStack space="xs" className="items-center mt-1">
                      <Badge
                        variant={isActive ? 'solid' : 'outline'}
                        className={isActive ? 'bg-green-100' : ''}
                      >
                        <BadgeText className={isActive ? 'text-green-700' : 'text-gray-600'}>
                          {isActive ? 'Ativo' : 'Inativo'}
                        </BadgeText>
                      </Badge>
                      {student.acquisition?.invitationMethod && (
                        <Badge variant="outline">
                          <BadgeText className="text-blue-600">
                            Via {student.acquisition.invitationMethod}
                          </BadgeText>
                        </Badge>
                      )}
                    </HStack>
                  </VStack>
                </HStack>

                {/* Contact Actions */}
                <HStack space="sm">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1"
                    onPress={() => handleContactStudent('message')}
                  >
                    <Icon as={MessageCircleIcon} size="xs" className="text-blue-600 mr-1" />
                    <ButtonText className="text-blue-600">Mensagem</ButtonText>
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1"
                    onPress={() => handleContactStudent('email')}
                  >
                    <Icon as={MailIcon} size="xs" className="text-green-600 mr-1" />
                    <ButtonText className="text-green-600">Email</ButtonText>
                  </Button>
                  <Button
                    size="sm"
                    variant="solid"
                    className="flex-1"
                    onPress={handleScheduleSession}
                  >
                    <Icon as={CalendarIcon} size="xs" className="text-white mr-1" />
                    <ButtonText>Agendar</ButtonText>
                  </Button>
                </HStack>

                {/* Student Info */}
                {student.acquisition && (
                  <VStack space="xs" className="bg-gray-50 rounded-lg p-3">
                    <Text className="text-sm font-medium text-gray-700">
                      Informações de Aquisição
                    </Text>
                    <HStack className="justify-between">
                      <Text className="text-xs text-gray-600">Data de Inscrição:</Text>
                      <Text className="text-xs text-gray-900">
                        {new Date(student.acquisition.invitationDate || '').toLocaleDateString(
                          'pt-PT'
                        )}
                      </Text>
                    </HStack>
                    <HStack className="justify-between">
                      <Text className="text-xs text-gray-600">Método de Convite:</Text>
                      <Text className="text-xs text-gray-900">
                        {student.acquisition.invitationMethod}
                      </Text>
                    </HStack>
                    <HStack className="justify-between">
                      <Text className="text-xs text-gray-600">Tempo para Conversão:</Text>
                      <Text className="text-xs text-gray-900">
                        {student.acquisition.conversionDays} dias
                      </Text>
                    </HStack>
                  </VStack>
                )}
              </VStack>
            </CardBody>
          </Card>

          {/* Progress Overview */}
          {student.progress && (
            <Card variant="elevated" className="bg-white shadow-sm">
              <CardHeader>
                <Heading size="md" className="text-gray-900">
                  Progresso das Aulas
                </Heading>
              </CardHeader>
              <CardBody>
                <VStack space="md">
                  {/* Progress Stats */}
                  <HStack space="lg" className="flex-wrap">
                    <VStack className="items-center">
                      <Text className="text-2xl font-bold text-blue-600">
                        {student.progress.completedSessions}
                      </Text>
                      <Text className="text-sm text-gray-600">Concluídas</Text>
                    </VStack>
                    <VStack className="items-center">
                      <Text className="text-2xl font-bold text-gray-600">
                        {student.progress.totalPlannedSessions}
                      </Text>
                      <Text className="text-sm text-gray-600">Planeadas</Text>
                    </VStack>
                    <VStack className="items-center">
                      <Text className="text-2xl font-bold text-green-600">
                        {Math.round(student.progress.completionRate * 100)}%
                      </Text>
                      <Text className="text-sm text-gray-600">Taxa Conclusão</Text>
                    </VStack>
                    {averageRating > 0 && (
                      <VStack className="items-center">
                        <HStack space="xs" className="items-center">
                          <Text className="text-2xl font-bold text-yellow-600">
                            {averageRating.toFixed(1)}
                          </Text>
                          <Icon as={StarIcon} size="sm" className="text-yellow-600" />
                        </HStack>
                        <Text className="text-sm text-gray-600">Avaliação</Text>
                      </VStack>
                    )}
                  </HStack>

                  {/* Progress Bar */}
                  <VStack space="xs">
                    <HStack className="justify-between items-center">
                      <Text className="text-sm text-gray-600">Progresso do Curso</Text>
                      <Text className="text-sm font-semibold text-gray-900">
                        {student.progress.completedSessions}/{student.progress.totalPlannedSessions}
                      </Text>
                    </HStack>
                    <VStack className="w-full bg-gray-200 rounded-full h-3">
                      <VStack
                        className="bg-blue-500 h-3 rounded-full"
                        style={{
                          width: `${Math.round(
                            (student.progress.completedSessions /
                              student.progress.totalPlannedSessions) *
                              100
                          )}%`,
                        }}
                      />
                    </VStack>
                  </VStack>

                  {/* Last and Next Sessions */}
                  <HStack className="justify-between">
                    <VStack>
                      <Text className="text-xs text-gray-500">Última Aula</Text>
                      <Text className="text-sm font-medium text-gray-900">
                        {student.progress.lastSessionDate
                          ? new Date(student.progress.lastSessionDate).toLocaleDateString('pt-PT')
                          : 'Nenhuma ainda'}
                      </Text>
                    </VStack>
                    <VStack className="items-end">
                      <Text className="text-xs text-gray-500">Próxima Aula</Text>
                      <Text className="text-sm font-medium text-gray-900">
                        {student.progress.nextSessionDate
                          ? new Date(student.progress.nextSessionDate).toLocaleDateString('pt-PT')
                          : 'A agendar'}
                      </Text>
                    </VStack>
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
          )}

          {/* Recent Sessions */}
          <Card variant="elevated" className="bg-white shadow-sm">
            <CardHeader>
              <HStack className="justify-between items-center">
                <Heading size="md" className="text-gray-900">
                  Sessões Recentes
                </Heading>
                <Text className="text-sm text-blue-600">Ver todas</Text>
              </HStack>
            </CardHeader>
            <CardBody>
              <VStack space="sm">
                {mockSessions.slice(0, 5).map(session => (
                  <HStack
                    key={session.id}
                    space="sm"
                    className="items-center py-2 border-b border-gray-100 last:border-b-0"
                  >
                    <VStack className="w-10 h-10 rounded-full items-center justify-center">
                      {session.status === 'completed' && (
                        <Icon as={CheckCircleIcon} size="sm" className="text-green-600" />
                      )}
                      {session.status === 'missed' && (
                        <Icon as={XCircleIcon} size="sm" className="text-red-600" />
                      )}
                      {session.status === 'scheduled' && (
                        <Icon as={ClockIcon} size="sm" className="text-blue-600" />
                      )}
                    </VStack>

                    <VStack className="flex-1">
                      <HStack className="justify-between items-start">
                        <VStack>
                          <Text className="text-sm font-medium text-gray-900">
                            {session.subject}
                          </Text>
                          <Text className="text-xs text-gray-600">
                            {new Date(session.date).toLocaleDateString('pt-PT')} às {session.time}
                          </Text>
                        </VStack>
                        <VStack className="items-end">
                          <Badge
                            variant="outline"
                            className={
                              session.status === 'completed'
                                ? 'bg-green-50'
                                : session.status === 'missed'
                                ? 'bg-red-50'
                                : 'bg-blue-50'
                            }
                          >
                            <BadgeText
                              className={
                                session.status === 'completed'
                                  ? 'text-green-700'
                                  : session.status === 'missed'
                                  ? 'text-red-700'
                                  : 'text-blue-700'
                              }
                            >
                              {session.status === 'completed'
                                ? 'Concluída'
                                : session.status === 'missed'
                                ? 'Faltou'
                                : 'Agendada'}
                            </BadgeText>
                          </Badge>
                          {session.rating && (
                            <HStack space="xs" className="items-center mt-1">
                              <Icon as={StarIcon} size="xs" className="text-yellow-500" />
                              <Text className="text-xs text-gray-600">{session.rating}/5</Text>
                            </HStack>
                          )}
                        </VStack>
                      </HStack>

                      {session.notes && (
                        <Text className="text-xs text-gray-500 mt-1">{session.notes}</Text>
                      )}
                    </VStack>
                  </HStack>
                ))}
              </VStack>
            </CardBody>
          </Card>

          {/* Action Buttons */}
          <VStack space="sm">
            <Button variant="solid" className="bg-blue-600" onPress={handleScheduleSession}>
              <Icon as={CalendarIcon} size="sm" className="text-white mr-2" />
              <ButtonText>Agendar Nova Sessão</ButtonText>
            </Button>
            <HStack space="sm">
              <Button
                variant="outline"
                className="flex-1"
                onPress={() => handleContactStudent('message')}
              >
                <Icon as={MessageCircleIcon} size="sm" className="text-blue-600 mr-2" />
                <ButtonText className="text-blue-600">Enviar Mensagem</ButtonText>
              </Button>
              <Button
                variant="outline"
                className="flex-1"
                onPress={() =>
                  Alert.alert('Em Breve', 'Funcionalidade de relatórios em desenvolvimento')
                }
              >
                <Icon as={TrendingUpIcon} size="sm" className="text-green-600 mr-2" />
                <ButtonText className="text-green-600">Ver Relatório</ButtonText>
              </Button>
            </HStack>
          </VStack>
        </VStack>
      </ScrollView>
    </MainLayout>
  );
};

export default StudentDetailPage;
