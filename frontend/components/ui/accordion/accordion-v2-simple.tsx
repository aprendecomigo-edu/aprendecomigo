'use client';
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

// Type definitions - simplified for testing
export type IAccordionProps = ViewProps & {
  variant?: 'filled' | 'unfilled';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
};

export type IAccordionItemProps = ViewProps & {
  value?: string;
  className?: string;
};

export type IAccordionHeaderProps = ViewProps & {
  className?: string;
};

export type IAccordionTriggerProps = PressableProps & {
  className?: string;
};

export type IAccordionTitleTextProps = TextProps & {
  className?: string;
};

export type IAccordionIconProps = ViewProps & {
  className?: string;
};

export type IAccordionContentProps = ViewProps & {
  className?: string;
};

export type IAccordionContentTextProps = TextProps & {
  className?: string;
};

// Simple style generator for testing
const getAccordionStyles = (variant?: string) => ({
  width: '100%',
  backgroundColor: variant === 'filled' ? '#ffffff' : 'transparent',
  shadowColor: variant === 'filled' ? '#000' : 'transparent',
  shadowOffset: { width: 0, height: 2 },
  shadowOpacity: variant === 'filled' ? 0.1 : 0,
  shadowRadius: variant === 'filled' ? 4 : 0,
  elevation: variant === 'filled' ? 2 : 0,
});

const getItemStyles = (variant?: string) => ({
  backgroundColor: variant === 'filled' ? '#ffffff' : 'transparent',
});

const getTriggerStyles = () => ({
  width: '100%',
  paddingVertical: 20,
  paddingHorizontal: 20,
  flexDirection: 'row' as const,
  justifyContent: 'space-between' as const,
  alignItems: 'center' as const,
});

const getTitleTextStyles = (size?: string) => ({
  color: '#1f2937',
  fontWeight: '700' as const,
  flex: 1,
  textAlign: 'left' as const,
  fontSize: size === 'sm' ? 14 : size === 'lg' ? 18 : 16,
});

const getContentStyles = () => ({
  paddingHorizontal: 20,
  paddingBottom: 20,
  marginTop: 8,
});

const getContentTextStyles = (size?: string) => ({
  color: '#4b5563',
  fontSize: size === 'sm' ? 14 : size === 'lg' ? 18 : 16,
});

// Main Accordion component - Simplified v2 without factory functions
export const Accordion = React.forwardRef<View, IAccordionProps>(
  ({ variant = 'filled', size = 'md', children, style, ...props }, ref) => {
    const contextValue = useMemo(() => ({ variant, size }), [variant, size]);

    const accordionStyles = getAccordionStyles(variant);

    return (
      <AccordionContext.Provider value={contextValue}>
        <View ref={ref} {...props} style={[accordionStyles, style]}>
          {children}
        </View>
      </AccordionContext.Provider>
    );
  },
);

// AccordionItem component
export const AccordionItem = React.forwardRef<View, IAccordionItemProps>(
  ({ children, style, ...props }, ref) => {
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

    const itemStyles = getItemStyles(variant);

    return (
      <AccordionItemContext.Provider value={itemContextValue}>
        <View ref={ref} {...props} style={[itemStyles, style]}>
          {children}
        </View>
      </AccordionItemContext.Provider>
    );
  },
);

// AccordionHeader component
export const AccordionHeader = React.forwardRef<View, IAccordionHeaderProps>(
  ({ children, style, ...props }, ref) => {
    return (
      <View ref={ref} {...props} style={[{ margin: 0 }, style]}>
        {children}
      </View>
    );
  },
);

// AccordionTrigger component
export const AccordionTrigger = React.forwardRef<View, IAccordionTriggerProps>(
  ({ children, onPress, style, ...props }, ref) => {
    const itemContext = useContext(AccordionItemContext);

    const handlePress = (event: any) => {
      itemContext?.onToggle?.();
      onPress?.(event);
    };

    const triggerStyles = getTriggerStyles();

    return (
      <Pressable ref={ref as any} {...props} onPress={handlePress} style={[triggerStyles, style]}>
        {children}
      </Pressable>
    );
  },
);

// AccordionTitleText component
export const AccordionTitleText = React.forwardRef<Text, IAccordionTitleTextProps>(
  ({ style, ...props }, ref) => {
    const context = useContext(AccordionContext);
    const { size } = context || {};

    const titleTextStyles = getTitleTextStyles(size);

    return <Text ref={ref} {...props} style={[titleTextStyles, style]} />;
  },
);

// AccordionIcon component - Simple placeholder
export const AccordionIcon = React.forwardRef<View, IAccordionIconProps>(
  ({ children, style, ...props }, ref) => {
    const itemContext = useContext(AccordionItemContext);

    const iconStyles = {
      width: 18,
      height: 18,
      transform: [{ rotate: itemContext?.isExpanded ? '180deg' : '0deg' }],
    };

    return (
      <View ref={ref} {...props} style={[iconStyles, style]}>
        {children}
      </View>
    );
  },
);

// AccordionContent component
export const AccordionContent = React.forwardRef<View, IAccordionContentProps>(
  ({ children, style, ...props }, ref) => {
    const itemContext = useContext(AccordionItemContext);

    if (!itemContext?.isExpanded) {
      return null;
    }

    const contentStyles = getContentStyles();

    return (
      <View ref={ref} {...props} style={[contentStyles, style]}>
        {children}
      </View>
    );
  },
);

// AccordionContentText component
export const AccordionContentText = React.forwardRef<Text, IAccordionContentTextProps>(
  ({ style, ...props }, ref) => {
    const context = useContext(AccordionContext);
    const { size } = context || {};

    const contentTextStyles = getContentTextStyles(size);

    return <Text ref={ref} {...props} style={[contentTextStyles, style]} />;
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
