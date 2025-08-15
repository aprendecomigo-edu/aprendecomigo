'use client';
import React, { createContext, useContext, useMemo } from 'react';
import type { ViewProps, TextInputProps, PressableProps } from 'react-native';
import { View, Pressable, TextInput, Platform } from 'react-native';
import { Svg } from 'react-native-svg';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';

import {
  Actionsheet,
  ActionsheetContent,
  ActionsheetItem,
  ActionsheetItemText,
  ActionsheetDragIndicator,
  ActionsheetDragIndicatorWrapper,
  ActionsheetBackdrop,
  ActionsheetScrollView,
  ActionsheetVirtualizedList,
  ActionsheetFlatList,
  ActionsheetSectionList,
  ActionsheetSectionHeaderText,
} from './select-actionsheet';

// Select Context for sharing state between components
interface SelectContextValue {
  size?: string;
  variant?: string;
  isDisabled?: boolean;
  isInvalid?: boolean;
  isFocused?: boolean;
  isHovered?: boolean;
}

const SelectContext = createContext<SelectContextValue>({});

// Icon component
type IPrimitiveIcon = {
  height?: number | string;
  width?: number | string;
  fill?: string;
  color?: string;
  size?: number | string;
  stroke?: string;
  as?: React.ElementType;
  className?: string;
  classNameColor?: string;
};

const PrimitiveIcon = React.forwardRef<React.ElementRef<typeof Svg>, IPrimitiveIcon>(
  ({ height, width, fill, color, classNameColor, size, stroke, as: AsComp, ...props }, ref) => {
    color = color ?? classNameColor;
    const sizeProps = useMemo(() => {
      if (size) return { size };
      if (height && width) return { height, width };
      if (height) return { height };
      if (width) return { width };
      return {};
    }, [size, height, width]);

    let colorProps = {};
    if (fill) {
      colorProps = { ...colorProps, fill: fill };
    }
    if (stroke !== 'currentColor') {
      colorProps = { ...colorProps, stroke: stroke };
    } else if (stroke === 'currentColor' && color !== undefined) {
      colorProps = { ...colorProps, stroke: color };
    }

    if (AsComp) {
      return <AsComp ref={ref} {...props} {...sizeProps} {...colorProps} />;
    }
    return <Svg ref={ref} height={height} width={width} {...colorProps} {...props} />;
  }
);

// Style definitions (reuse existing styles)
const selectStyle = tva({
  base: '',
});

const selectTriggerStyle = tva({
  base: 'border border-background-300 rounded flex-row items-center overflow-hidden data-[hover=true]:border-outline-400 data-[focus=true]:border-primary-700 data-[disabled=true]:opacity-40 data-[disabled=true]:data-[hover=true]:border-background-300',
  variants: {
    size: {
      xl: 'h-12',
      lg: 'h-11',
      md: 'h-10',
      sm: 'h-9',
    },
    variant: {
      underlined:
        'border-0 border-b rounded-none data-[hover=true]:border-primary-700 data-[focus=true]:border-primary-700 data-[focus=true]:web:shadow-[inset_0_-1px_0_0] data-[focus=true]:web:shadow-primary-700 data-[invalid=true]:border-error-700 data-[invalid=true]:web:shadow-error-700',
      outline:
        'data-[focus=true]:border-primary-700 data-[focus=true]:web:shadow-[inset_0_0_0_1px] data-[focus=true]:data-[hover=true]:web:shadow-primary-600 data-[invalid=true]:web:shadow-[inset_0_0_0_1px] data-[invalid=true]:border-error-700 data-[invalid=true]:web:shadow-error-700 data-[invalid=true]:data-[hover=true]:border-error-700',
      rounded:
        'rounded-full data-[focus=true]:border-primary-700 data-[focus=true]:web:shadow-[inset_0_0_0_1px] data-[focus=true]:web:shadow-primary-700 data-[invalid=true]:border-error-700 data-[invalid=true]:web:shadow-error-700',
    },
  },
});

const selectInputStyle = tva({
  base: 'py-auto px-3 placeholder:text-typography-500 web:w-full h-full text-typography-900 pointer-events-none web:outline-none ios:leading-[0px]',
  parentVariants: {
    size: {
      xl: 'text-xl',
      lg: 'text-lg',
      md: 'text-base',
      sm: 'text-sm',
    },
    variant: {
      underlined: 'px-0',
      outline: '',
      rounded: 'px-4',
    },
  },
});

