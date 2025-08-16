import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import type { ViewProps, PressableProps, TextProps } from 'react-native';
import { View, Pressable, Text, Platform } from 'react-native';
import Animated, { FadeIn, FadeOut } from 'react-native-reanimated';

// Menu Context for sharing state between components
interface MenuContextValue {
  isOpen?: boolean;
  isDisabled?: boolean;
}

const MenuContext = createContext<MenuContextValue>({});

// Style definitions (reuse existing styles)
const menuStyle = tva({
  base: 'rounded-md bg-background-0 border border-outline-100 p-1 shadow-hard-5',
});

const menuItemStyle = tva({
  base: 'min-w-[200px] p-3 flex-row items-center rounded data-[hover=true]:bg-background-50 data-[active=true]:bg-background-100 data-[focus=true]:bg-background-50 data-[focus=true]:web:outline-none data-[focus=true]:web:outline-0 data-[disabled=true]:opacity-40 data-[disabled=true]:web:cursor-not-allowed data-[focus-visible=true]:web:outline-2 data-[focus-visible=true]:web:outline-primary-700 data-[focus-visible=true]:web:outline data-[focus-visible=true]:web:cursor-pointer data-[disabled=true]:data-[focus=true]:bg-transparent',
});

const menuBackdropStyle = tva({
  base: 'absolute top-0 bottom-0 left-0 right-0 web:cursor-default',
});

const menuSeparatorStyle = tva({
  base: 'bg-background-200 h-px w-full',
});

const menuItemLabelStyle = tva({
  base: 'text-typography-700 font-normal font-body',
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
export type IMenuProps = ViewProps &
  VariantProps<typeof menuStyle> & {
    className?: string;
    isOpen?: boolean;
  };

export type IMenuItemProps = PressableProps &
  VariantProps<typeof menuItemStyle> & {
    className?: string;
    isDisabled?: boolean;
    isHovered?: boolean;
    isActive?: boolean;
    isFocused?: boolean;
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

// Main Menu component - Direct v2 implementation without factory
export const Menu = React.forwardRef<View, IMenuProps>(
  ({ className, isOpen = false, children, ...props }, ref) => {
    const contextValue = useMemo(() => ({ isOpen }), [isOpen]);

    return (
      <MenuContext.Provider value={contextValue}>
        <Animated.View
          ref={ref as any}
          initial={{
            opacity: 0,
            scale: 0.8,
          }}
          animate={{
            opacity: 1,
            scale: 1,
          }}
          exit={{
            opacity: 0,
            scale: 0.8,
          }}
          transition={{
            type: 'timing',
            duration: 100,
          }}
          {...props}
          className={menuStyle({ class: className })}
        >
          {children}
        </Animated.View>
      </MenuContext.Provider>
    );
  },
);

// MenuItem component
export const MenuItem = React.forwardRef<View, IMenuItemProps>(
  (
    {
      className,
      isDisabled = false,
      isHovered = false,
      isActive = false,
      isFocused = false,
      children,
      ...props
    },
    ref,
  ) => {
    const Component = Platform.OS === 'web' ? Pressable : Pressable;

    return (
      <Component
        ref={ref as any}
        disabled={isDisabled}
        {...props}
        className={menuItemStyle({ class: className })}
        // @ts-ignore - data attributes for styling
        data-disabled={isDisabled}
        data-hover={isHovered}
        data-active={isActive}
        data-focus={isFocused}
        data-focus-visible={isFocused}
      >
        {children}
      </Component>
    );
  },
);

// MenuBackdrop component
export const MenuBackdrop = React.forwardRef<View, IMenuBackdropProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <Pressable ref={ref as any} {...props} className={menuBackdropStyle({ class: className })}>
        {children}
      </Pressable>
    );
  },
);

// MenuSeparator component
export const MenuSeparator = React.forwardRef<View, IMenuSeparatorProps>(
  ({ className, ...props }, ref) => {
    return <View ref={ref} {...props} className={menuSeparatorStyle({ class: className })} />;
  },
);

// MenuItemLabel component
export const MenuItemLabel = React.forwardRef<Text, IMenuItemLabelProps>(
  (
    {
      className,
      isTruncated,
      bold,
      underline,
      strikeThrough,
      size = 'md',
      sub,
      italic,
      highlight,
      ...props
    },
    ref,
  ) => {
    return (
      <Text
        ref={ref}
        {...props}
        className={menuItemLabelStyle({
          isTruncated,
          bold,
          underline,
          strikeThrough,
          size,
          sub,
          italic,
          highlight,
          class: className,
        })}
      />
    );
  },
);

// Display names for debugging
Menu.displayName = 'Menu';
MenuItem.displayName = 'MenuItem';
MenuBackdrop.displayName = 'MenuBackdrop';
MenuSeparator.displayName = 'MenuSeparator';
MenuItemLabel.displayName = 'MenuItemLabel';
