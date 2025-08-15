'use client';
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

// Type definitions - simplified for testing
export type ITextareaProps = ViewProps & {
  variant?: 'default';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  isInvalid?: boolean;
  isDisabled?: boolean;
  className?: string;
};

export type ITextareaInputProps = TextInputProps & {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
};

// Simple style generators
const getTextareaStyles = (size?: string, isInvalid?: boolean, isDisabled?: boolean) => {
  const baseStyle = {
    width: '100%',
    minHeight: 100,
    borderWidth: 1,
    borderRadius: 6,
    borderColor: isInvalid ? '#dc2626' : '#d1d5db',
    backgroundColor: isDisabled ? '#f9fafb' : '#ffffff',
    opacity: isDisabled ? 0.4 : 1,
  };

  return baseStyle;
};

const getTextareaInputStyles = (size?: string) => {
  const fontSize = size === 'sm' ? 14 : size === 'lg' ? 18 : size === 'xl' ? 20 : 16;

  return {
    padding: 8,
    fontSize,
    color: '#111827',
    textAlignVertical: 'top' as const,
    height: '100%',
    width: '100%',
  };
};

// Main Textarea component - Simplified v2 without factory functions
export const Textarea = React.forwardRef<View, ITextareaProps>(
  (
    {
      variant = 'default',
      size = 'md',
      isInvalid = false,
      isDisabled = false,
      children,
      style,
      ...props
    },
    ref
  ) => {
    const contextValue = useMemo(
      () => ({ variant, size, isInvalid, isDisabled }),
      [variant, size, isInvalid, isDisabled]
    );

    const textareaStyles = getTextareaStyles(size, isInvalid, isDisabled);

    return (
      <TextareaContext.Provider value={contextValue}>
        <View ref={ref} {...props} style={[textareaStyles, style]}>
          {children}
        </View>
      </TextareaContext.Provider>
    );
  }
);

// TextareaInput component
export const TextareaInput = React.forwardRef<TextInput, ITextareaInputProps>(
  ({ size, multiline = true, editable, style, ...props }, ref) => {
    const context = useContext(TextareaContext);
    const { size: parentSize, isDisabled } = context || {};

    const textareaInputStyles = getTextareaInputStyles(size || parentSize);

    return (
      <TextInput
        ref={ref}
        {...props}
        multiline={multiline}
        editable={!isDisabled && editable}
        style={[textareaInputStyles, style]}
      />
    );
  }
);

// Display names for debugging
Textarea.displayName = 'Textarea';
TextareaInput.displayName = 'TextareaInput';
