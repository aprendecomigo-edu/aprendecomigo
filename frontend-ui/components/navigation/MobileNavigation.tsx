import { cn } from '@gluestack-ui/nativewind-utils/cn';
import { router, useSegments } from 'expo-router';
import type { Href } from 'expo-router';
import React, { useEffect, useState } from 'react';
import { Platform, Haptics } from 'react-native';

import { bottomTabNavItems, getNavigationItems, NAVIGATION_COLORS } from './navigation-config';

import { useAuth } from '@/api/authContext';
import { navigationApi } from '@/api/navigationApi';
import { Box } from '@/components/ui/box';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { NotificationBadge } from '@/components/ui/notification-badge';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';

interface MobileNavigationProps {
  className?: string;
}

/**
 * MobileNavigation component - renders the bottom tab navigation for mobile devices
 * Navigation items are configured in navigation-config.ts with role-based access
 * Only visible on mobile devices (hidden on md and larger screens)
 */
export const MobileNavigation = ({ className = '' }: MobileNavigationProps) => {
  const segments = useSegments();
  const { userProfile } = useAuth();
  const [notificationCounts, setNotificationCounts] = useState<Record<string, number>>({});

  // Get navigation items based on user role (fallback to bottom tabs for mobile)
  const navItems = React.useMemo(() => {
    return bottomTabNavItems;
  }, []);

  // Get current route based on segments
  const getCurrentRoute = () => {
    if (segments.length === 0) return '/home';
    const firstSegment = segments[0];
    return `/${firstSegment}`;
  };

  // Load notification counts
  useEffect(() => {
    const loadNotificationCounts = async () => {
      try {
        const response = await navigationApi.getNotificationCounts();
        const counts: Record<string, number> = {};

        // Map backend response fields to navigation items
        counts['home'] = response.overdue_tasks;
        counts['chat'] = 0; // Messages count not available in current API

        // Calculate total for overall notification badge
        counts['total'] = response.total_unread;

        setNotificationCounts(counts);
      } catch (error) {
        console.error('Failed to load notification counts:', error);
      }
    };

    loadNotificationCounts();

    // Poll for updates every 30 seconds
    const interval = setInterval(loadNotificationCounts, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleNavigation = (route: string) => {
    // Haptic feedback for better UX
    if (Platform.OS === 'ios') {
      Haptics.selectionAsync();
    }

    router.push(route as Href<string>);
  };

  const currentRoute = getCurrentRoute();

  return (
    <HStack
      className={cn(
        'justify-between w-full fixed left-0 bottom-0 right-0 p-3 items-center border-t-border-300 md:hidden border-t z-50',
        { 'pb-5': Platform.OS === 'ios' },
        { 'pb-5': Platform.OS === 'android' },
        className
      )}
      style={{ backgroundColor: NAVIGATION_COLORS.primary }}
      data-testid="bottom-navigation"
    >
      {navItems.map(item => {
        const isSelected = item.route === currentRoute;
        const notificationCount = notificationCounts[item.id] || 0;

        return (
          <Box key={item.id} className="relative flex-1">
            <Pressable
              className={cn(
                'px-0.5 flex-col items-center py-2 rounded-lg mx-1',
                'active:bg-white/10 active:scale-95',
                // Larger touch target for better accessibility
                'min-h-[48px] justify-center'
              )}
              onPress={() => handleNavigation(item.route)}
              style={{
                // Smooth transition for better feedback
                transform: [{ scale: isSelected ? 1.05 : 1 }],
              }}
            >
              <Box className="relative">
                <Icon
                  as={item.icon}
                  size="md"
                  className={cn('h-6 w-6', isSelected ? 'text-orange-400' : 'text-white')}
                />

                {/* Notification Badge */}
                {notificationCount > 0 && (
                  <NotificationBadge
                    count={notificationCount}
                    type="error"
                    size="sm"
                    maxCount={9}
                    className="-top-2 -right-2"
                  />
                )}
              </Box>

              <Text
                className={cn(
                  'text-xs text-center mt-1 font-medium',
                  isSelected ? 'text-orange-400' : 'text-white'
                )}
                numberOfLines={1}
              >
                {item.label}
              </Text>
            </Pressable>
          </Box>
        );
      })}
    </HStack>
  );
};
