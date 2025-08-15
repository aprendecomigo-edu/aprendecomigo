'use client';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import { View, ViewProps } from 'react-native';

// Divider Context for sharing state between components
interface DividerContextValue {
  orientation?: string;
}

const DividerContext = createContext<DividerContextValue>({});

// Scope for style context
const SCOPE = 'DIVIDER';

// Style definitions (reuse existing styles)
export const dividerStyle = tva({
  base: 'bg-background-200',
  variants: {
    orientation: {
      vertical: 'w-px h-full',
      horizontal: 'h-px w-full',
    },
  },
});

// Type definitions
export type IDividerProps = ViewProps &
  VariantProps<typeof dividerStyle> & {
    className?: string;
  };

// Main Divider component - Direct implementation without factory
export const Divider = React.forwardRef<View, IDividerProps>(
  ({ className, orientation = 'horizontal', ...props }, ref) => {
    const contextValue = useMemo(() => ({ orientation }), [orientation]);

    return (
      <DividerContext.Provider value={contextValue}>
        <View
          ref={ref}
          {...props}
          className={dividerStyle({
            orientation,
            class: className,
          })}
          role="separator"
          aria-orientation={orientation}
        />
      </DividerContext.Provider>
    );
  }
);

// Display names for debugging
Divider.displayName = 'Divider';
