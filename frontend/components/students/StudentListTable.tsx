import { useRouter } from 'expo-router';
import {
  Search,
  Filter,
  MoreVertical,
  Edit,
  Trash2,
  UserCheck,
  UserX,
  GraduationCap,
  Eye,
  SortAsc,
  SortDesc,
  Users,
  ChevronDown,
  ChevronUp,
} from 'lucide-react-native';
import React, { useState, useMemo } from 'react';

import { StudentProfile, EducationalSystem } from '@/api/userApi';
import { AuthGuard } from '@/components/auth/AuthGuard';
import ErrorBoundary from '@/components/common/ErrorBoundary';
import {
  Actionsheet,
  ActionsheetBackdrop,
  ActionsheetContent,
  ActionsheetDragIndicator,
  ActionsheetDragIndicatorWrapper,
  ActionsheetItem,
  ActionsheetItemText,
} from '@/components/ui/actionsheet';
import {
  AlertDialog,
  AlertDialogBackdrop,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogCloseButton,
  AlertDialogFooter,
  AlertDialogBody,
} from '@/components/ui/alert-dialog';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import {
  Select,
  SelectBackdrop,
  SelectContent,
  SelectDragIndicator,
  SelectDragIndicatorWrapper,
  SelectIcon,
  SelectInput,
  SelectItem,
  SelectPortal,
  SelectTrigger,
} from '@/components/ui/select';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { useToast } from '@/components/ui/toast';
import { VStack } from '@/components/ui/vstack';
import { useStudents } from '@/hooks/useStudents';

// Color constants
const COLORS = {
  primary: '#156082',
  secondary: '#FFC000',
  white: '#FFFFFF',
  gray: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    900: '#111827',
  },
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
} as const;

const SCHOOL_YEARS = [
  '1º ano',
  '2º ano',
  '3º ano',
  '4º ano',
  '5º ano',
  '6º ano',
  '7º ano',
  '8º ano',
  '9º ano',
  '10º ano',
  '11º ano',
  '12º ano',
];

interface StudentListTableProps {
  showAddButton?: boolean;
  onAddStudent?: () => void;
  onBulkImport?: () => void;
}

interface StudentRowProps {
  student: StudentProfile;
  onView: (student: StudentProfile) => void;
  onEdit: (student: StudentProfile) => void;
  onDelete: (student: StudentProfile) => void;
  onStatusChange: (student: StudentProfile, status: 'active' | 'inactive' | 'graduated') => void;
}

