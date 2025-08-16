import { cn } from '@gluestack-ui/nativewind-utils/cn';
import React from 'react';

import { Box } from '@/components/ui/box';
import { Text } from '@/components/ui/text';
import type { NotificationBadgeProps } from '@/types/navigation';

/**
 * NotificationBadge component - displays notification counts with customizable styling
 * Supports different types, sizes, and display modes
 */
export const NotificationBadge: React.FC<NotificationBadgeProps> = ({
  count,
  type = 'primary',
  size = 'md',
  showZero = false,
  maxCount = 99,
  className = '',
}) => {
  // Don't render if count is 0 and showZero is false
  if (count === 0 && !showZero) {
    return null;
  }

  // Format count display
  const displayCount = count > maxCount ? `${maxCount}+` : count.toString();

  // Size classes
  const sizeClasses = {
    sm: 'h-4 w-4 min-w-[16px]',
    md: 'h-5 w-5 min-w-[20px]',
    lg: 'h-6 w-6 min-w-[24px]',
  };

  // Text size classes
  const textSizeClasses = {
    sm: 'text-[10px]',
    md: 'text-[11px]',
    lg: 'text-[12px]',
  };

  // Type color classes
  const typeClasses = {
    primary: 'bg-primary-500',
    warning: 'bg-warning-500',
    error: 'bg-error-500',
    success: 'bg-success-500',
  };

  return (
    <Box
      className={cn(
        'absolute -top-1 -right-1 rounded-full flex items-center justify-center',
        sizeClasses[size],
        typeClasses[type],
        className,
      )}
    >
      <Text
        className={cn('font-semibold text-white text-center leading-none', textSizeClasses[size])}
      >
        {displayCount}
      </Text>
    </Box>
  );
};

/**
 * NotificationDot component - simple dot indicator for notifications
 */
export const NotificationDot: React.FC<{
  type?: NotificationBadgeProps['type'];
  size?: NotificationBadgeProps['size'];
  className?: string;
}> = ({ type = 'primary', size = 'md', className = '' }) => {
  const sizeClasses = {
    sm: 'h-2 w-2',
    md: 'h-3 w-3',
    lg: 'h-4 w-4',
  };

  const typeClasses = {
    primary: 'bg-primary-500',
    warning: 'bg-warning-500',
    error: 'bg-error-500',
    success: 'bg-success-500',
  };

  return (
    <Box
      className={cn(
        'absolute -top-1 -right-1 rounded-full',
        sizeClasses[size],
        typeClasses[type],
        className,
      )}
    />
  );
};

export default NotificationBadge;
