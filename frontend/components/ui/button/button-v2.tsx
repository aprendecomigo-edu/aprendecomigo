'use client';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import type { PressableProps, TextProps, ViewProps } from 'react-native';
import { ActivityIndicator, Pressable, Text, View } from 'react-native';
import { Svg } from 'react-native-svg';

// Button Context for sharing state between components
interface ButtonContextValue {
  variant?: string;
  size?: string;
  action?: string;
}

const ButtonContext = createContext<ButtonContextValue>({});

// Scope for style context
const SCOPE = 'BUTTON';

// Icon component
export type IPrimitiveIcon = React.ComponentPropsWithoutRef<typeof Svg> & {
  height?: number | string;
  width?: number | string;
  fill?: string;
  color?: string;
  size?: number | string;
  stroke?: string;
  as?: React.ElementType;
};

const PrimitiveIcon = React.forwardRef(
  (
    {
      height,
      width,
      fill,
      color,
      size,
      stroke = 'currentColor',
      as: AsComp,
      ...props
    }: IPrimitiveIcon,
    ref: React.Ref<Svg>
  ) => {
    const sizeProps = useMemo(() => {
      if (size) return { size };
      if (height && width) return { height, width };
      if (height) return { height };
      if (width) return { width };
      return {};
    }, [size, height, width]);

    const colorProps = stroke === 'currentColor' && color !== undefined ? color : stroke;

    if (AsComp) {
      return <AsComp ref={ref} fill={fill} {...props} {...sizeProps} stroke={colorProps} />;
    }
    return (
      <Svg ref={ref} height={height} width={width} fill={fill} stroke={colorProps} {...props} />
    );
  }
);

// Style definitions (reuse existing styles)
export const buttonStyle = tva({
  base: 'group/button rounded bg-primary-500 flex-row items-center justify-center data-[focus-visible=true]:web:outline-none data-[focus-visible=true]:web:ring-2 data-[disabled=true]:opacity-40',
  variants: {
    action: {
      primary: 'bg-primary-500 border-primary-300 hover:bg-primary-600 active:bg-primary-700',
      secondary:
        'bg-secondary-500 border-secondary-300 hover:bg-secondary-600 active:bg-secondary-700',
      positive: 'bg-success-500 border-success-300 hover:bg-success-600 active:bg-success-700',
      negative: 'bg-error-500 border-error-300 hover:bg-error-600 active:bg-error-700',
      default: 'bg-transparent hover:bg-background-50 active:bg-transparent',
    },
    variant: {
      solid: '',
      outline: 'bg-transparent border',
      link: 'bg-transparent',
    },
    size: {
      xs: 'px-3.5 h-8 gap-1',
      sm: 'px-4 h-9 gap-1.5',
      md: 'px-5 h-10 gap-2',
      lg: 'px-6 h-11 gap-2.5',
      xl: 'px-7 h-12 gap-2.5',
    },
  },
  compoundVariants: [
    {
      action: 'primary',
      variant: 'solid',
      class: 'bg-primary-500 hover:bg-primary-600 active:bg-primary-700',
    },
    {
      action: 'primary',
      variant: 'outline',
      class: 'border-primary-500 hover:bg-primary-50 active:bg-primary-100',
    },
    {
      action: 'primary',
      variant: 'link',
      class: 'hover:underline active:underline',
    },
    {
      action: 'secondary',
      variant: 'solid',
      class: 'bg-secondary-500 hover:bg-secondary-600 active:bg-secondary-700',
    },
    {
      action: 'secondary',
      variant: 'outline',
      class: 'border-secondary-500 hover:bg-secondary-50 active:bg-secondary-100',
    },
    {
      action: 'secondary',
      variant: 'link',
      class: 'hover:underline active:underline',
    },
    {
      action: 'positive',
      variant: 'solid',
      class: 'bg-success-500 hover:bg-success-600 active:bg-success-700',
    },
    {
      action: 'positive',
      variant: 'outline',
      class: 'border-success-500 hover:bg-success-50 active:bg-success-100',
    },
    {
      action: 'positive',
      variant: 'link',
      class: 'hover:underline active:underline',
    },
    {
      action: 'negative',
      variant: 'solid',
      class: 'bg-error-500 hover:bg-error-600 active:bg-error-700',
    },
    {
      action: 'negative',
      variant: 'outline',
      class: 'border-error-500 hover:bg-error-50 active:bg-error-100',
    },
    {
      action: 'negative',
      variant: 'link',
      class: 'hover:underline active:underline',
    },
    {
      action: 'default',
      variant: 'solid',
      class: 'bg-transparent hover:bg-background-50 active:bg-background-100',
    },
    {
      action: 'default',
      variant: 'outline',
      class: 'border-outline-200 hover:bg-background-50 active:bg-background-100',
    },
    {
      action: 'default',
      variant: 'link',
      class: 'hover:underline active:underline',
    },
  ],
});

