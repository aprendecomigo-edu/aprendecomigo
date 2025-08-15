'use client';
import React, { createContext, useContext, useMemo, useState } from 'react';
import {
  View,
  Pressable,
  Text,
  ScrollView,
  Modal,
  ViewProps,
  PressableProps,
  TextProps,
  ScrollViewProps,
} from 'react-native';

// Actionsheet Context for sharing state between components
interface ActionsheetContextValue {
  isOpen?: boolean;
  onClose?: () => void;
}

const ActionsheetContext = createContext<ActionsheetContextValue>({});

// Type definitions - simplified for testing
export type IActionsheetProps = ViewProps & {
  isOpen?: boolean;
  onClose?: () => void;
  className?: string;
};

export type IActionsheetBackdropProps = PressableProps & {
  className?: string;
};

export type IActionsheetContentProps = ViewProps & {
  className?: string;
};

export type IActionsheetItemProps = PressableProps & {
  className?: string;
};

export type IActionsheetItemTextProps = TextProps & {
  className?: string;
};

export type IActionsheetScrollViewProps = ScrollViewProps & {
  className?: string;
};

export type IActionsheetDragIndicatorProps = ViewProps & {
  className?: string;
};

export type IActionsheetDragIndicatorWrapperProps = ViewProps & {
  className?: string;
};

// Simple style generators
const getActionsheetStyles = () => ({
  flex: 1,
  justifyContent: 'flex-end' as const,
  alignItems: 'center' as const,
  backgroundColor: 'rgba(0,0,0,0.5)',
});

const getContentStyles = () => ({
  backgroundColor: '#ffffff',
  borderTopLeftRadius: 24,
  borderTopRightRadius: 24,
  width: '100%',
  maxHeight: '80%',
  padding: 20,
  paddingTop: 8,
});

const getItemStyles = () => ({
  width: '100%',
  flexDirection: 'row' as const,
  alignItems: 'center' as const,
  padding: 12,
  borderRadius: 4,
});

// Main Actionsheet component - Simplified v2 without factory functions
export const Actionsheet = React.forwardRef<View, IActionsheetProps>(
  ({ isOpen = false, onClose, children, style, ...props }, ref) => {
    const contextValue = useMemo(() => ({ isOpen, onClose }), [isOpen, onClose]);

    const actionsheetStyles = getActionsheetStyles();

    return (
      <ActionsheetContext.Provider value={contextValue}>
        <Modal visible={isOpen} transparent animationType="slide" onRequestClose={onClose}>
          <View ref={ref} {...props} style={[actionsheetStyles, style]}>
            {children}
          </View>
        </Modal>
      </ActionsheetContext.Provider>
    );
  }
);

// ActionsheetBackdrop component
export const ActionsheetBackdrop = React.forwardRef<View, IActionsheetBackdropProps>(
  ({ onPress, style, ...props }, ref) => {
    const context = useContext(ActionsheetContext);

    const handlePress = (event: any) => {
      context?.onClose?.();
      onPress?.(event);
    };

    return (
      <Pressable
        ref={ref as any}
        {...props}
        onPress={handlePress}
        style={[{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }, style]}
      />
    );
  }
);

// ActionsheetContent component
export const ActionsheetContent = React.forwardRef<View, IActionsheetContentProps>(
  ({ children, style, ...props }, ref) => {
    const contentStyles = getContentStyles();

    return (
      <View ref={ref} {...props} style={[contentStyles, style]}>
        {children}
      </View>
    );
  }
);

// ActionsheetDragIndicatorWrapper component
export const ActionsheetDragIndicatorWrapper = React.forwardRef<
  View,
  IActionsheetDragIndicatorWrapperProps
>(({ children, style, ...props }, ref) => (
  <View
    ref={ref}
    {...props}
    style={[{ width: '100%', paddingVertical: 4, alignItems: 'center' }, style]}
  >
    {children}
  </View>
));

// ActionsheetDragIndicator component
export const ActionsheetDragIndicator = React.forwardRef<View, IActionsheetDragIndicatorProps>(
  ({ style, ...props }, ref) => (
    <View
      ref={ref}
      {...props}
      style={[{ width: 64, height: 4, backgroundColor: '#9ca3af', borderRadius: 2 }, style]}
    />
  )
);

// ActionsheetScrollView component
export const ActionsheetScrollView = React.forwardRef<ScrollView, IActionsheetScrollViewProps>(
  ({ children, style, ...props }, ref) => (
    <ScrollView ref={ref} {...props} style={[{ width: '100%', maxHeight: '100%' }, style]}>
      {children}
    </ScrollView>
  )
);

// ActionsheetItem component
export const ActionsheetItem = React.forwardRef<View, IActionsheetItemProps>(
  ({ children, onPress, style, ...props }, ref) => {
    const itemStyles = getItemStyles();

    return (
      <Pressable ref={ref as any} {...props} onPress={onPress} style={[itemStyles, style]}>
        {children}
      </Pressable>
    );
  }
);

// ActionsheetItemText component
export const ActionsheetItemText = React.forwardRef<Text, IActionsheetItemTextProps>(
  ({ style, ...props }, ref) => (
    <Text ref={ref} {...props} style={[{ fontSize: 16, color: '#374151' }, style]} />
  )
);

// Display names for debugging
Actionsheet.displayName = 'Actionsheet';
ActionsheetBackdrop.displayName = 'ActionsheetBackdrop';
ActionsheetContent.displayName = 'ActionsheetContent';
ActionsheetDragIndicatorWrapper.displayName = 'ActionsheetDragIndicatorWrapper';
ActionsheetDragIndicator.displayName = 'ActionsheetDragIndicator';
ActionsheetScrollView.displayName = 'ActionsheetScrollView';
ActionsheetItem.displayName = 'ActionsheetItem';
ActionsheetItemText.displayName = 'ActionsheetItemText';
