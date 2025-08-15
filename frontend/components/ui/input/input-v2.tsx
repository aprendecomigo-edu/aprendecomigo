'use client';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import type { TextInputProps, ViewProps, PressableProps } from 'react-native';
import { View, Pressable, TextInput } from 'react-native';
import { Svg } from 'react-native-svg';

// Input Context for sharing state between components
interface InputContextValue {
  size?: string;
  variant?: string;
  isDisabled?: boolean;
  isInvalid?: boolean;
  isFocused?: boolean;
  isHovered?: boolean;
}

const InputContext = createContext<InputContextValue>({});

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
  }
);

// Style definitions
const inputStyle = tva({
  base: 'border-background-300 flex-row overflow-hidden content-center data-[hover=true]:border-outline-400 data-[focus=true]:border-primary-700 data-[focus=true]:hover:border-primary-700 data-[disabled=true]:opacity-40 data-[disabled=true]:hover:border-background-300 items-center',

  variants: {
    size: {
      xl: 'h-12',
      lg: 'h-11',
      md: 'h-10',
      sm: 'h-9',
    },

    variant: {
      underlined:
        'rounded-none border-b data-[invalid=true]:border-b-2 data-[invalid=true]:border-error-700 data-[invalid=true]:hover:border-error-700 data-[invalid=true]:data-[focus=true]:border-error-700 data-[invalid=true]:data-[focus=true]:hover:border-error-700 data-[invalid=true]:data-[disabled=true]:hover:border-error-700',

      outline:
        'rounded border data-[invalid=true]:border-error-700 data-[invalid=true]:hover:border-error-700 data-[invalid=true]:data-[focus=true]:border-error-700 data-[invalid=true]:data-[focus=true]:hover:border-error-700 data-[invalid=true]:data-[disabled=true]:hover:border-error-700 data-[focus=true]:web:ring-1 data-[focus=true]:web:ring-inset data-[focus=true]:web:ring-indicator-primary data-[invalid=true]:web:ring-1 data-[invalid=true]:web:ring-inset data-[invalid=true]:web:ring-indicator-error data-[invalid=true]:data-[focus=true]:hover:web:ring-1 data-[invalid=true]:data-[focus=true]:hover:web:ring-inset data-[invalid=true]:data-[focus=true]:hover:web:ring-indicator-error data-[invalid=true]:data-[disabled=true]:hover:web:ring-1 data-[invalid=true]:data-[disabled=true]:hover:web:ring-inset data-[invalid=true]:data-[disabled=true]:hover:web:ring-indicator-error',

      rounded:
        'rounded-full border data-[invalid=true]:border-error-700 data-[invalid=true]:hover:border-error-700 data-[invalid=true]:data-[focus=true]:border-error-700 data-[invalid=true]:data-[focus=true]:hover:border-error-700 data-[invalid=true]:data-[disabled=true]:hover:border-error-700 data-[focus=true]:web:ring-1 data-[focus=true]:web:ring-inset data-[focus=true]:web:ring-indicator-primary data-[invalid=true]:web:ring-1 data-[invalid=true]:web:ring-inset data-[invalid=true]:web:ring-indicator-error data-[invalid=true]:data-[focus=true]:hover:web:ring-1 data-[invalid=true]:data-[focus=true]:hover:web:ring-inset data-[invalid=true]:data-[focus=true]:hover:web:ring-indicator-error data-[invalid=true]:data-[disabled=true]:hover:web:ring-1 data-[invalid=true]:data-[disabled=true]:hover:web:ring-inset data-[invalid=true]:data-[disabled=true]:hover:web:ring-indicator-error',
    },
  },
});

const inputIconStyle = tva({
  base: 'justify-center items-center text-typography-400 fill-none',
  parentVariants: {
    size: {
      '2xs': 'h-3 w-3',
      xs: 'h-3.5 w-3.5',
      sm: 'h-4 w-4',
      md: 'h-[18px] w-[18px]',
      lg: 'h-5 w-5',
      xl: 'h-6 w-6',
    },
  },
});

