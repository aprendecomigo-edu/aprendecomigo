/**
 * Learning Insights Card Component
 *
 * Displays personalized learning insights based on session data
 * with achievements, suggestions, milestones, and warnings.
 */

import {
  Lightbulb,
  Trophy,
  Flag,
  AlertTriangle,
  Star,
  TrendingUp,
  BookOpen,
  Clock,
  Target,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  X,
} from 'lucide-react-native';
import React, { useState } from 'react';

import type { LearningInsight } from '@/api/analyticsApi';
import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useAnalytics } from '@/hooks/useAnalytics';

interface LearningInsightsCardProps {
  insights: LearningInsight[];
  onRefresh: () => Promise<void>;
}

/**
 * Get insight icon and styling based on type
 */
function getInsightTypeInfo(type: LearningInsight['type']) {
  switch (type) {
    case 'achievement':
      return {
        icon: Trophy,
        bgColor: 'bg-success-50',
        borderColor: 'border-success-200',
        iconColor: 'text-success-600',
        titleColor: 'text-success-900',
      };
    case 'milestone':
      return {
        icon: Flag,
        bgColor: 'bg-primary-50',
        borderColor: 'border-primary-200',
        iconColor: 'text-primary-600',
        titleColor: 'text-primary-900',
      };
    case 'suggestion':
      return {
        icon: Lightbulb,
        bgColor: 'bg-warning-50',
        borderColor: 'border-warning-200',
        iconColor: 'text-warning-600',
        titleColor: 'text-warning-900',
      };
    case 'warning':
      return {
        icon: AlertTriangle,
        bgColor: 'bg-error-50',
        borderColor: 'border-error-200',
        iconColor: 'text-error-600',
        titleColor: 'text-error-900',
      };
    default:
      return {
        icon: BookOpen,
        bgColor: 'bg-background-50',
        borderColor: 'border-outline-200',
        iconColor: 'text-typography-600',
        titleColor: 'text-typography-900',
      };
  }
}

/**
 * Individual insight item component
 */
