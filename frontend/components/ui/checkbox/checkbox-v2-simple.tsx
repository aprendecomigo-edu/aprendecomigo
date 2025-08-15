'use client';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import type { ViewProps, PressableProps, TextProps } from 'react-native';
import { View, Pressable, Text } from 'react-native';
import { Svg } from 'react-native-svg';

// Checkbox Context for sharing state between components
interface CheckboxContextValue {
  size?: string;
}

const CheckboxContext = createContext<CheckboxContextValue>({});

// Icon component
type IPrimitiveIcon = React.ComponentPropsWithoutRef<typeof Svg> & {
  height?: number | string;
  width?: number | string;
  fill?: string;
  color?: string;
  size?: number | string;
  stroke?: string;
  as?: React.ElementType;
  className?: string;
};

const PrimitiveIcon = React.forwardRef<React.ElementRef<typeof Svg>, IPrimitiveIcon>(
  ({ height, width, fill, color, size, stroke, as: AsComp, ...props }, ref) => {
    const sizeProps = useMemo(() => {
      if (size) return { size };
      if (height && width) return { height, width };
      if (height) return { height };
      if (width) return { width };
      return {};
    }, [size, height, width]);

    let colorProps = {};
    if (color) {
      colorProps = { ...colorProps, color: color };
    }
    if (stroke) {
      colorProps = { ...colorProps, stroke: stroke };
    }
    if (fill) {
      colorProps = { ...colorProps, fill: fill };
    }
    if (AsComp) {
      return <AsComp ref={ref} {...sizeProps} {...colorProps} {...props} />;
    }
    return <Svg ref={ref} height={height} width={width} {...colorProps} {...props} />;
  }
);

// Simplified style definitions
const checkboxStyle = tva({
  base: 'group/checkbox flex-row items-center justify-start gap-2',
  variants: {
    size: {
      lg: 'gap-2',
      md: 'gap-2',
      sm: 'gap-1.5',
    },
  },
});

const checkboxIndicatorStyle = tva({
  base: 'justify-center items-center border-outline-400 bg-transparent rounded',
  parentVariants: {
    size: {
      lg: 'w-6 h-6 border-[3px]',
      md: 'w-5 h-5 border-2',
      sm: 'w-4 h-4 border-2',
    },
  },
});

const checkboxLabelStyle = tva({
  base: 'text-typography-600',
  parentVariants: {
    size: {
      lg: 'text-lg',
      md: 'text-base',
      sm: 'text-sm',
    },
  },
});

const checkboxIconStyle = tva({
  base: 'text-typography-50 fill-none',
  parentVariants: {
    size: {
      sm: 'h-3 w-3',
      md: 'h-4 w-4',
      lg: 'h-5 w-5',
    },
  },
});

const checkboxGroupStyle = tva({
  base: 'gap-2',
});

// Type definitions
export type ICheckboxProps = PressableProps &
  VariantProps<typeof checkboxStyle> & {
    className?: string;
  };

export type ICheckboxIndicatorProps = ViewProps &
  VariantProps<typeof checkboxIndicatorStyle> & {
    className?: string;
  };

export type ICheckboxLabelProps = TextProps &
  VariantProps<typeof checkboxLabelStyle> & {
    className?: string;
  };

export type ICheckboxIconProps = IPrimitiveIcon &
  VariantProps<typeof checkboxIconStyle> & {
    className?: string;
  };

export type ICheckboxGroupProps = ViewProps &
  VariantProps<typeof checkboxGroupStyle> & {
    className?: string;
  };

// Main Checkbox component - Simplified v2 implementation
export const Checkbox = React.forwardRef<View, ICheckboxProps>(
  ({ className, size = 'md', children, ...props }, ref) => {
    const contextValue = useMemo(() => ({ size }), [size]);

    return (
      <CheckboxContext.Provider value={contextValue}>
        <Pressable
          ref={ref as any}
          {...props}
          className={checkboxStyle({ size, class: className })}
        >
          {children}
        </Pressable>
      </CheckboxContext.Provider>
    );
  }
);

// CheckboxIndicator component
export const CheckboxIndicator = React.forwardRef<View, ICheckboxIndicatorProps>(
  ({ className, children, ...props }, ref) => {
    const context = useContext(CheckboxContext);
    const { size } = context || {};

    return (
      <View
        ref={ref}
        {...props}
        className={checkboxIndicatorStyle({
          parentVariants: { size },
          class: className,
        })}
      >
        {children}
      </View>
    );
  }
);

// CheckboxLabel component
export const CheckboxLabel = React.forwardRef<Text, ICheckboxLabelProps>(
  ({ className, ...props }, ref) => {
    const context = useContext(CheckboxContext);
    const { size } = context || {};

    return (
      <Text
        ref={ref}
        {...props}
        className={checkboxLabelStyle({
          parentVariants: { size },
          class: className,
        })}
      />
    );
  }
);

// CheckboxIcon component
export const CheckboxIcon = React.forwardRef<any, ICheckboxIconProps>(
  ({ className, size, ...props }, ref) => {
    const context = useContext(CheckboxContext);
    const { size: parentSize } = context || {};

    if (typeof size === 'number') {
      return <PrimitiveIcon ref={ref} {...props} className={className} size={size} />;
    }

    return (
      <PrimitiveIcon
        ref={ref}
        {...props}
        className={checkboxIconStyle({
          parentVariants: { size: parentSize },
          class: className,
        })}
      />
    );
  }
);

// CheckboxGroup component
export const CheckboxGroup = React.forwardRef<View, ICheckboxGroupProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <View ref={ref} {...props} className={checkboxGroupStyle({ class: className })}>
        {children}
      </View>
    );
  }
);

// Display names for debugging
Checkbox.displayName = 'Checkbox';
CheckboxIndicator.displayName = 'CheckboxIndicator';
CheckboxLabel.displayName = 'CheckboxLabel';
CheckboxIcon.displayName = 'CheckboxIcon';
CheckboxGroup.displayName = 'CheckboxGroup';
