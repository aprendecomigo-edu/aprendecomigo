import {
  CalendarPlus,
  MessageCircleIcon,
  PlusIcon,
  SettingsIcon,
  UserPlusIcon,
  UsersIcon,
  MailIcon,
} from 'lucide-react-native';
import React from 'react';

import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<any>;
  variant: 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'info';
  onPress: () => void;
  disabled?: boolean;
}

interface QuickActionsPanelProps {
  onInviteTeacher: () => void;
  onAddStudent: () => void;
  onScheduleClass: () => void;
  onViewMessages: () => void;
  onManageUsers: () => void;
  onManageInvitations?: () => void;
  onSettings: () => void;
}

// Design system variant mappings
const VARIANT_STYLES = {
  primary: {
    container: 'feature-card-gradient border-primary-200',
    icon: 'text-primary-600 bg-primary-100',
  },
  secondary: {
    container: 'feature-card-gradient border-gray-200',
    icon: 'text-gray-600 bg-gray-100',
  },
  accent: {
    container: 'feature-card-gradient border-accent-200',
    icon: 'text-accent-600 bg-accent-100',
  },
  success: {
    container: 'feature-card-gradient border-success-200',
    icon: 'text-success-600 bg-success-100',
  },
  warning: {
    container: 'feature-card-gradient border-warning-200',
    icon: 'text-warning-600 bg-warning-100',
  },
  info: {
    container: 'feature-card-gradient border-info-200',
    icon: 'text-info-600 bg-info-100',
  },
} as const;

const QuickActionItem: React.FC<{ action: QuickAction }> = ({ action }) => {
  const styles = VARIANT_STYLES[action.variant];

  return (
    <Pressable
      onPress={action.onPress}
      disabled={action.disabled}
      className={`flex-1 min-w-0 ${
        action.disabled ? 'opacity-50' : 'active:scale-98 transition-transform'
      }`}
    >
      <VStack
        space="sm"
        className={`p-4 rounded-xl ${
          action.disabled ? 'border-gray-200 bg-gray-50' : styles.container
        }`}
      >
        <HStack space="sm" className="items-center">
          <VStack className={`p-2 rounded-lg ${action.disabled ? 'bg-gray-200' : styles.icon}`}>
            <Icon
              as={action.icon}
              size="sm"
              className={action.disabled ? 'text-gray-400' : 'text-white'}
            />
          </VStack>
          <VStack className="flex-1">
            <Text
              className={`font-semibold font-primary ${
                action.disabled ? 'text-gray-500' : 'text-gray-900'
              }`}
            >
              {action.title}
            </Text>
            <Text
              className={`text-sm font-body ${action.disabled ? 'text-gray-400' : 'text-gray-600'}`}
            >
              {action.description}
            </Text>
          </VStack>
        </HStack>
      </VStack>
    </Pressable>
  );
};

const QuickActionsPanel: React.FC<QuickActionsPanelProps> = ({
  onInviteTeacher,
  onAddStudent,
  onScheduleClass,
  onViewMessages,
  onManageUsers,
  onManageInvitations,
  onSettings,
}) => {
  const actions: QuickAction[] = [
    {
      id: 'invite-teacher',
      title: 'Convidar Professor',
      description: 'Adicione um novo professor à sua escola',
      icon: UserPlusIcon,
      variant: 'success',
      onPress: onInviteTeacher,
    },
    {
      id: 'add-student',
      title: 'Adicionar Estudante',
      description: 'Registre um novo estudante',
      icon: PlusIcon,
      variant: 'primary',
      onPress: onAddStudent,
    },
    {
      id: 'schedule-class',
      title: 'Agendar Aula',
      description: 'Marque uma nova aula',
      icon: CalendarPlus,
      variant: 'accent',
      onPress: onScheduleClass,
    },
    {
      id: 'view-messages',
      title: 'Mensagens',
      description: 'Veja conversas e comunicações',
      icon: MessageCircleIcon,
      variant: 'warning',
      onPress: onViewMessages,
    },
    {
      id: 'manage-users',
      title: 'Gerir Utilizadores',
      description: 'Gerencie estudantes e professores',
      icon: UsersIcon,
      variant: 'info',
      onPress: onManageUsers,
    },
    ...(onManageInvitations
      ? [
          {
            id: 'manage-invitations',
            title: 'Gerir Convites',
            description: 'Acompanhe status dos convites',
            icon: MailIcon,
            variant: 'accent' as const,
            onPress: onManageInvitations,
          },
        ]
      : []),
    {
      id: 'settings',
      title: 'Configurações',
      description: 'Ajuste as definições da escola',
      icon: SettingsIcon,
      variant: 'secondary',
      onPress: onSettings,
    },
  ];

  return (
    <VStack className="glass-container p-6 rounded-xl" space="md">
      <Heading size="md" className="font-primary text-gray-900">
        <Text className="bg-gradient-accent">Ações Rápidas</Text>
      </Heading>

      <VStack space="md">
        {/* Render actions in pairs */}
        {Array.from({ length: Math.ceil(actions.length / 2) }, (_, rowIndex) => (
          <HStack key={rowIndex} space="md" className="flex-wrap">
            {actions.slice(rowIndex * 2, rowIndex * 2 + 2).map(action => (
              <QuickActionItem key={action.id} action={action} />
            ))}
          </HStack>
        ))}
      </VStack>
    </VStack>
  );
};

export { QuickActionsPanel };
export default QuickActionsPanel;
