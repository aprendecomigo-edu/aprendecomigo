import {
  SearchIcon,
  FilterIcon,
  UsersIcon,
  TrendingUpIcon,
  ChevronRightIcon,
  BarChart3Icon,
  MessageSquareIcon,
  CalendarIcon,
  AwardIcon,
  AlertTriangleIcon,
} from 'lucide-react-native';
import React, { useMemo, useState, useCallback } from 'react';
import { FlatList, Pressable } from 'react-native';

import type { StudentProgress } from '@/api/teacherApi';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
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

interface StudentManagementProps {
  students: StudentProgress[];
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onStudentPress: (studentId: number) => void;
  onScheduleSession: (studentId: number) => void;
  onMessageStudent: (studentId: number) => void;
  isLoading?: boolean;
}

type FilterType = 'all' | 'active' | 'needs_attention' | 'high_performers' | 'new_students';

interface StudentCardProps {
  student: StudentProgress;
  onPress: () => void;
  onScheduleSession: () => void;
  onMessage: () => void;
}

const StudentCard = React.memo<StudentCardProps>(({
  student,
  onPress,
  onScheduleSession,
  onMessage,
}) => {
  const getStatusInfo = (student: StudentProgress) => {
    if (!student.last_session_date) {
      return { color: 'bg-blue-100 text-blue-800', label: 'Novo', priority: 'medium' };
    }

    const lastSessionDate = new Date(student.last_session_date);
    const daysSinceLastSession = Math.floor(
      (Date.now() - lastSessionDate.getTime()) / (1000 * 60 * 60 * 24),
    );

    if (daysSinceLastSession <= 3) {
      return { color: 'bg-green-100 text-green-800', label: 'Ativo', priority: 'low' };
    } else if (daysSinceLastSession <= 7) {
      return { color: 'bg-yellow-100 text-yellow-800', label: 'Moderado', priority: 'medium' };
    } else {
      return { color: 'bg-red-100 text-red-800', label: 'Inativo', priority: 'high' };
    }
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 60) return 'bg-yellow-500';
    if (percentage >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getProgressLabel = (percentage: number) => {
    if (percentage >= 80) return 'Excelente';
    if (percentage >= 60) return 'Bom';
    if (percentage >= 40) return 'Regular';
    return 'Precisa Atenção';
  };

  const status = getStatusInfo(student);
  const progressPercentage = Math.round(student.completion_percentage);

  return (
    <Pressable
      onPress={onPress}
      className="bg-white rounded-lg border border-gray-200 p-4 mb-3 shadow-sm hover:shadow-md transition-shadow"
      accessibilityLabel={`Ver detalhes de ${student.name}`}
      accessibilityRole="button"
    >
      <VStack space="sm">
        {/* Header */}
        <HStack space="md" className="items-start">
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
              <Badge className={status.color.split(' ')[0]}>
                <BadgeText className={status.color.split(' ')[1]}>{status.label}</BadgeText>
              </Badge>
            </HStack>
          </VStack>
        </HStack>

        {/* Progress Section */}
        <VStack space="xs">
          <HStack className="justify-between items-center">
            <Text className="text-sm font-medium text-gray-700">Progresso Geral</Text>
            <Text className="text-sm font-bold text-gray-900">
              {progressPercentage}% - {getProgressLabel(progressPercentage)}
            </Text>
          </HStack>
          <Box className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
            <Box
              className={`h-full rounded-full ${getProgressColor(student.completion_percentage)}`}
              style={{ width: `${Math.min(student.completion_percentage, 100)}%` }}
            />
          </Box>
        </VStack>

        {/* Stats */}
        <HStack space="lg" className="items-center">
          <VStack className="items-center">
            <Text className="text-xs text-gray-500">Última Aula</Text>
            <Text className="text-xs font-medium text-gray-700">
              {student.last_session_date
                ? new Date(student.last_session_date).toLocaleDateString('pt-PT', {
                    day: '2-digit',
                    month: 'short',
                  })
                : 'Nunca'}
            </Text>
          </VStack>

          {student.recent_assessments && student.recent_assessments.length > 0 && (
            <VStack className="items-center">
              <Text className="text-xs text-gray-500">Última Avaliação</Text>
              <Text className="text-xs font-medium text-gray-700">
                {student.recent_assessments[0].percentage}%
              </Text>
            </VStack>
          )}

          {student.skills_mastered && student.skills_mastered.length > 0 && (
            <VStack className="items-center">
              <Text className="text-xs text-gray-500">Competências</Text>
              <Text className="text-xs font-medium text-gray-700">
                {student.skills_mastered.length}
              </Text>
            </VStack>
          )}
        </HStack>

        {/* Quick Actions */}
        <HStack space="sm" className="pt-2">
          <Button
            size="sm"
            variant="outline"
            className="flex-1"
            onPress={onScheduleSession}
            accessibilityLabel={`Agendar sessão com ${student.name}`}
          >
            <Icon as={CalendarIcon} size="xs" className="text-blue-600 mr-1" />
            <ButtonText className="text-blue-600">Agendar</ButtonText>
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="flex-1"
            onPress={onMessage}
            accessibilityLabel={`Enviar mensagem para ${student.name}`}
          >
            <Icon as={MessageSquareIcon} size="xs" className="text-green-600 mr-1" />
            <ButtonText className="text-green-600">Mensagem</ButtonText>
          </Button>
          <Box className="items-center justify-center p-2">
            <Icon as={ChevronRightIcon} size="sm" className="text-gray-400" />
          </Box>
        </HStack>

        {/* Alert for students needing attention */}
        {(student.completion_percentage < 50 ||
          !student.last_session_date ||
          (student.last_session_date &&
            new Date(student.last_session_date) <
              new Date(Date.now() - 14 * 24 * 60 * 60 * 1000))) && (
          <Box className="bg-yellow-50 border border-yellow-200 rounded-lg p-2 mt-2">
            <HStack space="sm" className="items-center">
              <Icon as={AlertTriangleIcon} size="xs" className="text-yellow-600" />
              <Text className="text-xs text-yellow-800 flex-1">
                {student.completion_percentage < 50
                  ? 'Progresso baixo - considere agendar sessões adicionais'
                  : 'Sem aulas recentes - pode precisar de acompanhamento'}
              </Text>
            </HStack>
          </Box>
        )}
      </VStack>
    </Pressable>
  );
});

const StudentManagement: React.FC<StudentManagementProps> = ({
  students,
  searchQuery,
  onSearchChange,
  onStudentPress,
  onScheduleSession,
  onMessageStudent,
  isLoading = false,
}) => {
  const [filterBy, setFilterBy] = useState<FilterType>('all');

  // Filter students based on search query and filter criteria
  const filteredStudents = useMemo(() => {
    let filtered = students;

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      filtered = filtered.filter(
        student =>
          student.name.toLowerCase().includes(query) || student.email.toLowerCase().includes(query),
      );
    }

    // Apply category filter
    switch (filterBy) {
      case 'active':
        filtered = filtered.filter(
          student =>
            student.last_session_date &&
            new Date(student.last_session_date) >= new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
        );
        break;
      case 'needs_attention':
        filtered = filtered.filter(
          student =>
            student.completion_percentage < 50 ||
            !student.last_session_date ||
            new Date(student.last_session_date) < new Date(Date.now() - 14 * 24 * 60 * 60 * 1000),
        );
        break;
      case 'high_performers':
        filtered = filtered.filter(student => student.completion_percentage >= 80);
        break;
      case 'new_students':
        filtered = filtered.filter(student => !student.last_session_date);
        break;
      case 'all':
      default:
        // No additional filtering
        break;
    }

    // Sort by priority (needs attention first, then by progress)
    return filtered.sort((a, b) => {
      const aNeedsAttention =
        a.completion_percentage < 50 ||
        !a.last_session_date ||
        (a.last_session_date &&
          new Date(a.last_session_date) < new Date(Date.now() - 14 * 24 * 60 * 60 * 1000));
      const bNeedsAttention =
        b.completion_percentage < 50 ||
        !b.last_session_date ||
        (b.last_session_date &&
          new Date(b.last_session_date) < new Date(Date.now() - 14 * 24 * 60 * 60 * 1000));

      if (aNeedsAttention && !bNeedsAttention) return -1;
      if (!aNeedsAttention && bNeedsAttention) return 1;
      return b.completion_percentage - a.completion_percentage;
    });
  }, [students, searchQuery, filterBy]);

  // Calculate summary stats
  const stats = useMemo(() => {
    const total = students.length;
    const active = students.filter(
      s =>
        s.last_session_date &&
        new Date(s.last_session_date) >= new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    ).length;
    const needsAttention = students.filter(
      s =>
        s.completion_percentage < 50 ||
        !s.last_session_date ||
        (s.last_session_date &&
          new Date(s.last_session_date) < new Date(Date.now() - 14 * 24 * 60 * 60 * 1000)),
    ).length;
    const avgProgress =
      students.length > 0
        ? Math.round(
            students.reduce((sum, s) => sum + s.completion_percentage, 0) / students.length,
          )
        : 0;

    return { total, active, needsAttention, avgProgress };
  }, [students]);

  return (
    <VStack space="md">
      {/* Header with Stats */}
      <Card variant="elevated" className="bg-white shadow-sm">
        <CardHeader>
          <HStack className="justify-between items-center">
            <Heading size="md" className="text-gray-900">
              Gestão de Estudantes
            </Heading>
            <Badge className="bg-blue-100">
              <BadgeText className="text-blue-800">{stats.total}</BadgeText>
            </Badge>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack space="md">
            {/* Quick Stats */}
            <HStack space="lg" className="justify-around">
              <VStack className="items-center">
                <Text className="text-lg font-bold text-blue-600">{stats.total}</Text>
                <Text className="text-xs text-gray-500">Total</Text>
              </VStack>
              <VStack className="items-center">
                <Text className="text-lg font-bold text-green-600">{stats.active}</Text>
                <Text className="text-xs text-gray-500">Ativos</Text>
              </VStack>
              <VStack className="items-center">
                <Text className="text-lg font-bold text-red-600">{stats.needsAttention}</Text>
                <Text className="text-xs text-gray-500">Precisam Atenção</Text>
              </VStack>
              <VStack className="items-center">
                <Text className="text-lg font-bold text-purple-600">{stats.avgProgress}%</Text>
                <Text className="text-xs text-gray-500">Progresso Médio</Text>
              </VStack>
            </HStack>

            {/* Search and Filter */}
            <VStack space="sm">
              <HStack space="sm" className="items-center">
                <Box className="flex-1 relative">
                  <Input>
                    <InputField
                      placeholder="Pesquisar por nome ou email..."
                      value={searchQuery}
                      onChangeText={onSearchChange}
                      accessibilityLabel="Pesquisar estudantes"
                    />
                  </Input>
                  <Box className="absolute left-3 top-1/2 transform -translate-y-1/2">
                    <Icon as={SearchIcon} size="sm" className="text-gray-400" />
                  </Box>
                </Box>

                <Select
                  selectedValue={filterBy}
                  onValueChange={value => setFilterBy(value as FilterType)}
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
                      <SelectItem label="Alto Desempenho" value="high_performers" />
                      <SelectItem label="Novos Estudantes" value="new_students" />
                    </SelectContent>
                  </SelectPortal>
                </Select>
              </HStack>

              {/* Filter Summary */}
              {(searchQuery || filterBy !== 'all') && (
                <HStack space="sm" className="items-center flex-wrap">
                  {searchQuery && (
                    <Badge className="bg-blue-100">
                      <BadgeText className="text-blue-800">Pesquisa: "{searchQuery}"</BadgeText>
                    </Badge>
                  )}
                  {filterBy !== 'all' && (
                    <Badge className="bg-green-100">
                      <BadgeText className="text-green-800">
                        {filterBy === 'active'
                          ? 'Ativos'
                          : filterBy === 'needs_attention'
                            ? 'Precisam Atenção'
                            : filterBy === 'high_performers'
                              ? 'Alto Desempenho'
                              : 'Novos Estudantes'}
                      </BadgeText>
                    </Badge>
                  )}
                  <Pressable
                    onPress={() => {
                      onSearchChange('');
                      setFilterBy('all');
                    }}
                  >
                    <Text className="text-sm text-blue-600 underline">Limpar filtros</Text>
                  </Pressable>
                </HStack>
              )}
            </VStack>
          </VStack>
        </CardBody>
      </Card>

      {/* Students List */}
      {filteredStudents.length > 0 ? (
        <FlatList
          data={filteredStudents}
          keyExtractor={item => item.id.toString()}
          renderItem={useCallback(({ item }) => (
            <StudentCard
              student={item}
              onPress={() => onStudentPress(item.id)}
              onScheduleSession={() => onScheduleSession(item.id)}
              onMessage={() => onMessageStudent(item.id)}
            />
          ), [onStudentPress, onScheduleSession, onMessageStudent])}
          showsVerticalScrollIndicator={false}
          // Performance optimizations
          initialNumToRender={10}
          maxToRenderPerBatch={10}
          windowSize={10}
          removeClippedSubviews={true}
          getItemLayout={(data, index) => ({
            length: 200, // Approximate item height
            offset: 200 * index,
            index,
          })}
        />
      ) : (
        <Center className="py-12">
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
                    : filterBy === 'needs_attention'
                      ? 'Nenhum estudante que precisa de atenção encontrado.'
                      : filterBy === 'high_performers'
                        ? 'Nenhum estudante de alto desempenho encontrado.'
                        : filterBy === 'new_students'
                          ? 'Nenhum novo estudante encontrado.'
                          : 'Ainda não tem estudantes atribuídos.'}
              </Text>
            </VStack>
            {(searchQuery || filterBy !== 'all') && (
              <Button
                variant="outline"
                onPress={() => {
                  onSearchChange('');
                  setFilterBy('all');
                }}
              >
                <ButtonText>Limpar Filtros</ButtonText>
              </Button>
            )}
          </VStack>
        </Center>
      )}
    </VStack>
  );
};

export default StudentManagement;