const selectIconStyle = tva({
  base: 'text-background-500 fill-none',
  parentVariants: {
    size: {
      '2xs': 'h-3 w-3',
      xs: 'h-3.5 w-3.5',
      sm: 'h-4 w-4',
      md: 'h-[18px] w-[18px]',
      lg: 'h-5 w-5',
      xl: 'h-6 w-6',
    },
  },
});

// Type definitions
export type ISelectProps = ViewProps &
  VariantProps<typeof selectStyle> & {
    className?: string;
    isDisabled?: boolean;
    isInvalid?: boolean;
    isFocused?: boolean;
    isHovered?: boolean;
  };

export type ISelectTriggerProps = PressableProps &
  VariantProps<typeof selectTriggerStyle> & {
    className?: string;
  };

export type ISelectInputProps = TextInputProps &
  VariantProps<typeof selectInputStyle> & {
    className?: string;
  };

export type ISelectIconProps = IPrimitiveIcon &
  VariantProps<typeof selectIconStyle> & {
    className?: string;
  };

// Main Select component - Direct v2 implementation without factory
export const Select = React.forwardRef<View, ISelectProps>(
  ({ 
    className, 
    isDisabled = false,
    isInvalid = false,
    isFocused = false,
    isHovered = false,
    children, 
    ...props 
  }, ref) => {
    const contextValue = useMemo(
      () => ({ isDisabled, isInvalid, isFocused, isHovered }),
      [isDisabled, isInvalid, isFocused, isHovered]
    );

    return (
      <SelectContext.Provider value={contextValue}>
        <View
          ref={ref}
          {...props}
          className={selectStyle({ class: className })}
        >
          {children}
        </View>
      </SelectContext.Provider>
    );
  }
);

// SelectTrigger component
export const SelectTrigger = React.forwardRef<View, ISelectTriggerProps>(
  ({ className, size = 'md', variant = 'outline', children, ...props }, ref) => {
    const context = useContext(SelectContext);
    const { isDisabled, isInvalid, isFocused, isHovered } = context || {};

    const contextValue = useMemo(
      () => ({ size, variant, isDisabled, isInvalid, isFocused, isHovered }),
      [size, variant, isDisabled, isInvalid, isFocused, isHovered]
    );

    return (
      <SelectContext.Provider value={contextValue}>
        <Pressable
          ref={ref as any}
          disabled={isDisabled}
          {...props}
          className={selectTriggerStyle({ size, variant, class: className })}
          // @ts-ignore - data attributes for styling
          data-disabled={isDisabled}
          data-invalid={isInvalid}
          data-focus={isFocused}
          data-hover={isHovered}
        >
          {children}
        </Pressable>
      </SelectContext.Provider>
    );
  }
);

// SelectInput component
export const SelectInput = React.forwardRef<TextInput, ISelectInputProps>(
  ({ className, editable = false, ...props }, ref) => {
    const context = useContext(SelectContext);
    const { size, variant, isDisabled } = context || {};

    return (
      <TextInput
        ref={ref}
        editable={!isDisabled && editable}
        {...props}
        className={selectInputStyle({
          parentVariants: { size, variant },
          class: className,
        })}
      />
    );
  }
);

// SelectIcon component
export const SelectIcon = React.forwardRef<any, ISelectIconProps>(
  ({ className, size, ...props }, ref) => {
    const context = useContext(SelectContext);
    const { size: parentSize } = context || {};

    if (typeof size === 'number') {
      return (
        <PrimitiveIcon
          ref={ref}
          {...props}
          className={className}
          size={size}
        />
      );
    }

    return (
      <PrimitiveIcon
        ref={ref}
        {...props}
        className={selectIconStyle({
          parentVariants: { size: parentSize },
          class: className,
        })}
      />
    );
  }
);

// Actionsheet Components - These remain the same as v1 for compatibility
export const SelectPortal = Actionsheet;
export const SelectBackdrop = ActionsheetBackdrop;
export const SelectContent = ActionsheetContent;
export const SelectDragIndicator = ActionsheetDragIndicator;
export const SelectDragIndicatorWrapper = ActionsheetDragIndicatorWrapper;
export const SelectItem = ActionsheetItem;
export const SelectItemText = ActionsheetItemText;
export const SelectScrollView = ActionsheetScrollView;
export const SelectVirtualizedList = ActionsheetVirtualizedList;
export const SelectFlatList = ActionsheetFlatList;
export const SelectSectionList = ActionsheetSectionList;
export const SelectSectionHeaderText = ActionsheetSectionHeaderText;

// Display names for debugging
Select.displayName = 'Select';
SelectTrigger.displayName = 'SelectTrigger';
SelectInput.displayName = 'SelectInput';
SelectIcon.displayName = 'SelectIcon';