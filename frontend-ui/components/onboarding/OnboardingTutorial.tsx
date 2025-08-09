import React from 'react';

import { Box } from '@/components/ui/box';
import { Text } from '@/components/ui/text';

interface OnboardingTutorialProps {
  autoStart?: boolean;
  onComplete?: () => void;
  onSkip?: () => void;
}

export const OnboardingTutorial: React.FC<OnboardingTutorialProps> = ({
  autoStart,
  onComplete,
  onSkip,
}) => {
  // Placeholder implementation
  return (
    <Box className="hidden">
      <Text>Tutorial component placeholder</Text>
    </Box>
  );
};
