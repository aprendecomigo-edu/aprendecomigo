import { withStyleContextAndStates } from '@gluestack-ui/nativewind-utils/withStyleContextAndStates';
import { View } from 'react-native';
import { SCOPE, createUITooltip, createTooltipComponents } from './tooltip-common';

// Native-specific Root component using withStyleContextAndStates
const Root = withStyleContextAndStates(View, SCOPE);

// Create UITooltip with native-specific Root
const UITooltip = createUITooltip(Root);

// Create and export all tooltip components
export const { Tooltip, TooltipContent, TooltipText } = createTooltipComponents(UITooltip);