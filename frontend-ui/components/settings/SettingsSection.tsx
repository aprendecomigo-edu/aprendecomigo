/**
 * SettingsSection Component
 * 
 * Provides grouped settings sections with:
 * - Clean visual hierarchy
 * - Proper spacing and layout
 * - Card-based design following design guidelines
 * - Icon integration
 */

import React from 'react';
import type { LucideIcon } from 'lucide-react-native';

import { Box } from '@/components/ui/box';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface SettingsSectionProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  children: React.ReactNode;
  className?: string;
}

export const SettingsSection: React.FC<SettingsSectionProps> = ({
  title,
  description,
  icon,
  children,
  className = '',
}) => {
  return (
    <Box className={`feature-card-gradient rounded-3xl p-6 mb-6 ${className}`}>
      {/* Section Header */}
      <HStack className="items-center space-x-3 mb-4">
        {icon && (
          <Box className="w-10 h-10 bg-gradient-primary rounded-xl items-center justify-center">
            <Icon as={icon} size="md" className="text-white" />
          </Box>
        )}
        <VStack className="flex-1">
          <Heading size="md" className="text-gray-900 font-bold">
            {title}
          </Heading>
          {description && (
            <Text size="sm" className="text-gray-600">
              {description}
            </Text>
          )}
        </VStack>
      </HStack>

      {/* Section Content */}
      <VStack className="space-y-2">
        {children}
      </VStack>
    </Box>
  );
};