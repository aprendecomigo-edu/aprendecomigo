/**
 * Platform-aware Modal component that automatically resolves to the appropriate
 * platform-specific implementation:
 * - index.web.tsx for web platforms (uses withStyleContext)
 * - index.native.tsx for iOS/Android platforms (uses withStyleContextAndStates)
 *
 * This file serves as a fallback and should not be used in practice.
 * The platform-specific files will be automatically resolved by React Native.
 */

import { withStyleContext } from '@gluestack-ui/nativewind-utils/withStyleContext';
import { withStyleContextAndStates } from '@gluestack-ui/nativewind-utils/withStyleContextAndStates';
import { Platform, View } from 'react-native';

import { SCOPE, createUIModal, createModalComponents } from './modal-common';

// Fallback implementation (should be overridden by platform-specific files)
const Root =
  Platform.OS === 'web' ? withStyleContext(View, SCOPE) : withStyleContextAndStates(View, SCOPE);

const UIModal = createUIModal(Root);

export const {
  Modal,
  ModalBackdrop,
  ModalContent,
  ModalCloseButton,
  ModalHeader,
  ModalBody,
  ModalFooter,
} = createModalComponents(UIModal);
