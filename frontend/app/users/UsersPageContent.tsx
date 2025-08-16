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
// Simple teacher card component inline for now
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardHeader, CardBody } from '@/components/ui/card';
import { FlatList } from '@/components/ui/flat-list';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
// Removed COLORS import since we're using Tailwind classes

// Types
interface Tab {
  id: string;
  label: string;
  count?: number;
}

interface TabHeaderProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

interface TeachersTabProps {
  onAddTeacher: () => void;
  onInviteTeacher: () => void;
}

interface StudentsTabProps {
  onAddStudent: () => void;
  onBulkImport: () => void;
}

const TabHeader = ({ tabs, activeTab, onTabChange }: TabHeaderProps) => {
  return (
    <HStack className="bg-white rounded-lg border border-border-300 p-1" space="xs">
      {tabs.map(tab => (
        <Pressable
          key={tab.id}
          onPress={() => onTabChange(tab.id)}
          className={`flex-1 py-3 px-4 rounded-md ${
            activeTab === tab.id ? 'bg-primary-500' : 'bg-transparent'
          }`}
        >
          <HStack className="items-center justify-center" space="xs">
            <Text
              className={`text-sm font-medium ${
                activeTab === tab.id ? 'text-white' : 'text-typography-700'
              }`}
            >
              {tab.label}
            </Text>
            {tab.count !== undefined && (
              <Badge
                size="sm"
                variant={activeTab === tab.id ? 'outline' : 'solid'}
                className={activeTab === tab.id ? 'border-white bg-white' : 'bg-background-100'}
              >
                <BadgeText
                  className={`text-xs ${
                    activeTab === tab.id ? 'text-primary-500' : 'text-typography-600'
                  }`}
                >
                  {tab.count}
                </BadgeText>
              </Badge>
            )}
          </HStack>
        </Pressable>
      ))}
    </HStack>
  );
};

