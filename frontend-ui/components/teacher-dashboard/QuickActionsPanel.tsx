import {
  CalendarIcon,
  UsersIcon,
  TrendingUpIcon,
  MessageSquareIcon,
  BookOpenIcon,
  ClockIcon,
  PlusIcon,
  DownloadIcon,
  SettingsIcon,
  HelpCircleIcon,
  FileTextIcon,
  StarIcon,
  ZapIcon,
  BarChart3Icon,
} from 'lucide-react-native';
import React from 'react';
import { Pressable } from 'react-native';

import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: any;
  color: string;
  onPress: () => void;
  badge?: string;
  disabled?: boolean;
}

interface QuickActionsPanelProps {
  onScheduleSession: () => void;
  onViewStudents: () => void;
  onViewAnalytics: () => void;
  onViewSessions: () => void;
  onMessageCenter: () => void;
  onCreateLesson: () => void;
  onManageAvailability: () => void;
  onDownloadReports: () => void;
  onSettings: () => void;
  onHelp: () => void;
  pendingMessages?: number;
  upcomingSessions?: number;
  isLoading?: boolean;
}

const QuickActionButton: React.FC<{
  action: QuickAction;
  size?: 'sm' | 'md' | 'lg';
}> = ({ action, size = 'md' }) => {
  const sizeClasses = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };

  const iconSizes = {
    sm: 'sm' as const,
    md: 'md' as const,
    lg: 'lg' as const,
  };

  return (
    <Pressable
      onPress={action.onPress}
      disabled={action.disabled}
      className={`bg-white rounded-lg border border-gray-200 ${sizeClasses[size]} ${
        action.disabled ? 'opacity-50' : 'hover:shadow-md'
      } transition-shadow relative`}
      accessibilityLabel={action.title}
      accessibilityHint={action.description}
      accessibilityRole="button"
    >
      <VStack space="sm" className="items-center">
        <VStack className={`${action.color} rounded-full p-3 items-center justify-center relative`}>
          <Icon as={action.icon} size={iconSizes[size]} className="text-white" />
          {action.badge && (
            <Box className="absolute -top-1 -right-1">
              <Badge className="bg-red-500 w-5 h-5 rounded-full items-center justify-center">
                <BadgeText className="text-white text-xs">{action.badge}</BadgeText>
              </Badge>
            </Box>
          )}
        </VStack>
        
        <VStack className="items-center" space="xs">
          <Text className="text-sm font-semibold text-gray-900 text-center" numberOfLines={1}>
            {action.title}
          </Text>
          <Text className="text-xs text-gray-500 text-center" numberOfLines={2}>
            {action.description}
          </Text>
        </VStack>
      </VStack>
    </Pressable>
  );
};

