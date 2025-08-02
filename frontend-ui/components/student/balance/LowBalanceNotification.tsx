/**
 * Low Balance Notification Component
 * 
 * Toast notification system for real-time balance alerts with cross-platform
 * compatibility (Expo toast for mobile, custom toast for web).
 */

import React, { createContext, useContext, useState, useCallback, useRef } from 'react';
import { Platform, Animated, Dimensions } from 'react-native';
import { AlertTriangle, Clock, CreditCard, X, ShoppingCart } from 'lucide-react-native';
import useRouter from '@unitools/router';

import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Box } from '@/components/ui/box';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import type { ToastNotificationData, NotificationPriority } from '@/types/notification';

// Toast styling constants
const TOAST_COLORS = {
  low_balance: {
    bg: '#FEF3C7', // warning-100
    border: '#F59E0B', // warning-500
    text: '#92400E', // warning-800
    icon: '#D97706', // warning-600
  },
  balance_depleted: {
    bg: '#FEE2E2', // error-100
    border: '#EF4444', // error-500
    text: '#991B1B', // error-800
    icon: '#DC2626', // error-600
  },
  package_expiring: {
    bg: '#FEF3C7', // warning-100
    border: '#F59E0B', // warning-500
    text: '#92400E', // warning-800
    icon: '#D97706', // warning-600
  },
  success: {
    bg: '#DCFCE7', // success-100
    border: '#22C55E', // success-500
    text: '#166534', // success-800
    icon: '#16A34A', // success-600
  },
  error: {
    bg: '#FEE2E2', // error-100
    border: '#EF4444', // error-500
    text: '#991B1B', // error-800
    icon: '#DC2626', // error-600
  },
} as const;

interface LowBalanceToastContextType {
  showToast: (data: ToastNotificationData) => void;
  hideToast: (id: string) => void;
  hideAllToasts: () => void;
}

const LowBalanceToastContext = createContext<LowBalanceToastContextType | undefined>(undefined);

interface ToastItemProps {
  toast: ToastNotificationData;
  onDismiss: (id: string) => void;
  onAction: (data: ToastNotificationData) => void;
}

/**
 * Individual toast item component
 */
const ToastItem = ({ toast, onDismiss, onAction }: ToastItemProps) => {
  const [fadeAnim] = useState(new Animated.Value(0));
  const [slideAnim] = useState(new Animated.Value(-100));
  const router = useRouter();
  
  const colors = TOAST_COLORS[toast.type] || TOAST_COLORS.error;
  
  const getIcon = () => {
    switch (toast.type) {
      case 'low_balance':
      case 'balance_depleted':
        return AlertTriangle;
      case 'package_expiring':
        return Clock;
      default:
        return AlertTriangle;
    }
  };

  const getPriorityBadgeAction = (): 'error' | 'warning' | 'primary' | 'secondary' => {
    switch (toast.priority) {
      case 'urgent':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'primary';
      default:
        return 'secondary';
    }
  };

  React.useEffect(() => {
    // Animate in
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();

    // Auto dismiss (longer for urgent notifications)
    const duration = toast.duration || (toast.priority === 'urgent' ? 8000 : 5000);
    const timer = setTimeout(() => {
      handleDismiss();
    }, duration);

    return () => clearTimeout(timer);
  }, []);

  const handleDismiss = () => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: -100,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start(() => {
      onDismiss(toast.id);
    });
  };

  const handleAction = () => {
    if (toast.actionUrl) {
      router.push(toast.actionUrl);
    }
    onAction(toast);
    handleDismiss();
  };

  const IconComponent = getIcon();

  return (
    <Animated.View
      style={{
        opacity: fadeAnim,
        transform: [{ translateY: slideAnim }],
        position: 'absolute',
        top: Platform.OS === 'web' ? 20 : 60,
        left: 16,
        right: 16,
        zIndex: 9999,
        elevation: 8,
      }}
    >
      <Box
        className="rounded-lg shadow-lg p-4"
        style={{
          backgroundColor: colors.bg,
          borderLeftWidth: 4,
          borderLeftColor: colors.border,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: 2 },
          shadowOpacity: 0.25,
          shadowRadius: 3.84,
        }}
      >
        <VStack space="sm">
          <HStack className="items-start justify-between">
            <HStack space="sm" className="items-start flex-1">
              <Icon 
                as={IconComponent} 
                size="sm" 
                style={{ color: colors.icon }} 
              />
              <VStack space="xs" className="flex-1">
                <HStack space="xs" className="items-center flex-wrap">
                  <Text 
                    className="font-semibold text-sm"
                    style={{ color: colors.text }}
                  >
                    {toast.title}
                  </Text>
                  <Badge
                    variant="solid"
                    action={getPriorityBadgeAction()}
                    size="xs"
                  >
                    <Text className="text-xs">
                      {toast.priority}
                    </Text>
                  </Badge>
                </HStack>
                
                <Text 
                  className="text-sm"
                  style={{ color: colors.text }}
                >
                  {toast.message}
                </Text>
              </VStack>
            </HStack>

            <Pressable onPress={handleDismiss} className="p-1">
              <Icon 
                as={X} 
                size="sm" 
                style={{ color: colors.icon }} 
              />
            </Pressable>
          </HStack>

          {/* Action buttons */}
          {toast.actionLabel && (
            <HStack space="sm" className="mt-2">
              <Button
                action={toast.priority === 'urgent' ? 'negative' : 'primary'}
                variant="solid"
                size="sm"
                onPress={handleAction}
                className="flex-1"
              >
                <ButtonIcon as={ShoppingCart} />
                <ButtonText>{toast.actionLabel}</ButtonText>
              </Button>
              
              <Button
                action="secondary"
                variant="outline"
                size="sm"
                onPress={handleDismiss}
              >
                <ButtonText>Later</ButtonText>
              </Button>
            </HStack>
          )}
        </VStack>
      </Box>
    </Animated.View>
  );
};

