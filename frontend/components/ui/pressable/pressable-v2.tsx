'use client';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import { Pressable as RNPressable, PressableProps } from 'react-native';

// Pressable Context for sharing state between components
interface PressableContextValue {
  isPressed?: boolean;
  isHovered?: boolean;
  isFocused?: boolean;
}

const PressableContext = createContext<PressableContextValue>({});

// Scope for style context
const SCOPE = 'PRESSABLE';

// Style definitions
export const pressableStyle = tva({
  base: 'web:outline-none focus:outline-none data-[focus-visible=true]:web:outline-2 data-[focus-visible=true]:web:outline-indicator-primary data-[disabled=true]:opacity-40',
  variants: {
    variant: {
      default: '',
    },
  },
});

// Type definitions
export type IPressableProps = PressableProps &
  VariantProps<typeof pressableStyle> & {
    className?: string;
  };

// Main Pressable component - Direct implementation without factory
export const Pressable = React.forwardRef<RNPressable, IPressableProps>(
  ({ className, variant = 'default', children, ...props }, ref) => {
    const contextValue = useMemo(
      () => ({ variant }),
      [variant]
    );

    return (
      <PressableContext.Provider value={contextValue}>
        <RNPressable
          ref={ref as any}
          {...props}
          className={pressableStyle({ variant, class: className })}
        >
          {children}
        </RNPressable>
      </PressableContext.Provider>
    );
  }
);

// Display names for debugging
Pressable.displayName = 'Pressable';
