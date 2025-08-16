'use client';
import React, { createContext, useContext, useMemo } from 'react';
import { View, ViewProps } from 'react-native';

// Icon Context for sharing state between components
interface IconContextValue {
  size?: string;
}

const IconContext = createContext<IconContextValue>({});

// Type definitions - simplified for testing
export type IIconProps = ViewProps & {
  height?: number | string;
  width?: number | string;
  fill?: string;
  color?: string;
  size?: '2xs' | 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | number;
  stroke?: string;
  as?: React.ElementType;
  className?: string;
};

// Simple style generator for testing
const getIconStyles = (
  size?: string | number,
  height?: number | string,
  width?: number | string,
) => {
  if (typeof size === 'number') {
    return { width: size, height: size };
  }

  if (height && width) {
    return { height, width };
  }

  const sizeMap = {
    '2xs': 12,
    xs: 14,
    sm: 16,
    md: 18,
    lg: 20,
    xl: 24,
    '2xl': 28,
    '3xl': 32,
  };

  const dimension = sizeMap[size as keyof typeof sizeMap] || sizeMap.md;

  return {
    width: dimension,
    height: dimension,
  };
};

// Main Icon component - Simplified v2 without factory functions
export const Icon = React.forwardRef<View, IIconProps>(
  (
    {
      size = 'md',
      height,
      width,
      fill,
      color,
      stroke = 'currentColor',
      as: AsComp,
      children,
      style,
      ...props
    },
    ref,
  ) => {
    const contextValue = useMemo(() => ({ size }), [size]);

    const iconStyles = getIconStyles(size, height, width);

    if (AsComp) {
      return (
        <IconContext.Provider value={contextValue}>
          <AsComp
            ref={ref}
            fill={fill}
            stroke={color || stroke}
            style={[iconStyles, style]}
            {...props}
          >
            {children}
          </AsComp>
        </IconContext.Provider>
      );
    }

    return (
      <IconContext.Provider value={contextValue}>
        <View ref={ref} style={[iconStyles, { tintColor: color || stroke }, style]} {...props}>
          {children}
        </View>
      </IconContext.Provider>
    );
  },
);

// Display names for debugging
Icon.displayName = 'Icon';
