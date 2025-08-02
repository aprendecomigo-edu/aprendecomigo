import {
  Edit3,
  MessageCircle,
  MoreVertical,
  Bell,
  Shield,
  Activity,
  Eye,
  UserCheck,
} from 'lucide-react-native';
import React from 'react';

import { CircularProgress } from './profile-completion-indicator';

import { TeacherProfile } from '@/api/userApi';
import { Avatar } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Menu } from '@/components/ui/menu';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface AdminTeacherProfileHeaderProps {
  teacher: TeacherProfile;
  showActions?: boolean;
  onEdit?: () => void;
  onSendMessage?: () => void;
  onViewDetails?: () => void;
  onToggleStatus?: () => void;
  onSendReminder?: () => void;
}

// Color constants
const COLORS = {
  primary: '#156082',
  success: '#16A34A',
  warning: '#D97706',
  danger: '#DC2626',
  gray: {
    100: '#F3F4F6',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    900: '#111827',
  },
  white: '#FFFFFF',
};

const getCompletionStatusColor = (
  percentage: number,
  isComplete: boolean,
  hasCritical: boolean
) => {
  if (hasCritical || percentage < 30) return COLORS.danger;
  if (isComplete && percentage >= 80) return COLORS.success;
  return COLORS.warning;
};

const getStatusBadgeProps = (status?: string, isActive?: boolean) => {
  const actualStatus = status || (isActive ? 'active' : 'inactive');

  switch (actualStatus) {
    case 'active':
      return { variant: 'success' as const, text: 'Ativo' };
    case 'inactive':
      return { variant: 'secondary' as const, text: 'Inativo' };
    case 'pending':
      return { variant: 'outline' as const, text: 'Pendente' };
    default:
      return { variant: 'secondary' as const, text: 'Indefinido' };
  }
};

