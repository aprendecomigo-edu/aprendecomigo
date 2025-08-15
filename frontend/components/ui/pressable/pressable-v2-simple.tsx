'use client';
import React, { createContext, useContext, useMemo } from 'react';
import { Pressable as RNPressable, PressableProps } from 'react-native';

// Pressable Context for sharing state between components
interface PressableContextValue {
  isPressed?: boolean;
  isHovered?: boolean;
  isFocused?: boolean;
}

const PressableContext = createContext<PressableContextValue>({});

// Type definitions - simplified for testing
export type IPressableProps = PressableProps & {
  className?: string;
};

// Main Pressable component - Simplified v2 without factory functions
export const Pressable = React.forwardRef<RNPressable, IPressableProps>(
  ({ children, style, ...props }, ref) => {
    const contextValue = useMemo(() => ({}), []);

    return (
      <PressableContext.Provider value={contextValue}>
        <RNPressable ref={ref as any} {...props} style={[{ outline: 'none' }, style]}>
          {children}
        </RNPressable>
      </PressableContext.Provider>
    );
  }
);

// Display names for debugging
Pressable.displayName = 'Pressable';
