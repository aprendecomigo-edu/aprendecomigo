import { router, useSegments } from 'expo-router';
import type { Href } from 'expo-router';
import React, { useState, useEffect } from 'react';

import { sidebarNavItems, getNavigationItems, NAVIGATION_COLORS, type SidebarItem } from './navigation-config';

import { useAuth } from '@/api/authContext';
import { navigationApi } from '@/api/navigationApi';
import { Box } from '@/components/ui/box';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { VStack } from '@/components/ui/vstack';
import { NotificationBadge, NotificationDot } from '@/components/ui/notification-badge';

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
  const { userProfile } = useAuth();

  // Get navigation items based on user role
  const navItems = React.useMemo(() => {
    const userRole = userProfile?.user_type || 'student';
    return getNavigationItems(userRole);
  }, [userProfile]);

  // Get current route based on segments
  const getCurrentRoute = () => {
    if (segments.length === 0) return '/home';
    const firstSegment = segments[0];
    return `/${firstSegment}`;
  };

  // Update selected index based on current route
  useEffect(() => {
    const currentRoute = getCurrentRoute();
    const routeIndex = navItems.findIndex(item => item.route === currentRoute);
    if (routeIndex !== -1) {
      setSelectedIndex(routeIndex);
    } else {
      // Default to home if no match found
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
      className={`w-20 pt-6 h-full items-center border-r border-border-300 pb-5 ${className}`}
      space="md"
      style={{ backgroundColor: NAVIGATION_COLORS.primary }}
      data-testid="side-navigation"
    >
      <VStack className="items-center" space="md">
        {navItems.map((item, index) => {
          const isSelected = index === selectedIndex;
          const notificationCount = notificationCounts[item.id] || 0;
          
          return (
            <Box key={item.id} className="relative">
              <Pressable
                className={`p-3 rounded-full w-12 h-12 items-center justify-center ${
                  isSelected ? 'bg-orange-400' : 'hover:bg-white/10'
                }`}
                onPress={() => handlePress(index)}
              >
                <Icon as={item.icon} size="lg" className="text-white" />
              </Pressable>
              
              {/* Notification Badge */}
              {notificationCount > 0 && (
                <NotificationBadge
                  count={notificationCount}
                  type="error"
                  size="sm"
                  className="absolute -top-1 -right-1"
                />
              )}
              
              {/* Badge for special states */}
              {item.badge && (
                <Box className="absolute -top-1 -right-1">
                  {item.badge.variant === 'dot' ? (
                    <NotificationDot type="primary" size="sm" />
                  ) : (
                    <NotificationBadge
                      count={parseInt(item.badge.text || '0')}
                      type="primary"
                      size="sm"
                    />
                  )}
                </Box>
              )}
            </Box>
          );
        })}
      </VStack>

      <Box className="flex-1" />
    </VStack>
  );
};
