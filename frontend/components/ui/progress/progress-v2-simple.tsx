'use client';
import React, { createContext, useContext, useMemo } from 'react';
import { View, ViewProps } from 'react-native';

// Progress Context for sharing state between components
interface ProgressContextValue {
  size?: string;
  value?: number;
  max?: number;
}

const ProgressContext = createContext<ProgressContextValue>({});

// Type definitions - simplified for testing
export type IProgressProps = ViewProps & {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  value?: number;
  max?: number;
  className?: string;
};

export type IProgressFilledTrackProps = ViewProps & {
  className?: string;
};

// Simple style generator for testing
const getProgressStyles = (size?: string) => {
  const height =
    size === 'xs'
      ? 4
      : size === 'sm'
        ? 8
        : size === 'lg'
          ? 16
          : size === 'xl'
            ? 20
            : size === '2xl'
              ? 24
              : 12;

  return {
    backgroundColor: '#e5e7eb',
    borderRadius: height / 2,
    width: '100%',
    height,
    overflow: 'hidden' as const,
  };
};

const getFilledTrackStyles = (size?: string, percentage: number) => {
  const height =
    size === 'xs'
      ? 4
      : size === 'sm'
        ? 8
        : size === 'lg'
          ? 16
          : size === 'xl'
            ? 20
            : size === '2xl'
              ? 24
              : 12;

  return {
    backgroundColor: '#3b82f6',
    borderRadius: height / 2,
    height,
    width: `${percentage}%`,
    transition: 'width 0.3s ease-in-out',
  };
};

// Main Progress component - Simplified v2 without factory functions
export const Progress = React.forwardRef<View, IProgressProps>(
  ({ size = 'md', value = 0, max = 100, children, style, ...props }, ref) => {
    const contextValue = useMemo(
      () => ({
        size,
        value,
        max,
      }),
      [size, value, max],
    );

    const progressStyles = getProgressStyles(size);

    return (
      <ProgressContext.Provider value={contextValue}>
        <View
          ref={ref}
          {...props}
          style={[progressStyles, style]}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemax={max}
          aria-valuemin={0}
        >
          {children}
        </View>
      </ProgressContext.Provider>
    );
  },
);

// ProgressFilledTrack component
export const ProgressFilledTrack = React.forwardRef<View, IProgressFilledTrackProps>(
  ({ style, ...props }, ref) => {
    const context = useContext(ProgressContext);
    const { size, value = 0, max = 100 } = context || {};

    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
    const filledTrackStyles = getFilledTrackStyles(size, percentage);

    return <View ref={ref} {...props} style={[filledTrackStyles, style]} />;
  },
);

// Display names for debugging
Progress.displayName = 'Progress';
ProgressFilledTrack.displayName = 'ProgressFilledTrack';
