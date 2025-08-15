'use client';
import React, { createContext, useContext, useMemo } from 'react';
import type { ViewProps, PressableProps, TextProps } from 'react-native';
import { View, Pressable, Text } from 'react-native';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';

// Menu Context for sharing state between components
interface MenuContextValue {
  isOpen?: boolean;
}

const MenuContext = createContext<MenuContextValue>({});

// Simplified style definitions
const menuStyle = tva({
  base: 'rounded-md bg-background-0 border border-outline-100 p-1 shadow-hard-5',
});

const menuItemStyle = tva({
  base: 'min-w-[200px] p-3 flex-row items-center rounded',
});

const menuBackdropStyle = tva({
  base: 'absolute top-0 bottom-0 left-0 right-0',
});

const menuSeparatorStyle = tva({
  base: 'bg-background-200 h-px w-full',
});

const menuItemLabelStyle = tva({
  base: 'text-typography-700 font-normal font-body',
  variants: {
    size: {
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg',
    },
  },
});

// Type definitions
export type IMenuProps = ViewProps &
  VariantProps<typeof menuStyle> & {
    className?: string;
  };

export type IMenuItemProps = PressableProps &
  VariantProps<typeof menuItemStyle> & {
    className?: string;
  };

export type IMenuBackdropProps = PressableProps &
  VariantProps<typeof menuBackdropStyle> & {
    className?: string;
  };

export type IMenuSeparatorProps = ViewProps &
  VariantProps<typeof menuSeparatorStyle> & {
    className?: string;
  };

export type IMenuItemLabelProps = TextProps &
  VariantProps<typeof menuItemLabelStyle> & {
    className?: string;
  };

// Main Menu component - Simplified v2 implementation
export const Menu = React.forwardRef<View, IMenuProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <View
        ref={ref}
        {...props}
        className={menuStyle({ class: className })}
      >
        {children}
      </View>
    );
  }
);

// MenuItem component
export const MenuItem = React.forwardRef<View, IMenuItemProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <Pressable
        ref={ref as any}
        {...props}
        className={menuItemStyle({ class: className })}
      >
        {children}
      </Pressable>
    );
  }
);

// MenuBackdrop component
export const MenuBackdrop = React.forwardRef<View, IMenuBackdropProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <Pressable
        ref={ref as any}
        {...props}
        className={menuBackdropStyle({ class: className })}
      >
        {children}
      </Pressable>
    );
  }
);

// MenuSeparator component
export const MenuSeparator = React.forwardRef<View, IMenuSeparatorProps>(
  ({ className, ...props }, ref) => {
    return (
      <View
        ref={ref}
        {...props}
        className={menuSeparatorStyle({ class: className })}
      />
    );
  }
);

// MenuItemLabel component
export const MenuItemLabel = React.forwardRef<Text, IMenuItemLabelProps>(
  ({ className, size = 'md', ...props }, ref) => {
    return (
      <Text
        ref={ref}
        {...props}
        className={menuItemLabelStyle({
          size,
          class: className,
        })}
      />
    );
  }
);

// Display names for debugging
Menu.displayName = 'Menu';
MenuItem.displayName = 'MenuItem';
MenuBackdrop.displayName = 'MenuBackdrop';
MenuSeparator.displayName = 'MenuSeparator';
MenuItemLabel.displayName = 'MenuItemLabel';