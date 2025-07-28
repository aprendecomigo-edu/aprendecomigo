import { cn } from '@gluestack-ui/nativewind-utils/cn';
import { router, useSegments } from 'expo-router';
import type { Href } from 'expo-router';
import {
  PlusIcon,
  UserPlusIcon,
  UsersIcon,
  BookPlusIcon,
  BarChart3Icon,
  SettingsIcon,
  ChevronDownIcon,
  XIcon,
} from 'lucide-react-native';
import React, { useState, useMemo } from 'react';
import { Platform } from 'react-native';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Fab, FabIcon, FabLabel } from '@/components/ui/fab';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import {
  Modal,
  ModalBackdrop,
  ModalContent,
  ModalHeader,
  ModalBody,
} from '@/components/ui/modal';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import type { QuickAction } from '@/types/navigation';

interface QuickActionsProps {
  variant?: 'dropdown' | 'fab';
  className?: string;
  actions?: QuickAction[];
  onActionSelect?: (action: QuickAction) => void;
}

// Default admin quick actions
const DEFAULT_QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'invite-teacher',
    label: 'Invite Teacher',
    icon: UserPlusIcon,
    route: '/invitations?action=invite-teacher',
    variant: 'primary',
    permission: 'school_admin',
    context: ['dashboard', 'teachers', 'invitations'],
  },
  {
    id: 'add-student',
    label: 'Add Student',
    icon: UsersIcon,
    route: '/students?action=add-student',
    variant: 'primary',
    permission: 'school_admin',
    context: ['dashboard', 'students'],
  },
  {
    id: 'create-class',
    label: 'Create Class',
    icon: BookPlusIcon,
    route: '/classes?action=create-class',
    variant: 'secondary',
    permission: 'school_admin',
    context: ['dashboard', 'classes', 'calendar'],
  },
  {
    id: 'view-analytics',
    label: 'View Analytics',
    icon: BarChart3Icon,
    route: '/analytics',
    variant: 'outline',
    permission: 'school_admin',
    context: ['dashboard'],
  },
  {
    id: 'school-settings',
    label: 'School Settings',
    icon: SettingsIcon,
    route: '/settings?tab=school',
    variant: 'outline',
    permission: 'school_admin',
    context: ['dashboard', 'settings'],
  },
];

/**
 * QuickActions component - provides quick access to common admin actions
 * Can be rendered as a dropdown or floating action button
 */
