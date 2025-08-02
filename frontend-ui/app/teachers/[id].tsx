import { useLocalSearchParams, useRouter } from 'expo-router';
import {
  ArrowLeft,
  Edit3,
  MessageCircle,
  Calendar,
  MapPin,
  Phone,
  Mail,
  GraduationCap,
  Clock,
  BookOpen,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
} from 'lucide-react-native';
import React, { useState } from 'react';

import { MainLayout } from '@/components/layouts/MainLayout';
import { AdminEditTeacherModal } from '@/components/modals/AdminEditTeacherModal';
import { AdminTeacherProfileHeader } from '@/components/teachers/AdminTeacherProfileHeader';
import {
  ProfileCompletionIndicator,
  CircularProgress,
} from '@/components/teachers/ProfileCompletionIndicator';
import { Avatar } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useTeacherProfile } from '@/hooks/useTeacherProfile';

// Color constants
const COLORS = {
  primary: '#156082',
  secondary: '#FFC000',
  success: '#16A34A',
  warning: '#D97706',
  danger: '#DC2626',
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
  white: '#FFFFFF',
};

interface InfoItemProps {
  icon: any;
  label: string;
  value: string;
  emptyMessage?: string;
}

const InfoItem: React.FC<InfoItemProps> = ({
  icon,
  label,
  value,
  emptyMessage = 'Não informado',
}) => (
  <HStack space="sm" className="items-start">
    <Icon as={icon} size="sm" className="text-gray-500 mt-1" />
    <VStack className="flex-1">
      <Text className="text-sm font-medium text-gray-700">{label}</Text>
      <Text className="text-sm text-gray-600">{value || emptyMessage}</Text>
    </VStack>
  </HStack>
);

interface CourseCardProps {
  course: {
    id: number;
    course_name: string;
    grade_level: string;
    subject_area: string;
    is_active: boolean;
  };
}

const CourseCard: React.FC<CourseCardProps> = ({ course }) => (
  <Box className="p-3 bg-gray-50 rounded-lg border border-gray-200">
    <VStack space="xs">
      <HStack className="items-center justify-between">
        <Text className="font-medium text-gray-900">{course.course_name}</Text>
        <Badge variant={course.is_active ? 'success' : 'secondary'} size="sm">
          {course.is_active ? 'Ativo' : 'Inativo'}
        </Badge>
      </HStack>
      <Text className="text-sm text-gray-600">{course.subject_area}</Text>
      <Text className="text-xs text-gray-500">Nível: {course.grade_level}</Text>
    </VStack>
  </Box>
);

