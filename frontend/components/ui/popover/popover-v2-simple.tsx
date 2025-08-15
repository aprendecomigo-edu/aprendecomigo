'use client';
import React, { createContext, useContext, useMemo, useState } from 'react';
import { View, Pressable, Modal, ViewProps, PressableProps } from 'react-native';

// Popover Context
interface PopoverContextValue {
  isOpen?: boolean;
  onOpen?: () => void;
  onClose?: () => void;
  onToggle?: () => void;
}

const PopoverContext = createContext<PopoverContextValue>({});

// Type definitions
export type IPopoverProps = ViewProps & {};
export type IPopoverTriggerProps = PressableProps & {};
export type IPopoverContentProps = ViewProps & {};
export type IPopoverHeaderProps = ViewProps & {};
export type IPopoverBodyProps = ViewProps & {};
export type IPopoverFooterProps = ViewProps & {};
export type IPopoverBackdropProps = PressableProps & {};

// Main Popover component
export const Popover = React.forwardRef<View, IPopoverProps>(
  ({ children, ...props }, ref) => {
    const [isOpen, setIsOpen] = useState(false);
    
    const contextValue = useMemo(
      () => ({
        isOpen,
        onOpen: () => setIsOpen(true),
        onClose: () => setIsOpen(false),
        onToggle: () => setIsOpen(!isOpen),
      }),
      [isOpen]
    );

    return (
      <PopoverContext.Provider value={contextValue}>
        <View ref={ref} {...props}>
          {children}
        </View>
      </PopoverContext.Provider>
    );
  }
);

export const PopoverTrigger = React.forwardRef<View, IPopoverTriggerProps>(
  ({ children, onPress, ...props }, ref) => {
    const context = useContext(PopoverContext);
    
    const handlePress = (event: any) => {
      context?.onToggle?.();
      onPress?.(event);
    };

    return (
      <Pressable ref={ref as any} {...props} onPress={handlePress}>
        {children}
      </Pressable>
    );
  }
);

export const PopoverContent = React.forwardRef<View, IPopoverContentProps>(
  ({ children, style, ...props }, ref) => {
    const context = useContext(PopoverContext);
    
    if (!context?.isOpen) return null;
    
    return (
      <Modal visible={context.isOpen} transparent animationType="fade" onRequestClose={context.onClose}>
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.3)' }}>
          <View ref={ref} {...props} style={[{ backgroundColor: 'white', borderRadius: 8, padding: 16, margin: 20, minWidth: 200, shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.25, shadowRadius: 8, elevation: 8 }, style]}>
            {children}
          </View>
        </View>
      </Modal>
    );
  }
);

export const PopoverBackdrop = React.forwardRef<View, IPopoverBackdropProps>(
  ({ onPress, ...props }, ref) => {
    const context = useContext(PopoverContext);
    return (
      <Pressable
        ref={ref as any}
        {...props}
        onPress={() => { context?.onClose?.(); onPress?.(); }}
        style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
      />
    );
  }
);

export const PopoverHeader = React.forwardRef<View, IPopoverHeaderProps>(
  ({ children, style, ...props }, ref) => (
    <View ref={ref} {...props} style={[{ marginBottom: 12, borderBottomWidth: 1, borderBottomColor: '#e5e7eb', paddingBottom: 8 }, style]}>{children}</View>
  )
);

export const PopoverBody = React.forwardRef<View, IPopoverBodyProps>(
  ({ children, style, ...props }, ref) => (
    <View ref={ref} {...props} style={[{ marginBottom: 8 }, style]}>{children}</View>
  )
);

export const PopoverFooter = React.forwardRef<View, IPopoverFooterProps>(
  ({ children, style, ...props }, ref) => (
    <View ref={ref} {...props} style={[{ marginTop: 12, borderTopWidth: 1, borderTopColor: '#e5e7eb', paddingTop: 8, flexDirection: 'row', justifyContent: 'flex-end', gap: 8 }, style]}>{children}</View>
  )
);

// Display names
Popover.displayName = 'Popover';
PopoverTrigger.displayName = 'PopoverTrigger';
PopoverContent.displayName = 'PopoverContent';
PopoverBackdrop.displayName = 'PopoverBackdrop';
PopoverHeader.displayName = 'PopoverHeader';
PopoverBody.displayName = 'PopoverBody';
PopoverFooter.displayName = 'PopoverFooter';