/**
 * Low Balance Toast Provider
 */
export const LowBalanceToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastNotificationData[]>([]);
  const toastIdCounter = useRef(0);

  const showToast = useCallback((data: ToastNotificationData) => {
    // Generate unique ID if not provided
    const id = data.id || `toast-${++toastIdCounter.current}`;
    const newToast: ToastNotificationData = { ...data, id };

    // Remove any existing toast with the same type to avoid duplicates
    setToasts(prev => {
      const filtered = prev.filter(t => t.type !== data.type);
      return [...filtered, newToast];
    });
  }, []);

  const hideToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const hideAllToasts = useCallback(() => {
    setToasts([]);
  }, []);

  const handleToastAction = useCallback((data: ToastNotificationData) => {
    // Custom action handler if needed
    console.log('Toast action:', data);
  }, []);

  return (
    <LowBalanceToastContext.Provider value={{ showToast, hideToast, hideAllToasts }}>
      {children}
      {toasts.map(toast => (
        <ToastItem 
          key={toast.id} 
          toast={toast} 
          onDismiss={hideToast}
          onAction={handleToastAction}
        />
      ))}
    </LowBalanceToastContext.Provider>
  );
};

/**
 * Hook to use the Low Balance Toast context
 */
export const useLowBalanceToast = (): LowBalanceToastContextType => {
  const context = useContext(LowBalanceToastContext);
  if (context === undefined) {
    throw new Error('useLowBalanceToast must be used within a LowBalanceToastProvider');
  }
  return context;
};

/**
 * Higher-order component to show balance alerts
 */
export const withBalanceAlerts = <P extends object>(
  Component: React.ComponentType<P>
): React.ComponentType<P> => {
  return (props: P) => {
    return (
      <LowBalanceToastProvider>
        <Component {...props} />
      </LowBalanceToastProvider>
    );
  };
};

/**
 * Utility functions for showing specific balance notifications
 */
export const BalanceNotificationUtils = {
  showLowBalanceAlert: (
    showToast: (data: ToastNotificationData) => void,
    remainingHours: number
  ) => {
    showToast({
      id: 'low-balance-alert',
      type: 'low_balance',
      title: 'Low Balance Alert',
      message: `Only ${remainingHours.toFixed(1)} hours remaining. Purchase more to continue learning.`,
      priority: 'high',
      duration: 6000,
      actionLabel: 'Purchase Hours',
      actionUrl: '/purchase',
    });
  },

  showCriticalBalanceAlert: (
    showToast: (data: ToastNotificationData) => void,
    remainingHours: number
  ) => {
    showToast({
      id: 'critical-balance-alert',
      type: 'balance_depleted',
      title: 'Critical Balance',
      message: `Only ${remainingHours.toFixed(1)} hours left! Your learning will be interrupted soon.`,
      priority: 'urgent',
      duration: 8000,
      actionLabel: 'Buy Hours Now',
      actionUrl: '/purchase',
    });
  },

  showPackageExpiringAlert: (
    showToast: (data: ToastNotificationData) => void,
    daysUntilExpiry: number,
    hoursRemaining: number
  ) => {
    showToast({
      id: 'package-expiring-alert',
      type: 'package_expiring',
      title: 'Package Expiring Soon',
      message: `${hoursRemaining.toFixed(1)} hours expire in ${daysUntilExpiry} day${daysUntilExpiry === 1 ? '' : 's'}`,
      priority: 'high',
      duration: 6000,
      actionLabel: 'Renew Package',
      actionUrl: '/purchase',
    });
  },

  showBalanceDepletedAlert: (
    showToast: (data: ToastNotificationData) => void
  ) => {
    showToast({
      id: 'balance-depleted-alert',
      type: 'balance_depleted',
      title: 'Balance Depleted',
      message: 'Your tutoring hours have run out. Purchase more to continue learning.',
      priority: 'urgent',
      duration: 10000,
      actionLabel: 'Purchase Hours',
      actionUrl: '/purchase',
    });
  },
};