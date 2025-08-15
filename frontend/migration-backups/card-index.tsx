import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React from 'react';
import { View, ViewProps } from 'react-native';

import { cardStyle } from './styles';

// Define styles for CardHeader and CardBody
const cardHeaderStyle = tva({
  base: 'px-4 pt-4 pb-2',
});

const cardBodyStyle = tva({
  base: 'px-4 py-3',
});

type ICardProps = ViewProps & VariantProps<typeof cardStyle> & { className?: string };

const Card = React.forwardRef<React.ElementRef<typeof View>, ICardProps>(
  ({ className, size = 'md', variant = 'elevated', ...props }, ref) => {
    return <View className={cardStyle({ size, variant, class: className })} {...props} ref={ref} />;
  }
);

// CardHeader component
type ICardHeaderProps = ViewProps & { className?: string };

const CardHeader = React.forwardRef<React.ElementRef<typeof View>, ICardHeaderProps>(
  ({ className, ...props }, ref) => {
    return <View className={cardHeaderStyle({ class: className })} {...props} ref={ref} />;
  }
);

// CardBody component
type ICardBodyProps = ViewProps & { className?: string };

const CardBody = React.forwardRef<React.ElementRef<typeof View>, ICardBodyProps>(
  ({ className, ...props }, ref) => {
    return <View className={cardBodyStyle({ class: className })} {...props} ref={ref} />;
  }
);

Card.displayName = 'Card';
CardHeader.displayName = 'CardHeader';
CardBody.displayName = 'CardBody';

export { Card, CardHeader, CardBody };