export const buttonTextStyle = tva({
  base: 'font-medium',
  variants: {
    action: {
      primary: 'text-primary-500',
      secondary: 'text-secondary-500',
      positive: 'text-success-500',
      negative: 'text-error-500',
      default: 'text-typography-900',
    },
    variant: {
      solid: 'text-typography-0',
      outline: '',
      link: 'group-hover/button:underline group-active/button:underline',
    },
    size: {
      xs: 'text-xs',
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg',
      xl: 'text-xl',
    },
  },
  parentVariants: {
    action: {
      primary: '',
      secondary: '',
      positive: '',
      negative: '',
      default: '',
    },
    variant: {
      solid: '',
      outline: '',
      link: '',
    },
  },
  parentCompoundVariants: [
    {
      variant: 'solid',
      action: 'primary',
      class: 'text-typography-0 hover:text-typography-0 active:text-typography-0',
    },
    {
      variant: 'solid',
      action: 'secondary',
      class: 'text-typography-0 hover:text-typography-0 active:text-typography-0',
    },
    {
      variant: 'solid',
      action: 'positive',
      class: 'text-typography-0 hover:text-typography-0 active:text-typography-0',
    },
    {
      variant: 'solid',
      action: 'negative',
      class: 'text-typography-0 hover:text-typography-0 active:text-typography-0',
    },
  ],
});

export const buttonIconStyle = tva({
  base: 'fill-none',
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
  parentVariants: {
    size: {
      xs: 'h-3 w-3',
      sm: 'h-3.5 w-3.5',
      md: 'h-[18px] w-[18px]',
      lg: 'h-5 w-5',
      xl: 'h-6 w-6',
    },
  },
});

export const buttonGroupStyle = tva({
  base: '',
  variants: {
    space: {
      xs: 'gap-1',
      sm: 'gap-2',
      md: 'gap-3',
      lg: 'gap-4',
      xl: 'gap-5',
      '2xl': 'gap-6',
      '3xl': 'gap-7',
      '4xl': 'gap-8',
    },
    isAttached: {
      true: 'gap-0',
    },
  },
});

// Type definitions
export type IButtonProps = PressableProps &
  VariantProps<typeof buttonStyle> & {
    className?: string;
  };

export type IButtonTextProps = TextProps &
  VariantProps<typeof buttonTextStyle> & {
    className?: string;
  };

export type IButtonIcon = React.ComponentPropsWithoutRef<typeof PrimitiveIcon> &
  VariantProps<typeof buttonIconStyle> & {
    className?: string;
    as?: React.ElementType;
  };

export type IButtonGroupProps = ViewProps & VariantProps<typeof buttonGroupStyle>;

// Button Root Component - Direct implementation without factory
const ButtonRoot = React.forwardRef<View, PressableProps>(({ ...props }, ref) => {
  return <Pressable {...props} ref={ref as any} />;
});

// Main Button component - Direct implementation
export const Button = React.forwardRef<View, IButtonProps>(
  ({ className, variant = 'solid', size = 'md', action = 'primary', children, ...props }, ref) => {
    const contextValue = useMemo(() => ({ variant, size, action }), [variant, size, action]);

    return (
      <ButtonContext.Provider value={contextValue}>
        <ButtonRoot
          ref={ref}
          {...props}
          className={buttonStyle({ variant, size, action, class: className })}
        >
          {children}
        </ButtonRoot>
      </ButtonContext.Provider>
    );
  }
);

// ButtonText component - Direct implementation
export const ButtonText = React.forwardRef<Text, IButtonTextProps>(
  ({ className, variant, size, action, ...props }, ref) => {
    const context = useContext(ButtonContext);
    const { variant: parentVariant, size: parentSize, action: parentAction } = context || {};

    return (
      <Text
        ref={ref}
        {...props}
        className={buttonTextStyle({
          parentVariants: {
            variant: parentVariant,
            size: parentSize,
            action: parentAction,
          },
          variant,
          size,
          action,
          class: className,
        })}
      />
    );
  }
);

// ButtonSpinner component
export const ButtonSpinner = ActivityIndicator;

// ButtonIcon component - Direct implementation
export const ButtonIcon = React.forwardRef<any, IButtonIcon>(
  ({ className, size, ...props }, ref) => {
    const context = useContext(ButtonContext);
    const { size: parentSize } = context || {};

    if (typeof size === 'number') {
      return <PrimitiveIcon ref={ref} {...props} className={className} size={size} />;
    }

    return (
      <PrimitiveIcon
        ref={ref}
        {...props}
        className={buttonIconStyle({
          parentVariants: {
            size: parentSize,
          },
          size,
          class: className,
        })}
      />
    );
  }
);

// ButtonGroup component
export const ButtonGroup = React.forwardRef<View, IButtonGroupProps>(
  ({ className, space = 'md', isAttached = false, ...props }, ref) => {
    return (
      <View
        ref={ref}
        {...props}
        className={buttonGroupStyle({ space, isAttached, class: className })}
      />
    );
  }
);

// Display names for debugging
Button.displayName = 'Button';
ButtonText.displayName = 'ButtonText';
ButtonSpinner.displayName = 'ButtonSpinner';
ButtonIcon.displayName = 'ButtonIcon';
ButtonGroup.displayName = 'ButtonGroup';
