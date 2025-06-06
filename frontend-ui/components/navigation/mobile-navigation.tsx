import { cn } from '@gluestack-ui/nativewind-utils/cn';
import { router } from 'expo-router';
import type { Href } from 'expo-router';
import React from 'react';
import { Platform } from 'react-native';

import { bottomTabNavItems, NAVIGATION_COLORS } from './navigation-config';

import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';

interface MobileNavigationProps {
  className?: string;
}

/**
 * MobileNavigation component - renders the bottom tab navigation for mobile devices
 * Navigation items are configured in navigation-config.ts
 * Only visible on mobile devices (hidden on md and larger screens)
 */
export const MobileNavigation = ({ className = '' }: MobileNavigationProps) => {
  const handleNavigation = (route: string) => {
    router.push(route as Href<string>);
  };

  return (
    <HStack
      className={cn(
        'justify-between w-full fixed left-0 bottom-0 right-0 p-3 items-center border-t-border-300 md:hidden border-t z-50',
        { 'pb-5': Platform.OS === 'ios' },
        { 'pb-5': Platform.OS === 'android' },
        className
      )}
      style={{ backgroundColor: NAVIGATION_COLORS.primary }}
    >
      {bottomTabNavItems.map(item => {
        return (
          <Pressable
            className="px-0.5 flex-1 flex-col items-center"
            key={item.id}
            onPress={() => handleNavigation(item.route)}
          >
            <Icon as={item.icon} size="md" className="h-[32px] w-[65px] text-white" />
            <Text className="text-xs text-center text-white">{item.label}</Text>
          </Pressable>
        );
      })}
    </HStack>
  );
};
