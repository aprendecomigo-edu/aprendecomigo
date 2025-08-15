'use client';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import type { ViewProps, TextInputProps, PressableProps } from 'react-native';
import { View, Pressable, TextInput } from 'react-native';
import { Svg } from 'react-native-svg';

// Select Context for sharing state between components
interface SelectContextValue {
  size?: string;
  variant?: string;
}

const SelectContext = createContext<SelectContextValue>({});

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
    if (fill) {
      colorProps = { ...colorProps, fill: fill };
    }
    if (stroke) {
      colorProps = { ...colorProps, stroke: stroke };
    }
    if (color) {
      colorProps = { ...colorProps, color: color };
    }

    if (AsComp) {
      return <AsComp ref={ref} {...props} {...sizeProps} {...colorProps} />;
    }
    return <Svg ref={ref} height={height} width={width} {...colorProps} {...props} />;
  }
);

// Simplified style definitions
const selectStyle = tva({
  base: '',
});

const selectTriggerStyle = tva({
  base: 'border border-background-300 rounded flex-row items-center overflow-hidden',
  variants: {
    size: {
      xl: 'h-12',
      lg: 'h-11',
      md: 'h-10',
      sm: 'h-9',
    },
    variant: {
      underlined: 'border-0 border-b rounded-none',
      outline: '',
      rounded: 'rounded-full',
    },
  },
});

const selectInputStyle = tva({
  base: 'py-auto px-3 placeholder:text-typography-500 web:w-full h-full text-typography-900 pointer-events-none web:outline-none',
  parentVariants: {
    size: {
      xl: 'text-xl',
      lg: 'text-lg',
      md: 'text-base',
      sm: 'text-sm',
    },
    variant: {
      underlined: 'px-0',
      outline: '',
      rounded: 'px-4',
    },
  },
});

const selectIconStyle = tva({
  base: 'text-background-500 fill-none',
  parentVariants: {
    size: {
      sm: 'h-4 w-4',
      md: 'h-[18px] w-[18px]',
      lg: 'h-5 w-5',
      xl: 'h-6 w-6',
    },
  },
});

// Type definitions
export type ISelectProps = ViewProps &
  VariantProps<typeof selectStyle> & {
    className?: string;
  };

export type ISelectTriggerProps = PressableProps &
  VariantProps<typeof selectTriggerStyle> & {
    className?: string;
  };

export type ISelectInputProps = TextInputProps &
  VariantProps<typeof selectInputStyle> & {
    className?: string;
  };

export type ISelectIconProps = IPrimitiveIcon &
  VariantProps<typeof selectIconStyle> & {
    className?: string;
  };

// Main Select component - Simplified v2 implementation
export const Select = React.forwardRef<View, ISelectProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <View ref={ref} {...props} className={selectStyle({ class: className })}>
        {children}
      </View>
    );
  }
);

// SelectTrigger component
export const SelectTrigger = React.forwardRef<View, ISelectTriggerProps>(
  ({ className, size = 'md', variant = 'outline', children, ...props }, ref) => {
    const contextValue = useMemo(() => ({ size, variant }), [size, variant]);

    return (
      <SelectContext.Provider value={contextValue}>
        <Pressable
          ref={ref as any}
          {...props}
          className={selectTriggerStyle({ size, variant, class: className })}
        >
          {children}
        </Pressable>
      </SelectContext.Provider>
    );
  }
);

// SelectInput component
export const SelectInput = React.forwardRef<TextInput, ISelectInputProps>(
  ({ className, ...props }, ref) => {
    const context = useContext(SelectContext);
    const { size, variant } = context || {};

    return (
      <TextInput
        ref={ref}
        {...props}
        className={selectInputStyle({
          parentVariants: { size, variant },
          class: className,
        })}
      />
    );
  }
);

// SelectIcon component
export const SelectIcon = React.forwardRef<any, ISelectIconProps>(
  ({ className, size, ...props }, ref) => {
    const context = useContext(SelectContext);
    const { size: parentSize } = context || {};

    if (typeof size === 'number') {
      return <PrimitiveIcon ref={ref} {...props} className={className} size={size} />;
    }

    return (
      <PrimitiveIcon
        ref={ref}
        {...props}
        className={selectIconStyle({
          parentVariants: { size: parentSize },
          class: className,
        })}
      />
    );
  }
);

// Display names for debugging
Select.displayName = 'Select';
SelectTrigger.displayName = 'SelectTrigger';
SelectInput.displayName = 'SelectInput';
SelectIcon.displayName = 'SelectIcon';
