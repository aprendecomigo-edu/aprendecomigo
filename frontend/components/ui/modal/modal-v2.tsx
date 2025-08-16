import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import type { PressableProps, ScrollViewProps, ViewProps } from 'react-native';
import { Pressable, ScrollView, View } from 'react-native';
import Animated, { FadeIn, FadeOut } from 'react-native-reanimated';

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);
const AnimatedView = Animated.createAnimatedComponent(View);

// Modal Context for sharing state between components
interface ModalContextValue {
  size?: string;
}

const ModalContext = createContext<ModalContextValue>({});

// Scope for style context
const SCOPE = 'MODAL';

// Style definitions (reuse existing styles)
export const modalStyle = tva({
  base: 'group/modal w-full h-full justify-center items-center web:pointer-events-none',
  variants: {
    size: {
      xs: '',
      sm: '',
      md: '',
      lg: '',
      full: '',
    },
  },
});

export const modalBackdropStyle = tva({
  base: 'absolute left-0 top-0 right-0 bottom-0 bg-background-dark web:cursor-default',
});

export const modalContentStyle = tva({
  base: 'bg-background-0 rounded-md overflow-hidden border border-outline-100 shadow-hard-2 p-6',
  parentVariants: {
    size: {
      xs: 'w-[60%] max-w-[360px]',
      sm: 'w-[70%] max-w-[420px]',
      md: 'w-[80%] max-w-[510px]',
      lg: 'w-[90%] max-w-[640px]',
      full: 'w-full',
    },
  },
});

export const modalBodyStyle = tva({
  base: 'mt-4 mb-6',
});

export const modalCloseButtonStyle = tva({
  base: 'group/modal-close-button z-10 rounded data-[focus-visible=true]:web:bg-background-100 web:outline-0 cursor-pointer',
});

export const modalHeaderStyle = tva({
  base: 'justify-between items-center flex-row',
});

export const modalFooterStyle = tva({
  base: 'flex-row justify-end items-center gap-2',
});

// Type definitions
export type IModalProps = ViewProps &
  VariantProps<typeof modalStyle> & {
    className?: string;
    context?: ModalContextValue;
    pointerEvents?: 'auto' | 'none' | 'box-none' | 'box-only';
  };

export type IModalBackdropProps = PressableProps &
  VariantProps<typeof modalBackdropStyle> & {
    className?: string;
    entering?: any;
    exiting?: any;
  };

export type IModalContentProps = ViewProps &
  VariantProps<typeof modalContentStyle> & {
    className?: string;
    entering?: any;
    exiting?: any;
    pointerEvents?: 'auto' | 'none' | 'box-none' | 'box-only';
  };

export type IModalHeaderProps = ViewProps &
  VariantProps<typeof modalHeaderStyle> & { className?: string };

export type IModalBodyProps = ScrollViewProps &
  VariantProps<typeof modalBodyStyle> & {
    className?: string;
    contentContainerClassName?: string;
    indicatorClassName?: string;
  };

export type IModalFooterProps = ViewProps &
  VariantProps<typeof modalFooterStyle> & { className?: string };

export type IModalCloseButtonProps = PressableProps &
  VariantProps<typeof modalCloseButtonStyle> & { className?: string };

// Modal Root Component - Direct implementation without factory
const ModalRoot = React.forwardRef<View, ViewProps>(({ ...props }, ref) => {
  return <View {...props} ref={ref} />;
});

// Main Modal component - Direct implementation
export const Modal = React.forwardRef<View, IModalProps>(
  ({ className, size = 'md', context, pointerEvents = 'box-none', children, ...props }, ref) => {
    const contextValue = useMemo(() => ({ size, ...context }), [size, context]);

    return (
      <ModalContext.Provider value={contextValue}>
        <ModalRoot
          ref={ref}
          {...props}
          pointerEvents={pointerEvents}
          className={modalStyle({ size, class: className })}
        >
          {children}
        </ModalRoot>
      </ModalContext.Provider>
    );
  },
);

// ModalBackdrop component - Direct implementation
export const ModalBackdrop = React.forwardRef<View, IModalBackdropProps>(
  (
    { className, entering = FadeIn.duration(250), exiting = FadeOut.duration(250), ...props },
    ref,
  ) => {
    return (
      <AnimatedPressable
        ref={ref as any}
        entering={entering}
        exiting={exiting}
        {...props}
        className={modalBackdropStyle({ class: className })}
      />
    );
  },
);

// ModalContent component - Direct implementation
export const ModalContent = React.forwardRef<View, IModalContentProps>(
  (
    {
      className,
      size,
      entering = FadeIn.duration(250).springify().damping(18).stiffness(250),
      exiting = FadeOut.duration(250),
      pointerEvents = 'auto',
      ...props
    },
    ref,
  ) => {
    const context = useContext(ModalContext);
    const { size: parentSize } = context || {};

    return (
      <AnimatedView
        ref={ref}
        entering={entering}
        exiting={exiting}
        {...props}
        className={modalContentStyle({
          parentVariants: { size: parentSize },
          size,
          class: className,
        })}
        pointerEvents={pointerEvents}
      />
    );
  },
);

// ModalHeader component - Direct implementation
export const ModalHeader = React.forwardRef<View, IModalHeaderProps>(
  ({ className, ...props }, ref) => {
    return <View ref={ref} {...props} className={modalHeaderStyle({ class: className })} />;
  },
);

// ModalBody component - Direct implementation
export const ModalBody = React.forwardRef<ScrollView, IModalBodyProps>(
  ({ className, contentContainerClassName, indicatorClassName, ...props }, ref) => {
    return (
      <ScrollView
        ref={ref}
        {...props}
        className={modalBodyStyle({ class: className })}
        contentContainerStyle={[
          // Add any default contentContainer styles if needed
          props.contentContainerStyle,
        ]}
        indicatorStyle={[
          // Add any default indicator styles if needed
          props.indicatorStyle,
        ]}
      />
    );
  },
);

// ModalFooter component - Direct implementation
export const ModalFooter = React.forwardRef<View, IModalFooterProps>(
  ({ className, ...props }, ref) => {
    return <View ref={ref} {...props} className={modalFooterStyle({ class: className })} />;
  },
);

// ModalCloseButton component - Direct implementation
export const ModalCloseButton = React.forwardRef<View, IModalCloseButtonProps>(
  ({ className, ...props }, ref) => {
    return (
      <Pressable
        ref={ref as any}
        {...props}
        className={modalCloseButtonStyle({ class: className })}
      />
    );
  },
);

// Display names for debugging
Modal.displayName = 'Modal';
ModalBackdrop.displayName = 'ModalBackdrop';
ModalContent.displayName = 'ModalContent';
ModalHeader.displayName = 'ModalHeader';
ModalBody.displayName = 'ModalBody';
ModalFooter.displayName = 'ModalFooter';
ModalCloseButton.displayName = 'ModalCloseButton';
