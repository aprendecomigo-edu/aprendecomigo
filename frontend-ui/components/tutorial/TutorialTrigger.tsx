import { HelpCircle, Play } from 'lucide-react-native';
import React from 'react';

import { Button, ButtonIcon, ButtonText } from '@/components/ui/button';
import { Pressable } from '@/components/ui/pressable';
import { Icon } from '@/components/ui/icon';

import { useTutorial } from './TutorialContext';
import { TutorialConfig } from './types';

interface TutorialTriggerProps {
  config: TutorialConfig;
  variant?: 'button' | 'icon' | 'text';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  children?: React.ReactNode;
}

export const TutorialTrigger: React.FC<TutorialTriggerProps> = ({
  config,
  variant = 'button',
  size = 'md',
  className = '',
  children,
}) => {
  const { startTutorial, isTutorialCompleted, isTutorialSkipped } = useTutorial();

  const handlePress = () => {
    startTutorial(config);
  };

  const isCompleted = isTutorialCompleted(config.id);
  const isSkipped = isTutorialSkipped(config.id);

  if (variant === 'icon') {
    return (
      <Pressable
        onPress={handlePress}
        className={`p-2 rounded-full ${isCompleted ? 'bg-green-100' : 'bg-blue-100'} ${className}`}
      >
        <Icon
          as={isCompleted ? HelpCircle : Play}
          size={size}
          className={isCompleted ? 'text-green-600' : 'text-blue-600'}
        />
      </Pressable>
    );
  }

  if (variant === 'text') {
    return (
      <Pressable onPress={handlePress} className={className}>
        {children || (
          <ButtonText className={`${isCompleted ? 'text-green-600' : 'text-blue-600'} underline`}>
            {isCompleted ? 'Repetir tutorial' : 'Iniciar tutorial'}
          </ButtonText>
        )}
      </Pressable>
    );
  }

  return (
    <Button
      variant={isCompleted ? 'outline' : 'solid'}
      size={size}
      onPress={handlePress}
      className={`${
        isCompleted
          ? 'border-green-600 bg-green-50'
          : 'bg-blue-600'
      } ${className}`}
    >
      <ButtonIcon
        as={isCompleted ? HelpCircle : Play}
        size="sm"
        className={isCompleted ? 'text-green-600' : 'text-white'}
      />
      <ButtonText className={isCompleted ? 'text-green-600' : 'text-white'}>
        {children || (isCompleted ? 'Repetir tutorial' : 'Iniciar tutorial')}
      </ButtonText>
    </Button>
  );
};
