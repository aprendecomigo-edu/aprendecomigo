import { withStyleContext } from '@gluestack-ui/nativewind-utils/withStyleContext';
import { View } from 'react-native';
import { SCOPE, createUIToast, createToastComponents, useToast } from './toast-common';

// Web-specific Root component using withStyleContext
const Root = withStyleContext(View, SCOPE);

// Create UIToast with web-specific Root
const UIToast = createUIToast(Root);

// Create and export all toast components
export const { Toast, ToastTitle, ToastDescription } = createToastComponents(UIToast);

// Re-export useToast hook
export { useToast };