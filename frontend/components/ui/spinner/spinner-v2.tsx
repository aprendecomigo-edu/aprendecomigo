'use client';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import { ActivityIndicator, ActivityIndicatorProps } from 'react-native';

// Spinner Context for sharing state between components
interface SpinnerContextValue {
  size?: string;
  color?: string;
}

const SpinnerContext = createContext<SpinnerContextValue>({});

// Scope for style context
const SCOPE = 'SPINNER';

// Style definitions
export const spinnerStyle = tva({
  base: '',
  variants: {
    size: {
      small: '',
      large: '',
    },
  },
});

// Type definitions
export type ISpinnerProps = ActivityIndicatorProps &
  VariantProps<typeof spinnerStyle> & {
    className?: string;
  };

// Main Spinner component - Direct implementation without factory
export const Spinner = React.forwardRef<ActivityIndicator, ISpinnerProps>(
  ({ className, size = 'small', color = '#3b82f6', ...props }, ref) => {
    const contextValue = useMemo(() => ({ size, color }), [size, color]);

    return (
      <SpinnerContext.Provider value={contextValue}>
        <ActivityIndicator
          ref={ref}
          {...props}
          size={size}
          color={color}
          className={spinnerStyle({ size, class: className })}
        />
      </SpinnerContext.Provider>
    );
  },
);

// Display names for debugging
Spinner.displayName = 'Spinner';
