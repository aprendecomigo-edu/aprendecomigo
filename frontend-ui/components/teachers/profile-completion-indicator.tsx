import React from 'react';
import { AlertCircle, CheckCircle, Clock, Info } from 'lucide-react-native';

import { Box } from '@/components/ui/box';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tooltip } from '@/components/ui/tooltip';
import { Pressable } from '@/components/ui/pressable';

interface ProfileCompletionIndicatorProps {
  completionPercentage: number;
  isComplete: boolean;
  missingCritical?: string[];
  missingOptional?: string[];
  recommendations?: Array<{
    text: string;
    priority: 'high' | 'medium' | 'low';
  }>;
  size?: 'sm' | 'md' | 'lg';
  showDetails?: boolean;
  variant?: 'minimal' | 'detailed' | 'compact';
  onViewDetails?: () => void;
}

// Color constants for consistency
const COLORS = {
  success: '#16A34A',    // green-600
  warning: '#D97706',    // amber-600
  danger: '#DC2626',     // red-600
  info: '#2563EB',       // blue-600
  gray: {
    100: '#F3F4F6',
    300: '#D1D5DB',
    500: '#6B7280',
    700: '#374151',
    900: '#111827',
  }
};

const getCompletionStatus = (percentage: number, isComplete: boolean, hasCritical: boolean) => {
  if (hasCritical || percentage < 30) {
    return {
      status: 'critical' as const,
      color: COLORS.danger,
      icon: AlertCircle,
      label: 'Crítico',
      bgColor: '#FEF2F2' // red-50
    };
  } else if (isComplete && percentage >= 80) {
    return {
      status: 'complete' as const,
      color: COLORS.success,
      icon: CheckCircle,
      label: 'Completo',
      bgColor: '#F0FDF4' // green-50
    };
  } else {
    return {
      status: 'incomplete' as const,
      color: COLORS.warning,
      icon: Clock,
      label: 'Incompleto',
      bgColor: '#FFFBEB' // amber-50
    };
  }
};

const getProgressBarColor = (percentage: number, hasCritical: boolean) => {
  if (hasCritical || percentage < 30) return COLORS.danger;
  if (percentage >= 80) return COLORS.success;
  return COLORS.warning;
};

const MinimalIndicator: React.FC<ProfileCompletionIndicatorProps> = ({
  completionPercentage,
  isComplete,
  missingCritical = [],
  onViewDetails
}) => {
  const hasCritical = missingCritical.length > 0;
  const statusInfo = getCompletionStatus(completionPercentage, isComplete, hasCritical);
  
  return (
    <Pressable onPress={onViewDetails} className="flex-row items-center">
      <Box className="w-8 h-2 bg-gray-200 rounded-full mr-2">
        <Box 
          className="h-full rounded-full"
          style={{ 
            width: `${Math.max(completionPercentage, 5)}%`,
            backgroundColor: getProgressBarColor(completionPercentage, hasCritical)
          }}
        />
      </Box>
      <Text className="text-sm text-gray-600 min-w-12">
        {Math.round(completionPercentage)}%
      </Text>
    </Pressable>
  );
};

const CompactIndicator: React.FC<ProfileCompletionIndicatorProps> = ({
  completionPercentage,
  isComplete,
  missingCritical = [],
  onViewDetails
}) => {
  const hasCritical = missingCritical.length > 0;
  const statusInfo = getCompletionStatus(completionPercentage, isComplete, hasCritical);
  
  return (
    <Pressable onPress={onViewDetails}>
      <HStack className="items-center" space="xs">
        <Icon 
          as={statusInfo.icon} 
          size="xs" 
          style={{ color: statusInfo.color }}
        />
        <VStack>
          <Text className="text-sm font-medium" style={{ color: statusInfo.color }}>
            {Math.round(completionPercentage)}%
          </Text>
          <Text className="text-xs text-gray-500">
            {statusInfo.label}
          </Text>
        </VStack>
      </HStack>
    </Pressable>
  );
};