export default function TeacherProfilePage() {
  const { id } = useLocalSearchParams();
  const router = useRouter();
  const teacherId = parseInt(id as string);

  const [showEditModal, setShowEditModal] = useState(false);

  const {
    profile,
    loading,
    error,
    getCompletionStatus,
    getMissingCriticalFields,
    getRecommendations,
    getCompletionPercentage,
    getActiveCourses,
    isActive,
    hasCalendarIntegration,
    hasContactInfo,
    refresh,
  } = useTeacherProfile({
    teacherId,
    autoFetch: true,
  });

  const handleEditSuccess = (updatedTeacher: any) => {
    console.log('Teacher profile updated successfully!', updatedTeacher);
    // Refresh the current profile
    refresh();
  };

  const handleSendMessage = () => {
    console.log('Send message to teacher:', profile?.id);
    // TODO: Open message composer modal
  };

  const handleSendReminder = () => {
    console.log('Send profile completion reminder to:', profile?.id);
    // TODO: Send profile completion reminder
  };

  if (loading) {
    return (
      <MainLayout>
        <Box
          className="flex-1 justify-center items-center"
          style={{ backgroundColor: COLORS.gray[50] }}
        >
          <VStack className="items-center" space="md">
            <Spinner size="large" />
            <Text className="text-gray-500">Carregando perfil do professor...</Text>
          </VStack>
        </Box>
      </MainLayout>
    );
  }

  if (error || !profile) {
    return (
      <MainLayout>
        <Box
          className="flex-1 justify-center items-center p-6"
          style={{ backgroundColor: COLORS.gray[50] }}
        >
          <VStack className="items-center max-w-sm" space="lg">
            <Icon as={AlertTriangle} size="xl" className="text-red-500" />
            <VStack className="items-center" space="sm">
              <Heading size="lg" className="text-gray-900 text-center">
                Erro ao carregar perfil
              </Heading>
              <Text className="text-gray-600 text-center">
                {error || 'Professor não encontrado'}
              </Text>
            </VStack>
            <Button onPress={() => router.back()} className="w-full bg-primary-600">
              <ButtonText>Voltar</ButtonText>
            </Button>
          </VStack>
        </Box>
      </MainLayout>
    );
  }

  const completionStatus = getCompletionStatus();
  const missingCritical = getMissingCriticalFields();
  const recommendations = getRecommendations();
  const completionPercentage = getCompletionPercentage();
  const activeCourses = getActiveCourses();

  return (
    <MainLayout>
      <ScrollView
        className="flex-1"
        style={{ backgroundColor: COLORS.gray[50] }}
        showsVerticalScrollIndicator={false}
      >
        <VStack space="lg" className="p-6">
          {/* Header */}
          <HStack className="items-center justify-between">
            <HStack className="items-center" space="md">
              <Pressable onPress={() => router.back()} className="p-2 -ml-2">
                <Icon as={ArrowLeft} size="md" className="text-gray-700" />
              </Pressable>
              <VStack>
                <Heading size="lg" className="text-gray-900">
                  Perfil do Professor
                </Heading>
                <Text className="text-sm text-gray-500">Visualização administrativa</Text>
              </VStack>
            </HStack>

            <HStack space="sm">
              <Button
                variant="outline"
                size="sm"
                onPress={() => {
                  // TODO: Open message composer
                  console.log('Send message to teacher:', profile.id);
                }}
              >
                <Icon as={MessageCircle} size="sm" className="text-gray-600" />
                <ButtonText className="text-gray-600 ml-2">Mensagem</ButtonText>
              </Button>

              <Button
                size="sm"
                onPress={() => setShowEditModal(true)}
                style={{ backgroundColor: COLORS.primary }}
              >
                <Icon as={Edit3} size="sm" className="text-white" />
                <ButtonText className="text-white ml-2">Editar</ButtonText>
              </Button>
            </HStack>
          </HStack>

          {/* Admin Teacher Profile Header */}
          <AdminTeacherProfileHeader
            teacher={profile}
            onEdit={() => setShowEditModal(true)}
            onSendMessage={handleSendMessage}
            onSendReminder={handleSendReminder}
            onViewDetails={() => {
              // We're already on the details page, so scroll to completion section
              console.log('Scroll to completion details');
            }}
          />

          {/* Profile Completion Details */}
          <Card className="p-6 bg-white">
            <VStack space="lg">
              <Heading size="md" className="text-gray-900">
                Status do Perfil
              </Heading>

              <ProfileCompletionIndicator
                completionPercentage={completionPercentage}
                isComplete={profile.is_profile_complete || false}
                missingCritical={missingCritical}
                recommendations={recommendations}
                variant="detailed"
                onViewDetails={() => {
                  // TODO: Show detailed completion modal
                  console.log('Show completion details');
                }}
              />

              {recommendations.length > 0 && (
                <VStack space="sm">
                  <Text className="font-medium text-gray-700">
                    Recomendações para melhorar o perfil:
                  </Text>
                  {recommendations.slice(0, 3).map((rec, index) => (
                    <HStack key={index} space="xs" className="items-start">
                      <Icon
                        as={rec.priority === 'high' ? AlertTriangle : TrendingUp}
                        size="xs"
                        className={
                          rec.priority === 'high' ? 'text-red-500 mt-1' : 'text-blue-500 mt-1'
                        }
                      />
                      <Text className="text-sm text-gray-600 flex-1">{rec.text}</Text>
                    </HStack>
                  ))}
                </VStack>
              )}
            </VStack>
          </Card>

          {/* Contact Information */}
          <Card className="p-6 bg-white">
            <VStack space="lg">
              <Heading size="md" className="text-gray-900">
                Informações de Contato
              </Heading>

              <VStack space="md">
                <InfoItem icon={Mail} label="Email" value={profile.user.email} />

                <InfoItem icon={Phone} label="Telefone" value={profile.phone_number} />

                <InfoItem icon={MapPin} label="Endereço" value={profile.address} />

                <InfoItem
                  icon={Calendar}
                  label="Calendário"
                  value={hasCalendarIntegration() ? 'Integrado' : ''}
                  emptyMessage="Não integrado"
                />
              </VStack>
            </VStack>
          </Card>

          {/* Teaching Information */}
          <Card className="p-6 bg-white">
            <VStack space="lg">
              <Heading size="md" className="text-gray-900">
                Informações de Ensino
              </Heading>

              <VStack space="md">
                <InfoItem icon={GraduationCap} label="Formação" value={profile.education} />

                <InfoItem icon={Clock} label="Disponibilidade" value={profile.availability} />

                {/* Courses */}
                <VStack space="sm">
                  <HStack className="items-center justify-between">
                    <Text className="font-medium text-gray-700">
                      Cursos Ativos ({activeCourses.length})
                    </Text>
                    {activeCourses.length === 0 && (
                      <Badge variant="outline" size="sm">
                        Nenhum curso
                      </Badge>
                    )}
                  </HStack>

                  {activeCourses.length > 0 && (
                    <VStack space="sm">
                      {activeCourses.map(course => (
                        <CourseCard key={course.id} course={course} />
                      ))}
                    </VStack>
                  )}
                </VStack>
              </VStack>
            </VStack>
          </Card>

          {/* Recent Activity */}
          <Card className="p-6 bg-white">
            <VStack space="lg">
              <Heading size="md" className="text-gray-900">
                Atividade Recente
              </Heading>

              <VStack space="sm">
                <InfoItem
                  icon={Clock}
                  label="Última atividade"
                  value={
                    profile.last_activity
                      ? new Date(profile.last_activity).toLocaleDateString('pt-BR')
                      : ''
                  }
                  emptyMessage="Nunca"
                />

                <InfoItem
                  icon={Edit3}
                  label="Perfil atualizado"
                  value={
                    profile.last_profile_update
                      ? new Date(profile.last_profile_update).toLocaleDateString('pt-BR')
                      : ''
                  }
                  emptyMessage="Nunca"
                />

                <InfoItem
                  icon={BookOpen}
                  label="Criado em"
                  value={
                    profile.created_at
                      ? new Date(profile.created_at).toLocaleDateString('pt-BR')
                      : ''
                  }
                />
              </VStack>
            </VStack>
          </Card>
        </VStack>
      </ScrollView>

      {/* Admin Edit Teacher Modal */}
      {showEditModal && profile && (
        <AdminEditTeacherModal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          teacher={profile}
          onSuccess={handleEditSuccess}
        />
      )}
    </MainLayout>
  );
}
