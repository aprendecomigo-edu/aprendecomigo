import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo, useState } from 'react';
import { Pressable, View, PanGestureHandler, State } from 'react-native';

// Slider Context for sharing state between components
interface SliderContextValue {
  size?: string;
  orientation?: string;
  isReversed?: boolean;
  value?: number;
  min?: number;
  max?: number;
  onValueChange?: (value: number) => void;
}

const SliderContext = createContext<SliderContextValue>({});

// Scope for style context
const SCOPE = 'SLIDER';

// Style definitions (reuse existing styles)
export const sliderStyle = tva({
  base: 'justify-center items-center data-[disabled=true]:web:opacity-40 data-[disabled=true]:web:pointer-events-none',
  variants: {
    orientation: {
      horizontal: 'w-full',
      vertical: 'h-full',
    },
    size: {
      sm: '',
      md: '',
      lg: '',
    },
    isReversed: {
      true: '',
      false: '',
    },
  },
});

export const sliderThumbStyle = tva({
  base: 'bg-primary-500 absolute rounded-full data-[focus=true]:bg-primary-600 data-[active=true]:bg-primary-600 data-[hover=true]:bg-primary-600 data-[disabled=true]:bg-primary-500 web:cursor-pointer web:active:outline-4 web:active:outline web:active:outline-primary-400 data-[focus=true]:web:outline-4 data-[focus=true]:web:outline data-[focus=true]:web:outline-primary-400 shadow-hard-1',
  variants: {
    size: {
      sm: 'h-4 w-4',
      md: 'h-5 w-5',
      lg: 'h-6 w-6',
    },
  },
  parentVariants: {
    size: {
      sm: 'h-4 w-4',
      md: 'h-5 w-5',
      lg: 'h-6 w-6',
    },
  },
});

export const sliderTrackStyle = tva({
  base: 'bg-background-300 rounded-lg overflow-hidden',
  parentVariants: {
    orientation: {
      horizontal: 'w-full',
      vertical: 'h-full',
    },
    isReversed: {
      true: '',
      false: '',
    },
    size: {
      sm: '',
      md: '',
      lg: '',
    },
  },
  parentCompoundVariants: [
    {
      orientation: 'horizontal',
      size: 'sm',
      class: 'h-1 flex-row',
    },
    {
      orientation: 'horizontal',
      size: 'sm',
      isReversed: true,
      class: 'h-1 flex-row-reverse',
    },
    {
      orientation: 'horizontal',
      size: 'md',
      class: 'h-1 flex-row',
    },
    {
      orientation: 'horizontal',
      size: 'md',
      isReversed: true,
      class: 'h-[5px] flex-row-reverse',
    },
    {
      orientation: 'horizontal',
      size: 'lg',
      class: 'h-1.5 flex-row',
    },
    {
      orientation: 'horizontal',
      size: 'lg',
      isReversed: true,
      class: 'h-1.5 flex-row-reverse',
    },
    {
      orientation: 'vertical',
      size: 'sm',
      class: 'w-1 flex-col-reverse',
    },
    {
      orientation: 'vertical',
      size: 'sm',
      isReversed: true,
      class: 'w-1 flex-col',
    },
    {
      orientation: 'vertical',
      size: 'md',
      class: 'w-[5px] flex-col-reverse',
    },
    {
      orientation: 'vertical',
      size: 'md',
      isReversed: true,
      class: 'w-[5px] flex-col',
    },
    {
      orientation: 'vertical',
      size: 'lg',
      class: 'w-1.5 flex-col-reverse',
    },
    {
      orientation: 'vertical',
      size: 'lg',
      isReversed: true,
      class: 'w-1.5 flex-col',
    },
  ],
});

export const sliderFilledTrackStyle = tva({
  base: 'bg-primary-500 data-[focus=true]:bg-primary-600 data-[active=true]:bg-primary-600 data-[hover=true]:bg-primary-600',
  parentVariants: {
    orientation: {
      horizontal: 'h-full',
      vertical: 'w-full',
    },
  },
});

