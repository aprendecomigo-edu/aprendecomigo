/**
 * Platform-aware Button component that automatically resolves to the appropriate
 * platform-specific implementation:
 * - index.web.tsx for web platforms (uses withStyleContext)
 * - index.native.tsx for iOS/Android platforms (uses withStyleContextAndStates)
 * 
 * This file serves as a fallback and should not be used in practice.
 * The platform-specific files will be automatically resolved by React Native.
 */

import { Platform } from 'react-native';
import { withStyleContext } from '@gluestack-ui/nativewind-utils/withStyleContext';
import { withStyleContextAndStates } from '@gluestack-ui/nativewind-utils/withStyleContextAndStates';
import { ButtonWrapper, SCOPE, createUIButton, createButtonComponents } from './button-common';

// Fallback implementation (should be overridden by platform-specific files)
const Root = Platform.OS === 'web'
  ? withStyleContext(ButtonWrapper, SCOPE)
  : withStyleContextAndStates(ButtonWrapper, SCOPE);

const UIButton = createUIButton(Root);

export const { Button, ButtonText, ButtonSpinner, ButtonIcon, ButtonGroup } = createButtonComponents(UIButton);