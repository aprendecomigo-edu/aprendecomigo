'use client';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import type { ViewProps, TextProps } from 'react-native';
import { View, Text } from 'react-native';
import { Svg } from 'react-native-svg';

// Alert Context for sharing state between components
interface AlertContextValue {
  action?: string;
  variant?: string;
}

const AlertContext = createContext<AlertContextValue>({});

// Icon component
type IPrimitiveIcon = React.ComponentPropsWithoutRef<typeof Svg> & {
  height?: number | string;
  width?: number | string;
  fill?: string;
  color?: string;
  size?: number | string;
  stroke?: string;
  as?: React.ElementType;
  className?: string;
};

const PrimitiveIcon = React.forwardRef<React.ElementRef<typeof Svg>, IPrimitiveIcon>(
  ({ height, width, fill, color, size, stroke, as: AsComp, ...props }, ref) => {
    const sizeProps = useMemo(() => {
      if (size) return { size };
      if (height && width) return { height, width };
      if (height) return { height };
      if (width) return { width };
      return {};
    }, [size, height, width]);

    let colorProps = {};
    if (color) {
      colorProps = { ...colorProps, color: color };
    }
    if (stroke) {
      colorProps = { ...colorProps, stroke: stroke };
    }
    if (fill) {
      colorProps = { ...colorProps, fill: fill };
    }
    if (AsComp) {
      return <AsComp ref={ref} {...sizeProps} {...colorProps} {...props} />;
    }
    return <Svg ref={ref} height={height} width={width} {...colorProps} {...props} />;
  }
);

// Simplified style definitions
const alertStyle = tva({
  base: 'items-center py-3 px-4 rounded-md flex-row gap-2',
  variants: {
    action: {
      error: 'bg-background-error',
      warning: 'bg-background-warning',
      success: 'bg-background-success',
      info: 'bg-background-info',
      muted: 'bg-background-muted',
    },
    variant: {
      solid: '',
      outline: 'border bg-background-0',
    },
  },
});

const alertTextStyle = tva({
  base: 'flex-1 font-normal font-body',
  variants: {
    size: {
      sm: 'text-sm',
      md: 'text-md',
      lg: 'text-lg',
    },
  },
  parentVariants: {
    action: {
      error: 'text-error-800',
      warning: 'text-warning-800',
      success: 'text-success-800',
      info: 'text-info-800',
      muted: 'text-background-800',
    },
  },
});

const alertIconStyle = tva({
  base: 'fill-none',
  variants: {
    size: {
      sm: 'h-4 w-4',
      md: 'h-[18px] w-[18px]',
      lg: 'h-5 w-5',
    },
  },
  parentVariants: {
    action: {
      error: 'text-error-800',
      warning: 'text-warning-800',
      success: 'text-success-800',
      info: 'text-info-800',
      muted: 'text-secondary-800',
    },
  },
});

// Type definitions
export type IAlertProps = ViewProps &
  VariantProps<typeof alertStyle> & {
    className?: string;
  };

export type IAlertTextProps = TextProps &
  VariantProps<typeof alertTextStyle> & {
    className?: string;
  };

export type IAlertIconProps = IPrimitiveIcon &
  VariantProps<typeof alertIconStyle> & {
    className?: string;
  };

// Main Alert component - Simplified v2 implementation
export const Alert = React.forwardRef<View, IAlertProps>(
  ({ className, variant = 'solid', action = 'muted', children, ...props }, ref) => {
    const contextValue = useMemo(() => ({ variant, action }), [variant, action]);

    return (
      <AlertContext.Provider value={contextValue}>
        <View ref={ref} {...props} className={alertStyle({ action, variant, class: className })}>
          {children}
        </View>
      </AlertContext.Provider>
    );
  }
);

// AlertText component
export const AlertText = React.forwardRef<Text, IAlertTextProps>(
  ({ className, size = 'md', ...props }, ref) => {
    const context = useContext(AlertContext);
    const { action } = context || {};

    return (
      <Text
        ref={ref}
        {...props}
        className={alertTextStyle({
          size,
          parentVariants: { action },
          class: className,
        })}
      />
    );
  }
);

// AlertIcon component
export const AlertIcon = React.forwardRef<any, IAlertIconProps>(
  ({ className, size = 'md', ...props }, ref) => {
    const context = useContext(AlertContext);
    const { action } = context || {};

    if (typeof size === 'number') {
      return <PrimitiveIcon ref={ref} {...props} className={className} size={size} />;
    }

    return (
      <PrimitiveIcon
        ref={ref}
        {...props}
        className={alertIconStyle({
          parentVariants: { action },
          size,
          class: className,
        })}
      />
    );
  }
);

// Display names for debugging
Alert.displayName = 'Alert';
AlertText.displayName = 'AlertText';
AlertIcon.displayName = 'AlertIcon';
