import { useRouter } from 'expo-router';
import {
  UserPlus,
  Mail,
  Plus,
  AlertCircle,
  Users,
  GraduationCap,
  Building,
  Eye,
  Filter,
  MoreVertical,
  CheckSquare,
  Activity,
  ExternalLink,
  MessageCircle,
  Settings,
} from 'lucide-react-native';
import React, { useState, useEffect } from 'react';

import { useUserProfile } from '@/api/auth';
import { getTeachers, TeacherProfile } from '@/api/userApi';
import { MainLayout } from '@/components/layouts/MainLayout';
import { AddStudentModal } from '@/components/modals/AddStudentModal';
import { AddTeacherModal } from '@/components/modals/AddTeacherModal';
import { BulkImportStudentsModal } from '@/components/modals/BulkImportStudentsModal';
import { InviteTeacherModal } from '@/components/modals/InviteTeacherModal';
import { StudentListTable } from '@/components/students/StudentListTable';
import { BulkTeacherActions } from '@/components/teachers/BulkTeacherActions';
import { ProfileCompletionIndicator } from '@/components/teachers/ProfileCompletionIndicator';
import { TeacherAnalyticsDashboard } from '@/components/teachers/TeacherAnalyticsDashboard';
import { TeacherCommunicationPanel } from '@/components/teachers/TeacherCommunicationPanel';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Checkbox } from '@/components/ui/checkbox';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Menu } from '@/components/ui/menu';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useTeachers } from '@/hooks/useTeachers';

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
} as const;

type TabType = 'teachers' | 'students' | 'staff';
type TeacherViewMode = 'list' | 'analytics' | 'communication';

interface TabInfo {
  key: TabType;
  title: string;
}

interface ActionButtonProps {
  icon: any;
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'tertiary';
}

const ActionButton = ({ icon, title, onPress, variant = 'secondary' }: ActionButtonProps) => {
  const getButtonStyles = () => {
    switch (variant) {
      case 'primary':
        return {
          backgroundColor: COLORS.primary,
          borderColor: COLORS.primary,
        };
      case 'secondary':
        return {
          backgroundColor: COLORS.secondary,
          borderColor: COLORS.secondary,
        };
      case 'tertiary':
        return {
          backgroundColor: COLORS.white,
          borderColor: COLORS.gray[300],
        };
      default:
        return {
          backgroundColor: COLORS.white,
          borderColor: COLORS.gray[300],
        };
    }
  };

  const buttonStyles = getButtonStyles();
  const isLight = variant === 'tertiary';

  return (
    <Pressable
      className="rounded-md border px-3 py-2"
      style={{ ...buttonStyles, marginHorizontal: 2 }}
      onPress={onPress}
    >
      <HStack className="items-center" space="xs">
        <Icon as={icon} size="xs" className={isLight ? 'text-gray-700' : 'text-white'} />
        <Text className={`text-xs font-medium ${isLight ? 'text-gray-700' : 'text-white'}`}>
          {title}
        </Text>
      </HStack>
    </Pressable>
  );
};

interface TabHeaderProps {
  tabs: TabInfo[];
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

const TabHeader = ({ tabs, activeTab, onTabChange }: TabHeaderProps) => {
  const [hoveredTab, setHoveredTab] = React.useState<TabType | null>(null);

  return (
    <HStack className="w-full border-b border-gray-200">
      {tabs.map((tab, index) => {
        const isActive = activeTab === tab.key;
        const isHovered = hoveredTab === tab.key;
        const isLastTab = index === tabs.length - 1;

        return (
          <Pressable
            key={tab.key}
            className="flex-1 py-4 px-2"
            style={{
              backgroundColor: isActive
                ? `${COLORS.primary}10`
                : isHovered
                ? `${COLORS.gray[100]}80`
                : 'transparent',
              borderRightWidth: isLastTab ? 0 : 1,
              borderRightColor: COLORS.gray[200],
            }}
            onPress={() => onTabChange(tab.key)}
            onPressIn={() => setHoveredTab(tab.key)}
            onPressOut={() => setHoveredTab(null)}
            // Web hover states
            {...(typeof window !== 'undefined' && {
              onMouseEnter: () => setHoveredTab(tab.key),
              onMouseLeave: () => setHoveredTab(null),
            })}
          >
            <VStack className="items-center">
              <Text
                className={`text-base ${isActive ? 'font-bold' : 'font-medium'}`}
                style={{
                  color: isActive ? COLORS.primary : COLORS.gray[500],
                }}
              >
                {tab.title}
              </Text>
            </VStack>
          </Pressable>
        );
      })}
    </HStack>
  );
};

interface TeachersTabProps {
  teachers: TeacherProfile[];
  onAddTeacher: () => void;
  onInviteTeacher: () => void;
  onAddManually: () => void;
  userHasTeacherProfile: boolean;
  onRefresh?: () => void;
}

const TeachersTab = ({
  teachers,
  onAddTeacher,
  onInviteTeacher,
  onAddManually,
  userHasTeacherProfile,
  onRefresh,
}: TeachersTabProps) => {
  const router = useRouter();
  const [viewMode, setViewMode] = useState<TeacherViewMode>('list');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTeachers, setSelectedTeachers] = useState<Set<number>>(new Set());
  const [completionFilter, setCompletionFilter] = useState<
    'all' | 'complete' | 'incomplete' | 'critical'
  >('all');
  const [showFilters, setShowFilters] = useState(false);

