'use client';
import React, { createContext, useContext, useMemo } from 'react';
import { ActivityIndicator, ActivityIndicatorProps } from 'react-native';

// Spinner Context for sharing state between components
interface SpinnerContextValue {
  size?: string;
  color?: string;
}

const SpinnerContext = createContext<SpinnerContextValue>({});

// Type definitions - simplified for testing
export type ISpinnerProps = ActivityIndicatorProps & {
  className?: string;
};

// Main Spinner component - Simplified v2 without factory functions
export const Spinner = React.forwardRef<ActivityIndicator, ISpinnerProps>(
  ({ size = 'small', color = '#3b82f6', ...props }, ref) => {
    const contextValue = useMemo(
      () => ({ size, color }),
      [size, color]
    );

    return (
      <SpinnerContext.Provider value={contextValue}>
        <ActivityIndicator
          ref={ref}
          {...props}
          size={size}
          color={color}
        />
      </SpinnerContext.Provider>
    );
  }
);

// Display names for debugging
Spinner.displayName = 'Spinner';
