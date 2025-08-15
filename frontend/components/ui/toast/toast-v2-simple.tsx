'use client';
import React, { useState, useCallback } from 'react';
import type { TextProps, ViewProps } from 'react-native';
import { Text, View } from 'react-native';
import Animated from 'react-native-reanimated';

// Simple toast state management
interface ToastItem {
  id: string;
  title?: string;
  description?: string;
  variant?: 'solid' | 'outline';
  action?: 'error' | 'warning' | 'success' | 'info' | 'muted';
  duration?: number;
}

// Toast type definitions
export type IToastProps = ViewProps & {
  className?: string;
  variant?: 'solid' | 'outline';
  action?: 'error' | 'warning' | 'success' | 'info' | 'muted';
};

export type IToastTitleProps = TextProps & {
  className?: string;
  size?: '2xs' | 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | '6xl';
};

export type IToastDescriptionProps = TextProps & {
  className?: string;
  size?: '2xs' | 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | '6xl';
};

// Simple Toast Root
export const Toast = React.forwardRef<View, IToastProps>(
  ({ className = '', variant = 'solid', action = 'muted', ...props }, ref) => {
    const actionClasses = {
      error: 'bg-error-800',
      warning: 'bg-warning-700',
      success: 'bg-success-700',
      info: 'bg-info-700',
      muted: 'bg-secondary-700',
    };

    const variantClasses = {
      solid: '',
      outline: 'border bg-background-0',
    };

    const baseClasses =
      'p-4 m-1 rounded-md gap-1 web:pointer-events-auto shadow-hard-5 border-outline-100';
    const combinedClasses = `${baseClasses} ${actionClasses[action]} ${variantClasses[variant]} ${className}`;

    return <Animated.View ref={ref} {...props} className={combinedClasses} />;
  }
);

// Simple Toast Title
export const ToastTitle = React.forwardRef<Text, IToastTitleProps>(
  ({ className = '', size = 'md', ...props }, ref) => {
    const sizeClasses = {
      '2xs': 'text-2xs',
      xs: 'text-xs',
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg',
      xl: 'text-xl',
      '2xl': 'text-2xl',
      '3xl': 'text-3xl',
      '4xl': 'text-4xl',
      '5xl': 'text-5xl',
      '6xl': 'text-6xl',
    };

    const baseClasses = 'text-typography-0 font-medium font-body tracking-md text-left';
    const combinedClasses = `${baseClasses} ${sizeClasses[size]} ${className}`;

    return <Text ref={ref} {...props} className={combinedClasses} />;
  }
);

// Simple Toast Description
export const ToastDescription = React.forwardRef<Text, IToastDescriptionProps>(
  ({ className = '', size = 'md', ...props }, ref) => {
    const sizeClasses = {
      '2xs': 'text-2xs',
      xs: 'text-xs',
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg',
      xl: 'text-xl',
      '2xl': 'text-2xl',
      '3xl': 'text-3xl',
      '4xl': 'text-4xl',
      '5xl': 'text-5xl',
      '6xl': 'text-6xl',
    };

    const baseClasses = 'font-normal font-body tracking-md text-left text-typography-50';
    const combinedClasses = `${baseClasses} ${sizeClasses[size]} ${className}`;

    return <Text ref={ref} {...props} className={combinedClasses} />;
  }
);

// Simple toast hook - Direct implementation without factory
export function useToast() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const show = useCallback((toast: Omit<ToastItem, 'id'>) => {
    const id = Date.now().toString() + Math.random().toString(36);
    const newToast: ToastItem = {
      ...toast,
      id,
      duration: toast.duration ?? 5000,
    };

    setToasts(prev => [...prev, newToast]);

    // Auto-hide after duration
    if (newToast.duration > 0) {
      setTimeout(() => {
        hide(id);
      }, newToast.duration);
    }

    return id;
  }, []);

  const hide = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const hideAll = useCallback(() => {
    setToasts([]);
  }, []);

  return {
    toasts,
    show,
    hide,
    hideAll,
  };
}

// Simple Toast Container
export const ToastContainer = () => {
  const { toasts } = useToast();

  if (toasts.length === 0) return null;

  return (
    <View className="absolute top-0 left-0 right-0 z-50 flex-col items-center pt-safe">
      {toasts.map(toast => (
        <Toast key={toast.id} variant={toast.variant} action={toast.action}>
          {toast.title && <ToastTitle>{toast.title}</ToastTitle>}
          {toast.description && <ToastDescription>{toast.description}</ToastDescription>}
        </Toast>
      ))}
    </View>
  );
};

// Display names
Toast.displayName = 'Toast';
ToastTitle.displayName = 'ToastTitle';
ToastDescription.displayName = 'ToastDescription';