  // Filter teachers based on search and completion status
  const filteredTeachers = React.useMemo(() => {
    let filtered = teachers;

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        teacher =>
          teacher.user.name.toLowerCase().includes(query) ||
          teacher.user.email.toLowerCase().includes(query) ||
          teacher.specialty?.toLowerCase().includes(query) ||
          teacher.bio?.toLowerCase().includes(query)
      );
    }

    // Apply completion filter
    if (completionFilter !== 'all') {
      filtered = filtered.filter(teacher => {
        const completionScore = teacher.profile_completion_score || 0;
        const hasCritical = teacher.profile_completion?.missing_critical?.length > 0;

        switch (completionFilter) {
          case 'complete':
            return teacher.is_profile_complete && completionScore >= 80;
          case 'critical':
            return hasCritical || completionScore < 30;
          case 'incomplete':
            return !teacher.is_profile_complete && completionScore < 80 && !hasCritical;
          default:
            return true;
        }
      });
    }

    return filtered;
  }, [teachers, searchQuery, completionFilter]);

  const handleSelectTeacher = (teacherId: number, selected: boolean) => {
    const newSelected = new Set(selectedTeachers);
    if (selected) {
      newSelected.add(teacherId);
    } else {
      newSelected.delete(teacherId);
    }
    setSelectedTeachers(newSelected);
  };

  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      setSelectedTeachers(new Set(filteredTeachers.map(t => t.id)));
    } else {
      setSelectedTeachers(new Set());
    }
  };

  const handleViewTeacherProfile = (teacherId: number) => {
    router.push(`/teachers/${teacherId}`);
  };

  const handleClearSelection = () => {
    setSelectedTeachers(new Set());
  };

  const handleSendMessage = (teacherId: number) => {
    // TODO: Open message modal for specific teacher
    if (__DEV__) {
      console.log('Send message to teacher:', teacherId);
    }
  };

  const handleTeacherActions = (teacherId: number) => {
    // TODO: Show action menu for specific teacher
    if (__DEV__) {
      console.log('Show actions for teacher:', teacherId);
    }
  };

  const getLastActivityText = (teacher: TeacherProfile): string => {
    if (teacher.last_activity) {
      const date = new Date(teacher.last_activity);
      const now = new Date();
      const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

      if (diffDays === 0) return 'Hoje';
      if (diffDays === 1) return 'Ontem';
      if (diffDays < 7) return `${diffDays} dias atrás`;
      if (diffDays < 30) return `${Math.floor(diffDays / 7)} semanas atrás`;
      return date.toLocaleDateString('pt-BR');
    }
    return 'Nunca';
  };

  const getCoursesText = (teacher: TeacherProfile): string => {
    const courses = teacher.teacher_courses?.filter(c => c.is_active) || [];
    if (courses.length === 0) return 'Nenhum curso';
    if (courses.length === 1) return courses[0].course_name;
    return `${courses.length} cursos`;
  };

  const renderViewModeContent = () => {
    switch (viewMode) {
      case 'analytics':
        return (
          <TeacherAnalyticsDashboard
            onRefresh={onRefresh}
            onViewTeacher={handleViewTeacherProfile}
          />
        );
      case 'communication':
        return (
          <TeacherCommunicationPanel
            teachers={teachers}
            selectedTeachers={Array.from(selectedTeachers)}
            onTeacherSelect={handleSelectTeacher}
            onSelectAll={handleSelectAll}
            onRefresh={onRefresh}
          />
        );
      default:
        return renderTeachersList();
    }
  };

  const renderTeachersList = () => (
    <>
      {/* Search and Filters */}
      <VStack space="sm">
        <HStack space="sm" className="items-center">
          <Box className="flex-1">
            <Input className="bg-white">
              <InputField
                placeholder="Buscar professores..."
                value={searchQuery}
                onChangeText={setSearchQuery}
              />
            </Input>
          </Box>
          <Pressable
            onPress={() => setShowFilters(!showFilters)}
            className={`p-2 rounded-md border ${
              showFilters ? 'bg-blue-50 border-blue-300' : 'bg-white border-gray-300'
            }`}
          >
            <Icon
              as={Filter}
              size="sm"
              className={showFilters ? 'text-blue-600' : 'text-gray-500'}
            />
          </Pressable>
        </HStack>

        {showFilters && (
          <HStack space="sm" className="flex-wrap">
            {(['all', 'complete', 'incomplete', 'critical'] as const).map(filter => (
              <Pressable
                key={filter}
                onPress={() => setCompletionFilter(filter)}
                className={`px-3 py-1 rounded-full border ${
                  completionFilter === filter
                    ? 'bg-blue-100 border-blue-300'
                    : 'bg-white border-gray-300'
                }`}
              >
                <Text
                  className={`text-sm ${
                    completionFilter === filter ? 'text-blue-700' : 'text-gray-600'
                  }`}
                >
                  {filter === 'all'
                    ? 'Todos'
                    : filter === 'complete'
                    ? 'Completos'
                    : filter === 'incomplete'
                    ? 'Incompletos'
                    : 'Críticos'}
                </Text>
              </Pressable>
            ))}
          </HStack>
        )}
      </VStack>

      {/* Teachers Table */}
      <Box className="rounded-lg border border-gray-200 bg-white">
        <VStack>
          {/* Table header */}
          <HStack className="p-4 border-b border-gray-200 items-center">
            <Box className="w-8">
              <Checkbox
                value={
                  selectedTeachers.size > 0 && selectedTeachers.size === filteredTeachers.length
                }
                onValueChange={handleSelectAll}
              />
            </Box>
            <Text className="flex-1 font-medium text-gray-700">Professor</Text>
            <Text className="w-32 font-medium text-gray-700">Perfil</Text>
            <Text className="w-24 font-medium text-gray-700">Cursos</Text>
            <Text className="w-24 font-medium text-gray-700">Atividade</Text>
            <Text className="w-20 font-medium text-gray-700">Status</Text>
            <Text className="w-20 font-medium text-gray-700">Ações</Text>
          </HStack>

          {filteredTeachers.length === 0 ? (
            /* Empty state */
            <Box className="p-8">
              <Center>
                <VStack className="items-center" space="xs">
                  <Icon as={GraduationCap} size="lg" className="text-gray-400" />
                  <Text className="text-gray-500">
                    {searchQuery || completionFilter !== 'all'
                      ? 'Nenhum professor encontrado'
                      : 'Nenhum professor cadastrado'}
                  </Text>
                  <Text className="text-gray-400 text-sm text-center">
                    {searchQuery || completionFilter !== 'all'
                      ? 'Tente ajustar os filtros de busca'
                      : 'Use os botões acima para adicionar professores'}
                  </Text>
                </VStack>
              </Center>
            </Box>
          ) : (
            /* Teachers list */
            filteredTeachers.map((teacher, index) => (
              <HStack
                key={teacher.id}
                className={`p-4 items-center ${
                  index < filteredTeachers.length - 1 ? 'border-b border-gray-200' : ''
                }`}
              >
                {/* Selection checkbox */}
                <Box className="w-8">
                  <Checkbox
                    value={selectedTeachers.has(teacher.id)}
                    onValueChange={selected => handleSelectTeacher(teacher.id, selected)}
                  />
                </Box>

                {/* Teacher info */}
                <VStack className="flex-1" space="xs">
                  <Text className="font-medium text-gray-900">{teacher.user.name}</Text>
                  <Text className="text-sm text-gray-600">{teacher.user.email}</Text>
                  {teacher.specialty && (
                    <Text className="text-xs text-gray-500">{teacher.specialty}</Text>
                  )}
                </VStack>

                {/* Profile completion */}
                <Box className="w-32">
                  <ProfileCompletionIndicator
                    completionPercentage={teacher.profile_completion_score || 0}
                    isComplete={teacher.is_profile_complete || false}
                    missingCritical={teacher.profile_completion?.missing_critical}
                    variant="compact"
                    onViewDetails={() => handleViewTeacherProfile(teacher.id)}
                  />
                </Box>

                {/* Courses */}
                <Box className="w-24">
                  <Text className="text-sm text-gray-600">{getCoursesText(teacher)}</Text>
                </Box>

                {/* Last activity */}
                <Box className="w-24">
                  <Text className="text-xs text-gray-500">{getLastActivityText(teacher)}</Text>
                </Box>

                {/* Status */}
                <Box className="w-20">
                  <Badge
                    variant={
                      teacher.status === 'active'
                        ? 'success'
                        : teacher.status === 'inactive'
                        ? 'secondary'
                        : 'outline'
                    }
                    size="sm"
                  >
                    {teacher.status === 'active'
                      ? 'Ativo'
                      : teacher.status === 'inactive'
                      ? 'Inativo'
                      : 'Pendente'}
                  </Badge>
                </Box>

                {/* Actions */}
                <HStack className="w-20" space="xs">
                  <Pressable
                    onPress={() => handleViewTeacherProfile(teacher.id)}
                    className="p-1 rounded bg-blue-50"
                  >
                    <Icon as={ExternalLink} size="xs" className="text-blue-600" />
                  </Pressable>

                  <Pressable
                    onPress={() => handleSendMessage(teacher.id)}
                    className="p-1 rounded bg-green-50"
                  >
                    <Icon as={MessageCircle} size="xs" className="text-green-600" />
                  </Pressable>

                  <Pressable
                    onPress={() => handleTeacherActions(teacher.id)}
                    className="p-1 rounded bg-gray-50"
                  >
                    <Icon as={MoreVertical} size="xs" className="text-gray-400" />
                  </Pressable>
                </HStack>
              </HStack>
            ))
          )}
        </VStack>
      </Box>
    </>
  );

  return (
    <VStack space="md">
      {/* Header with view mode switcher */}
      <HStack className="w-full items-center justify-between">
        <VStack>
          <Heading size="lg" className="text-gray-900">
            Gestão de Professores
          </Heading>
          <Text className="text-sm text-gray-600">
            {filteredTeachers.length} professor{filteredTeachers.length !== 1 ? 'es' : ''}
            {selectedTeachers.size > 0 &&
              ` • ${selectedTeachers.size} selecionado${selectedTeachers.size > 1 ? 's' : ''}`}
          </Text>
        </VStack>

        <HStack space="sm">
          {!userHasTeacherProfile && (
            <ActionButton
              icon={UserPlus}
              title="Adicionar-me"
              onPress={onAddTeacher}
              variant="primary"
            />
          )}
          <ActionButton
            icon={Mail}
            title="Convidar"
            onPress={onInviteTeacher}
            variant="secondary"
          />
        </HStack>
      </HStack>

      {/* View Mode Switcher */}
      <HStack className="w-full border-b border-gray-200">
        {(['list', 'analytics', 'communication'] as const).map(mode => {
          const isActive = viewMode === mode;

          return (
            <Pressable
              key={mode}
              className="flex-1 py-3 px-4"
              style={{
                backgroundColor: isActive ? `${COLORS.primary}10` : 'transparent',
                borderBottomWidth: isActive ? 2 : 0,
                borderBottomColor: COLORS.primary,
              }}
              onPress={() => setViewMode(mode)}
            >
              <HStack className="items-center justify-center" space="xs">
                <Icon
                  as={mode === 'list' ? Users : mode === 'analytics' ? Activity : MessageCircle}
                  size="sm"
                  className={isActive ? 'text-primary-600' : 'text-gray-500'}
                />
                <Text
                  className={`text-sm font-medium ${
                    isActive ? 'text-primary-600' : 'text-gray-500'
                  }`}
                >
                  {mode === 'list' ? 'Lista' : mode === 'analytics' ? 'Análises' : 'Comunicação'}
                </Text>
              </HStack>
            </Pressable>
          );
        })}
      </HStack>

      {/* Content based on view mode */}
      {renderViewModeContent()}

      {/* Bulk Actions - only show in list mode */}
      {viewMode === 'list' && (
        <BulkTeacherActions
          selectedTeachers={Array.from(selectedTeachers)}
          teachers={teachers}
          onClearSelection={handleClearSelection}
          onActionComplete={() => {
            handleClearSelection();
            onRefresh?.();
          }}
        />
      )}
    </VStack>
  );
};

