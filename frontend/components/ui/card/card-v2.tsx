import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { isWeb } from '@/utils/platform';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import type { ViewProps } from 'react-native';
import { View } from 'react-native';

// Card Context for sharing state between components
interface CardContextValue {
  size?: string;
  variant?: string;
}

const CardContext = createContext<CardContextValue>({});

// Style definitions (reuse existing styles)
const baseStyle = isWeb ? 'flex flex-col relative z-0' : '';

export const cardStyle = tva({
  base: baseStyle,
  variants: {
    size: {
      sm: 'p-3 rounded',
      md: 'p-4 rounded-md',
      lg: 'p-6 rounded-xl',
    },
    variant: {
      elevated: 'bg-background-0',
      outline: 'border border-outline-200',
      ghost: 'rounded-none',
      filled: 'bg-background-50',
    },
  },
});

export const cardHeaderStyle = tva({
  base: 'px-4 pt-4 pb-2',
  parentVariants: {
    size: {
      sm: 'px-3 pt-3 pb-1.5',
      md: 'px-4 pt-4 pb-2',
      lg: 'px-6 pt-6 pb-3',
    },
  },
});

export const cardBodyStyle = tva({
  base: 'px-4 py-3',
  parentVariants: {
    size: {
      sm: 'px-3 py-2',
      md: 'px-4 py-3',
      lg: 'px-6 py-4',
    },
  },
});

export const cardFooterStyle = tva({
  base: 'px-4 pb-4 pt-2',
  parentVariants: {
    size: {
      sm: 'px-3 pb-3 pt-1.5',
      md: 'px-4 pb-4 pt-2',
      lg: 'px-6 pb-6 pt-3',
    },
  },
});

// Type definitions
export type ICardProps = ViewProps &
  VariantProps<typeof cardStyle> & {
    className?: string;
  };

export type ICardHeaderProps = ViewProps &
  VariantProps<typeof cardHeaderStyle> & {
    className?: string;
  };

export type ICardBodyProps = ViewProps &
  VariantProps<typeof cardBodyStyle> & {
    className?: string;
  };

export type ICardFooterProps = ViewProps &
  VariantProps<typeof cardFooterStyle> & {
    className?: string;
  };

// Main Card component - v2 implementation with context
export const Card = React.forwardRef<View, ICardProps>(
  ({ className, size = 'md', variant = 'elevated', children, ...props }, ref) => {
    const contextValue = useMemo(() => ({ size, variant }), [size, variant]);

    return (
      <CardContext.Provider value={contextValue}>
        <View ref={ref} {...props} className={cardStyle({ size, variant, class: className })}>
          {children}
        </View>
      </CardContext.Provider>
    );
  },
);

// CardHeader component
export const CardHeader = React.forwardRef<View, ICardHeaderProps>(
  ({ className, ...props }, ref) => {
    const context = useContext(CardContext);
    const { size } = context || {};

    return (
      <View
        ref={ref}
        {...props}
        className={cardHeaderStyle({
          parentVariants: { size },
          class: className,
        })}
      />
    );
  },
);

// CardBody component
export const CardBody = React.forwardRef<View, ICardBodyProps>(({ className, ...props }, ref) => {
  const context = useContext(CardContext);
  const { size } = context || {};

  return (
    <View
      ref={ref}
      {...props}
      className={cardBodyStyle({
        parentVariants: { size },
        class: className,
      })}
    />
  );
});

// CardFooter component
export const CardFooter = React.forwardRef<View, ICardFooterProps>(
  ({ className, ...props }, ref) => {
    const context = useContext(CardContext);
    const { size } = context || {};

    return (
      <View
        ref={ref}
        {...props}
        className={cardFooterStyle({
          parentVariants: { size },
          class: className,
        })}
      />
    );
  },
);

// Display names for debugging
Card.displayName = 'Card';
CardHeader.displayName = 'CardHeader';
CardBody.displayName = 'CardBody';
CardFooter.displayName = 'CardFooter';
