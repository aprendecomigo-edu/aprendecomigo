import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import { View, TextInput, ViewProps, TextInputProps } from 'react-native';

// Textarea Context for sharing state between components
interface TextareaContextValue {
  variant?: string;
  size?: string;
  isInvalid?: boolean;
  isDisabled?: boolean;
  isFocused?: boolean;
}

const TextareaContext = createContext<TextareaContextValue>({});

// Scope for style context
const SCOPE = 'TEXTAREA';

// Style definitions
export const textareaStyle = tva({
  base: 'w-full h-[100px] border border-background-300 rounded data-[hover=true]:border-outline-400 data-[focus=true]:border-primary-700 data-[focus=true]:data-[hover=true]:border-primary-700 data-[disabled=true]:opacity-40 data-[disabled=true]:bg-background-50 data-[disabled=true]:data-[hover=true]:border-background-300',
  variants: {
    variant: {
      default:
        'data-[focus=true]:border-primary-700 data-[focus=true]:web:ring-1 data-[focus=true]:web:ring-inset data-[focus=true]:web:ring-indicator-primary data-[invalid=true]:border-error-700 data-[invalid=true]:web:ring-1 data-[invalid=true]:web:ring-inset data-[invalid=true]:web:ring-indicator-error',
    },
    size: {
      sm: '',
      md: '',
      lg: '',
      xl: '',
    },
  },
});

export const textareaInputStyle = tva({
  base: 'p-2 web:outline-none border-0 text-typography-900 h-full w-full',
  variants: {
    size: {
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg',
      xl: 'text-xl',
    },
  },
});

// Type definitions
export type ITextareaProps = ViewProps &
  VariantProps<typeof textareaStyle> & {
    className?: string;
    isInvalid?: boolean;
    isDisabled?: boolean;
  };

export type ITextareaInputProps = TextInputProps &
  VariantProps<typeof textareaInputStyle> & {
    className?: string;
  };

// Main Textarea component - Direct implementation without factory
export const Textarea = React.forwardRef<View, ITextareaProps>(
  (
    {
      className,
      variant = 'default',
      size = 'md',
      isInvalid = false,
      isDisabled = false,
      children,
      ...props
    },
    ref,
  ) => {
    const contextValue = useMemo(
      () => ({ variant, size, isInvalid, isDisabled }),
      [variant, size, isInvalid, isDisabled],
    );

    return (
      <TextareaContext.Provider value={contextValue}>
        <View
          ref={ref}
          {...props}
          className={textareaStyle({ variant, size, class: className })}
          style={{
            opacity: isDisabled ? 0.4 : 1,
            borderColor: isInvalid ? '#dc2626' : undefined,
          }}
        >
          {children}
        </View>
      </TextareaContext.Provider>
    );
  },
);

// TextareaInput component
export const TextareaInput = React.forwardRef<TextInput, ITextareaInputProps>(
  ({ className, size, multiline = true, editable, ...props }, ref) => {
    const context = useContext(TextareaContext);
    const { size: parentSize, isDisabled } = context || {};

    return (
      <TextInput
        ref={ref}
        {...props}
        multiline={multiline}
        editable={!isDisabled && editable}
        className={textareaInputStyle({
          size: size || parentSize,
          class: className,
        })}
      />
    );
  },
);

// Display names for debugging
Textarea.displayName = 'Textarea';
TextareaInput.displayName = 'TextareaInput';