const inputFieldStyle = tva({
  base: 'bg-transparent flex-1 placeholder-typography-500 text-typography-900 align-middle data-[disabled=true]:web:cursor-not-allowed web:outline-0 web:outline-none web:data-[invalid=true]:ring-indicator-error web:data-[invalid=true]:ring-1',
  parentVariants: {
    variant: {
      underlined: 'web:py-1',
      outline: 'web:py-1.5 px-3',
      rounded: 'web:py-1.5 px-3',
    },
    size: {
      '2xs': 'text-2xs',
      xs: 'text-xs',
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg',
      xl: 'text-xl',
      '2xl': 'text-2xl',
      '3xl': 'text-3xl',
      '4xl': 'text-4xl',
      '5xl': 'text-5xl',
      '6xl': 'text-6xl',
    },
  },
});

const inputSlotStyle = tva({
  base: 'justify-center items-center web:disabled:cursor-not-allowed absolute right-0 h-full web:data-[disabled=true]:opacity-40',
  parentVariants: {
    variant: {
      rounded: 'pr-3',
      outline: 'pr-3',
      underlined: 'pr-1',
    },
  },
});

// Type definitions
export type IInputProps = ViewProps &
  VariantProps<typeof inputStyle> & {
    className?: string;
    isDisabled?: boolean;
    isInvalid?: boolean;
    isFocused?: boolean;
    isHovered?: boolean;
  };

export type IInputFieldProps = TextInputProps &
  VariantProps<typeof inputFieldStyle> & {
    className?: string;
  };

export type IInputIconProps = IPrimitiveIcon &
  VariantProps<typeof inputIconStyle> & {
    className?: string;
  };

export type IInputSlotProps = PressableProps &
  VariantProps<typeof inputSlotStyle> & {
    className?: string;
  };

// Main Input component - Direct v2 implementation without factory
export const Input = React.forwardRef<View, IInputProps>(
  (
    {
      className,
      size = 'md',
      variant = 'outline',
      isDisabled = false,
      isInvalid = false,
      isFocused = false,
      isHovered = false,
      children,
      ...props
    },
    ref
  ) => {
    const contextValue = useMemo(
      () => ({ size, variant, isDisabled, isInvalid, isFocused, isHovered }),
      [size, variant, isDisabled, isInvalid, isFocused, isHovered]
    );

    return (
      <InputContext.Provider value={contextValue}>
        <View
          ref={ref}
          {...props}
          className={inputStyle({ size, variant, class: className })}
          // @ts-ignore - data attributes for styling
          data-disabled={isDisabled}
          data-invalid={isInvalid}
          data-focus={isFocused}
          data-hover={isHovered}
        >
          {children}
        </View>
      </InputContext.Provider>
    );
  }
);

// InputField component
export const InputField = React.forwardRef<TextInput, IInputFieldProps>(
  ({ className, editable = true, ...props }, ref) => {
    const context = useContext(InputContext);
    const { size, variant, isDisabled, isInvalid } = context || {};

    return (
      <TextInput
        ref={ref}
        editable={!isDisabled && editable}
        {...props}
        className={inputFieldStyle({
          parentVariants: { size, variant },
          class: className,
        })}
        // @ts-ignore - data attributes for styling
        data-disabled={isDisabled}
        data-invalid={isInvalid}
      />
    );
  }
);

// InputIcon component
export const InputIcon = React.forwardRef<any, IInputIconProps>(
  ({ className, size, ...props }, ref) => {
    const context = useContext(InputContext);
    const { size: parentSize } = context || {};

    if (typeof size === 'number') {
      return <PrimitiveIcon ref={ref} {...props} className={className} size={size} />;
    }

    return (
      <PrimitiveIcon
        ref={ref}
        {...props}
        className={inputIconStyle({
          parentVariants: { size: parentSize },
          class: className,
        })}
      />
    );
  }
);

// InputSlot component
export const InputSlot = React.forwardRef<View, IInputSlotProps>(
  ({ className, children, disabled, ...props }, ref) => {
    const context = useContext(InputContext);
    const { variant, isDisabled } = context || {};

    return (
      <Pressable
        ref={ref as any}
        disabled={isDisabled || disabled}
        {...props}
        className={inputSlotStyle({
          parentVariants: { variant },
          class: className,
        })}
        // @ts-ignore - data attributes for styling
        data-disabled={isDisabled || disabled}
      >
        {children}
      </Pressable>
    );
  }
);

// Display names for debugging
Input.displayName = 'Input';
InputField.displayName = 'InputField';
InputIcon.displayName = 'InputIcon';
InputSlot.displayName = 'InputSlot';
