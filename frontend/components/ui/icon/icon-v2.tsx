'use client';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import { Svg } from 'react-native-svg';

// Icon Context for sharing state between components
interface IconContextValue {
  size?: string;
}

const IconContext = createContext<IconContextValue>({});

// Scope for style context
const SCOPE = 'ICON';

// Style definitions
export const iconStyle = tva({
  base: 'text-typography-700 fill-none',
  variants: {
    size: {
      '2xs': 'h-3 w-3',
      xs: 'h-3.5 w-3.5',
      sm: 'h-4 w-4',
      md: 'h-[18px] w-[18px]',
      lg: 'h-5 w-5',
      xl: 'h-6 w-6',
      '2xl': 'h-7 w-7',
      '3xl': 'h-8 w-8',
    },
  },
});

// Type definitions
export type IIconProps = React.ComponentPropsWithoutRef<typeof Svg> &
  VariantProps<typeof iconStyle> & {
    height?: number | string;
    width?: number | string;
    fill?: string;
    color?: string;
    size?: number | string;
    stroke?: string;
    as?: React.ElementType;
    className?: string;
  };

// Main Icon component - Direct implementation without factory
export const Icon = React.forwardRef<React.ElementRef<typeof Svg>, IIconProps>(
  (
    {
      className,
      size = 'md',
      height,
      width,
      fill,
      color,
      stroke = 'currentColor',
      as: AsComp,
      ...props
    },
    ref,
  ) => {
    const contextValue = useMemo(() => ({ size }), [size]);

    const sizeProps = useMemo(() => {
      if (size) return { size };
      if (height && width) return { height, width };
      if (height) return { height };
      if (width) return { width };
      return {};
    }, [size, height, width]);

    const colorProps = stroke === 'currentColor' && color !== undefined ? color : stroke;

    if (AsComp) {
      return (
        <IconContext.Provider value={contextValue}>
          <AsComp ref={ref} fill={fill} {...props} {...sizeProps} stroke={colorProps} />
        </IconContext.Provider>
      );
    }

    return (
      <IconContext.Provider value={contextValue}>
        <Svg
          ref={ref}
          height={height}
          width={width}
          fill={fill}
          stroke={colorProps}
          className={iconStyle({
            size: typeof size === 'string' ? size : undefined,
            class: className,
          })}
          {...props}
        />
      </IconContext.Provider>
    );
  },
);

// Display names for debugging
Icon.displayName = 'Icon';
