'use client';
import React, { createContext, useContext, useMemo } from 'react';
import type { ViewProps, TextProps, ImageProps } from 'react-native';
import { View, Text, Image, Platform } from 'react-native';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';

// Avatar Context for sharing state between components
interface AvatarContextValue {
  size?: string;
}

const AvatarContext = createContext<AvatarContextValue>({});

// Simplified style definitions
const avatarStyle = tva({
  base: 'rounded-full justify-center items-center relative bg-primary-600',
  variants: {
    size: {
      xs: 'w-6 h-6',
      sm: 'w-8 h-8',
      md: 'w-12 h-12',
      lg: 'w-16 h-16',
      xl: 'w-24 h-24',
      '2xl': 'w-32 h-32',
    },
  },
});

const avatarFallbackTextStyle = tva({
  base: 'text-typography-0 font-semibold overflow-hidden uppercase',
  parentVariants: {
    size: {
      xs: 'text-2xs',
      sm: 'text-xs',
      md: 'text-base',
      lg: 'text-xl',
      xl: 'text-3xl',
      '2xl': 'text-5xl',
    },
  },
});

const avatarGroupStyle = tva({
  base: 'flex-row-reverse relative',
});

const avatarBadgeStyle = tva({
  base: 'bg-success-500 rounded-full absolute right-0 bottom-0 border-background-0 border-2',
  parentVariants: {
    size: {
      xs: 'w-2 h-2',
      sm: 'w-2 h-2',
      md: 'w-3 h-3',
      lg: 'w-4 h-4',
      xl: 'w-6 h-6',
      '2xl': 'w-8 h-8',
    },
  },
});

const avatarImageStyle = tva({
  base: 'h-full w-full rounded-full absolute',
});

// Type definitions
export type IAvatarProps = ViewProps &
  VariantProps<typeof avatarStyle> & {
    className?: string;
  };

export type IAvatarBadgeProps = ViewProps &
  VariantProps<typeof avatarBadgeStyle> & {
    className?: string;
  };

export type IAvatarFallbackTextProps = TextProps &
  VariantProps<typeof avatarFallbackTextStyle> & {
    className?: string;
  };

export type IAvatarImageProps = ImageProps &
  VariantProps<typeof avatarImageStyle> & {
    className?: string;
  };

export type IAvatarGroupProps = ViewProps &
  VariantProps<typeof avatarGroupStyle> & {
    className?: string;
  };

// Main Avatar component - Simplified v2 implementation
export const Avatar = React.forwardRef<View, IAvatarProps>(
  ({ className, size = 'md', children, ...props }, ref) => {
    const contextValue = useMemo(
      () => ({ size }),
      [size]
    );

    return (
      <AvatarContext.Provider value={contextValue}>
        <View
          ref={ref}
          {...props}
          className={avatarStyle({ size, class: className })}
        >
          {children}
        </View>
      </AvatarContext.Provider>
    );
  }
);

// AvatarBadge component
export const AvatarBadge = React.forwardRef<View, IAvatarBadgeProps>(
  ({ className, size, children, ...props }, ref) => {
    const context = useContext(AvatarContext);
    const { size: parentSize } = context || {};

    return (
      <View
        ref={ref}
        {...props}
        className={avatarBadgeStyle({
          parentVariants: { size: parentSize },
          size,
          class: className,
        })}
      >
        {children}
      </View>
    );
  }
);

// AvatarFallbackText component
export const AvatarFallbackText = React.forwardRef<Text, IAvatarFallbackTextProps>(
  ({ className, size, ...props }, ref) => {
    const context = useContext(AvatarContext);
    const { size: parentSize } = context || {};

    return (
      <Text
        ref={ref}
        {...props}
        className={avatarFallbackTextStyle({
          parentVariants: { size: parentSize },
          size,
          class: className,
        })}
      />
    );
  }
);

// AvatarImage component
export const AvatarImage = React.forwardRef<Image, IAvatarImageProps>(
  ({ className, ...props }, ref) => {
    return (
      <Image
        ref={ref}
        {...props}
        className={avatarImageStyle({ class: className })}
      />
    );
  }
);

// AvatarGroup component
export const AvatarGroup = React.forwardRef<View, IAvatarGroupProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <View
        ref={ref}
        {...props}
        className={avatarGroupStyle({ class: className })}
      >
        {children}
      </View>
    );
  }
);

// Display names for debugging
Avatar.displayName = 'Avatar';
AvatarBadge.displayName = 'AvatarBadge';
AvatarFallbackText.displayName = 'AvatarFallbackText';
AvatarImage.displayName = 'AvatarImage';
AvatarGroup.displayName = 'AvatarGroup';