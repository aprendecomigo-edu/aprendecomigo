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

import { Card, CardBody, CardHeader } from '@/components/ui/card';
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
  color: string;
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

const QuickActionItem: React.FC<{ action: QuickAction }> = ({ action }) => (
  <Pressable
    onPress={action.onPress}
    disabled={action.disabled}
    className={`flex-1 min-w-0 ${action.disabled ? 'opacity-50' : ''}`}
  >
    <VStack
      space="sm"
      className={`p-4 rounded-lg border-2 border-dashed ${
        action.disabled
          ? 'border-gray-200 bg-gray-50'
          : `border-${action.color}-200 bg-${action.color}-50 hover:bg-${action.color}-100`
      }`}
    >
      <HStack space="sm" className="items-center">
        <Icon
          as={action.icon}
          size="sm"
          className={`${action.disabled ? 'text-gray-400' : `text-${action.color}-600`}`}
        />
        <Text
          className={`font-semibold flex-1 ${action.disabled ? 'text-gray-500' : 'text-gray-900'}`}
        >
          {action.title}
        </Text>
      </HStack>
      <Text className={`text-sm ${action.disabled ? 'text-gray-400' : 'text-gray-600'}`}>
        {action.description}
      </Text>
    </VStack>
  </Pressable>
);

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
      color: 'green',
      onPress: onInviteTeacher,
    },
    {
      id: 'add-student',
      title: 'Adicionar Estudante',
      description: 'Registre um novo estudante',
      icon: PlusIcon,
      color: 'blue',
      onPress: onAddStudent,
    },
    {
      id: 'schedule-class',
      title: 'Agendar Aula',
      description: 'Marque uma nova aula',
      icon: CalendarPlus,
      color: 'purple',
      onPress: onScheduleClass,
    },
    {
      id: 'view-messages',
      title: 'Mensagens',
      description: 'Veja conversas e comunicações',
      icon: MessageCircleIcon,
      color: 'orange',
      onPress: onViewMessages,
    },
    {
      id: 'manage-users',
      title: 'Gerir Utilizadores',
      description: 'Gerencie estudantes e professores',
      icon: UsersIcon,
      color: 'indigo',
      onPress: onManageUsers,
    },
    ...(onManageInvitations
      ? [
          {
            id: 'manage-invitations',
            title: 'Gerir Convites',
            description: 'Acompanhe status dos convites',
            icon: MailIcon,
            color: 'teal',
            onPress: onManageInvitations,
          },
        ]
      : []),
    {
      id: 'settings',
      title: 'Configurações',
      description: 'Ajuste as definições da escola',
      icon: SettingsIcon,
      color: 'gray',
      onPress: onSettings,
    },
  ];

  return (
    <Card variant="elevated" className="bg-white shadow-sm">
      <CardHeader>
        <Heading size="md" className="text-gray-900">
          Ações Rápidas
        </Heading>
      </CardHeader>
      <CardBody>
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
      </CardBody>
    </Card>
  );
};

export { QuickActionsPanel };
export default QuickActionsPanel;
