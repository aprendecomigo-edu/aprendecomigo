import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import type { TextProps, ViewProps } from 'react-native';
import { Text, View } from 'react-native';
import { Svg } from 'react-native-svg';

// Form Control Context for sharing state between components
interface FormControlContextValue {
  size?: string;
}

const FormControlContext = createContext<FormControlContextValue>({});

// Scope for style context
const SCOPE = 'FORM_CONTROL';

// Icon component
export type IPrimitiveIcon = React.ComponentPropsWithoutRef<typeof Svg> & {
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

// Style definitions (reuse existing styles)
const formControlStyle = tva({
  base: 'flex flex-col',
  variants: {
    size: {
      sm: '',
      md: '',
      lg: '',
    },
  },
});

const formControlErrorIconStyle = tva({
  base: 'text-error-700 fill-none',
  variants: {
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

const formControlErrorStyle = tva({
  base: 'flex flex-row justify-start items-center mt-1 gap-1',
});

const formControlErrorTextStyle = tva({
  base: 'text-error-700',
  variants: {
    isTruncated: {
      true: 'web:truncate',
    },
    bold: {
      true: 'font-bold',
    },
    underline: {
      true: 'underline',
    },
    strikeThrough: {
      true: 'line-through',
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
    sub: {
      true: 'text-xs',
    },
    italic: {
      true: 'italic',
    },
    highlight: {
      true: 'bg-yellow-500',
    },
  },
});

const formControlHelperStyle = tva({
  base: 'flex flex-row justify-start items-center mt-1',
});

const formControlHelperTextStyle = tva({
  base: 'text-typography-500',
  variants: {
    isTruncated: {
      true: 'web:truncate',
    },
    bold: {
      true: 'font-bold',
    },
    underline: {
      true: 'underline',
    },
    strikeThrough: {
      true: 'line-through',
    },
    size: {
      '2xs': 'text-2xs',
      xs: 'text-xs',
      sm: 'text-xs',
      md: 'text-sm',
      lg: 'text-base',
      xl: 'text-xl',
      '2xl': 'text-2xl',
      '3xl': 'text-3xl',
      '4xl': 'text-4xl',
      '5xl': 'text-5xl',
      '6xl': 'text-6xl',
    },
    sub: {
      true: 'text-xs',
    },
    italic: {
      true: 'italic',
    },
    highlight: {
      true: 'bg-yellow-500',
    },
  },
});

const formControlLabelStyle = tva({
  base: 'flex flex-row justify-start items-center mb-1',
});

const formControlLabelTextStyle = tva({
  base: 'font-medium text-typography-900',
  variants: {
    isTruncated: {
      true: 'web:truncate',
    },
    bold: {
      true: 'font-bold',
    },
    underline: {
      true: 'underline',
    },
    strikeThrough: {
      true: 'line-through',
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
    sub: {
      true: 'text-xs',
    },
    italic: {
      true: 'italic',
    },
    highlight: {
      true: 'bg-yellow-500',
    },
  },
});

const formControlLabelAstrickStyle = tva({
  base: 'font-medium text-typography-900',
  variants: {
    isTruncated: {
      true: 'web:truncate',
    },
    bold: {
      true: 'font-bold',
    },
    underline: {
      true: 'underline',
    },
    strikeThrough: {
      true: 'line-through',
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
    sub: {
      true: 'text-xs',
    },
    italic: {
      true: 'italic',
    },
    highlight: {
      true: 'bg-yellow-500',
    },
  },
});

// Type definitions
export type IFormControlProps = ViewProps &
  VariantProps<typeof formControlStyle> & {
    className?: string;
    context?: FormControlContextValue;
  };

export type IFormControlErrorProps = ViewProps &
  VariantProps<typeof formControlErrorStyle> & { className?: string };

export type IFormControlErrorTextProps = TextProps &
  VariantProps<typeof formControlErrorTextStyle> & { className?: string };

export type IFormControlErrorIconProps = React.ComponentProps<typeof PrimitiveIcon> &
  VariantProps<typeof formControlErrorIconStyle> & { className?: string };

export type IFormControlLabelProps = ViewProps &
  VariantProps<typeof formControlLabelStyle> & { className?: string };

export type IFormControlLabelTextProps = TextProps &
  VariantProps<typeof formControlLabelTextStyle> & { className?: string };

export type IFormControlLabelAstrickProps = TextProps &
  VariantProps<typeof formControlLabelAstrickStyle> & { className?: string };

export type IFormControlHelperProps = ViewProps &
  VariantProps<typeof formControlHelperStyle> & { className?: string };

export type IFormControlHelperTextProps = TextProps &
  VariantProps<typeof formControlHelperTextStyle> & { className?: string };

// Form Control Root Component - Direct implementation without factory
const FormControlRoot = React.forwardRef<View, ViewProps>(({ ...props }, ref) => {
  return <View {...props} ref={ref} />;
});

// Main FormControl component - Direct implementation
export const FormControl = React.forwardRef<View, IFormControlProps>(
  ({ className, size = 'md', context, children, ...props }, ref) => {
    const contextValue = useMemo(() => ({ size, ...context }), [size, context]);

    return (
      <FormControlContext.Provider value={contextValue}>
        <FormControlRoot
          ref={ref}
          {...props}
          className={formControlStyle({ size, class: className })}
        >
          {children}
        </FormControlRoot>
      </FormControlContext.Provider>
    );
  },
);

// FormControlError component - Direct implementation
export const FormControlError = React.forwardRef<View, IFormControlErrorProps>(
  ({ className, ...props }, ref) => {
    return <View ref={ref} {...props} className={formControlErrorStyle({ class: className })} />;
  },
);

// FormControlErrorText component - Direct implementation
export const FormControlErrorText = React.forwardRef<Text, IFormControlErrorTextProps>(
  ({ className, size, ...props }, ref) => {
    const context = useContext(FormControlContext);
    const { size: parentSize } = context || {};

    return (
      <Text
        ref={ref}
        {...props}
        className={formControlErrorTextStyle({
          parentVariants: { size: parentSize },
          size,
          class: className,
        })}
      />
    );
  },
);

// FormControlErrorIcon component - Direct implementation
export const FormControlErrorIcon = React.forwardRef<
  React.ElementRef<typeof PrimitiveIcon>,
  IFormControlErrorIconProps
>(({ className, size, ...props }, ref) => {
  const context = useContext(FormControlContext);
  const { size: parentSize } = context || {};

  if (typeof size === 'number') {
    return (
      <PrimitiveIcon
        ref={ref}
        {...props}
        className={formControlErrorIconStyle({ class: className })}
        size={size}
      />
    );
  } else if ((props.height !== undefined || props.width !== undefined) && size === undefined) {
    return (
      <PrimitiveIcon
        ref={ref}
        {...props}
        className={formControlErrorIconStyle({ class: className })}
      />
    );
  }
  return (
    <PrimitiveIcon
      ref={ref}
      {...props}
      className={formControlErrorIconStyle({
        parentVariants: { size: parentSize },
        size,
        class: className,
      })}
    />
  );
});

// FormControlLabel component - Direct implementation
export const FormControlLabel = React.forwardRef<View, IFormControlLabelProps>(
  ({ className, ...props }, ref) => {
    return <View ref={ref} {...props} className={formControlLabelStyle({ class: className })} />;
  },
);

// FormControlLabelText component - Direct implementation
export const FormControlLabelText = React.forwardRef<Text, IFormControlLabelTextProps>(
  ({ className, size, ...props }, ref) => {
    const context = useContext(FormControlContext);
    const { size: parentSize } = context || {};

    return (
      <Text
        ref={ref}
        {...props}
        className={formControlLabelTextStyle({
          parentVariants: { size: parentSize },
          size,
          class: className,
        })}
      />
    );
  },
);

// FormControlLabelAstrick component - Direct implementation
export const FormControlLabelAstrick = React.forwardRef<Text, IFormControlLabelAstrickProps>(
  ({ className, ...props }, ref) => {
    const context = useContext(FormControlContext);
    const { size: parentSize } = context || {};

    return (
      <Text
        ref={ref}
        {...props}
        className={formControlLabelAstrickStyle({
          parentVariants: { size: parentSize },
          class: className,
        })}
      />
    );
  },
);

// FormControlHelper component - Direct implementation
export const FormControlHelper = React.forwardRef<View, IFormControlHelperProps>(
  ({ className, ...props }, ref) => {
    return <View ref={ref} {...props} className={formControlHelperStyle({ class: className })} />;
  },
);

// FormControlHelperText component - Direct implementation
export const FormControlHelperText = React.forwardRef<Text, IFormControlHelperTextProps>(
  ({ className, size, ...props }, ref) => {
    const context = useContext(FormControlContext);
    const { size: parentSize } = context || {};

    return (
      <Text
        ref={ref}
        {...props}
        className={formControlHelperTextStyle({
          parentVariants: { size: parentSize },
          size,
          class: className,
        })}
      />
    );
  },
);

// Display names for debugging
FormControl.displayName = 'FormControl';
FormControlError.displayName = 'FormControlError';
FormControlErrorText.displayName = 'FormControlErrorText';
FormControlErrorIcon.displayName = 'FormControlErrorIcon';
FormControlLabel.displayName = 'FormControlLabel';
FormControlLabelText.displayName = 'FormControlLabelText';
FormControlLabelAstrick.displayName = 'FormControlLabelAstrick';
FormControlHelper.displayName = 'FormControlHelper';
FormControlHelperText.displayName = 'FormControlHelperText';
