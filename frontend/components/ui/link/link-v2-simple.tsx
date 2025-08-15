'use client';
import React, { createContext, useContext, useMemo } from 'react';
import { Text, Pressable, PressableProps, TextProps } from 'react-native';

// Link Context for sharing state between components
interface LinkContextValue {
  isDisabled?: boolean;
  isHovered?: boolean;
}

const LinkContext = createContext<LinkContextValue>({});

// Type definitions - simplified for testing
export type ILinkProps = PressableProps & {
  isDisabled?: boolean;
  className?: string;
};

export type ILinkTextProps = TextProps & {
  isTruncated?: boolean;
  bold?: boolean;
  underline?: boolean;
  strikeThrough?: boolean;
  size?: '2xs' | 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | '6xl';
  className?: string;
};

// Simple style generators
const getLinkStyles = (isDisabled?: boolean) => ({
  opacity: isDisabled ? 0.4 : 1,
  cursor: isDisabled ? 'not-allowed' : 'pointer',
});

const getLinkTextStyles = (
  bold?: boolean,
  underline?: boolean,
  strikeThrough?: boolean,
  size?: string
) => {
  const fontSize =
    size === '2xs'
      ? 10
      : size === 'xs'
      ? 12
      : size === 'sm'
      ? 14
      : size === 'lg'
      ? 18
      : size === 'xl'
      ? 20
      : 16;

  return {
    color: '#1d4ed8',
    fontSize,
    fontWeight: bold ? ('700' as const) : ('normal' as const),
    textDecorationLine: underline
      ? ('underline' as const)
      : strikeThrough
      ? ('line-through' as const)
      : ('none' as const),
  };
};

// Main Link component - Simplified v2 without factory functions
export const Link = React.forwardRef<Pressable, ILinkProps>(
  ({ isDisabled = false, disabled, children, style, ...props }, ref) => {
    const contextValue = useMemo(
      () => ({ isDisabled: isDisabled || disabled }),
      [isDisabled, disabled]
    );

    const finalDisabled = isDisabled || disabled;
    const linkStyles = getLinkStyles(finalDisabled);

    return (
      <LinkContext.Provider value={contextValue}>
        <Pressable ref={ref as any} {...props} disabled={finalDisabled} style={[linkStyles, style]}>
          {children}
        </Pressable>
      </LinkContext.Provider>
    );
  }
);

// LinkText component
export const LinkText = React.forwardRef<Text, ILinkTextProps>(
  (
    {
      isTruncated = false,
      bold = false,
      underline = true,
      strikeThrough = false,
      size = 'md',
      style,
      ...props
    },
    ref
  ) => {
    const linkTextStyles = getLinkTextStyles(bold, underline, strikeThrough, size);

    return (
      <Text
        ref={ref}
        {...props}
        style={[linkTextStyles, style]}
        numberOfLines={isTruncated ? 1 : undefined}
        ellipsizeMode={isTruncated ? 'tail' : undefined}
      />
    );
  }
);

// Display names for debugging
Link.displayName = 'Link';
LinkText.displayName = 'LinkText';
