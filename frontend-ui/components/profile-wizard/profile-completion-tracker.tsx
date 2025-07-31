import React from 'react';
import { CheckCircle2, AlertTriangle, Info } from 'lucide-react-native';

import { Box } from '@/components/ui/box';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Progress } from '@/components/ui/progress';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import {
  Popover,
  PopoverBackdrop,
  PopoverContent,
  PopoverHeader,
  PopoverBody,
} from '@/components/ui/popover';

interface CompletionData {
  completion_percentage: number;
  missing_critical: string[];
  missing_optional: string[];
  is_complete: boolean;
  scores_breakdown?: {
    basic_info: number;
    teaching_details: number;
    professional_info: number;
  };
  recommendations?: Array<{
    text: string;
    priority: 'high' | 'medium' | 'low';
  }>;
}

interface ProfileCompletionTrackerProps {
  completionData?: CompletionData;
  compact?: boolean;
  showDetails?: boolean;
  className?: string;
}

export const ProfileCompletionTracker: React.FC<ProfileCompletionTrackerProps> = ({
  completionData,
  compact = false,
  showDetails = false,
  className = '',
}) => {
  const [showPopover, setShowPopover] = React.useState(false);

  if (!completionData) {
    return null;
  }

  const { 
    completion_percentage, 
    missing_critical, 
    missing_optional, 
    is_complete,
    scores_breakdown,
    recommendations 
  } = completionData;

  const getCompletionColor = () => {
    if (completion_percentage >= 90) return 'text-green-600';
    if (completion_percentage >= 70) return 'text-blue-600';
    if (completion_percentage >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getCompletionBgColor = () => {
    if (completion_percentage >= 90) return 'bg-green-600';
    if (completion_percentage >= 70) return 'bg-blue-600';
    if (completion_percentage >= 50) return 'bg-yellow-600';
    return 'bg-red-600';
  };

  const getCompletionStatus = () => {
    if (is_complete) return 'Complete';
    if (completion_percentage >= 80) return 'Almost Done';
    if (completion_percentage >= 50) return 'In Progress';
    return 'Getting Started';
  };

  const getStatusIcon = () => {
    if (is_complete) return CheckCircle2;
    if (missing_critical.length > 0) return AlertTriangle;
    return Info;
  };

  // Compact version for mobile or inline display
  if (compact) {
    return (
      <Popover
        isOpen={showPopover}
        onClose={() => setShowPopover(false)}
        trigger={(triggerProps) => (
          <Box {...triggerProps} onPress={() => setShowPopover(true)}>
            <HStack space="xs" className={`items-center ${className}`}>
              <Badge 
                className={`${
                  is_complete ? 'bg-green-100' : 
                  completion_percentage >= 70 ? 'bg-blue-100' : 
                  completion_percentage >= 50 ? 'bg-yellow-100' : 'bg-red-100'
                }`}
              >
                <BadgeText className={getCompletionColor()}>
                  {Math.round(completion_percentage)}%
                </BadgeText>
              </Badge>
              <Icon 
                as={getStatusIcon()} 
                size={16} 
                className={getCompletionColor()} 
              />
            </HStack>
          </Box>
        )}
      >
        <PopoverBackdrop />
        <PopoverContent className="w-80">
          <PopoverHeader>
            <Text className="font-semibold text-gray-900">
              Profile Completion
            </Text>
          </PopoverHeader>
          <PopoverBody>
            <VStack space="md">
              {/* Progress Overview */}
              <VStack space="xs">
                <HStack className="items-center justify-between">
                  <Text className="text-sm font-medium text-gray-700">
                    {getCompletionStatus()}
                  </Text>
                  <Text className={`text-sm font-semibold ${getCompletionColor()}`}>
                    {Math.round(completion_percentage)}%
                  </Text>
                </HStack>
                <Progress value={completion_percentage} className="h-2">
                  <Progress.Indicator className={getCompletionBgColor()} />
                </Progress>
              </VStack>

              {/* Missing Critical Fields */}
              {missing_critical.length > 0 && (
                <VStack space="xs">
                  <Text className="text-sm font-medium text-red-700">
                    Required Fields Missing:
                  </Text>
                  {missing_critical.slice(0, 3).map((field, index) => (
                    <Text key={index} className="text-sm text-red-600">
                      • {field}
                    </Text>
                  ))}
                  {missing_critical.length > 3 && (
                    <Text className="text-sm text-red-600">
                      ... and {missing_critical.length - 3} more
                    </Text>
                  )}
                </VStack>
              )}

              {/* Top Recommendation */}
              {recommendations && recommendations.length > 0 && (
                <VStack space="xs">
                  <Text className="text-sm font-medium text-gray-700">
                    Next Step:
                  </Text>
                  <Text className="text-sm text-gray-600">
                    {recommendations[0].text}
                  </Text>
                </VStack>
              )}
            </VStack>
          </PopoverBody>
        </PopoverContent>
      </Popover>
    );
  }

  // Full detailed version
  return (
    <Card className={`${className}`}>
      <VStack space="md" className="p-4">
        {/* Header */}
        <HStack className="items-center justify-between">
          <HStack space="sm" className="items-center">
            <Icon 
              as={getStatusIcon()} 
              size={20} 
              className={getCompletionColor()} 
            />
            <Text className="font-semibold text-gray-900">
              Profile Completion
            </Text>
          </HStack>
          <Badge 
            className={`${
              is_complete ? 'bg-green-100' : 
              completion_percentage >= 70 ? 'bg-blue-100' : 
              completion_percentage >= 50 ? 'bg-yellow-100' : 'bg-red-100'
            }`}
          >
            <BadgeText className={getCompletionColor()}>
              {getCompletionStatus()}
            </BadgeText>
          </Badge>
        </HStack>

        {/* Progress Bar */}
        <VStack space="xs">
          <HStack className="items-center justify-between">
            <Text className="text-sm text-gray-600">
              Overall Progress
            </Text>
            <Text className={`text-sm font-semibold ${getCompletionColor()}`}>
              {Math.round(completion_percentage)}%
            </Text>
          </HStack>
          <Progress value={completion_percentage} className="h-3">
            <Progress.Indicator className={getCompletionBgColor()} />
          </Progress>
        </VStack>

        {/* Detailed Scores Breakdown */}
        {scores_breakdown && showDetails && (
          <VStack space="sm">
            <Text className="text-sm font-medium text-gray-700">
              Section Breakdown:
            </Text>
            {Object.entries(scores_breakdown).map(([section, score]) => (
              <HStack key={section} className="items-center justify-between">
                <Text className="text-sm text-gray-600 capitalize">
                  {section.replace('_', ' ')}
                </Text>
                <HStack space="xs" className="items-center">
                  <Box className="w-16 bg-gray-200 rounded-full h-2">
                    <Box 
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${score}%` }}
                    />
                  </Box>
                  <Text className="text-sm text-gray-600 w-10 text-right">
                    {Math.round(score)}%
                  </Text>
                </HStack>
              </HStack>
            ))}
          </VStack>
        )}

        {/* Missing Critical Fields */}
        {missing_critical.length > 0 && (
          <VStack space="xs" className="p-3 bg-red-50 rounded-lg">
            <HStack space="xs" className="items-center">
              <Icon as={AlertTriangle} size={16} className="text-red-500" />
              <Text className="text-sm font-medium text-red-700">
                Required Fields Missing ({missing_critical.length})
              </Text>
            </HStack>
            <VStack space="xs" className="ml-5">
              {missing_critical.slice(0, showDetails ? undefined : 3).map((field, index) => (
                <Text key={index} className="text-sm text-red-600">
                  • {field}
                </Text>
              ))}
              {!showDetails && missing_critical.length > 3 && (
                <Text className="text-sm text-red-600">
                  ... and {missing_critical.length - 3} more
                </Text>
              )}
            </VStack>
          </VStack>
        )}

        {/* Optional Fields */}
        {missing_optional.length > 0 && showDetails && (
          <VStack space="xs" className="p-3 bg-blue-50 rounded-lg">
            <HStack space="xs" className="items-center">
              <Icon as={Info} size={16} className="text-blue-500" />
              <Text className="text-sm font-medium text-blue-700">
                Optional Fields ({missing_optional.length})
              </Text>
            </HStack>
            <VStack space="xs" className="ml-5">
              {missing_optional.slice(0, 5).map((field, index) => (
                <Text key={index} className="text-sm text-blue-600">
                  • {field}
                </Text>
              ))}
              {missing_optional.length > 5 && (
                <Text className="text-sm text-blue-600">
                  ... and {missing_optional.length - 5} more
                </Text>
              )}
            </VStack>
          </VStack>
        )}

        {/* Recommendations */}
        {recommendations && recommendations.length > 0 && showDetails && (
          <VStack space="xs" className="p-3 bg-green-50 rounded-lg">
            <Text className="text-sm font-medium text-green-700">
              Recommendations:
            </Text>
            <VStack space="xs">
              {recommendations.slice(0, 3).map((rec, index) => (
                <HStack key={index} space="xs" className="items-start">
                  <Icon 
                    as={rec.priority === 'high' ? AlertTriangle : Info} 
                    size={14} 
                    className={`mt-0.5 ${
                      rec.priority === 'high' ? 'text-red-500' : 'text-green-500'
                    }`} 
                  />
                  <Text className="text-sm text-green-600 flex-1">
                    {rec.text}
                  </Text>
                </HStack>
              ))}
            </VStack>
          </VStack>
        )}

        {/* Completion Message */}
        {is_complete && (
          <VStack space="xs" className="p-3 bg-green-50 rounded-lg">
            <HStack space="xs" className="items-center">
              <Icon as={CheckCircle2} size={16} className="text-green-500" />
              <Text className="text-sm font-medium text-green-700">
                Profile Complete!
              </Text>
            </HStack>
            <Text className="text-sm text-green-600">
              Your profile is complete and ready to attract students. Great work!
            </Text>
          </VStack>
        )}
      </VStack>
    </Card>
  );
};