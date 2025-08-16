import { H3 } from '@expo/html-elements';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo, useState } from 'react';
import {
  View,
  Pressable,
  Text,
  Platform,
  TextProps,
  ViewProps,
  PressableProps,
} from 'react-native';
import { Svg } from 'react-native-svg';

// Accordion Context for sharing state between components
interface AccordionContextValue {
  variant?: string;
  size?: string;
}

interface AccordionItemContextValue {
  isExpanded?: boolean;
  onToggle?: () => void;
}

const AccordionContext = createContext<AccordionContextValue>({});
const AccordionItemContext = createContext<AccordionItemContextValue>({});

// Scope for style context
const SCOPE = 'ACCORDION';

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
  ({ height, width, fill, color, size, stroke = 'currentColor', as: AsComp, ...props }, ref) => {
    const sizeProps = useMemo(() => {
      if (size) return { size };
      if (height && width) return { height, width };
      if (height) return { height };
      if (width) return { width };
      return {};
    }, [size, height, width]);

    const colorProps = stroke === 'currentColor' && color !== undefined ? color : stroke;

    if (AsComp) {
      return <AsComp ref={ref} fill={fill} {...props} {...sizeProps} stroke={colorProps} />;
    }
    return (
      <Svg ref={ref} height={height} width={width} fill={fill} stroke={colorProps} {...props} />
    );
  },
);

// Style definitions
export const accordionStyle = tva({
  base: 'w-full',
  variants: {
    variant: {
      filled: 'bg-white shadow-hard-2',
      unfilled: '',
    },
    size: {
      sm: '',
      md: '',
      lg: '',
    },
  },
});

export const accordionItemStyle = tva({
  base: '',
  parentVariants: {
    variant: {
      filled: 'bg-background-0',
      unfilled: 'bg-transparent',
    },
  },
});

export const accordionTitleTextStyle = tva({
  base: 'text-typography-900 font-bold flex-1 text-left',
  parentVariants: {
    size: {
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg',
    },
  },
});

export const accordionIconStyle = tva({
  base: 'text-typography-900 fill-none',
  variants: {
    size: {
      '2xs': 'h-3 w-3',
      xs: 'h-3.5 w-3.5',
      sm: 'h-4 w-4',
      md: 'h-[18px] w-[18px]',
      lg: 'h-5 w-5',
      xl: 'h-6 w-6',
    },
  },
  parentVariants: {
    size: {
      sm: 'h-4 w-4',
      md: 'h-[18px] w-[18px]',
      lg: 'h-5 w-5',
    },
  },
});

export const accordionContentTextStyle = tva({
  base: 'text-typography-700 font-normal',
  parentVariants: {
    size: {
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg',
    },
  },
});

export const accordionHeaderStyle = tva({
  base: 'mx-0 my-0',
});

export const accordionContentStyle = tva({
  base: 'px-5 mt-2 pb-5',
});

export const accordionTriggerStyle = tva({
  base: 'w-full py-5 px-5 flex-row justify-between items-center web:outline-none focus:outline-none data-[disabled=true]:opacity-40 data-[disabled=true]:cursor-not-allowed data-[focus-visible=true]:bg-background-50',
});

// Type definitions
export type IAccordionProps = ViewProps &
  VariantProps<typeof accordionStyle> & {
    className?: string;
  };

export type IAccordionItemProps = ViewProps &
  VariantProps<typeof accordionItemStyle> & {
    className?: string;
    value?: string;
  };

export type IAccordionContentProps = ViewProps &
  VariantProps<typeof accordionContentStyle> & {
    className?: string;
  };

export type IAccordionContentTextProps = TextProps &
  VariantProps<typeof accordionContentTextStyle> & {
    className?: string;
  };

export type IAccordionIconProps = React.ComponentPropsWithoutRef<typeof PrimitiveIcon> &
  VariantProps<typeof accordionIconStyle> & {
    className?: string;
    as?: React.ElementType;
  };

export type IAccordionHeaderProps = ViewProps &
  VariantProps<typeof accordionHeaderStyle> & {
    className?: string;
  };

export type IAccordionTriggerProps = PressableProps &
  VariantProps<typeof accordionTriggerStyle> & {
    className?: string;
  };

export type IAccordionTitleTextProps = TextProps &
  VariantProps<typeof accordionTitleTextStyle> & {
    className?: string;
  };