interface StudentsTabProps {
  onAddStudent: () => void;
  onBulkImport: () => void;
}

const StudentsTab = ({ onAddStudent, onBulkImport }: StudentsTabProps) => {
  return (
    <StudentListTable
      showAddButton={true}
      onAddStudent={onAddStudent}
      onBulkImport={onBulkImport}
    />
  );
};

const StaffTab = () => {
  const handleAddStaff = () => {
    if (__DEV__) {
      console.log('Add staff');
    }
    // TODO: Implement add staff functionality
  };

  return (
    <VStack space="md">
      {/* Staff List with inline action buttons */}
      <HStack className="w-full items-center" space="lg">
        <Heading size="lg" className="text-gray-900">
          Lista de Colaboradores
        </Heading>
        <HStack style={{ paddingHorizontal: 4 }}>
          <ActionButton
            icon={Mail}
            title="Convidar colaborador"
            onPress={handleAddStaff}
            variant="secondary"
          />
        </HStack>
      </HStack>

      <Box className="rounded-lg border border-gray-200" style={{ backgroundColor: COLORS.white }}>
        <VStack>
          {/* Table header */}
          <HStack className="p-4 border-b border-gray-200">
            <Text className="flex-1 font-medium text-gray-700">Nome</Text>
            <Text className="flex-1 font-medium text-gray-700">Email</Text>
            <Text className="flex-1 font-medium text-gray-700">Cargo</Text>
            <Text className="w-20 font-medium text-gray-700">Status</Text>
          </HStack>

          {/* Empty state */}
          <Box className="p-8">
            <Center>
              <VStack className="items-center" space="xs">
                <Icon as={Building} size="lg" className="text-gray-400" />
                <Text className="text-gray-500">Nenhum colaborador cadastrado</Text>
                <Text className="text-gray-400 text-sm text-center">
                  Use os botões acima para adicionar colaboradores
                </Text>
              </VStack>
            </Center>
          </Box>
        </VStack>
      </Box>
    </VStack>
  );
};

