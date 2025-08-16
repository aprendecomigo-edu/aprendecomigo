import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo, useRef, useState, useCallback } from 'react';
import type { TextProps, ViewProps } from 'react-native';
import { Text, View } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withSpring,
  runOnJS,
} from 'react-native-reanimated';

// Toast Context for sharing state between components
interface ToastContextValue {
  variant?: string;
  action?: string;
}

const ToastContext = createContext<ToastContextValue>({});

// Scope for style context
const SCOPE = 'TOAST';

// Toast state management
interface ToastItem {
  id: string;
  title?: string;
  description?: string;
  variant?: 'solid' | 'outline';
  action?: 'error' | 'warning' | 'success' | 'info' | 'muted';
  duration?: number;
}

interface ToastState {
  toasts: ToastItem[];
  show: (toast: Omit<ToastItem, 'id'>) => string;
  hide: (id: string) => void;
  hideAll: () => void;
}

// Create toast hook implementation
const toastState: ToastState = {
  toasts: [],
  show: () => '',
  hide: () => {},
  hideAll: () => {},
};

// Style definitions (reuse existing styles)
export const toastStyle = tva({
  base: 'p-4 m-1 rounded-md gap-1 web:pointer-events-auto shadow-hard-5 border-outline-100',
  variants: {
    action: {
      error: 'bg-error-800',
      warning: 'bg-warning-700',
      success: 'bg-success-700',
      info: 'bg-info-700',
      muted: 'bg-secondary-700',
    },
    variant: {
      solid: '',
      outline: 'border bg-background-0',
    },
  },
});

export const toastTitleStyle = tva({
  base: 'text-typography-0 font-medium font-body tracking-md text-left',
  variants: {
    isTruncated: {
      true: '',
    },
    bold: {
      true: 'font-bold',
    },
    underline: {
      true: 'underline',
    },
    strikeThrough: {
      true: 'line-through',
    },
    size: {
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
    },
  },
  parentVariants: {
    variant: {
      solid: '',
      outline: '',
    },
    action: {
      error: '',
      warning: '',
      success: '',
      info: '',
      muted: '',
    },
  },
  parentCompoundVariants: [
    {
      variant: 'outline',
      action: 'error',
      class: 'text-error-800',
    },
    {
      variant: 'outline',
      action: 'warning',
      class: 'text-warning-800',
    },
    {
      variant: 'outline',
      action: 'success',
      class: 'text-success-800',
    },
    {
      variant: 'outline',
      action: 'info',
      class: 'text-info-800',
    },
    {
      variant: 'outline',
      action: 'muted',
      class: 'text-background-800',
    },
  ],
});

export const toastDescriptionStyle = tva({
  base: 'font-normal font-body tracking-md text-left',
  variants: {
    isTruncated: {
      true: '',
    },
    bold: {
      true: 'font-bold',
    },
    underline: {
      true: 'underline',
    },
    strikeThrough: {
      true: 'line-through',
    },
    size: {
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
    },
  },
  parentVariants: {
    variant: {
      solid: 'text-typography-50',
      outline: 'text-typography-900',
    },
  },
});

// Type definitions
export type IToastProps = ViewProps & {
  className?: string;
  context?: ToastContextValue;
} & VariantProps<typeof toastStyle>;

export type IToastTitleProps = TextProps & {
  className?: string;
} & VariantProps<typeof toastTitleStyle>;

export type IToastDescriptionProps = TextProps & {
  className?: string;
} & VariantProps<typeof toastDescriptionStyle>;

// Toast Root Component - Direct implementation without factory
const ToastRoot = React.forwardRef<View, ViewProps>(({ ...props }, ref) => {
  return <Animated.View {...props} ref={ref} />;
});

// Main Toast component - Direct implementation
export const Toast = React.forwardRef<View, IToastProps>(
  ({ className, variant = 'solid', action = 'muted', context, children, ...props }, ref) => {
    const contextValue = useMemo(
      () => ({ variant, action, ...context }),
      [variant, action, context],
    );

    return (
      <ToastContext.Provider value={contextValue}>
        <ToastRoot
          ref={ref}
          {...props}
          className={toastStyle({ variant, action, class: className })}
        >
          {children}
        </ToastRoot>
      </ToastContext.Provider>
    );
  },
);

// ToastTitle component - Direct implementation
export const ToastTitle = React.forwardRef<Text, IToastTitleProps>(
  ({ className, size = 'md', ...props }, ref) => {
    const context = useContext(ToastContext);
    const { variant: parentVariant, action: parentAction } = context || {};

    return (
      <Text
        ref={ref}
        {...props}
        className={toastTitleStyle({
          size,
          class: className,
          parentVariants: {
            variant: parentVariant,
            action: parentAction,
          },
        })}
      />
    );
  },
);

// ToastDescription component - Direct implementation
export const ToastDescription = React.forwardRef<Text, IToastDescriptionProps>(
  ({ className, size = 'md', ...props }, ref) => {
    const context = useContext(ToastContext);
    const { variant: parentVariant } = context || {};

    return (
      <Text
        ref={ref}
        {...props}
        className={toastDescriptionStyle({
          size,
          class: className,
          parentVariants: {
            variant: parentVariant,
          },
        })}
      />
    );
  },
);

// Toast hook implementation - Direct implementation without factory
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

// Toast Container component for rendering toasts
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

// Display names for debugging
Toast.displayName = 'Toast';
ToastTitle.displayName = 'ToastTitle';
ToastDescription.displayName = 'ToastDescription';
