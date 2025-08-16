'use client';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import type { ViewProps, PressableProps, TextProps } from 'react-native';
import { View, Pressable, Text } from 'react-native';
import { Svg } from 'react-native-svg';

// Radio Context for sharing state between components
interface RadioContextValue {
  size?: string;
}

const RadioContext = createContext<RadioContextValue>({});

// Icon component
type IPrimitiveIcon = {
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
  },
);

// Simplified style definitions
const radioStyle = tva({
  base: 'group/radio flex-row justify-start items-center',
  variants: {
    size: {
      sm: 'gap-1.5',
      md: 'gap-2',
      lg: 'gap-2',
    },
  },
});

const radioGroupStyle = tva({
  base: 'gap-2',
});

const radioIconStyle = tva({
  base: 'rounded-full justify-center items-center text-background-800 fill-background-800',
  parentVariants: {
    size: {
      sm: 'h-[9px] w-[9px]',
      md: 'h-3 w-3',
      lg: 'h-4 w-4',
    },
  },
});

const radioIndicatorStyle = tva({
  base: 'justify-center items-center bg-transparent border-outline-400 border-2 rounded-full',
  parentVariants: {
    size: {
      sm: 'h-4 w-4',
      md: 'h-5 w-5',
      lg: 'h-6 w-6',
    },
  },
});

const radioLabelStyle = tva({
  base: 'text-typography-600',
  parentVariants: {
    size: {
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg',
    },
  },
});

// Type definitions
export type IRadioProps = PressableProps &
  VariantProps<typeof radioStyle> & {
    className?: string;
  };

export type IRadioGroupProps = ViewProps &
  VariantProps<typeof radioGroupStyle> & {
    className?: string;
  };

export type IRadioIndicatorProps = ViewProps &
  VariantProps<typeof radioIndicatorStyle> & {
    className?: string;
  };

export type IRadioLabelProps = TextProps &
  VariantProps<typeof radioLabelStyle> & {
    className?: string;
  };

export type IRadioIconProps = IPrimitiveIcon &
  VariantProps<typeof radioIconStyle> & {
    className?: string;
  };

// Main Radio component - Simplified v2 implementation
export const Radio = React.forwardRef<View, IRadioProps>(
  ({ className, size = 'md', children, ...props }, ref) => {
    const contextValue = useMemo(() => ({ size }), [size]);

    return (
      <RadioContext.Provider value={contextValue}>
        <Pressable ref={ref as any} {...props} className={radioStyle({ size, class: className })}>
          {children}
        </Pressable>
      </RadioContext.Provider>
    );
  },
);

// RadioGroup component
export const RadioGroup = React.forwardRef<View, IRadioGroupProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <View ref={ref} {...props} className={radioGroupStyle({ class: className })}>
        {children}
      </View>
    );
  },
);

// RadioIndicator component
export const RadioIndicator = React.forwardRef<View, IRadioIndicatorProps>(
  ({ className, children, ...props }, ref) => {
    const context = useContext(RadioContext);
    const { size } = context || {};

    return (
      <View
        ref={ref}
        {...props}
        className={radioIndicatorStyle({
          parentVariants: { size },
          class: className,
        })}
      >
        {children}
      </View>
    );
  },
);

// RadioLabel component
export const RadioLabel = React.forwardRef<Text, IRadioLabelProps>(
  ({ className, ...props }, ref) => {
    const context = useContext(RadioContext);
    const { size } = context || {};

    return (
      <Text
        ref={ref}
        {...props}
        className={radioLabelStyle({
          parentVariants: { size },
          class: className,
        })}
      />
    );
  },
);

// RadioIcon component
export const RadioIcon = React.forwardRef<any, IRadioIconProps>(
  ({ className, size, ...props }, ref) => {
    const context = useContext(RadioContext);
    const { size: parentSize } = context || {};

    if (typeof size === 'number') {
      return <PrimitiveIcon ref={ref} {...props} className={className} size={size} />;
    }

    return (
      <PrimitiveIcon
        ref={ref}
        {...props}
        className={radioIconStyle({
          parentVariants: { size: parentSize },
          class: className,
        })}
      />
    );
  },
);

// Display names for debugging
Radio.displayName = 'Radio';
RadioGroup.displayName = 'RadioGroup';
RadioIndicator.displayName = 'RadioIndicator';
RadioLabel.displayName = 'RadioLabel';
RadioIcon.displayName = 'RadioIcon';
