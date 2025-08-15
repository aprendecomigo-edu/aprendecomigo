'use client';
import React from 'react';
import type { PressableProps, ScrollViewProps, ViewProps } from 'react-native';
import { Pressable, ScrollView, View } from 'react-native';
import Animated, { FadeIn, FadeOut } from 'react-native-reanimated';

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);
const AnimatedView = Animated.createAnimatedComponent(View);

// Simplified Modal implementation - no factory functions
export type IModalProps = ViewProps & { 
  className?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'full';
  pointerEvents?: 'auto' | 'none' | 'box-none' | 'box-only';
};

export type IModalBackdropProps = PressableProps & { 
  className?: string;
  entering?: any;
  exiting?: any;
};

export type IModalContentProps = ViewProps & { 
  className?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'full';
  entering?: any;
  exiting?: any;
  pointerEvents?: 'auto' | 'none' | 'box-none' | 'box-only';
};

export type IModalHeaderProps = ViewProps & { className?: string };
export type IModalBodyProps = ScrollViewProps & { className?: string };
export type IModalFooterProps = ViewProps & { className?: string };
export type IModalCloseButtonProps = PressableProps & { className?: string };

// Simple Modal Root
export const Modal = React.forwardRef<View, IModalProps>(
  ({ className = '', size = 'md', pointerEvents = 'box-none', ...props }, ref) => {
    const baseClasses = 'group/modal w-full h-full justify-center items-center web:pointer-events-none';
    
    return (
      <View
        ref={ref}
        {...props}
        pointerEvents={pointerEvents}
        className={`${baseClasses} ${className}`}
      />
    );
  }
);

// Simple Modal Backdrop
export const ModalBackdrop = React.forwardRef<View, IModalBackdropProps>(
  ({ className = '', entering = FadeIn.duration(250), exiting = FadeOut.duration(250), ...props }, ref) => {
    const baseClasses = 'absolute left-0 top-0 right-0 bottom-0 bg-background-dark web:cursor-default';
    
    return (
      <AnimatedPressable
        ref={ref as any}
        entering={entering}
        exiting={exiting}
        {...props}
        className={`${baseClasses} ${className}`}
      />
    );
  }
);

// Simple Modal Content
export const ModalContent = React.forwardRef<View, IModalContentProps>(
  ({ 
    className = '', 
    size = 'md', 
    entering = FadeIn.duration(250).springify().damping(18).stiffness(250),
    exiting = FadeOut.duration(250),
    pointerEvents = 'auto',
    ...props 
  }, ref) => {
    const sizeClasses = {
      xs: 'w-[60%] max-w-[360px]',
      sm: 'w-[70%] max-w-[420px]',
      md: 'w-[80%] max-w-[510px]',
      lg: 'w-[90%] max-w-[640px]',
      full: 'w-full',
    };
    
    const baseClasses = 'bg-background-0 rounded-md overflow-hidden border border-outline-100 shadow-hard-2 p-6';
    const combinedClasses = `${baseClasses} ${sizeClasses[size]} ${className}`;
    
    return (
      <AnimatedView
        ref={ref}
        entering={entering}
        exiting={exiting}
        {...props}
        className={combinedClasses}
        pointerEvents={pointerEvents}
      />
    );
  }
);

// Simple Modal Header
export const ModalHeader = React.forwardRef<View, IModalHeaderProps>(
  ({ className = '', ...props }, ref) => {
    const baseClasses = 'justify-between items-center flex-row';
    
    return (
      <View
        ref={ref}
        {...props}
        className={`${baseClasses} ${className}`}
      />
    );
  }
);

// Simple Modal Body
export const ModalBody = React.forwardRef<ScrollView, IModalBodyProps>(
  ({ className = '', ...props }, ref) => {
    const baseClasses = 'mt-4 mb-6';
    
    return (
      <ScrollView
        ref={ref}
        {...props}
        className={`${baseClasses} ${className}`}
      />
    );
  }
);

// Simple Modal Footer
export const ModalFooter = React.forwardRef<View, IModalFooterProps>(
  ({ className = '', ...props }, ref) => {
    const baseClasses = 'flex-row justify-end items-center gap-2';
    
    return (
      <View
        ref={ref}
        {...props}
        className={`${baseClasses} ${className}`}
      />
    );
  }
);

// Simple Modal Close Button
export const ModalCloseButton = React.forwardRef<View, IModalCloseButtonProps>(
  ({ className = '', ...props }, ref) => {
    const baseClasses = 'group/modal-close-button z-10 rounded data-[focus-visible=true]:web:bg-background-100 web:outline-0 cursor-pointer';
    
    return (
      <Pressable
        ref={ref as any}
        {...props}
        className={`${baseClasses} ${className}`}
      />
    );
  }
);

// Display names
Modal.displayName = 'Modal';
ModalBackdrop.displayName = 'ModalBackdrop';
ModalContent.displayName = 'ModalContent';
ModalHeader.displayName = 'ModalHeader';
ModalBody.displayName = 'ModalBody';
ModalFooter.displayName = 'ModalFooter';
ModalCloseButton.displayName = 'ModalCloseButton';