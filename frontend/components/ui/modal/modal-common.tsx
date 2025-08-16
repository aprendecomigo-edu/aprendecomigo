'use client';
import { createModal } from '@gluestack-ui/modal';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import { useStyleContext } from '@gluestack-ui/nativewind-utils/withStyleContext';
import { cssInterop } from 'nativewind';
import React from 'react';
import { Pressable, View, ScrollView } from 'react-native';
import Animated, { FadeIn, FadeOut } from 'react-native-reanimated';

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

export const SCOPE = 'MODAL';

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

// Common function to create UIModal with platform-specific Root
export function createUIModal(Root: React.ComponentType<any>) {
  const UIModal = createModal({
    Root: Root,
    Backdrop: AnimatedPressable,
    Content: Animated.View,
    Body: ScrollView,
    CloseButton: Pressable,
    Footer: View,
    Header: View,
  });

  cssInterop(UIModal, { className: 'style' });
  cssInterop(UIModal.Backdrop, { className: 'style' });
  cssInterop(UIModal.Content, { className: 'style' });
  cssInterop(UIModal.CloseButton, { className: 'style' });
  cssInterop(UIModal.Header, { className: 'style' });
  cssInterop(UIModal.Body, {
    className: 'style',
    contentContainerClassName: 'contentContainerStyle',
    indicatorClassName: 'indicatorStyle',
  });
  cssInterop(UIModal.Footer, { className: 'style' });

  return UIModal;
}

export type IModalProps = React.ComponentProps<any> &
  VariantProps<typeof modalStyle> & { className?: string };

export type IModalBackdropProps = React.ComponentProps<any> &
  VariantProps<typeof modalBackdropStyle> & { className?: string };

export type IModalContentProps = React.ComponentProps<any> &
  VariantProps<typeof modalContentStyle> & { className?: string };

export type IModalHeaderProps = React.ComponentProps<any> &
  VariantProps<typeof modalHeaderStyle> & { className?: string };

export type IModalBodyProps = React.ComponentProps<any> &
  VariantProps<typeof modalBodyStyle> & { className?: string };

export type IModalFooterProps = React.ComponentProps<any> &
  VariantProps<typeof modalFooterStyle> & { className?: string };

export type IModalCloseButtonProps = React.ComponentProps<any> &
  VariantProps<typeof modalCloseButtonStyle> & { className?: string };

// Common function to create Modal components
export function createModalComponents(UIModal: any) {
  const Modal = React.forwardRef<React.ElementRef<typeof UIModal>, IModalProps>(
    ({ className, size = 'md', ...props }, ref) => (
      <UIModal
        ref={ref}
        {...props}
        pointerEvents="box-none"
        className={modalStyle({ size, class: className })}
        context={{ size }}
      />
    ),
  );

  const ModalBackdrop = React.forwardRef<
    React.ElementRef<typeof UIModal.Backdrop>,
    IModalBackdropProps
  >(({ className, ...props }, ref) => {
    return (
      <UIModal.Backdrop
        ref={ref}
        entering={FadeIn.duration(250)}
        exiting={FadeOut.duration(250)}
        {...props}
        className={modalBackdropStyle({
          class: className,
        })}
      />
    );
  });

  const ModalContent = React.forwardRef<
    React.ElementRef<typeof UIModal.Content>,
    IModalContentProps
  >(({ className, size, ...props }, ref) => {
    const { size: parentSize } = useStyleContext(SCOPE);

    return (
      <UIModal.Content
        ref={ref}
        entering={FadeIn.duration(250).springify().damping(18).stiffness(250)}
        exiting={FadeOut.duration(250)}
        {...props}
        className={modalContentStyle({
          parentVariants: {
            size: parentSize,
          },
          size,
          class: className,
        })}
        pointerEvents="auto"
      />
    );
  });

  const ModalHeader = React.forwardRef<React.ElementRef<typeof UIModal.Header>, IModalHeaderProps>(
    ({ className, ...props }, ref) => {
      return (
        <UIModal.Header
          ref={ref}
          {...props}
          className={modalHeaderStyle({
            class: className,
          })}
        />
      );
    },
  );

  const ModalBody = React.forwardRef<React.ElementRef<typeof UIModal.Body>, IModalBodyProps>(
    ({ className, ...props }, ref) => {
      return (
        <UIModal.Body
          ref={ref}
          {...props}
          className={modalBodyStyle({
            class: className,
          })}
        />
      );
    },
  );

  const ModalFooter = React.forwardRef<React.ElementRef<typeof UIModal.Footer>, IModalFooterProps>(
    ({ className, ...props }, ref) => {
      return (
        <UIModal.Footer
          ref={ref}
          {...props}
          className={modalFooterStyle({
            class: className,
          })}
        />
      );
    },
  );

  const ModalCloseButton = React.forwardRef<
    React.ElementRef<typeof UIModal.CloseButton>,
    IModalCloseButtonProps
  >(({ className, ...props }, ref) => {
    return (
      <UIModal.CloseButton
        ref={ref}
        {...props}
        className={modalCloseButtonStyle({
          class: className,
        })}
      />
    );
  });

  // Assign display names
  Modal.displayName = 'Modal';
  ModalBackdrop.displayName = 'ModalBackdrop';
  ModalContent.displayName = 'ModalContent';
  ModalHeader.displayName = 'ModalHeader';
  ModalBody.displayName = 'ModalBody';
  ModalFooter.displayName = 'ModalFooter';
  ModalCloseButton.displayName = 'ModalCloseButton';

  return {
    Modal,
    ModalBackdrop,
    ModalContent,
    ModalCloseButton,
    ModalHeader,
    ModalBody,
    ModalFooter,
  };
}
