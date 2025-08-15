'use client';
import React, { createContext, useContext, useMemo } from 'react';
import { Platform, Text, Pressable, PressableProps, TextProps, View } from 'react-native';

// FAB Context for sharing state between components
interface FabContextValue {
  size?: string;
  placement?: string;
}

const FabContext = createContext<FabContextValue>({});

// Type definitions - simplified for testing
export type IFabProps = PressableProps & {
  size?: 'sm' | 'md' | 'lg';
  placement?: 'top right' | 'top left' | 'bottom right' | 'bottom left' | 'top center' | 'bottom center';
  className?: string;
};

export type IFabLabelProps = TextProps & {
  isTruncated?: boolean;
  bold?: boolean;
  underline?: boolean;
  strikeThrough?: boolean;
  className?: string;
};

export type IFabIconProps = React.ComponentProps<typeof View> & {
  className?: string;
};

// Simple style generator for testing
const getFabStyles = (size?: string, placement?: string) => {
  const padding = size === 'sm' ? 10 : size === 'lg' ? 16 : 12;
  
  let position = {};
  switch (placement) {
    case 'top right':
      position = { top: 16, right: 16 };
      break;
    case 'top left':
      position = { top: 16, left: 16 };
      break;
    case 'bottom left':
      position = { bottom: 16, left: 16 };
      break;
    case 'top center':
      position = { top: 16, alignSelf: 'center' as const };
      break;
    case 'bottom center':
      position = { bottom: 16, alignSelf: 'center' as const };
      break;
    case 'bottom right':
    default:
      position = { bottom: 16, right: 16 };
      break;
  }

  return {
    backgroundColor: '#3b82f6',
    borderRadius: 28,
    padding,
    flexDirection: 'row' as const,
    alignItems: 'center' as const,
    justifyContent: 'center' as const,
    position: 'absolute' as const,
    zIndex: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
    ...position,
  };
};

const getFabLabelStyles = (size?: string, bold?: boolean, underline?: boolean, strikeThrough?: boolean) => {
  const fontSize = size === 'sm' ? 14 : size === 'lg' ? 18 : 16;
  
  return {
    color: '#ffffff',
    fontSize,
    fontWeight: bold ? '700' as const : 'normal' as const,
    textDecorationLine: underline ? 'underline' as const : 
                       strikeThrough ? 'line-through' as const : 'none' as const,
    marginHorizontal: 8,
  };
};

const getFabIconStyles = (size?: string) => {
  const iconSize = size === 'sm' ? 16 : size === 'lg' ? 24 : 18;
  
  return {
    width: iconSize,
    height: iconSize,
    tintColor: '#ffffff',
  };
};

// Main FAB component - Simplified v2 without factory functions
export const Fab = React.forwardRef<View, IFabProps>(
  ({ size = 'md', placement = 'bottom right', children, style, ...props }, ref) => {
    const contextValue = useMemo(
      () => ({ size, placement }),
      [size, placement]
    );

    const fabStyles = getFabStyles(size, placement);

    return (
      <FabContext.Provider value={contextValue}>
        <Pressable
          ref={ref as any}
          {...props}
          style={[fabStyles, style]}
        >
          {children}
        </Pressable>
      </FabContext.Provider>
    );
  }
);

// FabLabel component
export const FabLabel = React.forwardRef<Text, IFabLabelProps>(
  ({
    isTruncated = false,
    bold = false,
    underline = false,
    strikeThrough = false,
    style,
    ...props
  }, ref) => {
    const context = useContext(FabContext);
    const { size } = context || {};
    
    const labelStyles = getFabLabelStyles(size, bold, underline, strikeThrough);

    return (
      <Text
        ref={ref}
        {...props}
        style={[labelStyles, style]}
        numberOfLines={isTruncated ? 1 : undefined}
        ellipsizeMode={isTruncated ? 'tail' : undefined}
      />
    );
  }
);

// FabIcon component - Simple placeholder
export const FabIcon = React.forwardRef<View, IFabIconProps>(
  ({ children, style, ...props }, ref) => {
    const context = useContext(FabContext);
    const { size } = context || {};
    
    const iconStyles = getFabIconStyles(size);

    return (
      <View
        ref={ref}
        {...props}
        style={[iconStyles, style]}
      >
        {children}
      </View>
    );
  }
);

// Display names for debugging
Fab.displayName = 'Fab';
FabLabel.displayName = 'FabLabel';
FabIcon.displayName = 'FabIcon';