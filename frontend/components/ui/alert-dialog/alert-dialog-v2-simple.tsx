'use client';
import React, { createContext, useContext, useMemo } from 'react';
import { View, Pressable, Text, Modal, ViewProps, PressableProps, TextProps } from 'react-native';

// AlertDialog Context
interface AlertDialogContextValue {
  isOpen?: boolean;
  onClose?: () => void;
}

const AlertDialogContext = createContext<AlertDialogContextValue>({});

// Type definitions
export type IAlertDialogProps = ViewProps & {
  isOpen?: boolean;
  onClose?: () => void;
};

export type IAlertDialogBackdropProps = PressableProps & {};
export type IAlertDialogContentProps = ViewProps & {};
export type IAlertDialogHeaderProps = ViewProps & {};
export type IAlertDialogBodyProps = ViewProps & {};
export type IAlertDialogFooterProps = ViewProps & {};

// Main AlertDialog component
export const AlertDialog = React.forwardRef<View, IAlertDialogProps>(
  ({ isOpen = false, onClose, children, ...props }, ref) => {
    const contextValue = useMemo(() => ({ isOpen, onClose }), [isOpen, onClose]);

    return (
      <AlertDialogContext.Provider value={contextValue}>
        <Modal visible={isOpen} transparent animationType="fade" onRequestClose={onClose}>
          <View
            ref={ref}
            {...props}
            style={{
              flex: 1,
              justifyContent: 'center',
              alignItems: 'center',
              backgroundColor: 'rgba(0,0,0,0.5)',
            }}
          >
            {children}
          </View>
        </Modal>
      </AlertDialogContext.Provider>
    );
  }
);

export const AlertDialogBackdrop = React.forwardRef<View, IAlertDialogBackdropProps>(
  ({ onPress, ...props }, ref) => {
    const context = useContext(AlertDialogContext);
    return (
      <Pressable
        ref={ref as any}
        {...props}
        onPress={() => {
          context?.onClose?.();
          onPress?.();
        }}
        style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
      />
    );
  }
);

export const AlertDialogContent = React.forwardRef<View, IAlertDialogContentProps>(
  ({ children, style, ...props }, ref) => (
    <View
      ref={ref}
      {...props}
      style={[
        { backgroundColor: 'white', borderRadius: 12, padding: 24, margin: 20, maxWidth: '90%' },
        style,
      ]}
    >
      {children}
    </View>
  )
);

export const AlertDialogHeader = React.forwardRef<View, IAlertDialogHeaderProps>(
  ({ children, style, ...props }, ref) => (
    <View ref={ref} {...props} style={[{ marginBottom: 16 }, style]}>
      {children}
    </View>
  )
);

export const AlertDialogBody = React.forwardRef<View, IAlertDialogBodyProps>(
  ({ children, style, ...props }, ref) => (
    <View ref={ref} {...props} style={[{ marginBottom: 20 }, style]}>
      {children}
    </View>
  )
);

export const AlertDialogFooter = React.forwardRef<View, IAlertDialogFooterProps>(
  ({ children, style, ...props }, ref) => (
    <View
      ref={ref}
      {...props}
      style={[{ flexDirection: 'row', justifyContent: 'flex-end', gap: 12 }, style]}
    >
      {children}
    </View>
  )
);

// Display names
AlertDialog.displayName = 'AlertDialog';
AlertDialogBackdrop.displayName = 'AlertDialogBackdrop';
AlertDialogContent.displayName = 'AlertDialogContent';
AlertDialogHeader.displayName = 'AlertDialogHeader';
AlertDialogBody.displayName = 'AlertDialogBody';
AlertDialogFooter.displayName = 'AlertDialogFooter';
