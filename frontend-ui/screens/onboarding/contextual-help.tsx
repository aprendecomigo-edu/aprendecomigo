import { HelpCircle, X, Info, AlertCircle, CheckCircle2, ExternalLink } from 'lucide-react-native';
import React, { useState, useEffect } from 'react';
import { Platform, Dimensions } from 'react-native';

import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import {
  Popover,
  PopoverBackdrop,
  PopoverContent,
  PopoverArrow,
  PopoverHeader,
  PopoverCloseButton,
  PopoverBody,
  PopoverFooter,
} from '@/components/ui/popover';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

const { width: screenWidth } = Dimensions.get('window');
const isMobile = Platform.OS !== 'web' || screenWidth < 768;

export interface HelpTip {
  id: string;
  title: string;
  content: string;
  type: 'info' | 'warning' | 'success' | 'tip';
  priority: 'low' | 'medium' | 'high';
  action?: {
    label: string;
    onPress: () => void;
  };
  dismissible?: boolean;
  persistent?: boolean;
}

interface ContextualHelpProps {
  tips: HelpTip[];
  position?: 'top' | 'bottom' | 'left' | 'right';
  trigger?: React.ReactNode;
  showBadge?: boolean;
  maxTips?: number;
  className?: string;
}

export const ContextualHelp: React.FC<ContextualHelpProps> = ({
  tips = [],
  position = 'bottom',
  trigger,
  showBadge = true,
  maxTips = 3,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [dismissedTips, setDismissedTips] = useState<string[]>([]);
  const [activeTips, setActiveTips] = useState<HelpTip[]>([]);

  // Filter and sort tips by priority
  useEffect(() => {
    const filteredTips = tips
      .filter(tip => !dismissedTips.includes(tip.id))
      .sort((a, b) => {
        const priorityOrder = { high: 3, medium: 2, low: 1 };
        return priorityOrder[b.priority] - priorityOrder[a.priority];
      })
      .slice(0, maxTips);

    setActiveTips(filteredTips);
  }, [tips, dismissedTips, maxTips]);

  const handleDismissTip = (tipId: string) => {
    setDismissedTips(prev => [...prev, tipId]);
  };

  const getTipIcon = (type: HelpTip['type']) => {
    switch (type) {
      case 'info':
        return <Icon as={Info} size={16} className="text-blue-500" />;
      case 'warning':
        return <Icon as={AlertCircle} size={16} className="text-yellow-500" />;
      case 'success':
        return <Icon as={CheckCircle2} size={16} className="text-green-500" />;
      case 'tip':
      default:
        return <Icon as={HelpCircle} size={16} className="text-purple-500" />;
    }
  };

  const getTipCardStyle = (type: HelpTip['type']) => {
    switch (type) {
      case 'info':
        return 'bg-blue-50 border-blue-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      case 'success':
        return 'bg-green-50 border-green-200';
      case 'tip':
      default:
        return 'bg-purple-50 border-purple-200';
    }
  };

  const defaultTrigger = (
    <Button
      variant="outline"
      size="sm"
      onPress={() => setIsOpen(true)}
      className={`border-blue-300 ${className}`}
    >
      <ButtonIcon as={HelpCircle} className="text-blue-600" />
      {!isMobile && <ButtonText className="text-blue-600 ml-2">Help</ButtonText>}
      {showBadge && activeTips.length > 0 && (
        <Badge className="bg-red-500 ml-2 min-w-5 h-5">
          <BadgeText className="text-white text-xs">{activeTips.length}</BadgeText>
        </Badge>
      )}
    </Button>
  );

  if (activeTips.length === 0) {
    return null;
  }

  return (
    <Popover isOpen={isOpen} onClose={() => setIsOpen(false)} placement={position}>
      {trigger || defaultTrigger}
      <PopoverBackdrop />
      <PopoverContent className={`${isMobile ? 'w-80' : 'w-96'} max-w-sm`}>
        <PopoverArrow />
        <PopoverHeader>
          <HStack className="items-center justify-between">
            <Heading size="md" className="text-gray-900">
              Helpful Tips
            </Heading>
            <PopoverCloseButton />
          </HStack>
        </PopoverHeader>

        <PopoverBody>
          <VStack space="md">
            {activeTips.map((tip, index) => (
              <Card key={tip.id} className={`${getTipCardStyle(tip.type)} border`}>
                <VStack space="sm" className="p-4">
                  {/* Tip Header */}
                  <HStack className="items-start justify-between">
                    <HStack space="sm" className="items-start flex-1">
                      {getTipIcon(tip.type)}
                      <VStack className="flex-1" space="xs">
                        <Text className="font-medium text-gray-900 text-sm">{tip.title}</Text>
                        <Text className="text-gray-700 text-sm">{tip.content}</Text>
                      </VStack>
                    </HStack>

                    {tip.dismissible !== false && (
                      <Button
                        variant="link"
                        size="sm"
                        onPress={() => handleDismissTip(tip.id)}
                        className="p-1 -mt-1 -mr-1"
                      >
                        <ButtonIcon as={X} size={14} className="text-gray-400" />
                      </Button>
                    )}
                  </HStack>

                  {/* Tip Action */}
                  {tip.action && (
                    <>
                      <Divider className="my-2" />
                      <Button
                        size="sm"
                        onPress={tip.action.onPress}
                        className="bg-white border border-gray-300 hover:bg-gray-50"
                      >
                        <ButtonText className="text-gray-700">{tip.action.label}</ButtonText>
                        <ButtonIcon as={ExternalLink} size={14} className="text-gray-500 ml-1" />
                      </Button>
                    </>
                  )}
                </VStack>
              </Card>
            ))}

            {/* Summary for dismissed tips */}
            {dismissedTips.length > 0 && (
              <Card className="bg-gray-50 border-gray-200">
                <HStack space="sm" className="p-3 items-center">
                  <Icon as={CheckCircle2} size={16} className="text-gray-500" />
                  <Text className="text-gray-600 text-sm flex-1">
                    {dismissedTips.length} tip{dismissedTips.length !== 1 ? 's' : ''} dismissed
                  </Text>
                  <Button variant="link" size="sm" onPress={() => setDismissedTips([])}>
                    <ButtonText className="text-blue-600 text-xs">Show all</ButtonText>
                  </Button>
                </HStack>
              </Card>
            )}
          </VStack>
        </PopoverBody>

        {activeTips.length > maxTips && (
          <PopoverFooter>
            <Text className="text-center text-gray-500 text-xs">
              Showing {maxTips} of {tips.length} tips
            </Text>
          </PopoverFooter>
        )}
      </PopoverContent>
    </Popover>
  );
};

// Hook for managing contextual help tips
export function useContextualHelp(contextId: string) {
  const [tips, setTips] = useState<HelpTip[]>([]);

  const addTip = (tip: HelpTip) => {
    setTips(prev => {
      const existing = prev.find(t => t.id === tip.id);
      if (existing) {
        return prev.map(t => (t.id === tip.id ? tip : t));
      }
      return [...prev, tip];
    });
  };

  const removeTip = (tipId: string) => {
    setTips(prev => prev.filter(tip => tip.id !== tipId));
  };

  const clearTips = () => {
    setTips([]);
  };

  const updateTip = (tipId: string, updates: Partial<HelpTip>) => {
    setTips(prev => prev.map(tip => (tip.id === tipId ? { ...tip, ...updates } : tip)));
  };

  return {
    tips,
    addTip,
    removeTip,
    clearTips,
    updateTip,
  };
}

// Predefined onboarding help tips
export const ONBOARDING_HELP_TIPS: Record<string, HelpTip[]> = {
  welcome: [
    {
      id: 'welcome-start',
      title: 'Welcome to your onboarding journey',
      content:
        'Take your time to complete each step. You can always skip steps and return to them later.',
      type: 'tip',
      priority: 'high',
      dismissible: true,
    },
    {
      id: 'welcome-help',
      title: 'Need assistance?',
      content:
        'Look for help icons throughout the platform. Our support team is here to help you succeed.',
      type: 'info',
      priority: 'medium',
      dismissible: true,
    },
  ],

  checklist: [
    {
      id: 'checklist-order',
      title: 'Recommended step order',
      content:
        'While you can complete steps in any order, we recommend starting with your school profile and then inviting teachers.',
      type: 'tip',
      priority: 'high',
      dismissible: true,
    },
    {
      id: 'checklist-skip',
      title: 'Skipping steps',
      content:
        'Skipped steps can be completed anytime from your dashboard. Your progress is always saved.',
      type: 'info',
      priority: 'medium',
      dismissible: true,
    },
    {
      id: 'checklist-progress',
      title: 'Track your progress',
      content:
        'The progress bar shows your completion status. Each completed step unlocks more platform features.',
      type: 'success',
      priority: 'low',
      dismissible: true,
    },
  ],

  teacher_invitation: [
    {
      id: 'teacher-email',
      title: 'Valid email required',
      content:
        "Make sure to use the teacher's primary email address. They'll need access to accept the invitation.",
      type: 'warning',
      priority: 'high',
      dismissible: false,
    },
    {
      id: 'teacher-role',
      title: 'Choose the right role',
      content:
        'Teacher roles determine platform permissions. You can always update roles later from the dashboard.',
      type: 'info',
      priority: 'medium',
      dismissible: true,
    },
  ],

  student_management: [
    {
      id: 'student-bulk',
      title: 'Bulk import available',
      content:
        'Need to add many students? Use the bulk import feature to upload a CSV file with student information.',
      type: 'tip',
      priority: 'medium',
      dismissible: true,
      action: {
        label: 'Learn more about bulk import',
        onPress: () => console.log('Navigate to bulk import help'),
      },
    },
    {
      id: 'student-parent',
      title: 'Parent information',
      content:
        "Adding parent contact information enables automatic updates about their child's progress and scheduling.",
      type: 'info',
      priority: 'low',
      dismissible: true,
    },
  ],
};
