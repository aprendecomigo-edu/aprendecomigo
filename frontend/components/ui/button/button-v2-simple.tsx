'use client';
import React, { createContext, useContext, useMemo } from 'react';
import type { PressableProps, TextProps, ViewProps } from 'react-native';
import { ActivityIndicator, Pressable, Text, View } from 'react-native';

// Button Context for sharing state between components
interface ButtonContextValue {
  variant?: string;
  size?: string;
  action?: string;
}

const ButtonContext = createContext<ButtonContextValue>({});

// Type definitions - minimal for testing
export type IButtonProps = PressableProps & {
  variant?: 'solid' | 'outline' | 'link';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  action?: 'primary' | 'secondary' | 'positive' | 'negative' | 'default';
  className?: string;
};

export type IButtonTextProps = TextProps & {
  className?: string;
};

export type IButtonGroupProps = ViewProps & {
  space?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  isAttached?: boolean;
};

// Simple style generator for testing
const getButtonStyles = (variant?: string, size?: string, action?: string) => {
  const baseStyle = {
    flexDirection: 'row' as const,
    alignItems: 'center' as const,
    justifyContent: 'center' as const,
    borderRadius: 4,
    paddingHorizontal:
      size === 'xs' ? 12 : size === 'sm' ? 16 : size === 'lg' ? 24 : size === 'xl' ? 28 : 20,
    paddingVertical:
      size === 'xs' ? 6 : size === 'sm' ? 8 : size === 'lg' ? 12 : size === 'xl' ? 14 : 10,
  };

  // Action colors
  const colors = {
    primary: '#3b82f6',
    secondary: '#6b7280',
    positive: '#10b981',
    negative: '#ef4444',
    default: '#000000',
  };

  const backgroundColor =
    variant === 'link'
      ? 'transparent'
      : variant === 'outline'
        ? 'transparent'
        : colors[action || 'primary'];

  const borderWidth = variant === 'outline' ? 1 : 0;
  const borderColor = colors[action || 'primary'];

  return {
    ...baseStyle,
    backgroundColor,
    borderWidth,
    borderColor,
  };
};

const getTextStyles = (variant?: string, action?: string) => {
  const colors = {
    primary: '#3b82f6',
    secondary: '#6b7280',
    positive: '#10b981',
    negative: '#ef4444',
    default: '#000000',
  };

  const color = variant === 'solid' ? '#ffffff' : colors[action || 'primary'];

  return {
    color,
    fontSize: 16,
    fontWeight: '500' as const,
  };
};

// Main Button component - Simplified v2 without factory functions
export const Button = React.forwardRef<View, IButtonProps>(
  ({ variant = 'solid', size = 'md', action = 'primary', children, style, ...props }, ref) => {
    const contextValue = useMemo(() => ({ variant, size, action }), [variant, size, action]);

    const buttonStyles = getButtonStyles(variant, size, action);

    return (
      <ButtonContext.Provider value={contextValue}>
        <Pressable ref={ref as any} {...props} style={[buttonStyles, style]}>
          {children}
        </Pressable>
      </ButtonContext.Provider>
    );
  },
);

// ButtonText component
export const ButtonText = React.forwardRef<Text, IButtonTextProps>(({ style, ...props }, ref) => {
  const context = useContext(ButtonContext);
  const { variant, action } = context || {};

  const textStyles = getTextStyles(variant, action);

  return <Text ref={ref} {...props} style={[textStyles, style]} />;
});

// ButtonSpinner component
export const ButtonSpinner = ActivityIndicator;

// ButtonIcon component - Simple placeholder
export const ButtonIcon = ({ children, ...props }: any) => {
  return <View {...props}>{children}</View>;
};

// ButtonGroup component
export const ButtonGroup = React.forwardRef<View, IButtonGroupProps>(
  ({ space = 'md', isAttached = false, style, ...props }, ref) => {
    const gap =
      space === 'xs' ? 4 : space === 'sm' ? 8 : space === 'lg' ? 16 : space === 'xl' ? 20 : 12;

    return (
      <View
        ref={ref}
        {...props}
        style={[
          {
            flexDirection: 'row',
            gap: isAttached ? 0 : gap,
          },
          style,
        ]}
      />
    );
  },
);

// Display names for debugging
Button.displayName = 'Button';
ButtonText.displayName = 'ButtonText';
ButtonSpinner.displayName = 'ButtonSpinner';
ButtonIcon.displayName = 'ButtonIcon';
ButtonGroup.displayName = 'ButtonGroup';
