'use client';
import React, { createContext, useContext, useMemo } from 'react';
import { View, ViewProps } from 'react-native';

// Divider Context for sharing state between components
interface DividerContextValue {
  orientation?: string;
}

const DividerContext = createContext<DividerContextValue>({});

// Type definitions - simplified for testing
export type IDividerProps = ViewProps & {
  orientation?: 'horizontal' | 'vertical';
  className?: string;
};

// Simple style generator for testing
const getDividerStyles = (orientation?: string) => {
  if (orientation === 'vertical') {
    return {
      backgroundColor: '#e5e7eb',
      width: 1,
      height: '100%',
    };
  } else {
    return {
      backgroundColor: '#e5e7eb',
      height: 1,
      width: '100%',
    };
  }
};

// Main Divider component - Simplified v2 without factory functions
export const Divider = React.forwardRef<View, IDividerProps>(
  ({ orientation = 'horizontal', style, ...props }, ref) => {
    const contextValue = useMemo(
      () => ({ orientation }),
      [orientation]
    );

    const dividerStyles = getDividerStyles(orientation);

    return (
      <DividerContext.Provider value={contextValue}>
        <View
          ref={ref}
          {...props}
          style={[dividerStyles, style]}
          role="separator"
          aria-orientation={orientation}
        />
      </DividerContext.Provider>
    );
  }
);

// Display names for debugging
Divider.displayName = 'Divider';