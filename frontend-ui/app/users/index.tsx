import { UserPlus, Mail, Plus } from 'lucide-react-native';
import React, { useState, useEffect } from 'react';

import { getTeachers, TeacherProfile } from '@/api/userApi';
import { MainLayout } from '@/components/layouts/main-layout';
import { AddTeacherModal } from '@/components/modals/add-teacher-modal';
import { Box } from '@/components/ui/box';
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
      className="flex-1 rounded-lg border px-6 py-4"
      style={{ ...buttonStyles, marginHorizontal: 4 }}
      onPress={onPress}
    >
      <HStack className="items-center justify-center" space="sm">
        <Icon as={icon} size="sm" className={isLight ? 'text-gray-700' : 'text-white'} />
        <Text className={`text-sm font-medium ${isLight ? 'text-gray-700' : 'text-white'}`}>
          {title}
        </Text>
      </HStack>
    </Pressable>
  );
};

const UserTypeCard = ({
  title,
  count,
  variant,
}: {
  title: string;
  count: number;
  variant: 'primary' | 'secondary' | 'tertiary';
}) => {
  const getCardStyles = () => {
    switch (variant) {
      case 'primary':
        return {
          backgroundColor: COLORS.primary,
        };
      case 'secondary':
        return {
          backgroundColor: COLORS.secondary,
        };
      case 'tertiary':
        return {
          backgroundColor: COLORS.secondary,
        };
      default:
        return {
          backgroundColor: COLORS.primary,
        };
    }
  };

  return (
    <Box className="flex-1 rounded-lg p-4" style={{ ...getCardStyles(), marginHorizontal: 8 }}>
      <VStack className="items-center" space="xs">
        <Text className="text-white text-lg font-bold">{title}</Text>
        <Text className="text-white text-sm">{count} ativos</Text>
      </VStack>
    </Box>
  );
};

export default function UsersPage() {
  const [isAddTeacherModalOpen, setIsAddTeacherModalOpen] = useState(false);
  const [teachers, setTeachers] = useState<TeacherProfile[]>([]);
  const [loading, setLoading] = useState(true);

  const handleAddMeAsTeacher = () => {
    setIsAddTeacherModalOpen(true);
  };

  const handleInviteTeacher = () => {
    console.log('Invite teacher');
    // TODO: Implement invite teacher functionality
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

  const fetchTeachers = async () => {
    try {
      setLoading(true);
      const teachersData = await getTeachers();
      setTeachers(teachersData);
    } catch (error) {
      console.error('Error fetching teachers:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTeachers();
  }, []);

  return (
    <MainLayout>
      <ScrollView
        className="flex-1"
        style={{ backgroundColor: COLORS.gray[50] }}
        showsVerticalScrollIndicator={false}
      >
        <VStack className="p-6" space="xl">
          {/* User Type Cards */}
          <HStack className="w-full" style={{ paddingHorizontal: 8 }}>
            <UserTypeCard title="Professores" count={teachers.length} variant="primary" />
            <UserTypeCard title="Alunos" count={0} variant="secondary" />
            <UserTypeCard title="Colaboradores" count={0} variant="tertiary" />
          </HStack>

          {/* Action Buttons */}
          <VStack space="md">
            <Heading size="md" className="text-gray-900">
              Ações Rápidas
            </Heading>
            <HStack className="w-full" style={{ paddingHorizontal: 4 }}>
              <ActionButton
                icon={UserPlus}
                title="Adicionar-me como professor"
                onPress={handleAddMeAsTeacher}
                variant="primary"
              />
              <ActionButton
                icon={Mail}
                title="Convidar professor"
                onPress={handleInviteTeacher}
                variant="secondary"
              />
              <ActionButton
                icon={Plus}
                title="Adicionar manualmente"
                onPress={handleAddManually}
                variant="tertiary"
              />
            </HStack>
          </VStack>

          {/* Users List Section */}
          <VStack space="md">
            <Heading size="lg" className="text-gray-900">
              Lista de Professores
            </Heading>

            <Box
              className="rounded-lg border border-gray-200"
              style={{ backgroundColor: COLORS.white }}
            >
              <VStack>
                {/* Table header */}
                <HStack className="p-4 border-b border-gray-200">
                  <Text className="flex-1 font-medium text-gray-700">Nome</Text>
                  <Text className="flex-1 font-medium text-gray-700">Email</Text>
                  <Text className="flex-1 font-medium text-gray-700">Especialidade</Text>
                  <Text className="w-20 font-medium text-gray-700">Status</Text>
                </HStack>

                {/* Loading state */}
                {loading ? (
                  <Box className="p-8">
                    <Center>
                      <VStack className="items-center" space="md">
                        <Spinner size="large" />
                        <Text className="text-gray-500">Carregando professores...</Text>
                      </VStack>
                    </Center>
                  </Box>
                ) : teachers.length === 0 ? (
                  /* Empty state */
                  <Box className="p-8">
                    <Center>
                      <VStack className="items-center" space="xs">
                        <Icon as={UserPlus} size="lg" className="text-gray-400" />
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
                      className={`p-4 ${
                        index < teachers.length - 1 ? 'border-b border-gray-200' : ''
                      }`}
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
        </VStack>
      </ScrollView>

      {/* Add Teacher Modal */}
      <AddTeacherModal
        isOpen={isAddTeacherModalOpen}
        onClose={() => setIsAddTeacherModalOpen(false)}
        onSuccess={handleTeacherProfileSuccess}
      />
    </MainLayout>
  );
}
