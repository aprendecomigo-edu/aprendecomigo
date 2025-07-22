import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import React from 'react';

import { boxStyle } from './styles';

type IBoxProps = React.ComponentPropsWithoutRef<'div'> &
  VariantProps<typeof boxStyle> & { className?: string };

const Box = React.forwardRef<HTMLDivElement, IBoxProps>(({ className, testID, ...props }, ref) => {
  return <div ref={ref} className={boxStyle({ class: className })} data-testid={testID} {...props} />;
});

Box.displayName = 'Box';
export { Box };
