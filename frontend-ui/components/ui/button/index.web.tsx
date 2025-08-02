import { withStyleContext } from '@gluestack-ui/nativewind-utils/withStyleContext';
import { ButtonWrapper, SCOPE, createUIButton, createButtonComponents } from './button-common';

// Web-specific Root component using withStyleContext
const Root = withStyleContext(ButtonWrapper, SCOPE);

// Create UIButton with web-specific Root
const UIButton = createUIButton(Root);

// Create and export all button components
export const { Button, ButtonText, ButtonSpinner, ButtonIcon, ButtonGroup } = createButtonComponents(UIButton);