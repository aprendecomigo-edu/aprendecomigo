'use client';
import React, { createContext, useContext, useMemo, useState } from 'react';
import { View, Pressable, Text, Modal, ViewProps, PressableProps, TextProps } from 'react-native';

// Tooltip Context
interface TooltipContextValue {
  isOpen?: boolean;
  onOpen?: () => void;
  onClose?: () => void;
}

const TooltipContext = createContext<TooltipContextValue>({});

// Type definitions
export type ITooltipProps = ViewProps & {};
export type ITooltipTriggerProps = PressableProps & {};
export type ITooltipContentProps = ViewProps & {};
export type ITooltipTextProps = TextProps & {};

// Main Tooltip component
export const Tooltip = React.forwardRef<View, ITooltipProps>(({ children, ...props }, ref) => {
  const [isOpen, setIsOpen] = useState(false);

  const contextValue = useMemo(
    () => ({
      isOpen,
      onOpen: () => setIsOpen(true),
      onClose: () => setIsOpen(false),
    }),
    [isOpen],
  );

  return (
    <TooltipContext.Provider value={contextValue}>
      <View ref={ref} {...props}>
        {children}
      </View>
    </TooltipContext.Provider>
  );
});

export const TooltipTrigger = React.forwardRef<View, ITooltipTriggerProps>(
  ({ children, onPressIn, onPressOut, ...props }, ref) => {
    const context = useContext(TooltipContext);

    return (
      <Pressable
        ref={ref as any}
        {...props}
        onPressIn={event => {
          context?.onOpen?.();
          onPressIn?.(event);
        }}
        onPressOut={event => {
          context?.onClose?.();
          onPressOut?.(event);
        }}
      >
        {children}
      </Pressable>
    );
  },
);

export const TooltipContent = React.forwardRef<View, ITooltipContentProps>(
  ({ children, style, ...props }, ref) => {
    const context = useContext(TooltipContext);

    if (!context?.isOpen) return null;

    return (
      <Modal
        visible={context.isOpen}
        transparent
        animationType="fade"
        onRequestClose={context.onClose}
      >
        <View
          style={{
            flex: 1,
            justifyContent: 'center',
            alignItems: 'center',
            backgroundColor: 'rgba(0,0,0,0.1)',
          }}
        >
          <View
            ref={ref}
            {...props}
            style={[
              {
                backgroundColor: '#374151',
                borderRadius: 6,
                paddingVertical: 8,
                paddingHorizontal: 12,
                maxWidth: 300,
                shadowColor: '#000',
                shadowOffset: { width: 0, height: 2 },
                shadowOpacity: 0.25,
                shadowRadius: 4,
                elevation: 4,
              },
              style,
            ]}
          >
            {children}
          </View>
        </View>
      </Modal>
    );
  },
);

export const TooltipText = React.forwardRef<Text, ITooltipTextProps>(({ style, ...props }, ref) => (
  <Text
    ref={ref}
    {...props}
    style={[
      {
        color: '#ffffff',
        fontSize: 14,
        textAlign: 'center',
      },
      style,
    ]}
  />
));

// Display names
Tooltip.displayName = 'Tooltip';
TooltipTrigger.displayName = 'TooltipTrigger';
TooltipContent.displayName = 'TooltipContent';
TooltipText.displayName = 'TooltipText';
