import React, { createContext, useContext, useMemo, useState } from 'react';
import type { TextInputProps, ViewProps, PressableProps } from 'react-native';
import { View, Pressable, TextInput, StyleSheet } from 'react-native';

// Input Context for sharing state between components
interface InputContextValue {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'outline' | 'underlined' | 'rounded';
  isDisabled?: boolean;
  isInvalid?: boolean;
  isFocused?: boolean;
}

const InputContext = createContext<InputContextValue>({});

// Type definitions
export type IInputProps = ViewProps & {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'outline' | 'underlined' | 'rounded';
  isDisabled?: boolean;
  isInvalid?: boolean;
  className?: string;
};

export type IInputFieldProps = TextInputProps & {
  className?: string;
};

export type IInputIconProps = ViewProps & {
  className?: string;
  children?: React.ReactNode;
};

export type IInputSlotProps = PressableProps & {
  className?: string;
};

// Style helpers
const getInputStyles = (
  size?: string,
  variant?: string,
  isDisabled?: boolean,
  isInvalid?: boolean,
  isFocused?: boolean,
) => {
  const baseStyle: any = {
    flexDirection: 'row',
    alignItems: 'center',
    overflow: 'hidden',
    opacity: isDisabled ? 0.4 : 1,
  };

  // Size styles
  const sizeStyles: any = {
    sm: { height: 36 },
    md: { height: 40 },
    lg: { height: 44 },
    xl: { height: 48 },
  };

  // Variant styles
  const variantStyles: any = {
    outline: {
      borderWidth: 1,
      borderRadius: 4,
      borderColor: isInvalid ? '#ef4444' : isFocused ? '#3b82f6' : '#d1d5db',
      backgroundColor: '#ffffff',
    },
    underlined: {
      borderBottomWidth: isInvalid ? 2 : 1,
      borderBottomColor: isInvalid ? '#ef4444' : isFocused ? '#3b82f6' : '#d1d5db',
      backgroundColor: 'transparent',
    },
    rounded: {
      borderWidth: 1,
      borderRadius: 24,
      borderColor: isInvalid ? '#ef4444' : isFocused ? '#3b82f6' : '#d1d5db',
      backgroundColor: '#ffffff',
    },
  };

  return {
    ...baseStyle,
    ...sizeStyles[size || 'md'],
    ...variantStyles[variant || 'outline'],
  };
};

const getInputFieldStyles = (size?: string, variant?: string, isDisabled?: boolean) => {
  const baseStyle: any = {
    flex: 1,
    backgroundColor: 'transparent',
    color: isDisabled ? '#9ca3af' : '#111827',
  };

  // Size text styles
  const sizeTextStyles: any = {
    sm: { fontSize: 14 },
    md: { fontSize: 16 },
    lg: { fontSize: 18 },
    xl: { fontSize: 20 },
  };

  // Variant padding styles
  const variantPaddingStyles: any = {
    outline: { paddingHorizontal: 12, paddingVertical: 6 },
    underlined: { paddingHorizontal: 0, paddingVertical: 4 },
    rounded: { paddingHorizontal: 12, paddingVertical: 6 },
  };

  return {
    ...baseStyle,
    ...sizeTextStyles[size || 'md'],
    ...variantPaddingStyles[variant || 'outline'],
  };
};

// Main Input component - Simplified v2 without factory functions
export const Input = React.forwardRef<View, IInputProps>(
  (
    {
      size = 'md',
      variant = 'outline',
      isDisabled = false,
      isInvalid = false,
      children,
      style,
      ...props
    },
    ref,
  ) => {
    const [isFocused, setIsFocused] = useState(false);

    const contextValue = useMemo(
      () => ({ size, variant, isDisabled, isInvalid, isFocused }),
      [size, variant, isDisabled, isInvalid, isFocused],
    );

    const inputStyles = getInputStyles(size, variant, isDisabled, isInvalid, isFocused);

    // Add focus handlers to children
    const enhancedChildren = React.Children.map(children, (child: any) => {
      if (child?.type === InputField) {
        return React.cloneElement(child, {
          onFocus: (e: any) => {
            setIsFocused(true);
            child.props?.onFocus?.(e);
          },
          onBlur: (e: any) => {
            setIsFocused(false);
            child.props?.onBlur?.(e);
          },
        });
      }
      return child;
    });

    return (
      <InputContext.Provider value={contextValue}>
        <View ref={ref} {...props} style={[inputStyles, style]}>
          {enhancedChildren}
        </View>
      </InputContext.Provider>
    );
  },
);

// InputField component
export const InputField = React.forwardRef<TextInput, IInputFieldProps>(
  ({ style, editable = true, placeholderTextColor, ...props }, ref) => {
    const context = useContext(InputContext);
    const { size, variant, isDisabled } = context || {};

    const inputFieldStyles = getInputFieldStyles(size, variant, isDisabled);

    return (
      <TextInput
        ref={ref}
        editable={!isDisabled && editable}
        placeholderTextColor={placeholderTextColor || '#9ca3af'}
        {...props}
        style={[inputFieldStyles, style]}
      />
    );
  },
);

// InputIcon component - Simple placeholder
export const InputIcon = React.forwardRef<View, IInputIconProps>(
  ({ children, style, ...props }, ref) => {
    const context = useContext(InputContext);
    const { size } = context || {};

    const sizeStyles: any = {
      sm: { width: 16, height: 16 },
      md: { width: 18, height: 18 },
      lg: { width: 20, height: 20 },
      xl: { width: 24, height: 24 },
    };

    return (
      <View
        ref={ref}
        {...props}
        style={[
          {
            justifyContent: 'center',
            alignItems: 'center',
            marginHorizontal: 8,
            ...sizeStyles[size || 'md'],
          },
          style,
        ]}
      >
        {children}
      </View>
    );
  },
);

// InputSlot component
export const InputSlot = React.forwardRef<View, IInputSlotProps>(
  ({ children, style, disabled, ...props }, ref) => {
    const context = useContext(InputContext);
    const { variant, isDisabled } = context || {};

    const slotStyles: any = {
      position: 'absolute',
      right: 0,
      height: '100%',
      justifyContent: 'center',
      alignItems: 'center',
      paddingRight: variant === 'underlined' ? 4 : 12,
    };

    return (
      <Pressable
        ref={ref as any}
        disabled={isDisabled || disabled}
        {...props}
        style={[slotStyles, style]}
      >
        {children}
      </Pressable>
    );
  },
);

// Display names for debugging
Input.displayName = 'Input';
InputField.displayName = 'InputField';
InputIcon.displayName = 'InputIcon';
InputSlot.displayName = 'InputSlot';
