import React, { memo, useCallback } from 'react';

import { Button, ButtonText } from '@/components/ui/button';
import { HStack } from '@/components/ui/hstack';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

import type { SectionKey } from '../types';
import { SECTIONS } from '../constants';

interface SectionNavigationProps {
  activeSection: SectionKey;
  onSectionChange: (section: SectionKey) => void;
}

export const SectionNavigation = memo<SectionNavigationProps>(({ 
  activeSection, 
  onSectionChange 
}) => {
  const handleSectionChange = useCallback((sectionKey: SectionKey) => {
    onSectionChange(sectionKey);
  }, [onSectionChange]);

  return (
    <VStack space="sm" className="mb-4">
      <Text size="sm" className="text-typography-600 font-medium">
        Configuration Sections
      </Text>
      <HStack space="sm" flexWrap="wrap">
        {SECTIONS.map(section => (
          <Button
            key={section.key}
            size="sm"
            variant={activeSection === section.key ? 'solid' : 'outline'}
            action={activeSection === section.key ? 'primary' : 'secondary'}
            onPress={() => handleSectionChange(section.key)}
            className="mb-2"
          >
            <ButtonText size="sm">{section.label}</ButtonText>
          </Button>
        ))}
      </HStack>
    </VStack>
  );
});

SectionNavigation.displayName = 'SectionNavigation';