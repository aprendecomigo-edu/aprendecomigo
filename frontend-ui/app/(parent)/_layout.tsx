/**
 * Parent Layout - Role-based layout for parent users
 *
 * Provides the navigation structure and authentication guard
 * for parent-specific routes with child account management features.
 */

import { Tabs } from 'expo-router';
import { Home, User, Settings, Users } from 'lucide-react-native';
import React from 'react';

import { AuthGuard } from '@/components/auth/auth-guard';
import { Icon } from '@/components/ui/icon';

export default function ParentLayout() {
  return (
    <AuthGuard allowedRoles={['parent']} redirectTo="/auth/signin">
      <Tabs
        screenOptions={{
          headerShown: false,
          tabBarStyle: {
            backgroundColor: '#ffffff',
            borderTopWidth: 1,
            borderTopColor: '#e5e7eb',
            paddingBottom: 8,
            height: 60,
          },
          tabBarActiveTintColor: '#3b82f6',
          tabBarInactiveTintColor: '#6b7280',
          tabBarLabelStyle: {
            fontSize: 12,
            fontWeight: '500',
            marginTop: 4,
          },
        }}
      >
        <Tabs.Screen
          name="dashboard/index"
          options={{
            title: 'Dashboard',
            tabBarIcon: ({ color, size }) => <Icon as={Home} size={size} color={color} />,
          }}
        />
        <Tabs.Screen
          name="overview/index"
          options={{
            title: 'Family Overview',
            tabBarIcon: ({ color, size }) => <Icon as={Users} size={size} color={color} />,
          }}
        />
        <Tabs.Screen
          name="child/[childId]"
          options={{
            title: 'Child Account',
            tabBarIcon: ({ color, size }) => <Icon as={User} size={size} color={color} />,
            href: null, // Hide from tab bar since it's a dynamic route
          }}
        />
        <Tabs.Screen
          name="settings/index"
          options={{
            title: 'Settings',
            tabBarIcon: ({ color, size }) => <Icon as={Settings} size={size} color={color} />,
          }}
        />
      </Tabs>
    </AuthGuard>
  );
}
