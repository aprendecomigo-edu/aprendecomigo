import { withStyleContextAndStates } from '@gluestack-ui/nativewind-utils/withStyleContextAndStates';
import { View } from 'react-native';

import { SCOPE, createUIModal, createModalComponents } from './modal-common';

// Native-specific Root component using withStyleContextAndStates
const Root = withStyleContextAndStates(View, SCOPE);

// Create UIModal with native-specific Root
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
