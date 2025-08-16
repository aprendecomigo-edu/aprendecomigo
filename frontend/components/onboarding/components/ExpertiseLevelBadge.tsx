import { Star } from 'lucide-react-native';
import React from 'react';

import { Badge, BadgeText } from '@/components/ui/badge';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';

interface ExpertiseLevelBadgeProps {
  level: string;
}

export const ExpertiseLevelBadge: React.FC<ExpertiseLevelBadgeProps> = ({ level }) => {
  const getExpertiseColor = (level: string) => {
    switch (level) {
      case 'expert':
        return 'bg-purple-100 text-purple-700';
      case 'advanced':
        return 'bg-blue-100 text-blue-700';
      case 'intermediate':
        return 'bg-green-100 text-green-700';
      case 'beginner':
        return 'bg-gray-100 text-gray-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getExpertiseIcon = (level: string) => {
    switch (level) {
      case 'expert':
        return 4;
      case 'advanced':
        return 3;
      case 'intermediate':
        return 2;
      case 'beginner':
        return 1;
      default:
        return 1;
    }
  };

  const stars = getExpertiseIcon(level);

  return (
    <Badge className={getExpertiseColor(level)}>
      <HStack space="xs" className="items-center">
        <HStack space="0">
          {Array.from({ length: stars }).map((_, i) => (
            <Icon key={i} as={Star} className="text-current" size="xs" />
          ))}
        </HStack>
        <BadgeText className="text-xs capitalize">{level}</BadgeText>
      </HStack>
    </Badge>
  );
};