// Type definitions
export type ISliderProps = React.ComponentProps<typeof View> &
  VariantProps<typeof sliderStyle> & {
    className?: string;
    value?: number;
    min?: number;
    max?: number;
    onValueChange?: (value: number) => void;
    isDisabled?: boolean;
  };

export type ISliderThumbProps = React.ComponentProps<typeof View> &
  VariantProps<typeof sliderThumbStyle> & {
    className?: string;
  };

export type ISliderTrackProps = React.ComponentProps<typeof Pressable> &
  VariantProps<typeof sliderTrackStyle> & {
    className?: string;
  };

export type ISliderFilledTrackProps = React.ComponentProps<typeof View> &
  VariantProps<typeof sliderFilledTrackStyle> & {
    className?: string;
  };

// Main Slider component - Direct implementation without factory
export const Slider = React.forwardRef<View, ISliderProps>(
  (
    {
      className,
      size = 'md',
      orientation = 'horizontal',
      isReversed = false,
      value = 0,
      min = 0,
      max = 100,
      onValueChange,
      isDisabled = false,
      children,
      ...props
    },
    ref,
  ) => {
    const [internalValue, setInternalValue] = useState(value);

    const contextValue = useMemo(
      () => ({
        size,
        orientation,
        isReversed,
        value: internalValue,
        min,
        max,
        onValueChange: (newValue: number) => {
          setInternalValue(newValue);
          onValueChange?.(newValue);
        },
      }),
      [size, orientation, isReversed, internalValue, min, max, onValueChange],
    );

    return (
      <SliderContext.Provider value={contextValue}>
        <View
          ref={ref}
          {...props}
          className={sliderStyle({
            orientation,
            isReversed,
            class: className,
          })}
          style={{
            opacity: isDisabled ? 0.4 : 1,
          }}
        >
          {children}
        </View>
      </SliderContext.Provider>
    );
  },
);

// SliderTrack component
export const SliderTrack = React.forwardRef<View, ISliderTrackProps>(
  ({ className, children, onPress, ...props }, ref) => {
    const context = useContext(SliderContext);
    const { orientation, size, isReversed } = context || {};

    const handleTrackPress = (event: any) => {
      // Simple track press handling - would need proper gesture handling in production
      onPress?.(event);
    };

    return (
      <Pressable
        ref={ref as any}
        {...props}
        onPress={handleTrackPress}
        className={sliderTrackStyle({
          parentVariants: {
            orientation,
            size,
            isReversed,
          },
          class: className,
        })}
      >
        {children}
      </Pressable>
    );
  },
);

// SliderFilledTrack component
export const SliderFilledTrack = React.forwardRef<View, ISliderFilledTrackProps>(
  ({ className, ...props }, ref) => {
    const context = useContext(SliderContext);
    const { orientation, value = 0, min = 0, max = 100 } = context || {};

    const percentage = ((value - min) / (max - min)) * 100;

    return (
      <View
        ref={ref}
        {...props}
        className={sliderFilledTrackStyle({
          parentVariants: { orientation },
          class: className,
        })}
        style={{
          ...(orientation === 'horizontal'
            ? { width: `${percentage}%` }
            : { height: `${percentage}%` }),
        }}
      />
    );
  },
);

// SliderThumb component
export const SliderThumb = React.forwardRef<View, ISliderThumbProps>(
  ({ className, size, ...props }, ref) => {
    const context = useContext(SliderContext);
    const { size: parentSize, value = 0, min = 0, max = 100, onValueChange } = context || {};

    const percentage = ((value - min) / (max - min)) * 100;

    return (
      <View
        ref={ref}
        {...props}
        className={sliderThumbStyle({
          size,
          parentVariants: { size: parentSize },
          class: className,
        })}
        style={{
          left: `${percentage}%`,
          marginLeft: -10, // Half the thumb width for centering
        }}
      />
    );
  },
);

// Display names for debugging
Slider.displayName = 'Slider';
SliderTrack.displayName = 'SliderTrack';
SliderFilledTrack.displayName = 'SliderFilledTrack';
SliderThumb.displayName = 'SliderThumb';
