'use client';
import React, { createContext, useContext, useMemo } from 'react';
import { Switch as RNSwitch, SwitchProps } from 'react-native';

// Switch Context for sharing state between components
interface SwitchContextValue {
  size?: string;
  isDisabled?: boolean;
  isInvalid?: boolean;
}

const SwitchContext = createContext<SwitchContextValue>({});

// Type definitions - simplified for testing
export type ISwitchProps = SwitchProps & {
  size?: 'sm' | 'md' | 'lg';
  isDisabled?: boolean;
  isInvalid?: boolean;
  className?: string;
};

// Simple style generator for testing
const getSwitchStyles = (size?: string, isDisabled?: boolean, isInvalid?: boolean) => {
  const scale = size === 'sm' ? 0.75 : size === 'lg' ? 1.25 : 1;

  return {
    opacity: isDisabled ? 0.4 : 1,
    transform: [{ scale }],
    ...(isInvalid && {
      borderWidth: 2,
      borderColor: '#dc2626',
      borderRadius: 12,
    }),
  };
};

// Main Switch component - Simplified v2 without factory functions
export const Switch = React.forwardRef<RNSwitch, ISwitchProps>(
  ({ size = 'md', isDisabled = false, isInvalid = false, disabled, style, ...props }, ref) => {
    const contextValue = useMemo(
      () => ({
        size,
        isDisabled: isDisabled || disabled,
        isInvalid,
      }),
      [size, isDisabled, disabled, isInvalid]
    );

    const finalDisabled = isDisabled || disabled;
    const switchStyles = getSwitchStyles(size, finalDisabled, isInvalid);

    return (
      <SwitchContext.Provider value={contextValue}>
        <RNSwitch ref={ref} {...props} disabled={finalDisabled} style={[switchStyles, style]} />
      </SwitchContext.Provider>
    );
  }
);

// Display names for debugging
Switch.displayName = 'Switch';
