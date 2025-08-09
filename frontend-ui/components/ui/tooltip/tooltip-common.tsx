'use client';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import { createTooltip } from '@gluestack-ui/tooltip';
import { cssInterop } from 'nativewind';
import React from 'react';
import { View, Text } from 'react-native';
import Animated, { FadeIn, FadeOut } from 'react-native-reanimated';

export const SCOPE = 'TOOLTIP';

export const tooltipStyle = tva({
  base: 'w-full h-full web:pointer-events-none',
});

export const tooltipContentStyle = tva({
  base: 'py-1 px-3 rounded-sm bg-background-900 web:pointer-events-auto',
});

export const tooltipTextStyle = tva({
  base: 'font-normal tracking-normal web:select-none text-xs text-typography-50',

  variants: {
    isTruncated: {
      true: {
        props: 'line-clamp-1 truncate',
      },
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

// Common function to create UITooltip with platform-specific Root
export function createUITooltip(Root: React.ComponentType<any>) {
  const UITooltip = createTooltip({
    Root: Root,
    Content: Animated.View,
    Text: Text,
  });

  cssInterop(UITooltip, { className: 'style' });
  cssInterop(UITooltip.Content, { className: 'style' });
  cssInterop(UITooltip.Text, { className: 'style' });

  return UITooltip;
}

export type ITooltipProps = React.ComponentProps<any> &
  VariantProps<typeof tooltipStyle> & { className?: string };
export type ITooltipContentProps = React.ComponentProps<any> &
  VariantProps<typeof tooltipContentStyle> & { className?: string };
export type ITooltipTextProps = React.ComponentProps<any> &
  VariantProps<typeof tooltipTextStyle> & { className?: string };

// Common function to create Tooltip components
export function createTooltipComponents(UITooltip: any) {
  const Tooltip = React.forwardRef<React.ElementRef<typeof UITooltip>, ITooltipProps>(
    ({ className, ...props }, ref) => {
      return <UITooltip ref={ref} className={tooltipStyle({ class: className })} {...props} />;
    }
  );

  const TooltipContent = React.forwardRef<
    React.ElementRef<typeof UITooltip.Content>,
    ITooltipContentProps & { className?: string }
  >(({ className, ...props }, ref) => {
    return (
      <UITooltip.Content
        ref={ref}
        {...props}
        className={tooltipContentStyle({
          class: className,
        })}
        pointerEvents="auto"
      />
    );
  });

  const TooltipText = React.forwardRef<
    React.ElementRef<typeof UITooltip.Text>,
    ITooltipTextProps & { className?: string }
  >(({ size, className, ...props }, ref) => {
    return (
      <UITooltip.Text
        ref={ref}
        className={tooltipTextStyle({ size, class: className })}
        {...props}
      />
    );
  });

  Tooltip.displayName = 'Tooltip';
  TooltipContent.displayName = 'TooltipContent';
  TooltipText.displayName = 'TooltipText';

  return { Tooltip, TooltipContent, TooltipText };
}