const TeachersTab = ({ onAddTeacher, onInviteTeacher }: TeachersTabProps) => {
  const [teachers, setTeachers] = useState<TeacherProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTeachers, setSelectedTeachers] = useState<string[]>([]);
  const [showDetails, setShowDetails] = useState<Record<string, boolean>>({});
  const [filterStatus, setFilterStatus] = useState<string>('all');

  const router = useRouter();

  useEffect(() => {
    loadTeachers();
  }, []);

  const loadTeachers = async () => {
    try {
      setLoading(true);
      const teachersData = await getTeachers();
      setTeachers(teachersData);
    } catch (error) {
      console.error('Error loading teachers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTeacherSelect = (teacherId: string) => {
    setSelectedTeachers(prev =>
      prev.includes(teacherId) ? prev.filter(id => id !== teacherId) : [...prev, teacherId],
    );
  };

  const handleSelectAll = () => {
    if (selectedTeachers.length === teachers.length) {
      setSelectedTeachers([]);
    } else {
      setSelectedTeachers(teachers.map(teacher => teacher.id.toString()));
    }
  };

  const handleViewProfile = (teacherId: string) => {
    router.push(`/teachers/${teacherId}`);
  };

  const toggleDetails = (teacherId: string) => {
    setShowDetails(prev => ({
      ...prev,
      [teacherId]: !prev[teacherId],
    }));
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'text-success-600';
      case 'pending':
        return 'text-warning-600';
      case 'inactive':
        return 'text-error-600';
      default:
        return 'text-typography-600';
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'solid';
      case 'pending':
        return 'outline';
      case 'inactive':
        return 'solid';
      default:
        return 'solid';
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'success';
      case 'pending':
        return 'warning';
      case 'inactive':
        return 'error';
      default:
        return 'muted';
    }
  };

  const filteredTeachers = teachers.filter(teacher => {
    if (filterStatus === 'all') return true;
    return teacher.status?.toLowerCase() === filterStatus.toLowerCase();
  });

  const renderTeacherCard = ({ item: teacher }: { item: TeacherProfile }) => (
    <Card key={teacher.id} className="p-4 bg-white rounded-lg border border-border-200">
      <HStack className="items-center justify-between">
        <VStack className="flex-1">
          <Text className="font-semibold text-typography-900">{teacher.user?.name || 'Unknown Teacher'}</Text>
          <Text className="text-sm text-typography-600">{teacher.user?.email || 'No email'}</Text>
          <Badge className={getStatusBadgeColor(teacher.status || 'pending')} variant={getStatusBadgeVariant(teacher.status || 'pending')}>
            <BadgeText>{teacher.status || 'pending'}</BadgeText>
          </Badge>
        </VStack>
        <Button onPress={() => handleViewProfile(teacher.id.toString())} size="sm" variant="outline">
          <ButtonText>View</ButtonText>
        </Button>
      </HStack>
    </Card>
  );

  if (loading) {
    return (
      <Box className="flex-1 justify-center items-center py-12">
        <Spinner size="large" />
        <Text className="mt-4 text-typography-600">Carregando professores...</Text>
      </Box>
    );
  }

  return (
    <VStack space="lg">
      {/* Actions Row */}
      <HStack className="justify-between items-center">
        <HStack space="md">
          <Button size="sm" onPress={onAddTeacher}>
            <ButtonIcon as={UserPlus} />
            <ButtonText>Adicionar Professor</ButtonText>
          </Button>
          <Button size="sm" variant="outline" onPress={onInviteTeacher}>
            <ButtonIcon as={Mail} />
            <ButtonText>Convidar Professor</ButtonText>
          </Button>
        </HStack>

        {/* Filter Dropdown */}
        <HStack space="sm" className="items-center">
          <Icon as={Filter} size="sm" className="text-typography-600" />
          <Text className="text-sm text-typography-600">Filtrar:</Text>
          <Pressable
            onPress={() => {
              // Toggle filter status: all -> active -> pending -> inactive -> all
              const nextStatus =
                filterStatus === 'all'
                  ? 'active'
                  : filterStatus === 'active'
                    ? 'pending'
                    : filterStatus === 'pending'
                      ? 'inactive'
                      : 'all';
              setFilterStatus(nextStatus);
            }}
            className="px-3 py-1 rounded-md border border-border-300"
          >
            <Text className="text-sm text-typography-700 capitalize">
              {filterStatus === 'all' ? 'Todos' : filterStatus}
            </Text>
          </Pressable>
        </HStack>
      </HStack>

      {/* Bulk Actions */}
      {selectedTeachers.length > 0 && (
        <BulkTeacherActions
          selectedTeachers={selectedTeachers.map(id => parseInt(id))}
          teachers={teachers}
          onClearSelection={() => setSelectedTeachers([])}
          onActionComplete={() => {
            // Refresh teachers list after action
            loadTeachers();
            setSelectedTeachers([]);
          }}
        />
      )}

      {/* Teachers List */}
      {filteredTeachers.length === 0 ? (
        <Card className="py-12">
          <CardBody>
            <VStack className="items-center" space="md">
              <Icon as={Users} size="xl" className="text-typography-400" />
              <Text className="text-lg font-semibold text-typography-700">
                Nenhum professor encontrado
              </Text>
              <Text className="text-center text-typography-600">
                {filterStatus === 'all'
                  ? 'Adicione professores à sua escola para começar.'
                  : `Nenhum professor com status "${filterStatus}" encontrado.`}
              </Text>
              {filterStatus === 'all' && (
                <Button onPress={onAddTeacher}>
                  <ButtonIcon as={Plus} />
                  <ButtonText>Adicionar Primeiro Professor</ButtonText>
                </Button>
              )}
            </VStack>
          </CardBody>
        </Card>
      ) : (
        <FlatList
          data={filteredTeachers}
          renderItem={renderTeacherCard}
          keyExtractor={teacher => teacher.id.toString()}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ gap: 12 }}
        />
      )}

      {/* Stats Summary */}
      {teachers.length > 0 && (
        <Card>
          <CardHeader>
            <Text className="font-semibold text-typography-900">Resumo</Text>
          </CardHeader>
          <CardBody>
            <HStack className="justify-between">
              <VStack className="items-center">
                <Text className="text-2xl font-bold text-success-600">
                  {teachers.filter(t => t.status?.toLowerCase() === 'active').length}
                </Text>
                <Text className="text-sm text-typography-600">Ativos</Text>
              </VStack>
              <VStack className="items-center">
                <Text className="text-2xl font-bold text-warning-600">
                  {teachers.filter(t => t.status?.toLowerCase() === 'pending').length}
                </Text>
                <Text className="text-sm text-typography-600">Pendentes</Text>
              </VStack>
              <VStack className="items-center">
                <Text className="text-2xl font-bold text-error-600">
                  {teachers.filter(t => t.status?.toLowerCase() === 'inactive').length}
                </Text>
                <Text className="text-sm text-typography-600">Inativos</Text>
              </VStack>
              <VStack className="items-center">
                <Text className="text-2xl font-bold text-typography-900">{teachers.length}</Text>
                <Text className="text-sm text-typography-600">Total</Text>
              </VStack>
            </HStack>
          </CardBody>
        </Card>
      )}
    </VStack>
  );
};

