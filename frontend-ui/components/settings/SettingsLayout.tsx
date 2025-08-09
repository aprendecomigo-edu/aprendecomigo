/**
 * SettingsLayout Component
 *
 * Provides a consistent layout for all settings pages with:
 * - Proper navigation header with back button
 * - Clean visual hierarchy following design guidelines
 * - Glassmorphism and gradient patterns
 * - Responsive design for web and mobile
 */

import { router } from 'expo-router';
import { ArrowLeft } from 'lucide-react-native';
import React from 'react';
import { ScrollView, Platform } from 'react-native';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface SettingsLayoutProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  onBack?: () => void;
  headerActions?: React.ReactNode;
}

export const SettingsLayout: React.FC<SettingsLayoutProps> = ({
  title,
  subtitle,
  children,
  onBack,
  headerActions,
}) => {
  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      router.back();
    }
  };

  return (
    <SafeAreaView className="flex-1 bg-gradient-page">
      {/* Header with navigation */}
      <Box className="glass-nav mx-4 mt-2 mb-4 rounded-2xl">
        <HStack className="items-center justify-between p-4">
          <HStack className="items-center space-x-3">
            <Pressable
              onPress={handleBack}
              className="w-10 h-10 rounded-full glass-light items-center justify-center active:scale-95 transition-all"
            >
              <Icon as={ArrowLeft} size="lg" className="text-gray-700" />
            </Pressable>
            <VStack className="flex-1">
              <Heading size="lg" className="text-gray-900 font-bold">
                {title}
              </Heading>
              {subtitle && (
                <Text size="sm" className="text-gray-600">
                  {subtitle}
                </Text>
              )}
            </VStack>
          </HStack>
          {headerActions && <Box>{headerActions}</Box>}
        </HStack>
      </Box>

      {/* Content area */}
      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: Platform.OS === 'ios' ? 100 : 80 }}
        showsVerticalScrollIndicator={false}
      >
        <Box className="px-4">{children}</Box>
      </ScrollView>
    </SafeAreaView>
  );
};
