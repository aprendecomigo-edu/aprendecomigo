import { router, useSegments } from 'expo-router';
import type { Href } from 'expo-router';
import React, { useState, useEffect } from 'react';

import {
  sidebarNavItems,
  getNavigationItems,
  NAVIGATION_COLORS,
  type SidebarItem,
} from './navigation-config';

import { useUserProfile } from '@/api/auth';
import { navigationApi } from '@/api/navigationApi';
import { Box } from '@/components/ui/box';
import { Icon } from '@/components/ui/icon';
import { NotificationBadge, NotificationDot } from '@/components/ui/notification-badge';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface SideNavigationProps {
  className?: string;
}

/**
 * SideNavigation component - renders the left sidebar navigation for desktop
 * Navigation items are configured in navigation-config.ts with role-based access
 */
export const SideNavigation = ({ className = '' }: SideNavigationProps) => {
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [notificationCounts, setNotificationCounts] = useState<Record<string, number>>({});
  const segments = useSegments();
  const { userProfile } = useUserProfile();

  // Get navigation items based on user role
  const navItems = React.useMemo(() => {
    const userRole = userProfile?.user_type || 'student';
    return getNavigationItems(userRole);
  }, [userProfile]);

  // Get current route based on segments
  const getCurrentRoute = () => {
    if (segments.length === 0) return '/home';

    // Handle grouped routes (e.g., (school-admin)/dashboard)
    if (segments[0].startsWith('(') && segments[0].endsWith(')')) {
      if (segments.length > 1) {
        return `/${segments[0]}/${segments[1]}`;
      }
      return `/${segments[0]}`;
    }

    const firstSegment = segments[0];
    return `/${firstSegment}`;
  };

  // Update selected index based on current route
  useEffect(() => {
    const currentRoute = getCurrentRoute();

    // Try exact match first
    let routeIndex = navItems.findIndex(item => item.route === currentRoute);

    // If no exact match, try partial matching for grouped routes
    if (routeIndex === -1) {
      routeIndex = navItems.findIndex(item => {
        // Handle grouped routes like /(school-admin)/dashboard
        if (item.route.includes('(') && currentRoute.includes('(')) {
          const itemParts = item.route.split('/');
          const currentParts = currentRoute.split('/');
          return itemParts[1] === currentParts[1]; // Compare group names
        }
        // Handle simple routes
        return (
          item.route.endsWith(segments[0]) ||
          currentRoute.endsWith(item.route.split('/').pop() || '')
        );
      });
    }

    if (routeIndex !== -1) {
      setSelectedIndex(routeIndex);
    } else {
      // Default to first item (dashboard) if no match found
      setSelectedIndex(0);
    }
  }, [segments, navItems]);

  // Load notification counts
  useEffect(() => {
    const loadNotificationCounts = async () => {
      try {
        const response = await navigationApi.getNotificationCounts();
        const counts: Record<string, number> = {};

        // Map backend response fields to navigation items
        counts['invitations'] = response.pending_invitations;
        counts['dashboard'] = response.overdue_tasks;
        counts['students'] = response.new_registrations;
        counts['teachers'] = response.incomplete_profiles;

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

  const handlePress = (index: number) => {
    setSelectedIndex(index);
    // Navigate based on route if available
    const selectedItem = navItems[index];
    if (selectedItem && selectedItem.route) {
      router.push(selectedItem.route as Href<string>);
    }
  };

  return (
    <VStack
      className={`w-64 pt-6 min-h-screen h-full glass-nav ${className}`}
      space="sm"
      data-testid="side-navigation"
    >
      <VStack className="flex-1 px-4" space="xs">
        {navItems.map((item, index) => {
          const isSelected = index === selectedIndex;
          const notificationCount = notificationCounts[item.id] || 0;

          return (
            <Box key={`nav-item-${item.id}`} className="relative">
              <Pressable
                className={`flex-row items-center px-3 py-3 rounded-lg active:scale-98 transition-transform ${
                  isSelected ? 'bg-gradient-primary' : 'glass-light'
                }`}
                onPress={() => handlePress(index)}
                accessibilityRole="button"
                accessibilityLabel={`Navigate to ${item.label}`}
                accessibilityState={{ selected: isSelected }}
              >
                <Icon
                  as={item.icon}
                  size="md"
                  className={`mr-3 ${isSelected ? 'text-white' : 'text-gray-700'}`}
                />
                <Text
                  className={`flex-1 font-primary font-medium ${
                    isSelected ? 'text-white' : 'text-gray-700'
                  }`}
                  numberOfLines={1}
                >
                  {item.label}
                </Text>

                {/* Notification Badge */}
                {notificationCount > 0 && (
                  <NotificationBadge
                    count={notificationCount}
                    type="error"
                    size="sm"
                    className="ml-2"
                  />
                )}

                {/* Badge for special states */}
                {item.badge && (
                  <Box className="ml-2">
                    {item.badge.variant === 'dot' ? (
                      <NotificationDot type="primary" size="sm" />
                    ) : (
                      <NotificationBadge
                        count={parseInt(item.badge.text || '0', 10)}
                        type="primary"
                        size="sm"
                      />
                    )}
                  </Box>
                )}
              </Pressable>
            </Box>
          );
        })}
      </VStack>
    </VStack>
  );
};