export const QuickActions: React.FC<QuickActionsProps> = ({
  variant = 'dropdown',
  className = '',
  actions = DEFAULT_QUICK_ACTIONS,
  onActionSelect,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const segments = useSegments();

  // Get current context for filtering relevant actions
  const currentContext = useMemo(() => {
    if (segments.length === 0) return 'dashboard';
    return segments[0];
  }, [segments]);

  // Filter actions based on current context and permissions
  const relevantActions = useMemo(() => {
    return actions.filter(action => {
      // If no context specified, show everywhere
      if (!action.context || action.context.length === 0) {
        return true;
      }
      // Show if current context is in action's context list
      return action.context.includes(currentContext);
    });
  }, [actions, currentContext]);

  const handleActionSelect = (action: QuickAction) => {
    setIsOpen(false);

    if (action.action) {
      action.action();
    } else if (action.route) {
      router.push(action.route as Href<string>);
    }

    if (onActionSelect) {
      onActionSelect(action);
    }
  };

  if (variant === 'fab') {
    return <QuickActionsFAB actions={relevantActions} onActionSelect={handleActionSelect} />;
  }

  return (
    <QuickActionsDropdown
      actions={relevantActions}
      isOpen={isOpen}
      onToggle={() => setIsOpen(!isOpen)}
      onActionSelect={handleActionSelect}
      className={className}
    />
  );
};

// Dropdown variant for desktop
interface QuickActionsDropdownProps {
  actions: QuickAction[];
  isOpen: boolean;
  onToggle: () => void;
  onActionSelect: (action: QuickAction) => void;
  className?: string;
}

const QuickActionsDropdown: React.FC<QuickActionsDropdownProps> = ({
  actions,
  isOpen,
  onToggle,
  onActionSelect,
  className,
}) => {
  if (actions.length === 0) {
    return null;
  }

  return (
    <Box className={cn('relative', className)}>
      <Button
        size="md"
        variant="solid"
        action="primary"
        onPress={onToggle}
        className="flex-row items-center"
      >
        <Icon as={PlusIcon} size="sm" className="mr-2 text-white" />
        <ButtonText className="mr-1">Quick Actions</ButtonText>
        <Icon
          as={ChevronDownIcon}
          size="sm"
          className={cn(
            'text-white transition-transform',
            isOpen && 'rotate-180'
          )}
        />
      </Button>

      <Modal isOpen={isOpen} onClose={() => onToggle()}>
        <ModalBackdrop />
        <ModalContent
          style={{
            position: 'absolute',
            top: 60,
            right: 20,
            margin: 0,
            width: 250,
            backgroundColor: 'transparent',
            borderWidth: 0,
          }}
        >
          <Box className="bg-background-0 border border-border-200 rounded-lg shadow-lg">
            <VStack space="xs" className="p-2">
              {actions.map((action) => (
                <QuickActionItem
                  key={action.id}
                  action={action}
                  onSelect={onActionSelect}
                />
              ))}
            </VStack>
          </Box>
        </ModalContent>
      </Modal>
    </Box>
  );
};

// FAB variant for mobile
interface QuickActionsFABProps {
  actions: QuickAction[];
  onActionSelect: (action: QuickAction) => void;
}

const QuickActionsFAB: React.FC<QuickActionsFABProps> = ({
  actions,
  onActionSelect,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (actions.length === 0) {
    return null;
  }

  // If only one action, show it directly
  if (actions.length === 1) {
    const action = actions[0];
    return (
      <Fab
        size="lg"
        placement="bottom right"
        onPress={() => onActionSelect(action)}
        className="mb-20 mr-4"
      >
        <FabIcon as={action.icon} />
        <FabLabel>{action.label}</FabLabel>
      </Fab>
    );
  }

  return (
    <>
      {/* Main FAB */}
      <Fab
        size="lg"
        placement="bottom right"
        onPress={() => setIsExpanded(!isExpanded)}
        className="mb-20 mr-4"
      >
        <FabIcon as={isExpanded ? XIcon : PlusIcon} />
      </Fab>

      {/* Expanded Actions */}
      {isExpanded && (
        <VStack
          space="sm"
          className="absolute bottom-32 right-4 mb-8"
        >
          {actions.slice(0, 4).map((action, index) => (
            <Fab
              key={action.id}
              size="md"
              onPress={() => {
                onActionSelect(action);
                setIsExpanded(false);
              }}
              style={{
                opacity: isExpanded ? 1 : 0,
                transform: [
                  {
                    translateY: isExpanded ? 0 : 20,
                  },
                ],
              }}
            >
              <FabIcon as={action.icon} />
            </Fab>
          ))}
        </VStack>
      )}

      {/* Backdrop */}
      {isExpanded && (
        <Pressable
          onPress={() => setIsExpanded(false)}
          className="absolute inset-0 bg-black/20"
          style={{ zIndex: -1 }}
        />
      )}
    </>
  );
};

// Individual action item
interface QuickActionItemProps {
  action: QuickAction;
  onSelect: (action: QuickAction) => void;
}

const QuickActionItem: React.FC<QuickActionItemProps> = ({
  action,
  onSelect,
}) => {
  const variantClasses = {
    primary: 'text-primary-600',
    secondary: 'text-secondary-600',
    outline: 'text-typography-700',
  };

  return (
    <Pressable
      onPress={() => onSelect(action)}
      className={cn(
        'p-3 rounded-lg flex-row items-center space-x-3',
        'hover:bg-background-50 active:bg-background-100'
      )}
    >
      <Icon
        as={action.icon}
        size="sm"
        className={variantClasses[action.variant || 'outline']}
      />
      <Text
        className="flex-1 font-medium text-typography-900"
        numberOfLines={1}
      >
        {action.label}
      </Text>
    </Pressable>
  );
};

export default QuickActions;