const StudentRow: React.FC<StudentRowProps> = React.memo(
  ({ student, onView, onEdit, onDelete, onStatusChange }) => {
    const [showActionsheet, setShowActionsheet] = useState(false);

    const getStatusBadge = (status?: string) => {
      switch (status) {
        case 'active':
          return (
            <Badge style={{ backgroundColor: `${COLORS.success}20` }}>
              <BadgeText style={{ color: COLORS.success }}>Ativo</BadgeText>
            </Badge>
          );
        case 'inactive':
          return (
            <Badge style={{ backgroundColor: `${COLORS.warning}20` }}>
              <BadgeText style={{ color: COLORS.warning }}>Inativo</BadgeText>
            </Badge>
          );
        case 'graduated':
          return (
            <Badge style={{ backgroundColor: `${COLORS.primary}20` }}>
              <BadgeText style={{ color: COLORS.primary }}>Formado</BadgeText>
            </Badge>
          );
        default:
          return (
            <Badge style={{ backgroundColor: `${COLORS.success}20` }}>
              <BadgeText style={{ color: COLORS.success }}>Ativo</BadgeText>
            </Badge>
          );
      }
    };

    return (
      <>
        <HStack className="p-4 border-b border-gray-200 items-center">
          {/* Student Info */}
          <VStack className="flex-1" space="xs">
            <Text className="font-medium text-gray-900">{student.user.name}</Text>
            <Text className="text-sm text-gray-600">{student.user.email}</Text>
          </VStack>

          {/* School Year */}
          <Box className="w-24">
            <Text className="text-sm text-gray-700">{student.school_year}</Text>
          </Box>

          {/* Educational System */}
          <Box className="w-32 md:block hidden">
            <Text className="text-sm text-gray-700">
              {student.educational_system?.name || 'N/A'}
            </Text>
          </Box>

          {/* Status */}
          <Box className="w-20">{getStatusBadge(student.status)}</Box>

          {/* Actions */}
          <Box className="w-12">
            <Pressable
              className="p-2 rounded-md hover:bg-gray-100"
              onPress={() => setShowActionsheet(true)}
              accessibilityRole="button"
              accessibilityLabel={`Abrir menu de ações para ${student.user.name}`}
              accessibilityHint="Toque para ver opções de editar, excluir ou alterar status do aluno"
            >
              <Icon as={MoreVertical} size="sm" className="text-gray-500" />
            </Pressable>
          </Box>
        </HStack>

        {/* Action Sheet */}
        <Actionsheet isOpen={showActionsheet} onClose={() => setShowActionsheet(false)}>
          <ActionsheetBackdrop />
          <ActionsheetContent>
            <ActionsheetDragIndicatorWrapper>
              <ActionsheetDragIndicator />
            </ActionsheetDragIndicatorWrapper>

            <ActionsheetItem
              onPress={() => {
                onView(student);
                setShowActionsheet(false);
              }}
              accessibilityRole="button"
              accessibilityLabel={`Ver perfil de ${student.user.name}`}
            >
              <Icon as={Eye} className="mr-3 text-gray-600" />
              <ActionsheetItemText>Ver Perfil</ActionsheetItemText>
            </ActionsheetItem>

            <ActionsheetItem
              onPress={() => {
                onEdit(student);
                setShowActionsheet(false);
              }}
              accessibilityRole="button"
              accessibilityLabel={`Editar dados de ${student.user.name}`}
            >
              <Icon as={Edit} className="mr-3 text-gray-600" />
              <ActionsheetItemText>Editar</ActionsheetItemText>
            </ActionsheetItem>

            {student.status !== 'active' && (
              <ActionsheetItem
                onPress={() => {
                  onStatusChange(student, 'active');
                  setShowActionsheet(false);
                }}
                accessibilityRole="button"
                accessibilityLabel={`Marcar ${student.user.name} como ativo`}
              >
                <Icon as={UserCheck} className="mr-3 text-green-600" />
                <ActionsheetItemText>Marcar como Ativo</ActionsheetItemText>
              </ActionsheetItem>
            )}

            {student.status !== 'inactive' && (
              <ActionsheetItem
                onPress={() => {
                  onStatusChange(student, 'inactive');
                  setShowActionsheet(false);
                }}
                accessibilityRole="button"
                accessibilityLabel={`Marcar ${student.user.name} como inativo`}
              >
                <Icon as={UserX} className="mr-3 text-yellow-600" />
                <ActionsheetItemText>Marcar como Inativo</ActionsheetItemText>
              </ActionsheetItem>
            )}

            {student.status !== 'graduated' && (
              <ActionsheetItem
                onPress={() => {
                  onStatusChange(student, 'graduated');
                  setShowActionsheet(false);
                }}
                accessibilityRole="button"
                accessibilityLabel={`Marcar ${student.user.name} como formado`}
              >
                <Icon as={GraduationCap} className="mr-3 text-blue-600" />
                <ActionsheetItemText>Marcar como Formado</ActionsheetItemText>
              </ActionsheetItem>
            )}

            <ActionsheetItem
              onPress={() => {
                onDelete(student);
                setShowActionsheet(false);
              }}
              accessibilityRole="button"
              accessibilityLabel={`Excluir aluno ${student.user.name}`}
              accessibilityHint="Atenção: esta ação não pode ser desfeita"
            >
              <Icon as={Trash2} className="mr-3 text-red-600" />
              <ActionsheetItemText className="text-red-600">Excluir</ActionsheetItemText>
            </ActionsheetItem>
          </ActionsheetContent>
        </Actionsheet>
      </>
    );
  }
);