const StudentsTab = ({ onAddStudent, onBulkImport }: StudentsTabProps) => {
  return (
    <VStack space="lg">
      {/* Actions Row */}
      <HStack className="justify-between items-center">
        <HStack space="md">
          <Button size="sm" onPress={onAddStudent}>
            <ButtonIcon as={UserPlus} />
            <ButtonText>Adicionar Aluno</ButtonText>
          </Button>
          <Button size="sm" variant="outline" onPress={onBulkImport}>
            <ButtonIcon as={Plus} />
            <ButtonText>Importar em Lote</ButtonText>
          </Button>
        </HStack>
      </HStack>

      {/* Students Table */}
      <StudentListTable />
    </VStack>
  );
};

const StaffTab = () => {
  return (
    <Card className="py-12">
      <CardBody>
        <VStack className="items-center" space="md">
          <Icon as={Building} size="xl" className="text-typography-400" />
          <Text className="text-lg font-semibold text-typography-700">Funcionários</Text>
          <Text className="text-center text-typography-600">
            Funcionalidade de gerenciamento de funcionários em breve.
          </Text>
        </VStack>
      </CardBody>
    </Card>
  );
};

export default function UsersPageContent() {
  const { userProfile } = useUserProfile();
  const [activeTab, setActiveTab] = useState('teachers');
  const [isAddTeacherModalOpen, setIsAddTeacherModalOpen] = useState(false);
  const [isInviteTeacherModalOpen, setIsInviteTeacherModalOpen] = useState(false);
  const [isAddStudentModalOpen, setIsAddStudentModalOpen] = useState(false);
  const [isBulkImportModalOpen, setIsBulkImportModalOpen] = useState(false);

  // Mock counts for tabs - in real app, get from API
  const tabs: Tab[] = [
    { id: 'teachers', label: 'Professores', count: 12 },
    { id: 'students', label: 'Alunos', count: 148 },
    { id: 'staff', label: 'Funcionários', count: 5 },
  ];

  const handleTeacherProfileSuccess = () => {
    setIsAddTeacherModalOpen(false);
    // Refresh teachers list if on teachers tab
  };

  const handleInviteSuccess = () => {
    setIsInviteTeacherModalOpen(false);
    // Show success message or refresh list
  };

  const handleStudentSuccess = () => {
    setIsAddStudentModalOpen(false);
    // Refresh students list if on students tab
  };

  const handleBulkImportSuccess = () => {
    setIsBulkImportModalOpen(false);
    // Refresh students list
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'teachers':
        return (
          <TeachersTab
            onAddTeacher={() => setIsAddTeacherModalOpen(true)}
            onInviteTeacher={() => setIsInviteTeacherModalOpen(true)}
          />
        );
      case 'students':
        return (
          <StudentsTab
            onAddStudent={() => setIsAddStudentModalOpen(true)}
            onBulkImport={() => setIsBulkImportModalOpen(true)}
          />
        );
      case 'staff':
        return <StaffTab />;
      default:
        return null;
    }
  };

  return (
    <MainLayout>
      <ScrollView
        className="flex-1"
        style={{ backgroundColor: '#f9fafb' }}
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
