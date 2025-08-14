import React from 'react';

import { Box } from '@/components/ui/box';
import { Card } from '@/components/ui/card';
import { HStack } from '@/components/ui/hstack';
import { Skeleton } from '@/components/ui/skeleton';
import { VStack } from '@/components/ui/vstack';

interface StepLoadingSkeletonProps {
  variant?: 'form' | 'card' | 'list' | 'preview';
  animated?: boolean;
}

const FormSkeleton: React.FC<{ animated: boolean }> = ({ animated }) => (
  <VStack space="lg" className="p-6">
    {/* Form Header */}
    <VStack space="sm">
      <Skeleton className={`h-6 w-3/4 ${animated ? 'animate-pulse' : ''}`} />
      <Skeleton className={`h-4 w-full ${animated ? 'animate-pulse' : ''}`} />
    </VStack>

    {/* Form Fields */}
    <VStack space="md">
      {/* Input Field */}
      <VStack space="xs">
        <Skeleton className={`h-4 w-24 ${animated ? 'animate-pulse' : ''}`} />
        <Skeleton className={`h-10 w-full rounded-lg ${animated ? 'animate-pulse' : ''}`} />
      </VStack>

      {/* Text Area */}
      <VStack space="xs">
        <Skeleton className={`h-4 w-32 ${animated ? 'animate-pulse' : ''}`} />
        <Skeleton className={`h-24 w-full rounded-lg ${animated ? 'animate-pulse' : ''}`} />
      </VStack>

      {/* Two Column Fields */}
      <HStack space="md">
        <VStack space="xs" className="flex-1">
          <Skeleton className={`h-4 w-20 ${animated ? 'animate-pulse' : ''}`} />
          <Skeleton className={`h-10 w-full rounded-lg ${animated ? 'animate-pulse' : ''}`} />
        </VStack>
        <VStack space="xs" className="flex-1">
          <Skeleton className={`h-4 w-16 ${animated ? 'animate-pulse' : ''}`} />
          <Skeleton className={`h-10 w-full rounded-lg ${animated ? 'animate-pulse' : ''}`} />
        </VStack>
      </HStack>

      {/* Select Field */}
      <VStack space="xs">
        <Skeleton className={`h-4 w-28 ${animated ? 'animate-pulse' : ''}`} />
        <Skeleton className={`h-10 w-full rounded-lg ${animated ? 'animate-pulse' : ''}`} />
      </VStack>
    </VStack>

    {/* Action Buttons */}
    <HStack space="sm" className="justify-end pt-4">
      <Skeleton className={`h-10 w-24 rounded-lg ${animated ? 'animate-pulse' : ''}`} />
      <Skeleton className={`h-10 w-32 rounded-lg ${animated ? 'animate-pulse' : ''}`} />
    </HStack>
  </VStack>
);

const CardSkeleton: React.FC<{ animated: boolean }> = ({ animated }) => (
  <Box className="p-6">
    <VStack space="lg">
      {Array.from({ length: 3 }).map((_, index) => (
        <Card key={index} className="p-4">
          <VStack space="sm">
            <HStack space="sm" className="items-center">
              <Skeleton className={`h-10 w-10 rounded-full ${animated ? 'animate-pulse' : ''}`} />
              <VStack space="xs" className="flex-1">
                <Skeleton className={`h-4 w-3/4 ${animated ? 'animate-pulse' : ''}`} />
                <Skeleton className={`h-3 w-1/2 ${animated ? 'animate-pulse' : ''}`} />
              </VStack>
            </HStack>
            <Skeleton className={`h-16 w-full rounded ${animated ? 'animate-pulse' : ''}`} />
          </VStack>
        </Card>
      ))}
    </VStack>
  </Box>
);

const ListSkeleton: React.FC<{ animated: boolean }> = ({ animated }) => (
  <VStack space="sm" className="p-6">
    {Array.from({ length: 5 }).map((_, index) => (
      <HStack key={index} space="sm" className="items-center p-3 bg-white rounded-lg">
        <Skeleton className={`h-8 w-8 rounded-full ${animated ? 'animate-pulse' : ''}`} />
        <VStack space="xs" className="flex-1">
          <Skeleton className={`h-4 w-full ${animated ? 'animate-pulse' : ''}`} />
          <Skeleton className={`h-3 w-2/3 ${animated ? 'animate-pulse' : ''}`} />
        </VStack>
        <Skeleton className={`h-6 w-16 rounded ${animated ? 'animate-pulse' : ''}`} />
      </HStack>
    ))}
  </VStack>
);

const PreviewSkeleton: React.FC<{ animated: boolean }> = ({ animated }) => (
  <VStack space="lg" className="p-6">
    {/* Header Section */}
    <Card className="p-6">
      <HStack space="md" className="items-center">
        <Skeleton className={`h-20 w-20 rounded-full ${animated ? 'animate-pulse' : ''}`} />
        <VStack space="sm" className="flex-1">
          <Skeleton className={`h-6 w-3/4 ${animated ? 'animate-pulse' : ''}`} />
          <Skeleton className={`h-4 w-1/2 ${animated ? 'animate-pulse' : ''}`} />
          <HStack space="xs">
            <Skeleton className={`h-6 w-16 rounded-full ${animated ? 'animate-pulse' : ''}`} />
            <Skeleton className={`h-6 w-20 rounded-full ${animated ? 'animate-pulse' : ''}`} />
          </HStack>
        </VStack>
      </HStack>
    </Card>

    {/* Content Sections */}
    <VStack space="md">
      {Array.from({ length: 3 }).map((_, index) => (
        <Card key={index} className="p-4">
          <VStack space="sm">
            <Skeleton className={`h-5 w-32 ${animated ? 'animate-pulse' : ''}`} />
            <Skeleton className={`h-4 w-full ${animated ? 'animate-pulse' : ''}`} />
            <Skeleton className={`h-4 w-5/6 ${animated ? 'animate-pulse' : ''}`} />
            <Skeleton className={`h-4 w-4/5 ${animated ? 'animate-pulse' : ''}`} />
          </VStack>
        </Card>
      ))}
    </VStack>

    {/* Stats Section */}
    <Card className="p-4">
      <HStack space="md" className="justify-around">
        {Array.from({ length: 4 }).map((_, index) => (
          <VStack key={index} space="xs" className="items-center">
            <Skeleton className={`h-8 w-12 ${animated ? 'animate-pulse' : ''}`} />
            <Skeleton className={`h-3 w-16 ${animated ? 'animate-pulse' : ''}`} />
          </VStack>
        ))}
      </HStack>
    </Card>
  </VStack>
);

export const StepLoadingSkeleton: React.FC<StepLoadingSkeletonProps> = ({
  variant = 'form',
  animated = true,
}) => {
  const renderSkeleton = () => {
    switch (variant) {
      case 'form':
        return <FormSkeleton animated={animated} />;
      case 'card':
        return <CardSkeleton animated={animated} />;
      case 'list':
        return <ListSkeleton animated={animated} />;
      case 'preview':
        return <PreviewSkeleton animated={animated} />;
      default:
        return <FormSkeleton animated={animated} />;
    }
  };

  return <Box className="flex-1 bg-gray-50">{renderSkeleton()}</Box>;
};

export default StepLoadingSkeleton;
