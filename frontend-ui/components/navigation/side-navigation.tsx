import { router, useSegments } from 'expo-router';
import type { Href } from 'expo-router';
import React, { useState, useEffect } from 'react';

import { sidebarNavItems, NAVIGATION_COLORS } from './navigation-config';

import { Box } from '@/components/ui/box';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { VStack } from '@/components/ui/vstack';

interface SideNavigationProps {
  className?: string;
}

/**
 * SideNavigation component - renders the left sidebar navigation for desktop
 * Navigation items are configured in navigation-config.ts
 */
export const SideNavigation = ({ className = '' }: SideNavigationProps) => {
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const segments = useSegments();

  // Get current route based on segments
  const getCurrentRoute = () => {
    if (segments.length === 0) return '/home';
    const firstSegment = segments[0];
    return `/${firstSegment}`;
  };

  // Update selected index based on current route
  useEffect(() => {
    const currentRoute = getCurrentRoute();
    const routeIndex = sidebarNavItems.findIndex(item => item.route === currentRoute);
    if (routeIndex !== -1) {
      setSelectedIndex(routeIndex);
    } else {
      // Default to home if no match found
      setSelectedIndex(0);
    }
  }, [segments]);

  const handlePress = (index: number) => {
    setSelectedIndex(index);
    // Navigate based on route if available
    const selectedItem = sidebarNavItems[index];
    if (selectedItem && selectedItem.route) {
      router.push(selectedItem.route as Href<string>);
    }
  };

  return (
    <VStack
      className={`w-20 pt-6 h-full items-center border-r border-border-300 pb-5 ${className}`}
      space="md"
      style={{ backgroundColor: NAVIGATION_COLORS.primary }}
      data-testid="side-navigation"
    >
      <VStack className="items-center" space="md">
        {sidebarNavItems.map((item, index) => {
          const isSelected = index === selectedIndex;
          return (
            <Pressable
              key={item.id}
              className={`p-3 rounded-full w-12 h-12 items-center justify-center ${
                isSelected ? 'bg-orange-400' : 'hover:bg-white/10'
              }`}
              onPress={() => handlePress(index)}
            >
              <Icon as={item.icon} size="lg" className="text-white" />
            </Pressable>
          );
        })}
      </VStack>

      <Box className="flex-1" />
    </VStack>
  );
};
