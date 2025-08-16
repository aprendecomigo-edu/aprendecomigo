import React, { createContext, useContext, useMemo, useState } from 'react';
import { Pressable, View, ViewProps, PressableProps } from 'react-native';

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

// Type definitions - simplified for testing
export type ISliderProps = ViewProps & {
  size?: 'sm' | 'md' | 'lg';
  orientation?: 'horizontal' | 'vertical';
  isReversed?: boolean;
  value?: number;
  min?: number;
  max?: number;
  onValueChange?: (value: number) => void;
  isDisabled?: boolean;
  className?: string;
};

export type ISliderThumbProps = ViewProps & {
  className?: string;
};

export type ISliderTrackProps = PressableProps & {
  className?: string;
};

export type ISliderFilledTrackProps = ViewProps & {
  className?: string;
};

// Simple style generator for testing
const getSliderStyles = (orientation?: string, isDisabled?: boolean) => ({
  justifyContent: 'center' as const,
  alignItems: 'center' as const,
  width: orientation === 'vertical' ? 20 : '100%',
  height: orientation === 'horizontal' ? 20 : '100%',
  opacity: isDisabled ? 0.4 : 1,
});

const getTrackStyles = (orientation?: string, size?: string, isReversed?: boolean) => {
  const baseStyle = {
    backgroundColor: '#e5e7eb',
    borderRadius: 8,
    overflow: 'hidden' as const,
  };

  if (orientation === 'horizontal') {
    return {
      ...baseStyle,
      width: '100%',
      height: size === 'sm' ? 4 : size === 'lg' ? 6 : 4,
      flexDirection: isReversed ? ('row-reverse' as const) : ('row' as const),
    };
  } else {
    return {
      ...baseStyle,
      height: '100%',
      width: size === 'sm' ? 4 : size === 'lg' ? 6 : 5,
      flexDirection: isReversed ? ('column' as const) : ('column-reverse' as const),
    };
  }
};

const getFilledTrackStyles = (orientation?: string) => ({
  backgroundColor: '#3b82f6',
  ...(orientation === 'horizontal' ? { height: '100%' } : { width: '100%' }),
});

const getThumbStyles = (size?: string) => {
  const thumbSize = size === 'sm' ? 16 : size === 'lg' ? 24 : 20;
  return {
    backgroundColor: '#3b82f6',
    borderRadius: thumbSize / 2,
    width: thumbSize,
    height: thumbSize,
    position: 'absolute' as const,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  };
};

// Main Slider component - Simplified v2 without factory functions
export const Slider = React.forwardRef<View, ISliderProps>(
  (
    {
      size = 'md',
      orientation = 'horizontal',
      isReversed = false,
      value = 0,
      min = 0,
      max = 100,
      onValueChange,
      isDisabled = false,
      children,
      style,
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

    const sliderStyles = getSliderStyles(orientation, isDisabled);

    return (
      <SliderContext.Provider value={contextValue}>
        <View ref={ref} {...props} style={[sliderStyles, style]}>
          {children}
        </View>
      </SliderContext.Provider>
    );
  },
);

// SliderTrack component
export const SliderTrack = React.forwardRef<View, ISliderTrackProps>(
  ({ children, onPress, style, ...props }, ref) => {
    const context = useContext(SliderContext);
    const { orientation, size, isReversed } = context || {};

    const handleTrackPress = (event: any) => {
      // Simple track press handling - would need proper gesture handling in production
      onPress?.(event);
    };

    const trackStyles = getTrackStyles(orientation, size, isReversed);

    return (
      <Pressable
        ref={ref as any}
        {...props}
        onPress={handleTrackPress}
        style={[trackStyles, style]}
      >
        {children}
      </Pressable>
    );
  },
);

// SliderFilledTrack component
export const SliderFilledTrack = React.forwardRef<View, ISliderFilledTrackProps>(
  ({ style, ...props }, ref) => {
    const context = useContext(SliderContext);
    const { orientation, value = 0, min = 0, max = 100 } = context || {};

    const percentage = ((value - min) / (max - min)) * 100;
    const filledTrackStyles = getFilledTrackStyles(orientation);

    const dimensionStyle =
      orientation === 'horizontal' ? { width: `${percentage}%` } : { height: `${percentage}%` };

    return <View ref={ref} {...props} style={[filledTrackStyles, dimensionStyle, style]} />;
  },
);

// SliderThumb component
export const SliderThumb = React.forwardRef<View, ISliderThumbProps>(({ style, ...props }, ref) => {
  const context = useContext(SliderContext);
  const { size, value = 0, min = 0, max = 100, orientation } = context || {};

  const percentage = ((value - min) / (max - min)) * 100;
  const thumbStyles = getThumbStyles(size);

  const positionStyle =
    orientation === 'horizontal'
      ? { left: `${percentage}%`, marginLeft: -(thumbStyles.width / 2) }
      : { bottom: `${percentage}%`, marginBottom: -(thumbStyles.height / 2) };

  return <View ref={ref} {...props} style={[thumbStyles, positionStyle, style]} />;
});

// Display names for debugging
Slider.displayName = 'Slider';
SliderTrack.displayName = 'SliderTrack';
SliderFilledTrack.displayName = 'SliderFilledTrack';
SliderThumb.displayName = 'SliderThumb';
