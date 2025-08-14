import { cn } from '@gluestack-ui/nativewind-utils/cn';
import { router, useSegments } from 'expo-router';
import type { Href } from 'expo-router';
import { ChevronRightIcon, HomeIcon } from 'lucide-react-native';
import React, { useMemo } from 'react';
import { Platform } from 'react-native';

import { Box } from '@/components/ui/box';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import type { BreadcrumbItem } from '@/types/navigation';

interface BreadcrumbProps {
  items?: BreadcrumbItem[];
  maxItems?: number;
  showHome?: boolean;
  className?: string;
}

// Route title mapping for automatic breadcrumb generation
const ROUTE_TITLES: Record<string, string> = {
  home: 'Dashboard',
  dashboard: 'Dashboard',
  teachers: 'Teachers',
  students: 'Students',
  classes: 'Classes',
  calendar: 'Calendar',
  chat: 'Messages',
  users: 'Users',
  settings: 'Settings',
  invitations: 'Invitations',
  profile: 'Profile',
  purchase: 'Purchase',
  onboarding: 'Getting Started',
  admin: 'Administration',
  balance: 'Balance',
  'school-admin': 'School Admin',
};

/**
 * Breadcrumb component - provides navigation trail showing current location
 * Supports automatic generation from current route or manual items
 */
export const Breadcrumb: React.FC<BreadcrumbProps> = ({
  items,
  maxItems = 5,
  showHome = true,
  className = '',
}) => {
  const segments = useSegments();

  // Generate breadcrumbs automatically from route segments if no items provided
  const breadcrumbItems = useMemo(() => {
    if (items) {
      return items;
    }

    const generatedItems: BreadcrumbItem[] = [];

    // Add home if requested
    if (showHome) {
      generatedItems.push({
        id: 'home',
        label: 'Home',
        route: '/home',
        isActive: segments.length === 0 || segments[0] === 'home',
      });
    }

    // Generate items from segments
    let currentPath = '';
    segments.forEach((segment, index) => {
      // Skip auth and other system routes
      if (['auth', '_layout', '+html', '+not-found'].includes(segment)) {
        return;
      }

      currentPath += `/${segment}`;
      const isLast = index === segments.length - 1;
      const title = ROUTE_TITLES[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);

      generatedItems.push({
        id: segment,
        label: title,
        route: isLast ? undefined : currentPath, // Don't make last item clickable
        isActive: isLast,
      });
    });

    return generatedItems;
  }, [items, segments, showHome]);

  // Truncate items if exceeding maxItems
  const displayItems = useMemo(() => {
    if (breadcrumbItems.length <= maxItems) {
      return breadcrumbItems;
    }

    const firstItem = breadcrumbItems[0];
    const lastItems = breadcrumbItems.slice(-(maxItems - 2));

    return [
      firstItem,
      {
        id: 'ellipsis',
        label: '...',
        isActive: false,
      },
      ...lastItems,
    ];
  }, [breadcrumbItems, maxItems]);

  const handleNavigation = (route: string) => {
    router.push(route as Href<string>);
  };

  // Don't render if no items
  if (displayItems.length <= 1) {
    return null;
  }

  return (
    <Box className={cn('flex-row items-center py-2', className)}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        className="flex-1"
        contentContainerStyle={{ alignItems: 'center' }}
      >
        <HStack space="xs" className="items-center px-1">
          {displayItems.map((item, index) => (
            <React.Fragment key={item.id}>
              {/* Breadcrumb Item */}
              <BreadcrumbItem
                item={item}
                onPress={item.route ? () => handleNavigation(item.route!) : undefined}
              />

              {/* Separator */}
              {index < displayItems.length - 1 && (
                <Icon as={ChevronRightIcon} size="sm" className="text-typography-400 mx-1" />
              )}
            </React.Fragment>
          ))}
        </HStack>
      </ScrollView>
    </Box>
  );
};

interface BreadcrumbItemProps {
  item: BreadcrumbItem;
  onPress?: () => void;
}

const BreadcrumbItem: React.FC<BreadcrumbItemProps> = ({ item, onPress }) => {
  const isClickable = !!onPress && !item.isActive;
  const isHome = item.id === 'home';

  const content = (
    <HStack space="xs" className="items-center">
      {isHome && (
        <Icon
          as={HomeIcon}
          size="sm"
          className={cn(item.isActive ? 'text-primary-600' : 'text-typography-500')}
        />
      )}
      <Text
        className={cn(
          'text-sm',
          item.isActive ? 'text-primary-600 font-semibold' : 'text-typography-600',
          isClickable && 'hover:text-primary-600',
          Platform.OS === 'web' && isClickable && 'cursor-pointer'
        )}
        numberOfLines={1}
      >
        {item.label}
      </Text>
    </HStack>
  );

  if (isClickable) {
    return (
      <Pressable
        onPress={onPress}
        className={cn('px-1 py-1 rounded', Platform.OS === 'web' && 'hover:bg-background-50')}
      >
        {content}
      </Pressable>
    );
  }

  return <Box className="px-1 py-1">{content}</Box>;
};

export default Breadcrumb;
