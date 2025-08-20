import { router } from 'expo-router';
import {
  SearchIcon,
  FilterIcon,
  UsersIcon,
  AlertTriangleIcon,
  RefreshCwIcon,
  ChevronRightIcon,
  CalendarIcon,
} from 'lucide-react-native';
import React, { useCallback } from 'react';
import { FlatList, Pressable, RefreshControl } from 'react-native';

import type { StudentProgress } from '@/api/teacherApi';
import MainLayout from '@/components/layouts/MainLayout';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import {
  Select,
  SelectTrigger,
  SelectInput,
  SelectIcon,
  SelectPortal,
  SelectBackdrop,
  SelectContent,
  SelectDragIndicatorWrapper,
  SelectDragIndicator,
  SelectItem,
} from '@/components/ui/select';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useTeacherStudents } from '@/hooks/useTeacherDashboard';
import { isWeb } from '@/utils/platform';

interface StudentListItemProps {
  student: StudentProgress;
  onPress: () => void;
}

const StudentListItem: React.FC<StudentListItemProps> = ({ student, onPress }) => {
  const getStatusColor = useCallback((student: StudentProgress) => {
    if (!student.last_session_date) {
      return { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Novo' };
    }

    const lastSessionDate = new Date(student.last_session_date);
    const daysSinceLastSession = Math.floor(
      (Date.now() - lastSessionDate.getTime()) / (1000 * 60 * 60 * 24),
    );

    if (daysSinceLastSession <= 7) {
      return { bg: 'bg-green-100', text: 'text-green-800', label: 'Ativo' };
    } else if (daysSinceLastSession <= 14) {
      return { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Moderado' };
    } else {
      return { bg: 'bg-red-100', text: 'text-red-800', label: 'Inativo' };
    }
  }, []);

  const getProgressColor = useCallback((percentage: number) => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 60) return 'bg-yellow-500';
    if (percentage >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  }, []);

  const status = getStatusColor(student);

  return (
    <Pressable
      onPress={onPress}
      className="bg-white rounded-lg border border-gray-200 p-4 mb-3 shadow-sm hover:shadow-md transition-shadow"
      accessibilityLabel={`Ver detalhes de ${student.name}`}
      accessibilityRole="button"
    >
      <HStack space="md" className="items-center">
        {/* Avatar */}
        <VStack className="w-12 h-12 bg-blue-100 rounded-full items-center justify-center">
          <Text className="text-lg font-bold text-blue-600">
            {student.name.charAt(0).toUpperCase()}
          </Text>
        </VStack>

        {/* Student Info */}
        <VStack className="flex-1" space="xs">
          <HStack className="justify-between items-start">
            <VStack className="flex-1">
              <Text className="text-base font-semibold text-gray-900">{student.name}</Text>
              <Text className="text-sm text-gray-500">{student.email}</Text>
            </VStack>

            {/* Status Badge */}
            <Badge className={status.bg}>
              <BadgeText className={status.text}>{status.label}</BadgeText>
            </Badge>
          </HStack>

          {/* Progress and Stats */}
          <HStack space="md" className="items-center">
            <VStack className="flex-1">
              <HStack className="justify-between items-center">
                <Text className="text-xs text-gray-500">Progresso</Text>
                <Text className="text-xs font-semibold text-gray-700">
                  {Math.round(student.completion_percentage)}%
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

            {/* Last Session */}
            <VStack className="items-end">
              <Text className="text-xs text-gray-500">Última aula</Text>
              <Text className="text-xs font-medium text-gray-700">
                {student.last_session_date
                  ? new Date(student.last_session_date).toLocaleDateString('pt-PT', {
                      day: '2-digit',
                      month: 'short',
                    })
                  : 'Nunca'}
              </Text>
            </VStack>
          </HStack>

          {/* Skills and Assessments */}
          {(student.skills_mastered?.length > 0 || student.recent_assessments?.length > 0) && (
            <HStack space="lg" className="items-center">
              {student.skills_mastered?.length > 0 && (
                <Text className="text-xs text-gray-500">
                  {student.skills_mastered.length} competência(s) dominada(s)
                </Text>
              )}
              {student.recent_assessments?.length > 0 && (
                <Text className="text-xs text-gray-500">
                  {student.recent_assessments.length} avaliação(ões) recente(s)
                </Text>
              )}
            </HStack>
          )}
        </VStack>

        {/* Arrow */}
        <Icon as={ChevronRightIcon} size="sm" className="text-gray-400" />
      </HStack>
    </Pressable>
  );
};

const TeacherStudentsPage = () => {
  const {
    students,
    filteredStudents,
    isLoading,
    error,
    searchQuery,
    filterBy,
    setSearchQuery,
    setFilterBy,
    refresh,
  } = useTeacherStudents();

  // TODO: Implement debounced search to avoid excessive API calls

  const handleStudentPress = useCallback((studentId: number) => {
    router.push(`/(teacher)/students/${studentId}`);
  }, []);

  const handleScheduleSession = useCallback(() => {
    router.push('/calendar/book');
  }, []);

  // Loading state
  if (isLoading && students.length === 0) {
    return (
      <MainLayout _title="Estudantes">
        <Center className="flex-1 p-6">
          <VStack space="md" className="items-center">
            <Icon as={UsersIcon} size="xl" className="text-blue-500" />
            <Text className="text-gray-600">Carregando estudantes...</Text>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  // Error state
  if (error && students.length === 0) {
    return (
      <MainLayout _title="Estudantes">
        <Center className="flex-1 p-6">
          <VStack space="lg" className="items-center max-w-md">
            <Icon as={AlertTriangleIcon} size="xl" className="text-red-500" />
            <VStack space="sm" className="items-center">
              <Heading size="lg" className="text-center text-gray-900">
                Erro ao Carregar Estudantes
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

  // Empty state
  if (!isLoading && students.length === 0) {
    return (
      <MainLayout _title="Estudantes">
        <Center className="flex-1 p-6">
          <VStack space="lg" className="items-center max-w-md">
            <Icon as={UsersIcon} size="xl" className="text-gray-400" />
            <VStack space="sm" className="items-center">
              <Heading size="lg" className="text-center text-gray-900">
                Nenhum Estudante Encontrado
              </Heading>
              <Text className="text-center text-gray-600">
                Ainda não tem estudantes atribuídos. Entre em contacto com a administração da
                escola.
              </Text>
            </VStack>
            <Button onPress={handleScheduleSession} variant="solid">
              <ButtonText>Agendar Primeira Aula</ButtonText>
            </Button>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  return (
    <MainLayout _title="Estudantes">
      <VStack className="flex-1 bg-gray-50">
        {/* Header and Search */}
        <VStack className="bg-white border-b border-gray-200 p-6" space="md">
          <HStack className="justify-between items-center">
            <VStack>
              <Heading size="lg" className="text-gray-900">
                Meus Estudantes
              </Heading>
              <Text className="text-gray-600">
                {filteredStudents.length} de {students.length} estudante(s)
              </Text>
            </VStack>

            <Pressable
              onPress={refresh}
              disabled={isLoading}
              className="p-2 rounded-md bg-gray-100 hover:bg-gray-200"
              accessibilityLabel="Atualizar lista de estudantes"
              accessibilityRole="button"
            >
              <Icon
                as={RefreshCwIcon}
                size="sm"
                className={`text-gray-600 ${isLoading ? 'animate-spin' : ''}`}
              />
            </Pressable>
          </HStack>

          {/* Search and Filter */}
          <VStack space="sm">
            <HStack space="sm" className="items-center">
              <Box className="flex-1 relative">
                <Input>
                  <InputField
                    placeholder="Pesquisar por nome ou email..."
                    value={searchQuery}
                    onChangeText={setSearchQuery}
                    accessibilityLabel="Pesquisar estudantes"
                  />
                </Input>
                <Box className="absolute left-3 top-1/2 transform -translate-y-1/2">
                  <Icon as={SearchIcon} size="sm" className="text-gray-400" />
                </Box>
              </Box>

              <Select
                selectedValue={filterBy}
                onValueChange={value => setFilterBy(value as 'all' | 'active' | 'needs_attention')}
              >
                <SelectTrigger variant="outline" size="md" className="min-w-32">
                  <SelectInput placeholder="Filtrar" />
                  <SelectIcon as={FilterIcon} />
                </SelectTrigger>
                <SelectPortal>
                  <SelectBackdrop />
                  <SelectContent>
                    <SelectDragIndicatorWrapper>
                      <SelectDragIndicator />
                    </SelectDragIndicatorWrapper>
                    <SelectItem label="Todos" value="all" />
                    <SelectItem label="Ativos" value="active" />
                    <SelectItem label="Precisam Atenção" value="needs_attention" />
                  </SelectContent>
                </SelectPortal>
              </Select>
            </HStack>

            {/* Filter Summary */}
            {(searchQuery || filterBy !== 'all') && (
              <HStack space="sm" className="items-center">
                {searchQuery && (
                  <Badge className="bg-blue-100">
                    <BadgeText className="text-blue-800">Pesquisa: "{searchQuery}"</BadgeText>
                  </Badge>
                )}
                {filterBy !== 'all' && (
                  <Badge className="bg-green-100">
                    <BadgeText className="text-green-800">
                      {filterBy === 'active' ? 'Ativos' : 'Precisam Atenção'}
                    </BadgeText>
                  </Badge>
                )}
                <Pressable
                  onPress={() => {
                    setSearchQuery('');
                    setFilterBy('all');
                  }}
                >
                  <Text className="text-sm text-blue-600">Limpar filtros</Text>
                </Pressable>
              </HStack>
            )}
          </VStack>
        </VStack>

        {/* Error Alert */}
        {error && students.length > 0 && (
          <Box className="bg-yellow-50 border-b border-yellow-200 p-4">
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

        {/* Students List */}
        {filteredStudents.length > 0 ? (
          <FlatList
            data={filteredStudents}
            keyExtractor={item => item.id.toString()}
            renderItem={({ item }) => (
              <StudentListItem student={item} onPress={() => handleStudentPress(item.id)} />
            )}
            contentContainerStyle={{
              padding: 16,
              paddingBottom: isWeb ? 16 : 100,
            }}
            refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refresh} />}
            showsVerticalScrollIndicator={false}
            // Performance optimizations for large lists
            initialNumToRender={10}
            maxToRenderPerBatch={10}
            windowSize={10}
            removeClippedSubviews={true}
            getItemLayout={
              (data, index) => ({
                length: 120,
                offset: 120 * index,
                index,
              }) // Approximate item height
            }
          />
        ) : (
          <Center className="flex-1 p-6">
            <VStack space="md" className="items-center max-w-md">
              <Icon as={SearchIcon} size="xl" className="text-gray-400" />
              <VStack space="sm" className="items-center">
                <Heading size="md" className="text-center text-gray-900">
                  Nenhum estudante encontrado
                </Heading>
                <Text className="text-center text-gray-600">
                  {searchQuery
                    ? `Nenhum resultado para "${searchQuery}". Tente ajustar os filtros de pesquisa.`
                    : filterBy === 'active'
                      ? 'Nenhum estudante ativo encontrado.'
                      : 'Nenhum estudante que precisa de atenção encontrado.'}
                </Text>
              </VStack>
              {(searchQuery || filterBy !== 'all') && (
                <Button
                  variant="outline"
                  onPress={() => {
                    setSearchQuery('');
                    setFilterBy('all');
                  }}
                >
                  <ButtonText>Limpar Filtros</ButtonText>
                </Button>
              )}
            </VStack>
          </Center>
        )}

        {/* Quick Actions FAB */}
        {!isWeb && (
          <Box className="absolute bottom-6 right-6">
            <Button
              onPress={handleScheduleSession}
              className="w-14 h-14 rounded-full bg-blue-600 shadow-lg"
              accessibilityLabel="Agendar nova sessão"
            >
              <Icon as={CalendarIcon} size="md" className="text-white" />
            </Button>
          </Box>
        )}
      </VStack>
    </MainLayout>
  );
};

export default TeacherStudentsPage;