function InsightItem({
  insight,
  onMarkRead,
}: {
  insight: LearningInsight;
  onMarkRead: (id: string) => void;
}) {
  const typeInfo = getInsightTypeInfo(insight.type);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleMarkRead = () => {
    if (!insight.is_read) {
      onMarkRead(insight.id);
    }
  };

  return (
    <Card
      className={`p-4 ${typeInfo.bgColor} ${typeInfo.borderColor} ${
        !insight.is_read ? 'ring-2 ring-primary-200' : ''
      }`}
    >
      <VStack space="sm">
        {/* Header */}
        <HStack className="items-start justify-between">
          <HStack space="sm" className="items-start flex-1">
            <Icon as={typeInfo.icon} size="sm" className={typeInfo.iconColor} />
            <VStack space="xs" className="flex-1">
              <HStack space="xs" className="items-center flex-wrap">
                <Text className={`font-medium ${typeInfo.titleColor}`}>{insight.title}</Text>
                {!insight.is_read && (
                  <Badge variant="solid" action="primary" size="xs">
                    <Text className="text-xs">New</Text>
                  </Badge>
                )}
              </HStack>

              {/* Show truncated description if not expanded */}
              <Text className="text-sm text-typography-700">
                {isExpanded
                  ? insight.description
                  : insight.description.length > 100
                  ? `${insight.description.substring(0, 100)}...`
                  : insight.description}
              </Text>

              {/* Expand/Collapse button for long descriptions */}
              {insight.description.length > 100 && (
                <Pressable onPress={() => setIsExpanded(!isExpanded)} className="self-start">
                  <HStack space="xs" className="items-center">
                    <Text className="text-xs text-primary-600 font-medium">
                      {isExpanded ? 'Show less' : 'Show more'}
                    </Text>
                    <Icon
                      as={isExpanded ? ChevronUp : ChevronDown}
                      size="xs"
                      className="text-primary-600"
                    />
                  </HStack>
                </Pressable>
              )}
            </VStack>
          </HStack>

          {/* Mark as read button */}
          {!insight.is_read && (
            <Pressable
              onPress={handleMarkRead}
              className="p-1 rounded-full hover:bg-white/50 active:bg-white/75"
            >
              <Icon as={X} size="xs" className="text-typography-400" />
            </Pressable>
          )}
        </HStack>

        {/* Footer with timestamp and type */}
        <HStack className="items-center justify-between">
          <Text className="text-xs text-typography-500">
            {new Date(insight.created_at).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </Text>

          <Badge
            variant="outline"
            action={
              insight.type === 'achievement'
                ? 'success'
                : insight.type === 'milestone'
                ? 'primary'
                : insight.type === 'warning'
                ? 'error'
                : 'secondary'
            }
            size="xs"
          >
            <Text className="text-xs capitalize">{insight.type}</Text>
          </Badge>
        </HStack>
      </VStack>
    </Card>
  );
}

/**
 * Learning Insights Card Component
 */
export function LearningInsightsCard({ insights, onRefresh }: LearningInsightsCardProps) {
  const { markInsightAsRead, insightsLoading, unreadInsights } = useAnalytics();
  const [showAll, setShowAll] = useState(false);

  const handleMarkRead = async (insightId: string) => {
    await markInsightAsRead(insightId);
  };

  const visibleInsights = showAll ? insights : insights.slice(0, 3);
  const hasMoreInsights = insights.length > 3;

  if (insights.length === 0) {
    return (
      <Card className="p-6">
        <VStack space="md">
          <HStack className="items-center justify-between">
            <VStack space="xs">
              <HStack className="items-center">
                <Icon as={Lightbulb} size="sm" className="text-typography-600 mr-2" />
                <Heading size="md" className="text-typography-900">
                  Learning Insights
                </Heading>
              </HStack>
              <Text className="text-sm text-typography-600">
                Personalized insights based on your learning patterns
              </Text>
            </VStack>

            <Button
              action="secondary"
              variant="outline"
              size="sm"
              onPress={onRefresh}
              disabled={insightsLoading}
            >
              {insightsLoading ? (
                <>
                  <Spinner size="sm" />
                  <ButtonText className="ml-2">Loading...</ButtonText>
                </>
              ) : (
                <>
                  <ButtonIcon as={RefreshCw} />
                  <ButtonText>Refresh</ButtonText>
                </>
              )}
            </Button>
          </HStack>

          <VStack space="md" className="items-center py-8">
            <Icon as={Lightbulb} size="xl" className="text-typography-300" />
            <VStack space="xs" className="items-center">
              <Text className="font-medium text-typography-600">No Insights Yet</Text>
              <Text className="text-sm text-typography-500 text-center max-w-sm">
                Keep attending sessions to unlock personalized learning insights and recommendations
              </Text>
            </VStack>
          </VStack>
        </VStack>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <VStack space="lg">
        {/* Header */}
        <HStack className="items-center justify-between">
          <VStack space="xs">
            <HStack className="items-center">
              <Icon as={Lightbulb} size="sm" className="text-typography-600 mr-2" />
              <Heading size="md" className="text-typography-900">
                Learning Insights
              </Heading>
              {unreadInsights.length > 0 && (
                <Badge variant="solid" action="primary" size="sm">
                  <Text className="text-xs">{unreadInsights.length} new</Text>
                </Badge>
              )}
            </HStack>
            <Text className="text-sm text-typography-600">
              Personalized insights based on your learning patterns
            </Text>
          </VStack>

          <Button
            action="secondary"
            variant="outline"
            size="sm"
            onPress={onRefresh}
            disabled={insightsLoading}
          >
            {insightsLoading ? (
              <>
                <Spinner size="sm" />
                <ButtonText className="ml-2">Loading...</ButtonText>
              </>
            ) : (
              <>
                <ButtonIcon as={RefreshCw} />
                <ButtonText>Refresh</ButtonText>
              </>
            )}
          </Button>
        </HStack>

        {/* Insights List */}
        <VStack space="md">
          {visibleInsights.map(insight => (
            <InsightItem key={insight.id} insight={insight} onMarkRead={handleMarkRead} />
          ))}

          {/* Show More/Less Button */}
          {hasMoreInsights && (
            <Button
              action="secondary"
              variant="outline"
              size="sm"
              onPress={() => setShowAll(!showAll)}
              className="self-center"
            >
              <ButtonIcon as={showAll ? ChevronUp : ChevronDown} />
              <ButtonText>{showAll ? 'Show Less' : `Show ${insights.length - 3} More`}</ButtonText>
            </Button>
          )}
        </VStack>

        {/* Summary Stats */}
        <HStack space="md" className="justify-center pt-4 border-t border-outline-200">
          <VStack space="0" className="items-center">
            <Text className="text-lg font-bold text-success-600">
              {insights.filter(i => i.type === 'achievement').length}
            </Text>
            <Text className="text-xs text-typography-600">Achievements</Text>
          </VStack>

          <VStack space="0" className="items-center">
            <Text className="text-lg font-bold text-primary-600">
              {insights.filter(i => i.type === 'milestone').length}
            </Text>
            <Text className="text-xs text-typography-600">Milestones</Text>
          </VStack>

          <VStack space="0" className="items-center">
            <Text className="text-lg font-bold text-warning-600">
              {insights.filter(i => i.type === 'suggestion').length}
            </Text>
            <Text className="text-xs text-typography-600">Suggestions</Text>
          </VStack>

          {insights.filter(i => i.type === 'warning').length > 0 && (
            <VStack space="0" className="items-center">
              <Text className="text-lg font-bold text-error-600">
                {insights.filter(i => i.type === 'warning').length}
              </Text>
              <Text className="text-xs text-typography-600">Warnings</Text>
            </VStack>
          )}
        </HStack>
      </VStack>
    </Card>
  );
}
