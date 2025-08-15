'use client';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import { View, ViewProps } from 'react-native';

// Progress Context for sharing state between components
interface ProgressContextValue {
  size?: string;
  value?: number;
  max?: number;
}

const ProgressContext = createContext<ProgressContextValue>({});

// Scope for style context
const SCOPE = 'PROGRESS';

// Style definitions (reuse existing styles)
export const progressStyle = tva({
  base: 'bg-background-300 rounded-full w-full',
  variants: {
    size: {
      xs: 'h-1',
      sm: 'h-2',
      md: 'h-3',
      lg: 'h-4',
      xl: 'h-5',
      '2xl': 'h-6',
    },
  },
});

export const progressFilledTrackStyle = tva({
  base: 'bg-primary-500 rounded-full',
  variants: {
    size: {
      xs: 'h-1',
      sm: 'h-2',
      md: 'h-3',
      lg: 'h-4',
      xl: 'h-5',
      '2xl': 'h-6',
    },
  },
  parentVariants: {
    size: {
      xs: 'h-1',
      sm: 'h-2',
      md: 'h-3',
      lg: 'h-4',
      xl: 'h-5',
      '2xl': 'h-6',
    },
  },
});

// Type definitions
export type IProgressProps = ViewProps &
  VariantProps<typeof progressStyle> & {
    className?: string;
    value?: number;
    max?: number;
  };

export type IProgressFilledTrackProps = ViewProps &
  VariantProps<typeof progressFilledTrackStyle> & {
    className?: string;
  };

// Main Progress component - Direct implementation without factory
export const Progress = React.forwardRef<View, IProgressProps>(
  ({ className, size = 'md', value = 0, max = 100, children, ...props }, ref) => {
    const contextValue = useMemo(
      () => ({
        size,
        value,
        max,
      }),
      [size, value, max]
    );

    return (
      <ProgressContext.Provider value={contextValue}>
        <View
          ref={ref}
          {...props}
          className={progressStyle({ size, class: className })}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemax={max}
          aria-valuemin={0}
        >
          {children}
        </View>
      </ProgressContext.Provider>
    );
  }
);

// ProgressFilledTrack component
export const ProgressFilledTrack = React.forwardRef<View, IProgressFilledTrackProps>(
  ({ className, ...props }, ref) => {
    const context = useContext(ProgressContext);
    const { size, value = 0, max = 100 } = context || {};

    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

    return (
      <View
        ref={ref}
        {...props}
        className={progressFilledTrackStyle({
          size,
          parentVariants: { size },
          class: className,
        })}
        style={{
          width: `${percentage}%`,
          transition: 'width 0.3s ease-in-out',
        }}
      />
    );
  }
);

// Display names for debugging
Progress.displayName = 'Progress';
ProgressFilledTrack.displayName = 'ProgressFilledTrack';
