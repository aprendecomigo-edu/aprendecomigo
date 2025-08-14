import { withStyleContextAndStates } from '@gluestack-ui/nativewind-utils/withStyleContextAndStates';
import { View } from 'react-native';

import { SCOPE, createUIToast, createToastComponents, useToast } from './toast-common';

// Native-specific Root component using withStyleContextAndStates
const Root = withStyleContextAndStates(View, SCOPE);

// Create UIToast with native-specific Root
const UIToast = createUIToast(Root);

// Create and export all toast components
export const { Toast, ToastTitle, ToastDescription } = createToastComponents(UIToast);

// Re-export useToast hook
export { useToast };
