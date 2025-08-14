/**
 * SettingsActionItem Component
 *
 * Individual action setting item with:
 * - Clean navigation design
 * - Icon integration
 * - Chevron indicator
 * - Badge support
 */

import type { LucideIcon } from 'lucide-react-native';
import { ChevronRight } from 'lucide-react-native';
import React from 'react';

import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface SettingsActionItemProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  onPress: () => void;
  disabled?: boolean;
  badge?: {
    text: string;
    variant?: 'solid' | 'outline';
    action?: 'primary' | 'secondary' | 'positive' | 'negative' | 'warning' | 'info' | 'muted';
  };
  showChevron?: boolean;
  className?: string;
}

export const SettingsActionItem: React.FC<SettingsActionItemProps> = ({
  title,
  description,
  icon,
  onPress,
  disabled = false,
  badge,
  showChevron = true,
  className = '',
}) => {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      className={`glass-light rounded-2xl p-4 active:scale-98 transition-all ${
        disabled ? 'opacity-50' : ''
      } ${className}`}
    >
      <HStack className="items-center justify-between">
        <HStack className="items-center space-x-3 flex-1">
          {icon && (
            <Box className="w-8 h-8 bg-gray-100 rounded-lg items-center justify-center">
              <Icon as={icon} size="sm" className="text-gray-600" />
            </Box>
          )}
          <VStack className="flex-1">
            <Text className={`font-medium ${disabled ? 'text-gray-400' : 'text-gray-900'}`}>
              {title}
            </Text>
            {description && (
              <Text size="sm" className={`${disabled ? 'text-gray-300' : 'text-gray-600'}`}>
                {description}
              </Text>
            )}
          </VStack>
        </HStack>

        <HStack className="items-center space-x-2">
          {badge && (
            <Badge variant={badge.variant || 'outline'} action={badge.action || 'muted'} size="sm">
              <BadgeText>{badge.text}</BadgeText>
            </Badge>
          )}

          {showChevron && (
            <Icon
              as={ChevronRight}
              size="sm"
              className={disabled ? 'text-gray-300' : 'text-gray-400'}
            />
          )}
        </HStack>
      </HStack>
    </Pressable>
  );
};
