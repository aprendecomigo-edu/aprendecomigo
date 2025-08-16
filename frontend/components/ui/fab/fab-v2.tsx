'use client';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import { Platform, Text, Pressable, PressableProps, TextProps } from 'react-native';
import { Svg } from 'react-native-svg';

// FAB Context for sharing state between components
interface FabContextValue {
  size?: string;
  placement?: string;
}

const FabContext = createContext<FabContextValue>({});

// Scope for style context
const SCOPE = 'FAB';

// Icon component
export type IPrimitiveIcon = React.ComponentPropsWithoutRef<typeof Svg> & {
  height?: number | string;
  width?: number | string;
  fill?: string;
  color?: string;
  size?: number | string;
  stroke?: string;
  as?: React.ElementType;
};

const PrimitiveIcon = React.forwardRef<React.ElementRef<typeof Svg>, IPrimitiveIcon>(
  ({ height, width, fill, color, size, stroke, as: AsComp, ...props }, ref) => {
    const sizeProps = useMemo(() => {
      if (size) return { size };
      if (height && width) return { height, width };
      if (height) return { height };
      if (width) return { width };
      return {};
    }, [size, height, width]);

    let colorProps = {};
    if (color) {
      colorProps = { ...colorProps, color: color };
    }
    if (stroke) {
      colorProps = { ...colorProps, stroke: stroke };
    }
    if (fill) {
      colorProps = { ...colorProps, fill: fill };
    }
    if (AsComp) {
      return <AsComp ref={ref} {...sizeProps} {...colorProps} {...props} />;
    }
    return <Svg ref={ref} height={height} width={width} {...colorProps} {...props} />;
  },
);

// Style definitions (reuse existing styles)
export const fabStyle = tva({
  base: 'group/fab bg-primary-500 rounded-full z-20 p-4 flex-row items-center justify-center absolute hover:bg-primary-600 active:bg-primary-700 disabled:opacity-40 disabled:pointer-events-all disabled:cursor-not-allowed data-[focus=true]:web:outline-none data-[focus-visible=true]:web:ring-2 data-[focus-visible=true]:web:ring-indicator-info shadow-hard-2',
  variants: {
    size: {
      sm: 'px-2.5 py-2.5',
      md: 'px-3 py-3',
      lg: 'px-4 py-4',
    },
    placement: {
      'top right': 'top-4 right-4',
      'top left': 'top-4 left-4',
      'bottom right': 'bottom-4 right-4',
      'bottom left': 'bottom-4 left-4',
      'top center': 'top-4 self-center',
      'bottom center': 'bottom-4 self-center',
    },
  },
});

export const fabLabelStyle = tva({
  base: 'text-typography-50 font-normal font-body tracking-md text-left mx-2',
  variants: {
    isTruncated: {
      true: '',
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
  parentVariants: {
    size: {
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg',
    },
  },
});

export const fabIconStyle = tva({
  base: 'text-typography-50 hover:text-typography-0 active:text-typography-0 fill-none',
  variants: {
    size: {
      '2xs': 'h-3 w-3',
      xs: 'h-3.5 w-3.5',
      sm: 'h-4 w-4',
      md: 'w-[18px] h-[18px]',
      lg: 'h-5 w-5',
      xl: 'h-6 w-6',
    },
  },
});

// Type definitions
export type IFabProps = PressableProps &
  VariantProps<typeof fabStyle> & {
    className?: string;
  };

export type IFabLabelProps = TextProps &
  VariantProps<typeof fabLabelStyle> & {
    className?: string;
  };

export type IFabIconProps = React.ComponentPropsWithoutRef<typeof PrimitiveIcon> &
  VariantProps<typeof fabIconStyle> & {
    className?: string;
    as?: React.ElementType;
  };

// Main FAB component - Direct implementation without factory
export const Fab = React.forwardRef<Pressable, IFabProps>(
  ({ className, size = 'md', placement = 'bottom right', children, ...props }, ref) => {
    const contextValue = useMemo(() => ({ size, placement }), [size, placement]);

    return (
      <FabContext.Provider value={contextValue}>
        <Pressable
          ref={ref as any}
          {...props}
          className={fabStyle({ size, placement, class: className })}
        >
          {children}
        </Pressable>
      </FabContext.Provider>
    );
  },
);

// FabLabel component
export const FabLabel = React.forwardRef<Text, IFabLabelProps>(
  (
    {
      className,
      size,
      isTruncated = false,
      bold = false,
      underline = false,
      strikeThrough = false,
      ...props
    },
    ref,
  ) => {
    const context = useContext(FabContext);
    const { size: parentSize } = context || {};

    return (
      <Text
        ref={ref}
        {...props}
        className={fabLabelStyle({
          parentVariants: { size: parentSize },
          size,
          isTruncated,
          bold,
          underline,
          strikeThrough,
          class: className,
        })}
      />
    );
  },
);

// FabIcon component
export const FabIcon = React.forwardRef<any, IFabIconProps>(
  ({ className, size, ...props }, ref) => {
    const context = useContext(FabContext);
    const { size: parentSize } = context || {};

    if (typeof size === 'number') {
      return <PrimitiveIcon ref={ref} {...props} className={className} size={size} />;
    } else if ((props.height !== undefined || props.width !== undefined) && size === undefined) {
      return <PrimitiveIcon ref={ref} {...props} className={className} />;
    }

    return (
      <PrimitiveIcon
        ref={ref}
        {...props}
        className={fabIconStyle({
          size,
          class: className,
        })}
      />
    );
  },
);

// Display names for debugging
Fab.displayName = 'Fab';
FabLabel.displayName = 'FabLabel';
FabIcon.displayName = 'FabIcon';
