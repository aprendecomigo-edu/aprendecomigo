'use client';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import type { ViewProps, PressableProps, TextProps } from 'react-native';
import { View, Pressable, Text, Platform } from 'react-native';
import { Svg } from 'react-native-svg';

// Radio Context for sharing state between components
interface RadioContextValue {
  size?: string;
  isDisabled?: boolean;
  isInvalid?: boolean;
  isChecked?: boolean;
  isHovered?: boolean;
  isActive?: boolean;
  isFocused?: boolean;
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
  }
);

// Style definitions (reuse existing styles)
const radioStyle = tva({
  base: 'group/radio flex-row justify-start items-center web:cursor-pointer data-[disabled=true]:web:cursor-not-allowed',
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
  base: 'justify-center items-center bg-transparent border-outline-400 border-2 rounded-full data-[focus-visible=true]:web:outline-2 data-[focus-visible=true]:web:outline-primary-700 data-[focus-visible=true]:web:outline data-[checked=true]:border-primary-600 data-[checked=true]:bg-transparent data-[hover=true]:border-outline-500 data-[hover=true]:bg-transparent data-[hover=true]:data-[checked=true]:bg-transparent data-[hover=true]:data-[checked=true]:border-primary-700 data-[hover=true]:data-[invalid=true]:border-error-700 data-[hover=true]:data-[disabled=true]:opacity-40 data-[hover=true]:data-[disabled=true]:border-outline-400 data-[hover=true]:data-[disabled=true]:data-[invalid=true]:border-error-400 data-[active=true]:bg-transparent data-[active=true]:border-primary-800 data-[invalid=true]:border-error-700 data-[disabled=true]:opacity-40 data-[disabled=true]:data-[checked=true]:border-outline-400 data-[disabled=true]:data-[checked=true]:bg-transparent data-[disabled=true]:data-[invalid=true]:border-error-400',
  parentVariants: {
    size: {
      sm: 'h-4 w-4',
      md: 'h-5 w-5',
      lg: 'h-6 w-6',
    },
  },
});

const radioLabelStyle = tva({
  base: 'text-typography-600 data-[checked=true]:text-typography-900 data-[hover=true]:text-typography-900 data-[hover=true]:data-[disabled=true]:text-typography-600 data-[hover=true]:data-[disabled=true]:data-[checked=true]:text-typography-900 data-[active=true]:text-typography-900 data-[active=true]:data-[checked=true]:text-typography-900 data-[disabled=true]:opacity-40 web:select-none',
  parentVariants: {
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

// Type definitions
export type IRadioProps = PressableProps &
  VariantProps<typeof radioStyle> & {
    className?: string;
    isDisabled?: boolean;
    isInvalid?: boolean;
    isChecked?: boolean;
    isHovered?: boolean;
    isActive?: boolean;
    isFocused?: boolean;
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

// Main Radio component - Direct v2 implementation without factory
export const Radio = React.forwardRef<View, IRadioProps>(
  (
    {
      className,
      size = 'md',
      isDisabled = false,
      isInvalid = false,
      isChecked = false,
      isHovered = false,
      isActive = false,
      isFocused = false,
      children,
      ...props
    },
    ref
  ) => {
    const contextValue = useMemo(
      () => ({ size, isDisabled, isInvalid, isChecked, isHovered, isActive, isFocused }),
      [size, isDisabled, isInvalid, isChecked, isHovered, isActive, isFocused]
    );

    const Component = Platform.OS === 'web' ? View : Pressable;

    return (
      <RadioContext.Provider value={contextValue}>
        <Component
          ref={ref as any}
          disabled={isDisabled}
          {...props}
          className={radioStyle({ size, class: className })}
          // @ts-ignore - data attributes for styling
          data-disabled={isDisabled}
          data-invalid={isInvalid}
          data-checked={isChecked}
          data-hover={isHovered}
          data-active={isActive}
          data-focus={isFocused}
        >
          {children}
        </Component>
      </RadioContext.Provider>
    );
  }
);

// RadioGroup component
export const RadioGroup = React.forwardRef<View, IRadioGroupProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <View ref={ref} {...props} className={radioGroupStyle({ class: className })}>
        {children}
      </View>
    );
  }
);

// RadioIndicator component
export const RadioIndicator = React.forwardRef<View, IRadioIndicatorProps>(
  ({ className, children, ...props }, ref) => {
    const context = useContext(RadioContext);
    const { size, isDisabled, isInvalid, isChecked, isHovered, isActive, isFocused } =
      context || {};

    return (
      <View
        ref={ref}
        {...props}
        className={radioIndicatorStyle({
          parentVariants: { size },
          class: className,
        })}
        // @ts-ignore - data attributes for styling
        data-disabled={isDisabled}
        data-invalid={isInvalid}
        data-checked={isChecked}
        data-hover={isHovered}
        data-active={isActive}
        data-focus-visible={isFocused}
      >
        {children}
      </View>
    );
  }
);

// RadioLabel component
export const RadioLabel = React.forwardRef<Text, IRadioLabelProps>(
  ({ className, ...props }, ref) => {
    const context = useContext(RadioContext);
    const { size, isDisabled, isChecked, isHovered, isActive } = context || {};

    return (
      <Text
        ref={ref}
        {...props}
        className={radioLabelStyle({
          parentVariants: { size },
          class: className,
        })}
        // @ts-ignore - data attributes for styling
        data-disabled={isDisabled}
        data-checked={isChecked}
        data-hover={isHovered}
        data-active={isActive}
      />
    );
  }
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
  }
);

// Display names for debugging
Radio.displayName = 'Radio';
RadioGroup.displayName = 'RadioGroup';
RadioIndicator.displayName = 'RadioIndicator';
RadioLabel.displayName = 'RadioLabel';
RadioIcon.displayName = 'RadioIcon';
