import { router } from 'expo-router';
import { 
  SearchIcon, 
  FilterIcon, 
  MoreVerticalIcon,
  UserIcon,
  CalendarIcon,
  TrendingUpIcon,
  MessageCircleIcon,
  PhoneIcon,
  MailIcon
} from 'lucide-react-native';
import React, { useState, useMemo, useCallback } from 'react';
import { Alert } from 'react-native';

import { useAuth } from '@/api/authContext';
import { getUserAdminSchools, SchoolMembership } from '@/api/userApi';
import MainLayout from '@/components/layouts/main-layout';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Menu, MenuItem, MenuItemLabel } from '@/components/ui/menu';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import useTutorStudents from '@/hooks/useTutorStudents';

const TutorStudentsPage = () => {
  const { userProfile } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');
  
  // For now, using a mock school ID - in real app, get from tutor context
  const mockSchoolId = 1;
  
  const { 
    students, 
    totalStudents, 
    activeStudents,
    isLoading, 
    error, 
    refresh 
  } = useTutorStudents(mockSchoolId);

  // Filter students based on search and status
  const filteredStudents = useMemo(() => {
    let filtered = students;

    // Apply search filter
    if (searchQuery.trim()) {
      filtered = filtered.filter(student =>
        student.user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        student.user.email.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(student => {
        const isActive = student.progress?.lastSessionDate && 
          (Date.now() - new Date(student.progress.lastSessionDate).getTime()) / (1000 * 60 * 60 * 24) <= 7;
        return filterStatus === 'active' ? isActive : !isActive;
      });
    }

    return filtered;
  }, [students, searchQuery, filterStatus]);

  const handleStudentPress = useCallback((studentId: number) => {
    router.push(`/(tutor)/students/${studentId}`);
  }, []);

  const handleContactStudent = useCallback((student: any, method: 'email' | 'phone' | 'message') => {
    switch (method) {
      case 'email':
        Alert.alert(
          'Enviar Email',
          `Abrir cliente de email para ${student.user.email}?`,
          [
            { text: 'Cancelar', style: 'cancel' },
            { text: 'Abrir', onPress: () => console.log('Open email client') }
          ]
        );
        break;
      case 'phone':
        Alert.alert(
          'Ligar',
          `Ligar para ${student.user.name}?`,
          [
            { text: 'Cancelar', style: 'cancel' },
            { text: 'Ligar', onPress: () => console.log('Make phone call') }
          ]
        );
        break;
      case 'message':
        router.push(`/chat?student=${student.id}`);
        break;
    }
  }, []);

  const handleScheduleSession = useCallback((student: any) => {
    router.push(`/calendar/book?student=${student.id}`);
  }, []);

  if (isLoading) {
    return (
      <MainLayout _title="Meus Estudantes">
        <Center className="flex-1 p-6">
          <VStack space="md" className="items-center">
            <Icon as={UserIcon} size="xl" className="text-blue-500" />
            <Text className="text-gray-600">Carregando estudantes...</Text>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout _title="Meus Estudantes">
        <Center className="flex-1 p-6">
          <VStack space="lg" className="items-center max-w-md">
            <Icon as={UserIcon} size="xl" className="text-gray-400" />
            <VStack space="sm" className="items-center">
              <Heading size="lg" className="text-center text-gray-900">
                Erro ao Carregar
              </Heading>
              <Text className="text-center text-gray-600">
                {error}
              </Text>
            </VStack>
            <Button onPress={refresh} variant="solid">
              <ButtonText>Tentar Novamente</ButtonText>
            </Button>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  return (
    <MainLayout _title="Meus Estudantes">
      <ScrollView 
        className="flex-1 bg-gray-50"
        contentContainerStyle={{ paddingBottom: 100 }}
      >
        <VStack className="p-6" space="lg">
          {/* Header */}
          <VStack space="sm">
            <HStack className="justify-between items-center">
              <VStack>
                <Heading size="xl" className="text-gray-900">
                  Meus Estudantes
                </Heading>
                <Text className="text-gray-600">
                  {totalStudents} estudantes • {activeStudents} ativos
                </Text>
              </VStack>
              <Button 
                variant="solid" 
                onPress={() => router.push('/(tutor)/acquisition')}
              >
                <ButtonText>Convidar +</ButtonText>
              </Button>
            </HStack>
          </VStack>

          {/* Search and Filter */}
          <VStack space="sm">
            <HStack space="sm">
              <VStack className="flex-1">
                <Input variant="outline">
                  <Icon as={SearchIcon} size="sm" className="text-gray-400 ml-3" />
                  <InputField
                    placeholder="Procurar estudantes..."
                    value={searchQuery}
                    onChangeText={setSearchQuery}
                  />
                </Input>
              </VStack>
              <Menu
                trigger={({ ...triggerProps }) => (
                  <Pressable {...triggerProps} className="p-3 bg-white border border-gray-300 rounded-lg">
                    <Icon as={FilterIcon} size="sm" className="text-gray-600" />
                  </Pressable>
                )}
              >
                <MenuItem onPress={() => setFilterStatus('all')}>
                  <MenuItemLabel>Todos</MenuItemLabel>
                </MenuItem>
                <MenuItem onPress={() => setFilterStatus('active')}>
                  <MenuItemLabel>Ativos</MenuItemLabel>
                </MenuItem>
                <MenuItem onPress={() => setFilterStatus('inactive')}>
                  <MenuItemLabel>Inativos</MenuItemLabel>
                </MenuItem>
              </Menu>
            </HStack>
            
            {/* Filter indicator */}
            {filterStatus !== 'all' && (
              <HStack space="xs" className="items-center">
                <Badge variant="outline">
                  <BadgeText>
                    Filtro: {filterStatus === 'active' ? 'Ativos' : 'Inativos'}
                  </BadgeText>
                </Badge>
                <Pressable onPress={() => setFilterStatus('all')}>
                  <Text className="text-xs text-blue-600">Limpar</Text>
                </Pressable>
              </HStack>
            )}
          </VStack>

          {/* Students Grid/List */}
          {filteredStudents.length === 0 ? (
            <Card variant="elevated" className="bg-white shadow-sm">
              <CardBody>
                <VStack space="md" className="items-center py-8">
                  <Icon as={UserIcon} size="xl" className="text-gray-300" />
                  <Text className="text-lg font-medium text-gray-600">
                    {searchQuery ? 'Nenhum estudante encontrado' : 'Nenhum estudante ainda'}
                  </Text>
                  <Text className="text-sm text-gray-500 text-center max-w-sm">
                    {searchQuery 
                      ? 'Tente ajustar os termos de pesquisa ou filtros'
                      : 'Comece convidando estudantes para fazer crescer o seu negócio de tutoria'
                    }
                  </Text>
                  {!searchQuery && (
                    <Button 
                      onPress={() => router.push('/(tutor)/acquisition')}
                      variant="solid"
                    >
                      <ButtonText>Convidar Estudantes</ButtonText>
                    </Button>
                  )}
                </VStack>
              </CardBody>
            </Card>
          ) : (
            <VStack space="sm">
              {filteredStudents.map((student) => {
                const isActive = student.progress?.lastSessionDate && 
                  (Date.now() - new Date(student.progress.lastSessionDate).getTime()) / (1000 * 60 * 60 * 24) <= 7;
                
                return (
                  <Card key={student.id} variant="elevated" className="bg-white shadow-sm">
                    <CardBody>
                      <Pressable onPress={() => handleStudentPress(student.id)}>
                        <VStack space="sm">
                          <HStack className="justify-between items-start">
                            <HStack space="sm" className="items-center flex-1">
                              <VStack className="w-12 h-12 bg-blue-100 rounded-full items-center justify-center">
                                <Text className="text-lg font-bold text-blue-600">
                                  {student.user.name.charAt(0).toUpperCase()}
                                </Text>
                              </VStack>
                              <VStack className="flex-1">
                                <Text className="text-lg font-semibold text-gray-900">
                                  {student.user.name}
                                </Text>
                                <Text className="text-sm text-gray-600">
                                  {student.user.email}
                                </Text>
                                <HStack space="xs" className="items-center mt-1">
                                  <Badge 
                                    variant={isActive ? "solid" : "outline"}
                                    className={isActive ? "bg-green-100" : ""}
                                  >
                                    <BadgeText className={isActive ? "text-green-700" : "text-gray-600"}>
                                      {isActive ? 'Ativo' : 'Inativo'}
                                    </BadgeText>
                                  </Badge>
                                  {student.acquisition?.invitationMethod && (
                                    <Badge variant="outline">
                                      <BadgeText className="text-blue-600">
                                        {student.acquisition.invitationMethod}
                                      </BadgeText>
                                    </Badge>
                                  )}
                                </HStack>
                              </VStack>
                            </HStack>
                            
                            <Menu
                              trigger={({ ...triggerProps }) => (
                                <Pressable {...triggerProps} className="p-2">
                                  <Icon as={MoreVerticalIcon} size="sm" className="text-gray-400" />
                                </Pressable>
                              )}
                            >
                              <MenuItem onPress={() => handleContactStudent(student, 'message')}>
                                <Icon as={MessageCircleIcon} size="sm" className="text-gray-600 mr-2" />
                                <MenuItemLabel>Enviar Mensagem</MenuItemLabel>
                              </MenuItem>
                              <MenuItem onPress={() => handleContactStudent(student, 'email')}>
                                <Icon as={MailIcon} size="sm" className="text-gray-600 mr-2" />
                                <MenuItemLabel>Enviar Email</MenuItemLabel>
                              </MenuItem>
                              <MenuItem onPress={() => handleScheduleSession(student)}>
                                <Icon as={CalendarIcon} size="sm" className="text-gray-600 mr-2" />
                                <MenuItemLabel>Agendar Aula</MenuItemLabel>
                              </MenuItem>
                            </Menu>
                          </HStack>

                          {/* Progress Information */}
                          {student.progress && (
                            <VStack space="xs">
                              <HStack className="justify-between items-center">
                                <Text className="text-sm text-gray-600">
                                  Progresso das Aulas
                                </Text>
                                <Text className="text-sm font-semibold text-gray-900">
                                  {student.progress.completedSessions}/{student.progress.totalPlannedSessions}
                                </Text>
                              </HStack>
                              <VStack className="w-full bg-gray-200 rounded-full h-2">
                                <VStack
                                  className="bg-blue-500 h-2 rounded-full"
                                  style={{ 
                                    width: `${Math.round(
                                      (student.progress.completedSessions / student.progress.totalPlannedSessions) * 100
                                    )}%` 
                                  }}
                                />
                              </VStack>
                              <HStack className="justify-between items-center">
                                <Text className="text-xs text-gray-500">
                                  {student.progress.lastSessionDate 
                                    ? `Última: ${new Date(student.progress.lastSessionDate).toLocaleDateString('pt-PT')}`
                                    : 'Primeira aula pendente'
                                  }
                                </Text>
                                <Text className="text-xs text-gray-500">
                                  {student.progress.nextSessionDate 
                                    ? `Próxima: ${new Date(student.progress.nextSessionDate).toLocaleDateString('pt-PT')}`
                                    : ''
                                  }
                                </Text>
                              </HStack>
                            </VStack>
                          )}

                          {/* Quick Actions */}
                          <HStack space="xs" className="pt-2">
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="flex-1"
                              onPress={() => handleScheduleSession(student)}
                            >
                              <Icon as={CalendarIcon} size="xs" className="text-blue-600 mr-1" />
                              <ButtonText className="text-blue-600 text-xs">Agendar</ButtonText>
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="flex-1"
                              onPress={() => handleContactStudent(student, 'message')}
                            >
                              <Icon as={MessageCircleIcon} size="xs" className="text-green-600 mr-1" />
                              <ButtonText className="text-green-600 text-xs">Mensagem</ButtonText>
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="flex-1"
                              onPress={() => handleStudentPress(student.id)}
                            >
                              <Icon as={TrendingUpIcon} size="xs" className="text-purple-600 mr-1" />
                              <ButtonText className="text-purple-600 text-xs">Ver Detalhes</ButtonText>
                            </Button>
                          </HStack>
                        </VStack>
                      </Pressable>
                    </CardBody>
                  </Card>
                );
              })}
            </VStack>
          )}

          {/* Summary Card */}
          {filteredStudents.length > 0 && (
            <Card variant="elevated" className="bg-blue-50 border border-blue-200 shadow-sm">
              <CardBody>
                <HStack className="justify-between items-center">
                  <VStack>
                    <Text className="text-sm text-blue-700">
                      Estudantes {filterStatus === 'all' ? 'Totais' : filterStatus === 'active' ? 'Ativos' : 'Inativos'}
                    </Text>
                    <Text className="text-2xl font-bold text-blue-900">
                      {filteredStudents.length}
                    </Text>
                  </VStack>
                  <VStack className="items-end">
                    <Text className="text-sm text-blue-700">
                      Taxa de Retenção
                    </Text>
                    <Text className="text-2xl font-bold text-blue-900">
                      {Math.round((activeStudents / totalStudents) * 100) || 0}%
                    </Text>
                  </VStack>
                </HStack>
              </CardBody>
            </Card>
          )}
        </VStack>
      </ScrollView>
    </MainLayout>
  );
};

export default TutorStudentsPage;