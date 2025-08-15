'use client';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import { Switch as RNSwitch, SwitchProps } from 'react-native';

// Switch Context for sharing state between components
interface SwitchContextValue {
  size?: string;
  isDisabled?: boolean;
  isInvalid?: boolean;
}

const SwitchContext = createContext<SwitchContextValue>({});

// Scope for style context
const SCOPE = 'SWITCH';

// Style definitions (reuse existing styles)
export const switchStyle = tva({
  base: 'data-[focus=true]:outline-0 data-[focus=true]:ring-2 data-[focus=true]:ring-indicator-primary web:cursor-pointer disabled:cursor-not-allowed data-[disabled=true]:opacity-40 data-[invalid=true]:border-error-700 data-[invalid=true]:rounded-xl data-[invalid=true]:border-2',
  variants: {
    size: {
      sm: 'scale-75',
      md: '',
      lg: 'scale-125',
    },
  },
});

// Type definitions
export type ISwitchProps = SwitchProps &
  VariantProps<typeof switchStyle> & {
    className?: string;
    isDisabled?: boolean;
    isInvalid?: boolean;
  };

// Main Switch component - Direct implementation without factory
export const Switch = React.forwardRef<RNSwitch, ISwitchProps>(
  ({ className, size = 'md', isDisabled = false, isInvalid = false, disabled, ...props }, ref) => {
    const contextValue = useMemo(
      () => ({
        size,
        isDisabled: isDisabled || disabled,
        isInvalid,
      }),
      [size, isDisabled, disabled, isInvalid]
    );

    const finalDisabled = isDisabled || disabled;

    return (
      <SwitchContext.Provider value={contextValue}>
        <RNSwitch
          ref={ref}
          {...props}
          disabled={finalDisabled}
          className={switchStyle({
            size,
            class: className,
          })}
          style={{
            opacity: finalDisabled ? 0.4 : 1,
            transform: [
              {
                scale: size === 'sm' ? 0.75 : size === 'lg' ? 1.25 : 1,
              },
            ],
            ...(isInvalid && {
              borderWidth: 2,
              borderColor: '#dc2626',
              borderRadius: 12,
            }),
          }}
        />
      </SwitchContext.Provider>
    );
  }
);

// Display names for debugging
Switch.displayName = 'Switch';