export default function UsersPage() {
  const { userProfile } = useUserProfile();
  const [activeTab, setActiveTab] = useState<TabType>('teachers');
  const [isAddTeacherModalOpen, setIsAddTeacherModalOpen] = useState(false);
  const [isInviteTeacherModalOpen, setIsInviteTeacherModalOpen] = useState(false);
  const [isAddStudentModalOpen, setIsAddStudentModalOpen] = useState(false);
  const [isBulkImportModalOpen, setIsBulkImportModalOpen] = useState(false);
  const [teachers, setTeachers] = useState<TeacherProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter tabs based on user role
  const tabs: TabInfo[] = React.useMemo(() => {
    const allTabs: TabInfo[] = [
      {
        key: 'teachers',
        title: 'Professores',
      },
      {
        key: 'students',
        title: 'Alunos',
      },
      {
        key: 'staff',
        title: 'Colaboradores',
      },
    ];

    // Students should not see the student tab
    if (userProfile?.user_type === 'student') {
      return allTabs.filter(tab => tab.key !== 'students');
    }

    // Teachers and admins can see all tabs
    return allTabs;
  }, [userProfile?.user_type]);

  const handleAddMeAsTeacher = () => {
    setIsAddTeacherModalOpen(true);
  };

  const handleInviteTeacher = () => {
    setIsInviteTeacherModalOpen(true);
  };

  const handleAddManually = () => {
    if (__DEV__) {
      console.log('Add manually');
    }
    // TODO: Implement manual user addition functionality
  };

  const handleTeacherProfileSuccess = () => {
    if (__DEV__) {
      console.log('Teacher profile created successfully!');
    }
    // Refresh teachers list
    fetchTeachers();
  };

  const handleInviteSuccess = () => {
    if (__DEV__) {
      console.log('Teacher invitation sent successfully!');
    }
    // Optionally refresh teachers list or show success message
  };

  const handleAddStudent = () => {
    setIsAddStudentModalOpen(true);
  };

  const handleBulkImport = () => {
    setIsBulkImportModalOpen(true);
  };

  const handleBulkImportSuccess = () => {
    if (__DEV__) {
      console.log('Bulk import completed successfully!');
    }
    // Student list will refresh automatically via useStudents hook
  };

  const handleStudentSuccess = () => {
    if (__DEV__) {
      console.log('Student created successfully!');
    }
    // Student list will refresh automatically via useStudents hook
  };

  const fetchTeachers = async () => {
    try {
      setLoading(true);
      setError(null);

      const teachersData = await getTeachers();
      setTeachers(teachersData);
    } catch (error: any) {
      if (__DEV__) {
        console.error('Error fetching teachers:', error); // TODO: Review for sensitive data
      }

      setError('Failed to load teachers. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTeachers();
  }, []);

  // Check if current user has a teacher profile
  const userHasTeacherProfile = React.useMemo(() => {
    if (!userProfile || !teachers.length) return false;
    return teachers.some(teacher => teacher.user.id === userProfile.id);
  }, [userProfile, teachers]);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'teachers':
        return (
          <TeachersTab
            teachers={teachers}
            onAddTeacher={handleAddMeAsTeacher}
            onInviteTeacher={handleInviteTeacher}
            onAddManually={handleAddManually}
            userHasTeacherProfile={userHasTeacherProfile}
            onRefresh={fetchTeachers}
          />
        );
      case 'students':
        return <StudentsTab onAddStudent={handleAddStudent} onBulkImport={handleBulkImport} />;
      case 'staff':
        return <StaffTab />;
      default:
        return (
          <TeachersTab
            teachers={teachers}
            onAddTeacher={handleAddMeAsTeacher}
            onInviteTeacher={handleInviteTeacher}
            onAddManually={handleAddManually}
            userHasTeacherProfile={userHasTeacherProfile}
            onRefresh={fetchTeachers}
          />
        );
    }
  };

  // Show loading if checking auth status
  if (loading && !error) {
    return (
      <MainLayout>
        <Box className="flex-1" style={{ backgroundColor: COLORS.gray[50] }}>
          <Center className="flex-1">
            <VStack className="items-center" space="md">
              <Spinner size="large" />
              <Text className="text-gray-500">Carregando...</Text>
            </VStack>
          </Center>
        </Box>
      </MainLayout>
    );
  }

  // Show general error
  if (error && !loading) {
    return (
      <MainLayout>
        <Box className="flex-1" style={{ backgroundColor: COLORS.gray[50] }}>
          <Center className="flex-1">
            <VStack className="items-center max-w-sm mx-auto" space="lg">
              <Icon as={AlertCircle} size="xl" className="text-red-500" />
              <VStack className="items-center" space="sm">
                <Heading size="lg" className="text-gray-900 text-center">
                  Error Loading Data
                </Heading>
                <Text className="text-gray-600 text-center">{error}</Text>
              </VStack>
              <Button onPress={fetchTeachers} className="w-full bg-primary-600">
                <ButtonText>Try Again</ButtonText>
              </Button>
            </VStack>
          </Center>
        </Box>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <ScrollView
        className="flex-1"
        style={{ backgroundColor: COLORS.gray[50] }}
        showsVerticalScrollIndicator={false}
      >
        <VStack className="p-6" space="xl">
          {/* Tab Header */}
          <TabHeader tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />

          {/* Tab Content */}
          {renderTabContent()}
        </VStack>
      </ScrollView>

      {/* Add Teacher Modal */}
      <AddTeacherModal
        isOpen={isAddTeacherModalOpen}
        onClose={() => setIsAddTeacherModalOpen(false)}
        onSuccess={handleTeacherProfileSuccess}
      />

      {/* Invite Teacher Modal */}
      <InviteTeacherModal
        isOpen={isInviteTeacherModalOpen}
        onClose={() => setIsInviteTeacherModalOpen(false)}
        onSuccess={handleInviteSuccess}
      />

      {/* Add Student Modal */}
      <AddStudentModal
        isOpen={isAddStudentModalOpen}
        onClose={() => setIsAddStudentModalOpen(false)}
        onSuccess={handleStudentSuccess}
      />

      {/* Bulk Import Students Modal */}
      <BulkImportStudentsModal
        isOpen={isBulkImportModalOpen}
        onClose={() => setIsBulkImportModalOpen(false)}
        onSuccess={handleBulkImportSuccess}
      />
    </MainLayout>
  );
}
