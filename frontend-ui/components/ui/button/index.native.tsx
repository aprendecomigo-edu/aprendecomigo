import { withStyleContextAndStates } from '@gluestack-ui/nativewind-utils/withStyleContextAndStates';
import { ButtonWrapper, SCOPE, createUIButton, createButtonComponents } from './button-common';

// Native-specific Root component using withStyleContextAndStates
const Root = withStyleContextAndStates(ButtonWrapper, SCOPE);

// Create UIButton with native-specific Root
const UIButton = createUIButton(Root);

// Create and export all button components
export const { Button, ButtonText, ButtonSpinner, ButtonIcon, ButtonGroup } = createButtonComponents(UIButton);