const formatLastActivity = (lastActivity?: string): string => {
  if (!lastActivity) return 'Nunca';

  const date = new Date(lastActivity);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Hoje';
  if (diffDays === 1) return 'Ontem';
  if (diffDays < 7) return `${diffDays} dias atrás`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} semanas atrás`;
  return date.toLocaleDateString('pt-BR');
};

export const AdminTeacherProfileHeader: React.FC<AdminTeacherProfileHeaderProps> = ({
  teacher,
  showActions = true,
  onEdit,
  onSendMessage,
  onViewDetails,
  onToggleStatus,
  onSendReminder,
}) => {
  const completionPercentage = teacher.profile_completion_score || 0;
  const isComplete = teacher.is_profile_complete || false;
  const hasCritical = teacher.profile_completion?.missing_critical?.length > 0;
  const activeCourses = teacher.teacher_courses?.filter(c => c.is_active) || [];

  const statusBadge = getStatusBadgeProps(teacher.status);
  const completionColor = getCompletionStatusColor(completionPercentage, isComplete, hasCritical);

  const needsAttention = hasCritical || completionPercentage < 50;

  return (
    <Box className="bg-white border border-gray-200 rounded-lg p-6">
      <VStack space="lg">
        {/* Main Header */}
        <HStack space="lg" className="items-start">
          {/* Avatar and Status */}
          <VStack className="items-center" space="sm">
            <Box className="relative">
              <Avatar size="xl" className="bg-blue-100">
                <Text className="text-blue-600 text-lg font-bold">
                  {teacher.user.name.charAt(0).toUpperCase()}
                </Text>
              </Avatar>

              {needsAttention && (
                <Box className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
                  <Icon as={Bell} size="xs" className="text-white" />
                </Box>
              )}
            </Box>

            <Badge variant={statusBadge.variant} size="sm">
              {statusBadge.text}
            </Badge>
          </VStack>

          {/* Teacher Information */}
          <VStack className="flex-1" space="sm">
            <VStack space="xs">
              <HStack className="items-center justify-between">
                <Heading size="md" className="text-gray-900">
                  {teacher.user.name}
                </Heading>

                {needsAttention && (
                  <Badge variant="destructive" size="sm">
                    Atenção necessária
                  </Badge>
                )}
              </HStack>

              <Text className="text-gray-600">{teacher.user.email}</Text>

              {teacher.specialty && (
                <Text className="text-sm text-gray-500">Especialidade: {teacher.specialty}</Text>
              )}
            </VStack>

            {/* Quick Stats Grid */}
            <HStack space="lg" className="mt-3">
              <VStack className="items-center">
                <Text className="text-lg font-bold text-gray-900">{activeCourses.length}</Text>
                <Text className="text-xs text-gray-500">Cursos</Text>
              </VStack>

              <VStack className="items-center">
                <Text className="text-lg font-bold text-gray-900">€{teacher.hourly_rate || 0}</Text>
                <Text className="text-xs text-gray-500">Por hora</Text>
              </VStack>

              <VStack className="items-center">
                <Text className="text-xs text-gray-500 mb-1">Atividade</Text>
                <Text className="text-sm font-medium text-gray-700">
                  {formatLastActivity(teacher.last_activity)}
                </Text>
              </VStack>
            </HStack>

            {/* Profile Insights */}
            {(hasCritical || !isComplete) && (
              <Box className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded">
                <Text className="text-xs text-amber-800">
                  {hasCritical
                    ? `${teacher.profile_completion?.missing_critical?.length} campo(s) crítico(s) em falta`
                    : 'Perfil incompleto - pode afetar visibilidade para estudantes'}
                </Text>
              </Box>
            )}
          </VStack>

          {/* Profile Completion Circle */}
          <VStack className="items-center" space="xs">
            <CircularProgress
              percentage={completionPercentage}
              size={70}
              strokeWidth={6}
              color={completionColor}
            />
            <Text className="text-xs text-gray-500 text-center">Perfil</Text>
          </VStack>
        </HStack>

        {/* Action Buttons */}
        {showActions && (
          <HStack className="justify-between items-center">
            <HStack space="sm">
              {onViewDetails && (
                <Button variant="outline" size="sm" onPress={onViewDetails}>
                  <Icon as={Eye} size="sm" className="text-gray-600" />
                  <ButtonText className="text-gray-600 ml-2">Ver detalhes</ButtonText>
                </Button>
              )}

              {onSendMessage && (
                <Button variant="outline" size="sm" onPress={onSendMessage}>
                  <Icon as={MessageCircle} size="sm" className="text-gray-600" />
                  <ButtonText className="text-gray-600 ml-2">Mensagem</ButtonText>
                </Button>
              )}

              {needsAttention && onSendReminder && (
                <Button
                  variant="outline"
                  size="sm"
                  onPress={onSendReminder}
                  className="border-amber-300"
                >
                  <Icon as={Bell} size="sm" className="text-amber-600" />
                  <ButtonText className="text-amber-600 ml-2">Lembrete</ButtonText>
                </Button>
              )}
            </HStack>

            <HStack space="sm">
              {onEdit && (
                <Button size="sm" onPress={onEdit} style={{ backgroundColor: COLORS.primary }}>
                  <Icon as={Edit3} size="sm" className="text-white" />
                  <ButtonText className="text-white ml-2">Editar</ButtonText>
                </Button>
              )}

              {/* More Actions Menu */}
              <Pressable className="p-2 border border-gray-300 rounded-md bg-white">
                <Icon as={MoreVertical} size="sm" className="text-gray-500" />
              </Pressable>
            </HStack>
          </HStack>
        )}

        {/* Critical Actions Alert */}
        {hasCritical && (
          <Box className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <HStack className="items-center justify-between">
              <HStack space="sm" className="items-center flex-1">
                <Icon as={Shield} size="sm" className="text-red-600" />
                <VStack className="flex-1">
                  <Text className="text-sm font-medium text-red-800">Ação urgente necessária</Text>
                  <Text className="text-xs text-red-700">
                    Campos críticos em falta podem impactar a qualidade do serviço
                  </Text>
                </VStack>
              </HStack>

              {onSendReminder && (
                <Button
                  size="sm"
                  variant="outline"
                  onPress={onSendReminder}
                  className="border-red-300"
                >
                  <ButtonText className="text-red-600">Notificar</ButtonText>
                </Button>
              )}
            </HStack>
          </Box>
        )}
      </VStack>
    </Box>
  );
};

export default AdminTeacherProfileHeader;
