/**
 * Layout for payment monitoring admin routes.
 *
 * Provides authentication guards, navigation structure,
 * and common layout elements for payment monitoring screens.
 */

import { Slot, useRouter, usePathname } from 'expo-router';
import {
  AlertTriangle,
  BarChart3,
  CreditCard,
  FileText,
  Settings,
  Shield,
  Users,
  Zap,
} from 'lucide-react-native';
import React from 'react';

import { AuthGuard } from '@/components/auth/auth-guard';
import { Box } from '@/components/ui/box';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

const navigationItems = [
  {
    name: 'Dashboard',
    href: '/admin/payments/dashboard',
    icon: BarChart3,
    description: 'Overview & metrics',
  },
  {
    name: 'Transactions',
    href: '/admin/payments/transactions',
    icon: CreditCard,
    description: 'Transaction monitoring',
  },
  {
    name: 'Refunds',
    href: '/admin/payments/refunds',
    icon: FileText,
    description: 'Refund management',
  },
  {
    name: 'Disputes',
    href: '/admin/payments/disputes',
    icon: AlertTriangle,
    description: 'Dispute handling',
  },
  {
    name: 'Fraud Alerts',
    href: '/admin/payments/fraud',
    icon: Shield,
    description: 'Fraud detection',
  },
  {
    name: 'Webhooks',
    href: '/admin/payments/webhooks',
    icon: Zap,
    description: 'Webhook monitoring',
  },
  {
    name: 'Audit Log',
    href: '/admin/payments/audit',
    icon: Users,
    description: 'Activity tracking',
  },
];

function PaymentAdminNavigation() {
  const router = useRouter();
  const pathname = usePathname();

  return (
    <VStack space="xs" className="w-full">
      <Heading size="sm" className="text-typography-700 px-4 py-2 border-b border-border-200">
        Payment Monitoring
      </Heading>

      <VStack space="xs" className="px-2">
        {navigationItems.map(item => {
          const isActive = pathname === item.href;
          const IconComponent = item.icon;

          return (
            <Pressable
              key={item.href}
              onPress={() => router.push(item.href as any)}
              className={`
                flex-row items-center px-3 py-3 rounded-lg transition-colors
                ${
                  isActive
                    ? 'bg-primary-50 border border-primary-200'
                    : 'hover:bg-background-50 active:bg-background-100'
                }
              `}
            >
              <Icon
                as={IconComponent}
                size="sm"
                className={`mr-3 ${isActive ? 'text-primary-600' : 'text-typography-500'}`}
              />
              <VStack flex={1} space="xs">
                <Text
                  size="sm"
                  className={`font-medium ${isActive ? 'text-primary-700' : 'text-typography-700'}`}
                >
                  {item.name}
                </Text>
                <Text
                  size="xs"
                  className={`${isActive ? 'text-primary-600' : 'text-typography-500'}`}
                >
                  {item.description}
                </Text>
              </VStack>
            </Pressable>
          );
        })}
      </VStack>
    </VStack>
  );
}

export default function PaymentAdminLayout() {
  return (
    <AuthGuard requiredRoles={['admin', 'payment_admin']}>
      <HStack flex={1} className="bg-background-0">
        {/* Sidebar Navigation */}
        <Box className="w-64 bg-background-50 border-r border-border-200 h-full">
          <VStack space="md" className="py-4">
            <PaymentAdminNavigation />
          </VStack>
        </Box>

        {/* Main Content Area */}
        <VStack flex={1} className="h-full">
          <Slot />
        </VStack>
      </HStack>
    </AuthGuard>
  );
}