// Main Accordion component - Direct implementation without factory
export const Accordion = React.forwardRef<View, IAccordionProps>(
  ({ className, variant = 'filled', size = 'md', children, ...props }, ref) => {
    const contextValue = useMemo(() => ({ variant, size }), [variant, size]);

    return (
      <AccordionContext.Provider value={contextValue}>
        <View ref={ref} {...props} className={accordionStyle({ variant, class: className })}>
          {children}
        </View>
      </AccordionContext.Provider>
    );
  },
);

// AccordionItem component
export const AccordionItem = React.forwardRef<View, IAccordionItemProps>(
  ({ className, children, value, ...props }, ref) => {
    const context = useContext(AccordionContext);
    const { variant } = context || {};
    const [isExpanded, setIsExpanded] = useState(false);

    const itemContextValue = useMemo(
      () => ({
        isExpanded,
        onToggle: () => setIsExpanded(!isExpanded),
      }),
      [isExpanded],
    );

    return (
      <AccordionItemContext.Provider value={itemContextValue}>
        <View
          ref={ref}
          {...props}
          className={accordionItemStyle({
            parentVariants: { variant },
            class: className,
          })}
        >
          {children}
        </View>
      </AccordionItemContext.Provider>
    );
  },
);

// AccordionHeader component
export const AccordionHeader = React.forwardRef<View, IAccordionHeaderProps>(
  ({ className, ...props }, ref) => {
    const HeaderComponent = (Platform.OS === 'web' ? H3 : View) as React.ComponentType<any>;

    return (
      <HeaderComponent
        ref={ref}
        {...props}
        className={accordionHeaderStyle({
          class: className,
        })}
      />
    );
  },
);

// AccordionTrigger component
export const AccordionTrigger = React.forwardRef<View, IAccordionTriggerProps>(
  ({ className, children, onPress, ...props }, ref) => {
    const itemContext = useContext(AccordionItemContext);

    const handlePress = (event: any) => {
      itemContext?.onToggle?.();
      onPress?.(event);
    };

    return (
      <Pressable
        ref={ref as any}
        {...props}
        onPress={handlePress}
        className={accordionTriggerStyle({
          class: className,
        })}
      >
        {children}
      </Pressable>
    );
  },
);

// AccordionTitleText component
export const AccordionTitleText = React.forwardRef<Text, IAccordionTitleTextProps>(
  ({ className, ...props }, ref) => {
    const context = useContext(AccordionContext);
    const { size } = context || {};

    return (
      <Text
        ref={ref}
        {...props}
        className={accordionTitleTextStyle({
          parentVariants: { size },
          class: className,
        })}
      />
    );
  },
);

// AccordionIcon component
export const AccordionIcon = React.forwardRef<any, IAccordionIconProps>(
  ({ size, className, ...props }, ref) => {
    const context = useContext(AccordionContext);
    const itemContext = useContext(AccordionItemContext);
    const { size: parentSize } = context || {};

    if (typeof size === 'number') {
      return <PrimitiveIcon ref={ref} {...props} className={className} size={size} />;
    }

    return (
      <PrimitiveIcon
        ref={ref}
        {...props}
        className={accordionIconStyle({
          size,
          parentVariants: { size: parentSize },
          class: className,
        })}
        style={{
          transform: [{ rotate: itemContext?.isExpanded ? '180deg' : '0deg' }],
        }}
      />
    );
  },
);

// AccordionContent component
export const AccordionContent = React.forwardRef<View, IAccordionContentProps>(
  ({ className, children, ...props }, ref) => {
    const itemContext = useContext(AccordionItemContext);

    if (!itemContext?.isExpanded) {
      return null;
    }

    return (
      <View
        ref={ref}
        {...props}
        className={accordionContentStyle({
          class: className,
        })}
      >
        {children}
      </View>
    );
  },
);

// AccordionContentText component
export const AccordionContentText = React.forwardRef<Text, IAccordionContentTextProps>(
  ({ className, ...props }, ref) => {
    const context = useContext(AccordionContext);
    const { size } = context || {};

    return (
      <Text
        ref={ref}
        {...props}
        className={accordionContentTextStyle({
          parentVariants: { size },
          class: className,
        })}
      />
    );
  },
);

// Display names for debugging
Accordion.displayName = 'Accordion';
AccordionItem.displayName = 'AccordionItem';
AccordionHeader.displayName = 'AccordionHeader';
AccordionTrigger.displayName = 'AccordionTrigger';
AccordionTitleText.displayName = 'AccordionTitleText';
AccordionIcon.displayName = 'AccordionIcon';
AccordionContent.displayName = 'AccordionContent';
AccordionContentText.displayName = 'AccordionContentText';
