import React from 'react';

import { Box } from '../box';
import { HStack } from '../hstack';
import { Icon } from '../icon';
import { Pressable } from '../pressable';
import { Text } from '../text';

export interface TabItem {
  id: string;
  label: string;
  icon?: React.ComponentType<any>;
}

export interface TabsProps {
  items: TabItem[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  className?: string;
  tabClassName?: string;
  activeTabClassName?: string;
}

export const Tabs: React.FC<TabsProps> = ({
  items,
  activeTab,
  onTabChange,
  className = '',
  tabClassName = '',
  activeTabClassName = '',
}) => {
  return (
    <Box className={`glass-nav rounded-2xl p-2 ${className}`}>
      <HStack space="xs">
        {items.map(item => {
          const isActive = item.id === activeTab;
          const IconComponent = item.icon;

          return (
            <Pressable
              key={item.id}
              onPress={() => onTabChange(item.id)}
              className={`
                flex-1 rounded-xl px-4 py-3 items-center justify-center
                ${
                  isActive
                    ? `bg-primary-600 shadow-sm ${activeTabClassName}`
                    : `bg-transparent ${tabClassName}`
                }
              `}
              accessibilityRole="tab"
              accessibilityState={{ selected: isActive }}
              accessibilityLabel={`${item.label} tab`}
            >
              <HStack space="sm" className="items-center">
                {IconComponent && (
                  <Icon
                    as={IconComponent}
                    size="sm"
                    className={isActive ? 'text-white' : 'text-typography-600'}
                  />
                )}
                <Text
                  className={`
                    font-primary font-medium text-sm
                    ${isActive ? 'text-white' : 'text-typography-700'}
                  `}
                >
                  {item.label}
                </Text>
              </HStack>
            </Pressable>
          );
        })}
      </HStack>
    </Box>
  );
};

export default Tabs;
