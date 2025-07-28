import {
  UserPlus,
  Mail,
  Plus,
  AlertCircle,
  Users,
  GraduationCap,
  Building,
} from 'lucide-react-native';
import React, { useState, useEffect } from 'react';

import { useAuth } from '@/api/authContext';
import { getTeachers, TeacherProfile } from '@/api/userApi';
import { MainLayout } from '@/components/layouts/main-layout';
import { AddStudentModal } from '@/components/modals/add-student-modal';
import { AddTeacherModal } from '@/components/modals/add-teacher-modal';
import { InviteTeacherModal } from '@/components/modals/invite-teacher-modal';
import { BulkImportStudentsModal } from '@/components/modals/bulk-import-students-modal';
import { StudentListTable } from '@/components/students/StudentListTable';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

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
}

const TeachersTab = ({
  teachers,
  onAddTeacher,
  onInviteTeacher,
  onAddManually,
  userHasTeacherProfile,
}: TeachersTabProps) => {
  return (
    <VStack space="md">
      {/* Teachers List with inline action buttons */}
      <HStack className="w-full items-center" space="lg">
        <Heading size="lg" className="text-gray-900">
          Lista de Professores
        </Heading>
        <HStack style={{ paddingHorizontal: 4 }}>
          {!userHasTeacherProfile && (
            <ActionButton
              icon={UserPlus}
              title="Adicionar-me como professor"
              onPress={onAddTeacher}
              variant="primary"
            />
          )}
          <ActionButton
            icon={Mail}
            title="Convidar professor"
            onPress={onInviteTeacher}
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
            <Text className="flex-1 font-medium text-gray-700">Especialidade</Text>
            <Text className="w-20 font-medium text-gray-700">Status</Text>
          </HStack>

          {teachers.length === 0 ? (
            /* Empty state */
            <Box className="p-8">
              <Center>
                <VStack className="items-center" space="xs">
                  <Icon as={GraduationCap} size="lg" className="text-gray-400" />
                  <Text className="text-gray-500">Nenhum professor cadastrado</Text>
                  <Text className="text-gray-400 text-sm text-center">
                    Use os botões acima para adicionar professores
                  </Text>
                </VStack>
              </Center>
            </Box>
          ) : (
            /* Teachers list */
            teachers.map((teacher, index) => (
              <HStack
                key={teacher.id}
                className={`p-4 ${index < teachers.length - 1 ? 'border-b border-gray-200' : ''}`}
              >
                <Text className="flex-1 text-gray-900">{teacher.user.name}</Text>
                <Text className="flex-1 text-gray-600">{teacher.user.email}</Text>
                <Text className="flex-1 text-gray-600">
                  {teacher.specialty || 'Não especificado'}
                </Text>
                <Text className="w-20 text-green-600 text-sm">Ativo</Text>
              </HStack>
            ))
          )}
        </VStack>
      </Box>
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
    console.log('Add staff');
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
  const { userProfile } = useAuth();
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
    console.log('Add manually');
    // TODO: Implement manual user addition functionality
  };

  const handleTeacherProfileSuccess = () => {
    console.log('Teacher profile created successfully!');
    // Refresh teachers list
    fetchTeachers();
  };

  const handleInviteSuccess = () => {
    console.log('Teacher invitation sent successfully!');
    // Optionally refresh teachers list or show success message
  };

  const handleAddStudent = () => {
    setIsAddStudentModalOpen(true);
  };

  const handleBulkImport = () => {
    setIsBulkImportModalOpen(true);
  };

  const handleBulkImportSuccess = () => {
    console.log('Bulk import completed successfully!');
    // Student list will refresh automatically via useStudents hook
  };

  const handleStudentSuccess = () => {
    console.log('Student created successfully!');
    // Student list will refresh automatically via useStudents hook
  };

  const fetchTeachers = async () => {
    try {
      setLoading(true);
      setError(null);

      const teachersData = await getTeachers();
      setTeachers(teachersData);
    } catch (error: any) {
      console.error('Error fetching teachers:', error);

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
