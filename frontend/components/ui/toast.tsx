import React, { createContext, useContext, useState, useCallback } from 'react';
import { Animated, Dimensions } from 'react-native';

import { Box } from './box';
import { HStack } from './hstack';
import { Icon } from './icon';
import { Pressable } from './pressable';
import { Text } from './text';

import { CheckCircle, AlertCircle, X } from '@/components/ui/icons';

const COLORS = {
  success: '#10B981',
  error: '#EF4444',
  white: '#FFFFFF',
  gray: {
    700: '#374151',
  },
} as const;

type ToastType = 'success' | 'error';

interface ToastData {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

interface ToastContextType {
  showToast: (type: ToastType, message: string, duration?: number) => void;
  hideToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

interface ToastItemProps {
  toast: ToastData;
  onDismiss: (id: string) => void;
}

const ToastItem = ({ toast, onDismiss }: ToastItemProps) => {
  const [fadeAnim] = useState(new Animated.Value(0));
  const [slideAnim] = useState(new Animated.Value(-100));

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

    // Auto dismiss
    const timer = setTimeout(() => {
      handleDismiss();
    }, toast.duration || 4000);

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

  const getToastStyles = () => {
    return {
      backgroundColor: toast.type === 'success' ? COLORS.success : COLORS.error,
    };
  };

  const getIcon = () => {
    return toast.type === 'success' ? CheckCircle : AlertCircle;
  };

  return (
    <Animated.View
      style={{
        opacity: fadeAnim,
        transform: [{ translateY: slideAnim }],
        position: 'absolute',
        top: 60,
        left: 16,
        right: 16,
        zIndex: 9999,
      }}
    >
      <Box
        className="rounded-lg shadow-lg"
        style={{
          ...getToastStyles(),
          elevation: 8,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: 2 },
          shadowOpacity: 0.25,
          shadowRadius: 3.84,
        }}
      >
        <HStack className="items-center justify-between p-4">
          <HStack className="flex-1 items-center" space="sm">
            <Icon as={getIcon()} size="sm" className="text-white" />
            <Text className="flex-1 text-white font-medium text-sm">{toast.message}</Text>
          </HStack>
          <Pressable onPress={handleDismiss} className="ml-2">
            <Icon as={X} size="sm" className="text-white" />
          </Pressable>
        </HStack>
      </Box>
    </Animated.View>
  );
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  const showToast = useCallback((type: ToastType, message: string, duration = 4000) => {
    const id = Date.now().toString();
    const newToast: ToastData = { id, type, message, duration };

    setToasts(prev => [...prev, newToast]);
  }, []);

  const hideToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ showToast, hideToast }}>
      {children}
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} onDismiss={hideToast} />
      ))}
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};