const DetailedIndicator: React.FC<ProfileCompletionIndicatorProps> = ({
  completionPercentage,
  isComplete,
  missingCritical = [],
  missingOptional = [],
  recommendations = [],
  onViewDetails
}) => {
  const hasCritical = missingCritical.length > 0;
  const statusInfo = getCompletionStatus(completionPercentage, isComplete, hasCritical);
  
  const highPriorityRecommendations = recommendations.filter(r => r.priority === 'high');
  
  return (
    <Box 
      className="p-4 rounded-lg border"
      style={{ 
        backgroundColor: statusInfo.bgColor,
        borderColor: statusInfo.color 
      }}
    >
      <VStack space="sm">
        {/* Status Header */}
        <HStack className="items-center justify-between">
          <HStack className="items-center" space="xs">
            <Icon 
              as={statusInfo.icon} 
              size="sm" 
              style={{ color: statusInfo.color }}
            />
            <Text className="font-semibold" style={{ color: statusInfo.color }}>
              {statusInfo.label} - {Math.round(completionPercentage)}%
            </Text>
          </HStack>
          
          {onViewDetails && (
            <Pressable onPress={onViewDetails}>
              <Icon as={Info} size="sm" className="text-gray-500" />
            </Pressable>
          )}
        </HStack>

        {/* Progress Bar */}
        <Box className="w-full h-2 bg-gray-200 rounded-full">
          <Box 
            className="h-full rounded-full transition-all duration-300"
            style={{ 
              width: `${Math.max(completionPercentage, 2)}%`,
              backgroundColor: statusInfo.color
            }}
          />
        </Box>

        {/* Missing Fields Summary */}
        {(missingCritical.length > 0 || missingOptional.length > 0) && (
          <HStack className="flex-wrap" space="xs">
            {missingCritical.length > 0 && (
              <Badge variant="destructive" size="sm">
                {missingCritical.length} crítico{missingCritical.length > 1 ? 's' : ''}
              </Badge>
            )}
            {missingOptional.length > 0 && (
              <Badge variant="secondary" size="sm">
                {missingOptional.length} opcional{missingOptional.length > 1 ? 'is' : ''}
              </Badge>
            )}
          </HStack>
        )}

        {/* High Priority Recommendations */}
        {highPriorityRecommendations.length > 0 && (
          <VStack space="xs">
            <Text className="text-xs font-medium text-gray-700">
              Próximos passos:
            </Text>
            {highPriorityRecommendations.slice(0, 2).map((rec, index) => (
              <Text key={index} className="text-xs text-gray-600">
                • {rec.text}
              </Text>
            ))}
            {highPriorityRecommendations.length > 2 && (
              <Text className="text-xs text-gray-500">
                +{highPriorityRecommendations.length - 2} mais...
              </Text>
            )}
          </VStack>
        )}
      </VStack>
    </Box>
  );
};

export const ProfileCompletionIndicator: React.FC<ProfileCompletionIndicatorProps> = (props) => {
  const { variant = 'detailed', showDetails = true } = props;
  
  switch (variant) {
    case 'minimal':
      return <MinimalIndicator {...props} />;
    case 'compact':
      return <CompactIndicator {...props} />;
    case 'detailed':
    default:
      return <DetailedIndicator {...props} />;
  }
};

// Additional helper component for circular progress
interface CircularProgressProps {
  percentage: number;
  size?: number;
  strokeWidth?: number;
  color?: string;
  backgroundColor?: string;
  showPercentage?: boolean;
}

export const CircularProgress: React.FC<CircularProgressProps> = ({
  percentage,
  size = 40,
  strokeWidth = 4,
  color = COLORS.info,
  backgroundColor = COLORS.gray[300],
  showPercentage = true
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <Box className="relative" style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        className="transform -rotate-90"
      >
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={backgroundColor}
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-300 ease-in-out"
        />
      </svg>
      
      {showPercentage && (
        <Box className="absolute inset-0 flex items-center justify-center">
          <Text className="text-xs font-semibold text-gray-700">
            {Math.round(percentage)}%
          </Text>
        </Box>
      )}
    </Box>
  );
};

export default ProfileCompletionIndicator;