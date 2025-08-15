/**
 * SettingsToggleItem Component
 *
 * Individual toggle setting item with:
 * - Clean toggle switch design
 * - Proper visual states
 * - Icon integration
 * - Accessibility support
 */

import type { LucideIcon } from 'lucide-react-native';
import React, { useCallback } from 'react';

import { Box } from '@/components/ui/box';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface SettingsToggleItemProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  value: boolean;
  onValueChange: (value: boolean) => void;
  disabled?: boolean;
  className?: string;
}

export const SettingsToggleItem = React.memo<SettingsToggleItemProps>(({
  title,
  description,
  icon,
  value,
  onValueChange,
  disabled = false,
  className = '',
}) => {
  const handlePress = useCallback(() => {
    if (!disabled) {
      onValueChange(!value);
    }
  }, [disabled, onValueChange, value]);

  return (
    <Pressable
      onPress={handlePress}
      disabled={disabled}
      className={`glass-light rounded-2xl p-4 active:scale-98 transition-all ${
        disabled ? 'opacity-50' : ''
      } ${className}`}
    >
      <HStack className="items-center justify-between">
        <HStack className="items-center space-x-3 flex-1">
          {icon && (
            <Box
              className={`w-8 h-8 rounded-lg items-center justify-center ${
                value ? 'bg-gradient-accent' : 'bg-gray-200'
              }`}
            >
              <Icon as={icon} size="sm" className={value ? 'text-white' : 'text-gray-600'} />
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

        <Switch value={value} onValueChange={onValueChange} disabled={disabled} className="ml-3" />
      </HStack>
    </Pressable>
  );
}, (prevProps, nextProps) => {
  // Custom comparison function for SettingsToggleItem
  return (
    prevProps.title === nextProps.title &&
    prevProps.description === nextProps.description &&
    prevProps.value === nextProps.value &&
    prevProps.disabled === nextProps.disabled &&
    prevProps.className === nextProps.className
  );
});
