import React from 'react';
import { Pressable } from 'react-native';

import {
  isMobile,
  TouchFriendly,
  getResponsiveSpacing,
  getResponsiveTextSize,
} from './ResponsiveContainer';

import { Box } from '@/components/ui/box';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { ChevronRight } from '@/components/ui/icons';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface MobileOptimizedCardProps {
  children?: React.ReactNode;
  title?: string;
  subtitle?: string;
  icon?: React.ComponentType<any>;
  onPress?: () => void;
  showChevron?: boolean;
  variant?: 'elevated' | 'outline' | 'filled';
  size?: 'sm' | 'md' | 'lg';
  touchFeedback?: boolean;
  accessibilityLabel?: string;
  accessibilityHint?: string;
  className?: string;
}

export const MobileOptimizedCard: React.FC<MobileOptimizedCardProps> = ({
  children,
  title,
  subtitle,
  icon: IconComponent,
  onPress,
  showChevron = false,
  variant = 'elevated',
  size = 'md',
  touchFeedback = true,
  accessibilityLabel,
  accessibilityHint,
  className = '',
}) => {
  const getSizeClasses = () => {
    const mobile = isMobile();

    switch (size) {
      case 'sm':
        return {
          padding: mobile ? 'p-3' : 'p-4',
          titleSize: mobile ? 'text-sm' : getResponsiveTextSize('sm'),
          subtitleSize: mobile ? 'text-xs' : getResponsiveTextSize('xs'),
          iconSize: 'sm' as const,
          spacing: 'sm' as const,
        };
      case 'lg':
        return {
          padding: mobile ? 'p-5' : 'p-6',
          titleSize: mobile ? 'text-lg' : getResponsiveTextSize('lg'),
          subtitleSize: mobile ? 'text-sm' : getResponsiveTextSize('sm'),
          iconSize: 'lg' as const,
          spacing: 'lg' as const,
        };
      default: // md
        return {
          padding: mobile ? 'p-4' : 'p-5',
          titleSize: mobile ? 'text-base' : getResponsiveTextSize('md'),
          subtitleSize: mobile ? 'text-sm' : getResponsiveTextSize('sm'),
          iconSize: 'md' as const,
          spacing: 'md' as const,
        };
    }
  };

  const sizeClasses = getSizeClasses();

  const getVariantClasses = () => {
    switch (variant) {
      case 'outline':
        return 'border border-gray-200 bg-white';
      case 'filled':
        return 'bg-gray-50 border border-gray-100';
      default: // elevated
        return 'bg-white shadow-sm border border-gray-100';
    }
  };

  const getPressableClasses = () => {
    if (!onPress) return '';
    return touchFeedback
      ? 'active:bg-gray-50 active:scale-[0.98] transition-all duration-150'
      : 'active:opacity-80';
  };

  const cardContent = (
    <>
      {(title || subtitle || IconComponent) && (
        <CardHeader className={sizeClasses.padding}>
          <HStack space={sizeClasses.spacing} className="items-center">
            {IconComponent && (
              <TouchFriendly minSize="minTouch">
                <Icon as={IconComponent} size={sizeClasses.iconSize} className="text-blue-600" />
              </TouchFriendly>
            )}

            <VStack className="flex-1" space="xs">
              {title && (
                <Heading
                  size={size === 'sm' ? 'sm' : size === 'lg' ? 'lg' : 'md'}
                  className={`${sizeClasses.titleSize} text-gray-900`}
                  numberOfLines={2}
                >
                  {title}
                </Heading>
              )}

              {subtitle && (
                <Text
                  className={`${sizeClasses.subtitleSize} text-gray-600`}
                  numberOfLines={isMobile() ? 2 : 3}
                >
                  {subtitle}
                </Text>
              )}
            </VStack>

            {onPress && showChevron && (
              <TouchFriendly minSize="minTouch">
                <Icon as={ChevronRight} size="sm" className="text-gray-400" />
              </TouchFriendly>
            )}
          </HStack>
        </CardHeader>
      )}

      {children && (
        <CardBody className={title || subtitle ? 'pt-0' : sizeClasses.padding}>{children}</CardBody>
      )}
    </>
  );

  const cardClasses = `w-full ${getVariantClasses()} rounded-lg overflow-hidden ${className}`;

  if (onPress) {
    return (
      <Pressable
        onPress={onPress}
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel || title}
        accessibilityHint={accessibilityHint}
        className={`${getPressableClasses()}`}
      >
        <Card className={cardClasses}>{cardContent}</Card>
      </Pressable>
    );
  }

  return <Card className={cardClasses}>{cardContent}</Card>;
};

// Specialized card for list items
interface MobileListCardProps extends Omit<MobileOptimizedCardProps, 'children'> {
  primaryText: string;
  secondaryText?: string;
  tertiaryText?: string;
  rightElement?: React.ReactNode;
  avatar?: React.ReactNode;
  badge?: React.ReactNode;
  divider?: boolean;
}

export const MobileListCard: React.FC<MobileListCardProps> = ({
  primaryText,
  secondaryText,
  tertiaryText,
  rightElement,
  avatar,
  badge,
  divider = false,
  icon: IconComponent,
  onPress,
  touchFeedback = true,
  accessibilityLabel,
  accessibilityHint,
  className = '',
  ...props
}) => {
  const mobile = isMobile();
  const minTouchHeight = mobile ? 'min-h-[56px]' : 'min-h-[48px]';

  const content = (
    <Box className={`${minTouchHeight} px-4 py-3 ${className}`}>
      <HStack space="md" className="items-center h-full">
        {/* Left side - Avatar or Icon */}
        {(avatar || IconComponent) && (
          <Box className="flex-shrink-0">
            {avatar ||
              (IconComponent && (
                <TouchFriendly minSize="minTouch">
                  <Icon as={IconComponent} size="md" className="text-blue-600" />
                </TouchFriendly>
              ))}
          </Box>
        )}

        {/* Content */}
        <VStack className="flex-1" space="xs">
          <HStack className="justify-between items-start">
            <Text
              className={`font-medium ${getResponsiveTextSize('md')} text-gray-900 flex-1`}
              numberOfLines={1}
            >
              {primaryText}
            </Text>

            {badge && <Box className="ml-2 flex-shrink-0">{badge}</Box>}
          </HStack>

          {secondaryText && (
            <Text
              className={`${getResponsiveTextSize('sm')} text-gray-600`}
              numberOfLines={mobile ? 1 : 2}
            >
              {secondaryText}
            </Text>
          )}

          {tertiaryText && (
            <Text className={`${getResponsiveTextSize('xs')} text-gray-500`} numberOfLines={1}>
              {tertiaryText}
            </Text>
          )}
        </VStack>

        {/* Right side element */}
        {rightElement && <Box className="flex-shrink-0 ml-2">{rightElement}</Box>}

        {/* Chevron for pressable items */}
        {onPress && !rightElement && (
          <TouchFriendly minSize="minTouch">
            <Icon as={ChevronRight} size="sm" className="text-gray-400" />
          </TouchFriendly>
        )}
      </HStack>

      {/* Divider */}
      {divider && <Box className="absolute bottom-0 left-16 right-4 h-px bg-gray-200" />}
    </Box>
  );

  if (onPress) {
    return (
      <Pressable
        onPress={onPress}
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel || primaryText}
        accessibilityHint={accessibilityHint}
        className={
          touchFeedback ? 'active:bg-gray-50 transition-colors duration-150' : 'active:opacity-80'
        }
      >
        {content}
      </Pressable>
    );
  }

  return content;
};

export default MobileOptimizedCard;