export const StudentListTable: React.FC<StudentListTableProps> = ({
  showAddButton = true,
  onAddStudent,
  onBulkImport,
}) => {
  const router = useRouter();
  const { showToast } = useToast();

  const {
    students,
    totalCount,
    educationalSystems,
    isLoading,
    isUpdating,
    isDeleting,
    error,
    filters,
    currentPage,
    hasNextPage,
    loadMoreStudents,
    refreshStudents,
    updateStudentStatusRecord,
    deleteStudentRecord,
    setSearch,
    setStatusFilter,
    setEducationalSystemFilter,
    setSchoolYearFilter,
    setSortOrder,
    clearFilters,
  } = useStudents();

  // Local state
  const [searchQuery, setSearchQuery] = useState(filters.search || '');
  const [showFilters, setShowFilters] = useState(false);
  const [deleteStudent, setDeleteStudent] = useState<StudentProfile | null>(null);
  const [sortBy, setSortBy] = useState<string>('name');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  // Search with debounce
  React.useEffect(() => {
    const timeoutId = setTimeout(() => {
      setSearch(searchQuery);
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, setSearch]);

  // Handle sorting
  const handleSort = (field: string) => {
    let newDirection: 'asc' | 'desc' = 'asc';
    if (sortBy === field && sortDirection === 'asc') {
      newDirection = 'desc';
    }

    setSortBy(field);
    setSortDirection(newDirection);

    const ordering = newDirection === 'desc' ? `-${field}` : field;
    setSortOrder(ordering);
  };

  // Handle student actions - memoized to prevent unnecessary re-renders
  const handleViewStudent = React.useCallback(
    (student: StudentProfile) => {
      router.push(`/students/${student.id}`);
    },
    [router]
  );

  const handleEditStudent = React.useCallback(
    (student: StudentProfile) => {
      router.push(`/students/${student.id}?edit=true`);
    },
    [router]
  );

  const handleDeleteStudent = React.useCallback((student: StudentProfile) => {
    setDeleteStudent(student);
  }, []);

  const confirmDeleteStudent = React.useCallback(async () => {
    if (!deleteStudent) return;

    try {
      await deleteStudentRecord(deleteStudent.id);
      showToast('success', 'Aluno excluído com sucesso');
      setDeleteStudent(null);
    } catch (error: any) {
      showToast('error', error.message || 'Erro ao excluir aluno');
    }
  }, [deleteStudent, deleteStudentRecord, showToast]);

  const handleStatusChange = React.useCallback(
    async (student: StudentProfile, status: 'active' | 'inactive' | 'graduated') => {
      try {
        await updateStudentStatusRecord(student.id, status);
        showToast('success', 'Status do aluno atualizado com sucesso');
      } catch (error: any) {
        showToast('error', error.message || 'Erro ao atualizar status do aluno');
      }
    },
    [updateStudentStatusRecord, showToast]
  );

  // Filter summary
  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (filters.search) count++;
    if (filters.status) count++;
    if (filters.educational_system) count++;
    if (filters.school_year) count++;
    return count;
  }, [filters]);

  if (error && !students.length) {
    return (
      <Box className="p-8">
        <Center>
          <VStack className="items-center" space="md">
            <Icon as={Users} size="xl" className="text-red-400" />
            <Heading size="lg" className="text-gray-900">
              Erro ao carregar alunos
            </Heading>
            <Text className="text-gray-600 text-center">{error}</Text>
            <Button onPress={refreshStudents}>
              <ButtonText>Tentar Novamente</ButtonText>
            </Button>
          </VStack>
        </Center>
      </Box>
    );
  }

  return (
    <AuthGuard requiredRoles={['school_owner', 'school_admin']}>
      <ErrorBoundary>
        <VStack space="md" className="flex-1">
          {/* Header with search and actions */}
          <VStack space="md">
            {/* Title and action buttons */}
            <HStack className="items-center justify-between">
              <VStack>
                <Heading size="lg" className="text-gray-900">
                  Lista de Alunos
                </Heading>
                <Text className="text-sm text-gray-600">
                  {totalCount} {totalCount === 1 ? 'aluno encontrado' : 'alunos encontrados'}
                </Text>
              </VStack>

              {showAddButton && (
                <HStack space="sm">
                  {onBulkImport && (
                    <Button
                      variant="outline"
                      onPress={onBulkImport}
                      accessibilityLabel="Importar alunos de arquivo CSV"
                      accessibilityHint="Toque para selecionar um arquivo CSV e importar múltiplos alunos"
                    >
                      <ButtonText>Importar CSV</ButtonText>
                    </Button>
                  )}
                  {onAddStudent && (
                    <Button
                      onPress={onAddStudent}
                      style={{ backgroundColor: COLORS.primary }}
                      accessibilityLabel="Adicionar novo aluno"
                      accessibilityHint="Toque para abrir o formulário de criação de aluno"
                    >
                      <ButtonText className="text-white">Adicionar Aluno</ButtonText>
                    </Button>
                  )}
                </HStack>
              )}
            </HStack>

            {/* Search and filters */}
            <VStack space="sm">
              <HStack space="sm" className="items-center">
                {/* Search */}
                <Box className="flex-1">
                  <Input>
                    <HStack className="items-center px-3">
                      <Icon as={Search} size="sm" className="text-gray-400" />
                      <InputField
                        placeholder="Buscar por nome ou email..."
                        value={searchQuery}
                        onChangeText={setSearchQuery}
                        className="flex-1 ml-2"
                        accessibilityLabel="Campo de busca de alunos"
                        accessibilityHint="Digite o nome ou email do aluno que deseja encontrar"
                      />
                    </HStack>
                  </Input>
                </Box>

                {/* Filter toggle */}
                <Button
                  variant="outline"
                  onPress={() => setShowFilters(!showFilters)}
                  className={activeFiltersCount > 0 ? 'border-primary-600' : ''}
                  accessibilityLabel={`${showFilters ? 'Ocultar' : 'Mostrar'} filtros de busca`}
                  accessibilityHint={`${
                    activeFiltersCount > 0
                      ? `${activeFiltersCount} filtro${activeFiltersCount > 1 ? 's' : ''} ativo${
                          activeFiltersCount > 1 ? 's' : ''
                        }`
                      : 'Nenhum filtro ativo'
                  }`}
                >
                  <HStack space="xs" className="items-center">
                    <Icon as={Filter} size="sm" />
                    <ButtonText>
                      Filtros {activeFiltersCount > 0 && `(${activeFiltersCount})`}
                    </ButtonText>
                    <Icon as={showFilters ? ChevronUp : ChevronDown} size="xs" />
                  </HStack>
                </Button>
              </HStack>

              {/* Filter Panel */}
              {showFilters && (
                <Box className="p-4 rounded-lg border border-gray-200 bg-gray-50">
                  <VStack space="md">
                    <HStack space="md" className="flex-wrap">
                      {/* Status filter */}
                      <Box className="flex-1 min-w-48">
                        <Text className="text-sm font-medium text-gray-700 mb-1">Status</Text>
                        <Select
                          selectedValue={filters.status || ''}
                          onValueChange={value => setStatusFilter(value || undefined)}
                        >
                          <SelectTrigger>
                            <SelectInput placeholder="Todos os status" />
                            <SelectIcon as={ChevronDown} />
                          </SelectTrigger>
                          <SelectPortal>
                            <SelectBackdrop />
                            <SelectContent>
                              <SelectDragIndicatorWrapper>
                                <SelectDragIndicator />
                              </SelectDragIndicatorWrapper>
                              <SelectItem label="Todos os status" value="" />
                              <SelectItem label="Ativo" value="active" />
                              <SelectItem label="Inativo" value="inactive" />
                              <SelectItem label="Formado" value="graduated" />
                            </SelectContent>
                          </SelectPortal>
                        </Select>
                      </Box>

                      {/* Educational System filter */}
                      <Box className="flex-1 min-w-48">
                        <Text className="text-sm font-medium text-gray-700 mb-1">
                          Sistema Educacional
                        </Text>
                        <Select
                          selectedValue={filters.educational_system?.toString() || ''}
                          onValueChange={value =>
                            setEducationalSystemFilter(value ? parseInt(value) : undefined)
                          }
                        >
                          <SelectTrigger>
                            <SelectInput placeholder="Todos os sistemas" />
                            <SelectIcon as={ChevronDown} />
                          </SelectTrigger>
                          <SelectPortal>
                            <SelectBackdrop />
                            <SelectContent>
                              <SelectDragIndicatorWrapper>
                                <SelectDragIndicator />
                              </SelectDragIndicatorWrapper>
                              <SelectItem label="Todos os sistemas" value="" />
                              {educationalSystems.map(system => (
                                <SelectItem
                                  key={system.id}
                                  label={system.name}
                                  value={system.id.toString()}
                                />
                              ))}
                            </SelectContent>
                          </SelectPortal>
                        </Select>
                      </Box>

                      {/* School Year filter */}
                      <Box className="flex-1 min-w-48">
                        <Text className="text-sm font-medium text-gray-700 mb-1">Ano Escolar</Text>
                        <Select
                          selectedValue={filters.school_year || ''}
                          onValueChange={value => setSchoolYearFilter(value || undefined)}
                        >
                          <SelectTrigger>
                            <SelectInput placeholder="Todos os anos" />
                            <SelectIcon as={ChevronDown} />
                          </SelectTrigger>
                          <SelectPortal>
                            <SelectBackdrop />
                            <SelectContent>
                              <SelectDragIndicatorWrapper>
                                <SelectDragIndicator />
                              </SelectDragIndicatorWrapper>
                              <SelectItem label="Todos os anos" value="" />
                              {SCHOOL_YEARS.map(year => (
                                <SelectItem key={year} label={year} value={year} />
                              ))}
                            </SelectContent>
                          </SelectPortal>
                        </Select>
                      </Box>
                    </HStack>

                    {/* Filter actions */}
                    <HStack space="sm" className="justify-end">
                      <Button variant="outline" size="sm" onPress={clearFilters}>
                        <ButtonText>Limpar Filtros</ButtonText>
                      </Button>
                    </HStack>
                  </VStack>
                </Box>
              )}
            </VStack>
          </VStack>

          {/* Table */}
          <Box
            className="flex-1 rounded-lg border border-gray-200"
            style={{ backgroundColor: COLORS.white }}
          >
            {/* Table Header */}
            <HStack className="p-4 border-b border-gray-200 bg-gray-50">
              <Pressable
                className="flex-1 flex-row items-center"
                onPress={() => handleSort('user__name')}
                accessibilityRole="button"
                accessibilityLabel={`Ordenar por nome ${
                  sortBy === 'user__name'
                    ? sortDirection === 'asc'
                      ? 'em ordem decrescente'
                      : 'em ordem crescente'
                    : 'em ordem crescente'
                }`}
              >
                <Text className="font-medium text-gray-700">Nome</Text>
                {sortBy === 'user__name' && (
                  <Icon
                    as={sortDirection === 'asc' ? SortAsc : SortDesc}
                    size="xs"
                    className="ml-1 text-gray-600"
                  />
                )}
              </Pressable>

              <Pressable
                className="w-24 flex-row items-center"
                onPress={() => handleSort('school_year')}
                accessibilityRole="button"
                accessibilityLabel={`Ordenar por ano escolar ${
                  sortBy === 'school_year'
                    ? sortDirection === 'asc'
                      ? 'em ordem decrescente'
                      : 'em ordem crescente'
                    : 'em ordem crescente'
                }`}
              >
                <Text className="font-medium text-gray-700">Ano</Text>
                {sortBy === 'school_year' && (
                  <Icon
                    as={sortDirection === 'asc' ? SortAsc : SortDesc}
                    size="xs"
                    className="ml-1 text-gray-600"
                  />
                )}
              </Pressable>

              <Box className="w-32 md:block hidden">
                <Text className="font-medium text-gray-700">Sistema</Text>
              </Box>

              <Box className="w-20">
                <Text className="font-medium text-gray-700">Status</Text>
              </Box>

              <Box className="w-12">
                <Text className="font-medium text-gray-700">Ações</Text>
              </Box>
            </HStack>

            {/* Table Body */}
            {isLoading && students.length === 0 ? (
              <Box className="p-8">
                <Center>
                  <VStack className="items-center" space="md">
                    <Spinner size="large" />
                    <Text className="text-gray-500">Carregando alunos...</Text>
                  </VStack>
                </Center>
              </Box>
            ) : students.length === 0 ? (
              <Box className="p-8">
                <Center>
                  <VStack className="items-center" space="md">
                    <Icon as={Users} size="xl" className="text-gray-400" />
                    <Heading size="lg" className="text-gray-900">
                      Nenhum aluno encontrado
                    </Heading>
                    <Text className="text-gray-600 text-center">
                      {activeFiltersCount > 0
                        ? 'Tente ajustar os filtros para encontrar alunos.'
                        : 'Adicione o primeiro aluno para começar.'}
                    </Text>
                    {activeFiltersCount > 0 && (
                      <Button variant="outline" onPress={clearFilters}>
                        <ButtonText>Limpar Filtros</ButtonText>
                      </Button>
                    )}
                  </VStack>
                </Center>
              </Box>
            ) : (
              <ScrollView className="flex-1">
                <VStack>
                  {students.map(student => (
                    <StudentRow
                      key={student.id}
                      student={student}
                      onView={handleViewStudent}
                      onEdit={handleEditStudent}
                      onDelete={handleDeleteStudent}
                      onStatusChange={handleStatusChange}
                    />
                  ))}

                  {/* Load More Button */}
                  {hasNextPage && (
                    <Box className="p-4 border-t border-gray-200">
                      <Center>
                        <Button variant="outline" onPress={loadMoreStudents} disabled={isLoading}>
                          {isLoading ? (
                            <HStack space="xs" className="items-center">
                              <Spinner size="small" />
                              <ButtonText>Carregando...</ButtonText>
                            </HStack>
                          ) : (
                            <ButtonText>Carregar Mais</ButtonText>
                          )}
                        </Button>
                      </Center>
                    </Box>
                  )}
                </VStack>
              </ScrollView>
            )}
          </Box>

          {/* Delete Confirmation Dialog */}
          <AlertDialog isOpen={!!deleteStudent} onClose={() => setDeleteStudent(null)}>
            <AlertDialogBackdrop />
            <AlertDialogContent>
              <AlertDialogHeader>
                <Heading size="lg">Confirmar Exclusão</Heading>
                <AlertDialogCloseButton />
              </AlertDialogHeader>
              <AlertDialogBody>
                <Text>
                  Tem certeza que deseja excluir o aluno{' '}
                  <Text className="font-semibold">{deleteStudent?.user.name}</Text>? Esta ação não
                  pode ser desfeita.
                </Text>
              </AlertDialogBody>
              <AlertDialogFooter>
                <HStack space="sm" className="justify-end">
                  <Button
                    variant="outline"
                    onPress={() => setDeleteStudent(null)}
                    disabled={isDeleting}
                  >
                    <ButtonText>Cancelar</ButtonText>
                  </Button>
                  <Button
                    onPress={confirmDeleteStudent}
                    disabled={isDeleting}
                    style={{ backgroundColor: COLORS.error }}
                  >
                    {isDeleting ? (
                      <HStack space="xs" className="items-center">
                        <Spinner size="small" />
                        <ButtonText className="text-white">Excluindo...</ButtonText>
                      </HStack>
                    ) : (
                      <ButtonText className="text-white">Excluir</ButtonText>
                    )}
                  </Button>
                </HStack>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </VStack>
      </ErrorBoundary>
    </AuthGuard>
  );
};
