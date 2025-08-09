import { withStyleContext } from '@gluestack-ui/nativewind-utils/withStyleContext';
import { View } from 'react-native';

import { SCOPE, createUIModal, createModalComponents } from './modal-common';

// Web-specific Root component using withStyleContext
const Root = withStyleContext(View, SCOPE);

// Create UIModal with web-specific Root
const UIModal = createUIModal(Root);

// Create and export all modal components
export const {
  Modal,
  ModalBackdrop,
  ModalContent,
  ModalCloseButton,
  ModalHeader,
  ModalBody,
  ModalFooter,
} = createModalComponents(UIModal);
