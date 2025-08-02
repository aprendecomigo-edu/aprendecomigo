import { withStyleContext } from '@gluestack-ui/nativewind-utils/withStyleContext';
import { View } from 'react-native';
import { SCOPE, createUITooltip, createTooltipComponents } from './tooltip-common';

// Web-specific Root component using withStyleContext
const Root = withStyleContext(View, SCOPE);

// Create UITooltip with web-specific Root
const UITooltip = createUITooltip(Root);

// Create and export all tooltip components
export const { Tooltip, TooltipContent, TooltipText } = createTooltipComponents(UITooltip);