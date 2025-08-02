import React, { ReactNode } from 'react';
import { Platform } from 'react-native';

import { Box } from '@/components/ui/box';
import { Pressable } from '@/components/ui/pressable';

interface TutorialHighlightProps {
  children: ReactNode;
  id: string;
  isActive?: boolean;
  onPress?: () => void;
  className?: string;
}

export const TutorialHighlight: React.FC<TutorialHighlightProps> = ({
  children,
  id,
  isActive = false,
  onPress,
  className = '',
}) => {
  const highlightStyles = isActive
    ? {
        shadowColor: '#3B82F6',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
        elevation: 8,
        borderWidth: 2,
        borderColor: '#3B82F6',
      }
    : {};

  const animationStyles = isActive
    ? {
        transform: Platform.OS === 'web' ? 'scale(1.05)' : undefined,
      }
    : {};

  if (onPress) {
    return (
      <Pressable
        onPress={onPress}
        className={`${className} ${
          isActive ? 'bg-blue-50' : ''
        } rounded-lg transition-all duration-200`}
        style={[highlightStyles, animationStyles]}
        testID={`tutorial-highlight-${id}`}
      >
        <Box className="relative">
          {children}
          {isActive && (
            <Box
              className="absolute inset-0 bg-blue-600 opacity-10 rounded-lg pointer-events-none"
              style={{ zIndex: -1 }}
            />
          )}
        </Box>
      </Pressable>
    );
  }

  return (
    <Box
      className={`${className} ${
        isActive ? 'bg-blue-50' : ''
      } rounded-lg transition-all duration-200`}
      style={[highlightStyles, animationStyles]}
      testID={`tutorial-highlight-${id}`}
    >
      <Box className="relative">
        {children}
        {isActive && (
          <Box
            className="absolute inset-0 bg-blue-600 opacity-10 rounded-lg pointer-events-none"
            style={{ zIndex: -1 }}
          />
        )}
      </Box>
    </Box>
  );
};