const QuickActionsPanel: React.FC<QuickActionsPanelProps> = ({
  onScheduleSession,
  onViewStudents,
  onViewAnalytics,
  onViewSessions,
  onMessageCenter,
  onCreateLesson,
  onManageAvailability,
  onDownloadReports,
  onSettings,
  onHelp,
  pendingMessages = 0,
  upcomingSessions = 0,
  isLoading = false,
}) => {
  // Primary actions (most frequently used)
  const primaryActions: QuickAction[] = [
    {
      id: 'schedule',
      title: 'Agendar Sessão',
      description: 'Nova aula com estudantes',
      icon: CalendarIcon,
      color: 'bg-blue-600',
      onPress: onScheduleSession,
      badge: upcomingSessions > 0 ? upcomingSessions.toString() : undefined,
    },
    {
      id: 'students',
      title: 'Estudantes',
      description: 'Ver progresso e detalhes',
      icon: UsersIcon,
      color: 'bg-green-600',
      onPress: onViewStudents,
    },
    {
      id: 'analytics',
      title: 'Analytics',
      description: 'Relatórios e métricas',
      icon: BarChart3Icon,
      color: 'bg-purple-600',
      onPress: onViewAnalytics,
    },
    {
      id: 'messages',
      title: 'Mensagens',
      description: 'Centro de comunicação',
      icon: MessageSquareIcon,
      color: 'bg-orange-600',
      onPress: onMessageCenter,
      badge: pendingMessages > 0 ? pendingMessages.toString() : undefined,
    },
  ];

  // Secondary actions (useful but less frequent)
  const secondaryActions: QuickAction[] = [
    {
      id: 'sessions',
      title: 'Sessões',
      description: 'Gerir aulas e horários',
      icon: ClockIcon,
      color: 'bg-teal-600',
      onPress: onViewSessions,
    },
    {
      id: 'lesson',
      title: 'Criar Lição',
      description: 'Materiais de ensino',
      icon: BookOpenIcon,
      color: 'bg-indigo-600',
      onPress: onCreateLesson,
    },
    {
      id: 'availability',
      title: 'Disponibilidade',
      description: 'Gerir horários livres',
      icon: ZapIcon,
      color: 'bg-yellow-600',
      onPress: onManageAvailability,
    },
    {
      id: 'reports',
      title: 'Relatórios',
      description: 'Descarregar dados',
      icon: DownloadIcon,
      color: 'bg-gray-600',
      onPress: onDownloadReports,
    },
  ];

  // Utility actions (settings and help)
  const utilityActions: QuickAction[] = [
    {
      id: 'settings',
      title: 'Configurações',
      description: 'Perfil e preferências',
      icon: SettingsIcon,
      color: 'bg-gray-500',
      onPress: onSettings,
    },
    {
      id: 'help',
      title: 'Ajuda',
      description: 'Suporte e tutoriais',
      icon: HelpCircleIcon,
      color: 'bg-blue-500',
      onPress: onHelp,
    },
  ];

  return (
    <VStack space="md">
      {/* Primary Actions */}
      <Card variant="elevated" className="bg-white shadow-sm">
        <CardHeader>
          <HStack className="justify-between items-center">
            <Heading size="md" className="text-gray-900">
              Ações Principais
            </Heading>
            <Icon as={StarIcon} size="sm" className="text-yellow-500" />
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack space="sm">
            {/* Grid layout for primary actions */}
            <HStack space="sm">
              <QuickActionButton action={primaryActions[0]} size="lg" />
              <VStack space="sm" className="flex-1">
                <QuickActionButton action={primaryActions[1]} size="sm" />
                <QuickActionButton action={primaryActions[2]} size="sm" />
              </VStack>
            </HStack>
            <QuickActionButton action={primaryActions[3]} size="md" />
          </VStack>
        </CardBody>
      </Card>

      {/* Secondary Actions */}
      <Card variant="elevated" className="bg-white shadow-sm">
        <CardHeader>
          <Heading size="md" className="text-gray-900">
            Ferramentas de Ensino
          </Heading>
        </CardHeader>
        <CardBody>
          <VStack space="sm">
            <HStack space="sm">
              {secondaryActions.slice(0, 2).map(action => (
                <Box key={action.id} className="flex-1">
                  <QuickActionButton action={action} size="md" />
                </Box>
              ))}
            </HStack>
            <HStack space="sm">
              {secondaryActions.slice(2, 4).map(action => (
                <Box key={action.id} className="flex-1">
                  <QuickActionButton action={action} size="md" />
                </Box>
              ))}
            </HStack>
          </VStack>
        </CardBody>
      </Card>

      {/* Utility Actions */}
      <Card variant="elevated" className="bg-white shadow-sm">
        <CardHeader>
          <Heading size="md" className="text-gray-900">
            Configurações
          </Heading>
        </CardHeader>
        <CardBody>
          <HStack space="sm">
            {utilityActions.map(action => (
              <Box key={action.id} className="flex-1">
                <QuickActionButton action={action} size="md" />
              </Box>
            ))}
          </HStack>
        </CardBody>
      </Card>

      {/* Quick Tips */}
      <Card variant="elevated" className="bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-dashed border-blue-200">
        <CardBody>
          <VStack space="sm" className="items-center">
            <Icon as={ZapIcon} size="md" className="text-blue-600" />
            <VStack space="xs" className="items-center">
              <Text className="text-sm font-semibold text-gray-900">Dica Rápida</Text>
              <Text className="text-xs text-gray-600 text-center">
                Use as ações principais para acesso rápido às funcionalidades mais importantes.
                Personalize no menu de configurações!
              </Text>
            </VStack>
          </VStack>
        </CardBody>
      </Card>
    </VStack>
  );
};

export default QuickActionsPanel;